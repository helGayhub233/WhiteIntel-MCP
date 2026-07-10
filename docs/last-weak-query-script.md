# Last Weak Query Script Usage Guide

> Source: Internal script documentation
> date: 2026-07-10

This document describes the standalone lightweight script `threat-intel-monitor/scripts/query_last_weak_single.py`. The script follows the API conventions in the project's `docs` directory and the existing implementation in `threat-intel-monitor/scripts/query_last_weak.py`, but remains a single file with zero project-internal dependencies for easy standalone execution.

The script is designed with a "minimal parameters, out-of-the-box" approach. Typically, only a domain name is required; other parameters automatically use default values when not provided. Passwords are displayed in plaintext by default.

## Script Location

```text
threat-intel-monitor/scripts/query_last_weak_single.py
```

## Capabilities

- Supports single or multiple domain inputs
- Supports `--query-time` to specify the query time window
- Supports `txt/csv` domain file input
- Built-in sequential QPS control, default `0.2 QPS`
- Automatic delayed retry on timeout, `429`, `5xx`, rate limiting, or upstream error prompts
- Supports stdout or CSV file output
- Displays plaintext passwords by default; passwords are hidden only when `--mask-passwords` is explicitly specified

## API Defaults

- Base URL: `https://api.whiteintel.io`
- Endpoint: `/get_last_weak.php`
- API Key source:
  - Priority: command-line `--apikey`
  - Fallback: environment variable `WHITEINTEL_API_KEY`

## Requirements

The script only depends on the Python standard library. Python 3.9+ is recommended.

## Basic Usage

First, set the environment variable:

```bash
export WHITEINTEL_API_KEY="your_api_key"
```

Simplest usage, only passing a domain:

```bash
python threat-intel-monitor/scripts/query_last_weak_single.py \
  example.com
```

This automatically uses default values:

- Query time: `1` day
- `QPS=0.2`
- Timeout: `30` seconds
- Max retries: `3`
- Max pages to fetch: `1`
- Plaintext passwords displayed by default

Query a single domain, manually specifying query time:

```bash
python threat-intel-monitor/scripts/query_last_weak_single.py \
  --domain example.com \
  --query-time 1
```

Pass multiple domains using positional arguments:

```bash
python threat-intel-monitor/scripts/query_last_weak_single.py \
  example.com test.com \
  --query-time 3
```

Specify multiple `--domain` flags simultaneously:

```bash
python threat-intel-monitor/scripts/query_last_weak_single.py \
  --domain example.com \
  --domain foo.example.com \
  --query-time 7
```

Read domains from a file:

```bash
python threat-intel-monitor/scripts/query_last_weak_single.py \
  --domains-file threat-intel-monitor/config/domains.csv \
  --query-time 1
```

Write results to a file:

```bash
python threat-intel-monitor/scripts/query_last_weak_single.py \
  --domain example.com \
  --query-time 1 \
  --output /tmp/last_weak_example.csv
```

## Common Parameters

| Parameter | Description | Default |
|---|---|---|
| `--domain` | Domain, can be repeated or comma-separated | None |
| `domains` | Positional argument domain list | None |
| `--domains-file` | Domain file, supports `txt/csv` | None |
| `--query-time` / `--days` | Query time window (days), range `1-30` | `1` |
| `--limit` | Records per page, range `1-5000` | `500` |
| `--max-pages` | Max pages to fetch per domain | `1` |
| `--qps` | Requests per second | `0.2 QPS` |
| `--timeout` | Single request timeout in seconds | `30` |
| `--max-retries` | Max retries per page | `3` |
| `--retry-wait` | Initial retry wait in seconds | `10` |
| `--backoff` | Backoff multiplier | `2` |
| `--base-url` | API base URL | `https://api.whiteintel.io` |
| `--endpoint` | API endpoint path | `/get_last_weak.php` |
| `--apikey` | Manually pass API Key | None |
| `--mask-passwords` | Hide passwords (sends `mask_password=1`) | Off |
| `--output` | Output CSV file path | stdout |

## File Input Format

### Text File

Supports the following forms:

```text
example.com
foo.example.com
# Comment lines are ignored
bar.example.com baz.example.com
```

### CSV File

For CSV, at minimum include a `domain` column, with an optional `enabled` column:

```csv
domain,enabled
example.com,true
foo.example.com,true
disabled.example.com,false
```

When `enabled` is `false/no/0/n`, the domain is skipped.

## QPS and Retry Logic

The script processes requests sequentially (no concurrency).

- `--qps 0.2` means at most 1 request per 5 seconds
- Rate limiting is checked before each request
- Automatic delayed retry occurs in these situations:
  - Network timeout
  - `HTTP 408/429/500/502/503/504`
  - Response body contains keywords such as `timeout`, `rate limit`, `upstream request failed`
- If the response headers contain `Retry-After`, that value is used for the wait
- Otherwise, exponential backoff is used:
  - 1st retry waits `retry_wait`
  - 2nd retry waits `retry_wait * backoff`
  - 3rd retry waits `retry_wait * backoff^2`

Example:

```bash
python threat-intel-monitor/scripts/query_last_weak_single.py \
  --domain example.com \
  --query-time 1 \
  --qps 0.2 \
  --timeout 20 \
  --max-retries 3 \
  --retry-wait 10 \
  --backoff 2
```

## Output Structure

The script outputs CSV. Each `results` record from the API is expanded into one row. If a domain query fails and has no results, an additional error summary row is preserved.

Example:

```csv
domain,status,raw_count,pages_fetched,page,http_status,remaining_daily_calls,url,username,password,log_date,error,attempts
example.com,SUCCESS,2,1,1,200,88,https://portal.example.com,alice@example.com,123456,2026-05-25 10:00:00,,
example.com,SUCCESS,2,1,1,200,88,https://mail.example.com,bob@example.com,abcdef,2026-05-25 11:00:00,,
failed.example.com,FAILED,0,0,1,,,,,,,"Upstream request timed out.",4
```

Key fields:

- `domain`: Queried domain
- `status`: Domain query status, can be `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`
- `raw_count`: Total raw result count for this domain
- `pages_fetched`: Number of pages actually fetched successfully
- `page`: Current record's page number; failure summary rows also include the failed page number when possible
- `http_status`: HTTP status code for this page
- `remaining_daily_calls`: Remaining quota returned by the API
- `error`: Error information in failure summary rows; usually empty for success rows
- `attempts`: Final attempt count in failure summary rows
- `password`: Plaintext password displayed by default; hidden by the API when `--mask-passwords` is used

In addition to the above fixed fields, the script also expands the raw fields from the API `results` into the CSV, for example:

- `url`
- `username`
- `password`
- `log_date`
- And other result fields returned by the API

## Exit Codes

- Exit code `0`: All domain queries succeeded
- Exit code `2`: Failures or partial successes exist
- Parameter validation failures or missing API Key cause an immediate exit with an error message

## Recommended Usage

- For initial testing, use a single domain + `--query-time 1`
- For minimum input, run `python ... query_last_weak_single.py example.com`
- If the target API enforces strict QPS, keep the default `--qps 0.2`
- For bulk domain queries, use `--domains-file`
- For connectivity verification, keep the default `--max-pages 1`
- For sensitive data, explicitly add `--mask-passwords`
- For Excel or BI tool use, specify `--output xxx.csv`

## Help Command

```bash
python threat-intel-monitor/scripts/query_last_weak_single.py --help
```
