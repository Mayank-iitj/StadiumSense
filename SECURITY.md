# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅        |

## Security Features

### Rate Limiting
All AI-powered endpoints enforce per-IP rate limits to prevent abuse:

| Endpoint | Limit |
|---|---|
| `POST /api/ask` | 10 requests/minute |
| `POST /api/route` | 15 requests/minute |
| `POST /api/request-help` | 5 requests/minute |

### Input Validation
All request bodies are validated via Pydantic with strict field constraints (`min_length`, `max_length`). Invalid input returns HTTP 422.

### CORS Policy
CORS is restricted to `http://localhost:5173` and `http://localhost:8000` in development. In production, configure the `ALLOWED_ORIGINS` environment variable.

### API Key Security
- The `ANTHROPIC_API_KEY` is loaded from environment variables only — never hardcoded
- The `.env` file is excluded from version control via `.gitignore`
- Use `.env.example` as a template

### No PII Collection
StadiumSense does not collect or store any personally identifiable information. Help requests are ephemeral in-memory only and are not persisted to disk.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by opening a GitHub issue marked `[SECURITY]` or contact the maintainer directly. Do not disclose vulnerabilities publicly until they have been addressed.
