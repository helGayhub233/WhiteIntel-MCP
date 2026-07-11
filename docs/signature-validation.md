# Signature Validation

> Source: https://docs.whiteintel.io/whiteintel-api-doc/webhooks/signature-validation
> date: 2025-07-10

To ensure the authenticity of incoming webhook requests from WhiteIntel, you **must verify the HMAC signature** of each request.

Each request includes these headers:

| Header | Description |
|---|---|
| `X-Signature` | Base64-encoded HMAC SHA256 digest. |
| `X-Signature-Version` | Currently always `v1`. |
| `X-Timestamp` | ISO 8601 UTC timestamp. |
| `User-Agent` | Always `WhiteIntel-Webhook`. |

---

## Validation Logic

You must:

1. Compute HMAC SHA256 with your secret key using the `X-Timestamp` value as the message.
2. Base64 encode the result.
3. Compare with the `X-Signature` header securely (constant-time comparison).

---

## Important Notes

- Use constant-time comparison (e.g. `hash_equals` in PHP, `hmac.compare_digest` in Python, `timingSafeEqual` in Node.js) to avoid timing attacks.
- Optionally reject if `X-Timestamp` is too old (recommended: ±5 minutes).
- Event `description` values are static based on the match types and will never change unless officially announced.

---

## Example: PHP

```php
<?php
$timestamp = $_SERVER["HTTP_X_TIMESTAMP"];
$providedSignature = $_SERVER["HTTP_X_SIGNATURE"];
$secret = "your_hmac_secret"; // Replace with your actual secret

// Step 1: Validate timestamp freshness (±5 minutes)
$receivedTime = strtotime($timestamp);
$now = time();
$skew = 300; // 5 minutes

if (!$receivedTime || abs($now - $receivedTime) > $skew) {
    http_response_code(400);
    exit("Invalid or expired timestamp");
}

// Step 2: Generate expected signature
$expectedSignature = base64_encode(hash_hmac("sha256", $timestamp, $secret, true));

// Step 3: Secure signature comparison
if (!hash_equals($expectedSignature, $providedSignature)) {
    http_response_code(403);
    exit("Invalid signature");
}

// ✅ Signature is valid — proceed with processing
?>
```

---

## Example: Node.js (Express)

```javascript
const express = require("express");
const crypto = require("crypto");

const app = express();
const SECRET = "your_hmac_secret";
const MAX_SKEW_MS = 5 * 60 * 1000; // 5 minutes

app.use(express.json());

app.post("/webhook", (req, res) => {
  const timestamp = req.header("X-Timestamp");
  const receivedSignature = req.header("X-Signature");

  // 1. Validate timestamp
  const ts = Date.parse(timestamp);
  if (isNaN(ts)) {
    return res.status(400).send("Invalid timestamp");
  }

  const now = Date.now();
  if (Math.abs(now - ts) > MAX_SKEW_MS) {
    return res.status(400).send("Timestamp too old or in future");
  }

  // 2. Compute expected signature: base64(HMAC_SHA256(timestamp, secret))
  const expectedSignature = crypto
    .createHmac("sha256", SECRET)
    .update(timestamp, "utf8")
    .digest("base64");

  // 3. Compare using constant-time method
  const isValid = crypto.timingSafeEqual(
    Buffer.from(expectedSignature),
    Buffer.from(receivedSignature)
  );

  if (!isValid) {
    return res.status(403).send("Invalid signature");
  }

  res.status(200).send("Webhook verified");
});

app.listen(3000, () => {
  console.log("Webhook listener running on port 3000");
});
```

---

## Example: Python (Flask)

```python
import hmac
import hashlib
import base64
from flask import Flask, request, abort
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

SECRET = b"your_hmac_secret"
MAX_SKEW = timedelta(minutes=5)

@app.route("/webhook", methods=["POST"])
def webhook():
    # 1. Read headers
    timestamp = request.headers.get("X-Timestamp")
    signature = request.headers.get("X-Signature")

    if not timestamp or not signature:
        abort(400, "Missing required headers")

    # 2. Parse and validate timestamp freshness
    try:
        if "Z" in timestamp:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif "+" not in timestamp and "-" not in timestamp[10:]:
            ts = datetime.fromisoformat(timestamp + "+00:00")
        else:
            ts = datetime.fromisoformat(timestamp)

        now = datetime.now(timezone.utc)
        if abs(now - ts) > MAX_SKEW:
            abort(400, "Timestamp too old or in future")
    except Exception:
        abort(400, "Invalid timestamp format")

    # 3. Compute expected HMAC signature (base64-encoded)
    expected = base64.b64encode(
        hmac.new(SECRET, timestamp.encode(), hashlib.sha256).digest()
    ).decode()

    # 4. Constant-time comparison to avoid timing attacks
    if not hmac.compare_digest(expected, signature):
        abort(403, "Invalid signature")

    return "Webhook verified", 200
```

---

## Example: Java (Spring Boot)

```java
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.Base64;

@RestController
public class WebhookController {

    private static final String SECRET = "your_hmac_secret";
    private static final Duration MAX_SKEW = Duration.ofMinutes(5);

    @PostMapping("/webhook")
    public ResponseEntity<String> receiveWebhook(
            @RequestHeader("X-Timestamp") String timestamp,
            @RequestHeader("X-Signature") String signature) {

        // 1. Validate timestamp freshness
        try {
            Instant ts = Instant.parse(timestamp);
            Instant now = Instant.now();
            if (Duration.between(ts, now).abs().compareTo(MAX_SKEW) > 0) {
                return ResponseEntity.status(400).body("Timestamp too old or in future");
            }
        } catch (DateTimeParseException e) {
            return ResponseEntity.status(400).body("Invalid timestamp format");
        }

        // 2. Generate expected signature using timestamp only
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(SECRET.getBytes(), "HmacSHA256"));
            byte[] hmac = mac.doFinal(timestamp.getBytes());
            String expected = Base64.getEncoder().encodeToString(hmac);

            // 3. Securely compare
            if (!MessageDigest.isEqual(expected.getBytes(), signature.getBytes())) {
                return ResponseEntity.status(403).body("Invalid signature");
            }
        } catch (Exception e) {
            return ResponseEntity.status(500).body("Server error during verification");
        }

        return ResponseEntity.ok("Webhook received and verified");
    }
}
```

---

## Example: .NET Core (C#)

```csharp
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Primitives;
using System;
using System.Security.Cryptography;
using System.Text;

[ApiController]
[Route("webhook")]
public class WebhookController : ControllerBase
{
    private const string SecretKey = "your_hmac_secret";
    private static readonly TimeSpan MaxSkew = TimeSpan.FromMinutes(5);

    [HttpPost]
    public IActionResult ReceiveWebhook()
    {
        if (!Request.Headers.TryGetValue("X-Timestamp", out StringValues timestampHeader) ||
            !Request.Headers.TryGetValue("X-Signature", out StringValues signatureHeader))
        {
            return BadRequest("Missing headers");
        }

        string timestamp = timestampHeader.ToString();
        string providedSignature = signatureHeader.ToString();

        // Validate timestamp freshness
        if (!DateTimeOffset.TryParse(timestamp, out DateTimeOffset parsedTimestamp))
            return BadRequest("Invalid timestamp format");

        var now = DateTimeOffset.UtcNow;
        if (Math.Abs((now - parsedTimestamp).TotalMinutes) > MaxSkew.TotalMinutes)
            return BadRequest("Timestamp too old or too far in the future");

        // Generate signature using timestamp only
        byte[] keyBytes = Encoding.UTF8.GetBytes(SecretKey);
        byte[] messageBytes = Encoding.UTF8.GetBytes(timestamp);

        using var hmac = new HMACSHA256(keyBytes);
        byte[] hash = hmac.ComputeHash(messageBytes);
        string expectedSignature = Convert.ToBase64String(hash);

        // Constant-time comparison
        if (!CryptographicOperations.FixedTimeEquals(
                Encoding.UTF8.GetBytes(expectedSignature),
                Encoding.UTF8.GetBytes(providedSignature)))
        {
            return StatusCode(403, "Invalid signature");
        }

        return Ok("Webhook verified");
    }
}
```

---

## Example: Ruby (Sinatra)

```ruby
require "sinatra"
require "openssl"
require "base64"
require "time"

SECRET = "your_hmac_secret"
MAX_SKEW_SECONDS = 300  # 5 minutes

post "/webhook" do
  timestamp = request.env["HTTP_X_TIMESTAMP"]
  signature = request.env["HTTP_X_SIGNATURE"]

  # Validate timestamp
  begin
    received_time = Time.iso8601(timestamp)
    if (Time.now - received_time).abs > MAX_SKEW_SECONDS
      halt 400, "Invalid or expired timestamp"
    end
  rescue ArgumentError
    halt 400, "Invalid timestamp format"
  end

  # Validate HMAC signature
  expected = Base64.strict_encode64(
    OpenSSL::HMAC.digest("sha256", SECRET, timestamp)
  )

  unless Rack::Utils.secure_compare(expected, signature)
    halt 403, "Invalid signature"
  end

  status 200
  "Webhook verified"
end
```

---

## Support

For technical questions or integration assistance, contact `info@whiteintel.io`.
