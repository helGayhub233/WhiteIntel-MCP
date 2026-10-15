# Authentication

> Source: https://docs.whiteintel.io/whiteintel-api-doc/overview/authentication
> date: 2026-10-15

In order to obtain your API Key, visit your Organizations page or Profile page on the Whiteintel platform.

Authentication is performed by passing the key in the JSON request body under the `apikey` field. Requests without a valid API key return `403 Forbidden`.

```json
{
  "apikey": "YOUR_API_KEY"
}
```

See the individual endpoint pages in this directory for the access requirements that apply to each API.
