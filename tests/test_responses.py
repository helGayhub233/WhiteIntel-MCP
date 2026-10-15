from __future__ import annotations

import json
import unittest

from jsonschema import Draft202012Validator

from whiteintel_mcp.models.responses import WhiteIntelResponse
from whiteintel_mcp.responses import MAX_OUTPUT_BYTES, bounded_response_payload, tool_result


class ResponseTests(unittest.TestCase):
    def assert_public(self, result):
        self.assertEqual(json.loads(result.content[0].text), result.structured_content)
        self.assertLessEqual(len(result.content[0].text.encode("utf-8")), MAX_OUTPUT_BYTES)
        Draft202012Validator(WhiteIntelResponse.model_json_schema()).validate(result.structured_content)
        return result.structured_content

    def test_documented_record_shapes_are_counted(self):
        shapes = (
            ({"results": [{"id": 1}]}, 1),
            ({"data": {"results": [1, 2]}}, 2),
            ({"suppliers": [{"id": 1}]}, 1),
            ({"logs": [{"id": 1}]}, 1),
            ({"results": {"11": {"id": 11}, "12": {"id": 12}}}, 2),
            ({"results": {"compromised_credentials": [{"id": 1}, {"id": 2}]}}, 1),
            ({"results": {"computer_count": 1843}}, 0),
            ({"results": []}, 0),
        )
        for shape, count in shapes:
            with self.subTest(shape=shape):
                payload = bounded_response_payload({"success": True, "http_status": 200, **shape}, {})
                self.assertEqual(payload["returned_count"], count)

    def test_top_level_results_at_last_page_stop(self):
        payload = bounded_response_payload(
            {"success": True, "http_status": 200, "results": [1], "total": 1}, {"limit": 1}
        )
        self.assertEqual((payload["returned_count"], payload["completeness"], payload["next_action"]),
                         (1, "complete", "stop"))

    def test_conflicting_metadata_never_claims_complete(self):
        cases = (
            {"results": [1], "total": 100, "has_more": False},
            {"results": [1], "total": 1, "has_more": True},
            {"results": [1], "total": 1, "meta": {"total": 100}},
            {"results": [1], "has_more": False, "meta": {"has_more": True}},
        )
        for body in cases:
            with self.subTest(body=body):
                payload = bounded_response_payload({"success": True, "http_status": 200, **body}, {"limit": 100})
                self.assertEqual(payload["completeness"], "unknown")
                self.assertEqual(payload["next_action"], "unknown")

    def test_unknown_page_size_does_not_guess_offset(self):
        payload = bounded_response_payload({"success": True, "http_status": 200, "logs": [1], "total": 3}, {"page": 3})
        self.assertEqual(payload["completeness"], "unknown")
        payload = bounded_response_payload({"success": True, "http_status": 200, "logs": [1], "total": 3, "per_page": 1}, {"page": 3})
        self.assertEqual(payload["completeness"], "complete")

    def test_multibyte_large_page_keeps_prefix_and_requires_refinement(self):
        records = [{"id": i, "summary": "情报" * 8192} for i in range(100)]
        original = {"success": True, "http_status": 200, "results": records, "total": 200}
        result = self.assert_public(tool_result(bounded_response_payload(original, {"limit": 100})))
        retained = len(result["results"])
        self.assertGreater(retained, 0)
        self.assertLess(retained, 100)
        self.assertEqual([row["id"] for row in result["results"]], list(range(retained)))
        self.assertEqual(result["returned_count"], retained)
        self.assertEqual(result["output"]["omitted_records"], 100 - retained)
        self.assertEqual(result["output"]["truncated_fields"], 100)
        self.assertEqual(result["next_action"], "refine_query")
        self.assertEqual(len(original["results"]), 100)
        self.assertEqual(len(original["results"][0]["summary"]), 16384)

    def test_clipped_field_requires_refinement_even_without_omitted_rows(self):
        result = self.assert_public(tool_result(bounded_response_payload({
            "success": True, "http_status": 200, "results": [{"summary": "x" * 8192}], "total": 1,
        }, {"limit": 1})))
        self.assertEqual(result["returned_count"], 1)
        self.assertLessEqual(len(result["results"][0]["summary"]), 4096)
        self.assertEqual(result["output"]["omitted_records"], 0)
        self.assertEqual(result["next_action"], "refine_query")

    def test_huge_id_mapping_keeps_an_ordered_prefix(self):
        rows = {str(i): {"summary": "x" * 8192} for i in range(100)}
        result = self.assert_public(tool_result(bounded_response_payload({
            "success": True, "http_status": 200, "results": rows,
        }, {})))
        self.assertEqual(list(result["results"]), list(rows)[:result["returned_count"]])
        self.assertEqual(result["output"]["omitted_records"], 100 - result["returned_count"])

    def test_non_record_objects_and_error_details_obey_budget(self):
        for payload in (
            {"success": True, "http_status": 200, "results": {str(i): "x" * 1000 for i in range(300)}},
            {"success": False, "http_status": 400, "error": {"code": "INVALID_REQUEST", "message": "x" * 100000,
                "validation_errors": [{"loc": ["query"], "message": "x" * 1000} for _ in range(300)]}},
        ):
            with self.subTest(success=payload["success"]):
                call = tool_result(payload)
                result = self.assert_public(call)
                self.assertTrue(result["truncated"])
                self.assertEqual(call.is_error, not payload["success"])
                self.assertEqual(result["next_action"], "refine_query" if payload["success"] else "stop")


if __name__ == "__main__":
    unittest.main()
