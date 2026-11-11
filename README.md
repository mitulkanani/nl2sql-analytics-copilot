# Natural Language to SQL Analytics Copilot

A safety-first analytics assistant that converts business questions into SQL, validates generated queries against an approved schema, executes them with read-only protections, and returns results with an explanation and a chart suggestion.

The project includes a deterministic mock provider so it can be demoed without API credentials, plus an optional OpenAI provider that uses structured JSON output.

## Highlights

- Ask questions in plain English and receive a SQL query, explanation, and result set.
- Approved schema catalog for `customers`, `products`, `orders`, and `order_items`.
- AST-based SQL validation with SQLGlot when installed.
- SQLite database opened with `mode=ro`, `PRAGMA query_only`, and a SQLite authorizer that permits only read operations on approved tables.
- Blocks multi-statement SQL, writes, DDL, pragmas, attached databases, SQL comments, unknown tables, and dangerous SQLite functions.
- Enforces a maximum result size and execution timeout.
- Query history stored separately from the read-only analytics database.
- Lightweight responsive dashboard served directly by FastAPI; no frontend build step required.
- Docker Compose, CI workflow, CLI, and API documentation.

> **Scope note:** this is a single-workspace demo over a synthetic SQLite commerce dataset. It is not yet a secure multi-tenant BI platform. For production, use a dedicated read-only database account, tenant-aware row-level security, per-user authorization, query cost controls, and a managed database such as PostgreSQL or a warehouse.

## Architecture

```text
Browser / CLI
     |
     v
 FastAPI API ---- Query history (separate SQLite file)
     |
     v
 Query service
     |
     +---- Mock provider (demo / CI)
     |
     +---- OpenAI provider (structured JSON output)
     |
     v
 SQL policy layer (SQLGlot AST + approved catalog)
     |
     v
 SQLite read-only executor
     |   - mode=ro
     |   - query_only
     |   - authorizer allowlist
     |   - timeout and row limit
     v
 Synthetic analytics dataset
```

## Quick start

Python 3.11+ is recommended.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1

python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open:

- Dashboard: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/api/health

The first startup creates `data/analytics.db` with synthetic customers, products, orders, and order items. It also creates a separate `data/query_history.db` for query history.

## Example questions

- Show monthly revenue trend.
- Which products have the highest revenue?
- Compare sales by region.
- How many orders are in each status?
- Which customers generated the most revenue?

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Provider and database health |
| `GET` | `/api/schema` | Return approved tables and columns |
| `POST` | `/api/query` | Generate, validate, and execute a natural-language query |
| `GET` | `/api/history?limit=20` | Recent query history |
| `GET` | `/docs` | Interactive OpenAPI documentation |

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/query \\
  -H "Content-Type: application/json" \\
  -d '{"question":"Show monthly revenue trend"}'
```

## Provider configuration

The default is `AI_PROVIDER=mock`. This uses deterministic query templates for common demo questions and requires no API key.

To use OpenAI:

```bash
python -m pip install -e ".[dev,openai]"
cp .env.example .env
```

Set the following values in `.env`:

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
```

The OpenAI adapter requests a strict structured response containing SQL, an explanation, and chart metadata. The model does not receive a database connection or tool execution capability. Every returned query is independently validated before execution. OpenAI structured outputs documentation: https://developers.openai.com/api/docs/guides/structured-outputs

## Security model

1. The model is asked to use only the schema catalog and generate a single read-only query.
2. SQLGlot parses the query and checks the statement type, referenced tables, columns, and disallowed functions.
3. If SQLGlot is unavailable, a conservative fallback checks statement shape and tables; the database authorizer remains the final enforcement layer. Install the declared dependencies for the full AST validation path.
4. The analytics database is opened using SQLite's read-only URI mode.
5. `PRAGMA query_only` and an SQLite authorizer deny writes, DDL, metadata reads, unapproved tables, and dangerous functions.
6. A progress handler interrupts queries that exceed the configured time budget.
7. Results are capped at `MAX_ROWS` (default 100), and query history is stored in a separate database.

This is defense in depth, not a guarantee that generated SQL is correct or that a production data warehouse is safe by default. For PostgreSQL, also create a dedicated role with only `CONNECT`, schema `USAGE`, and `SELECT` grants on explicitly approved views/tables; do not rely on application-side parsing alone.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Dashboard: http://localhost:8000/

## Tests

```bash
pytest
```

Tests use temporary SQLite databases and the deterministic mock provider. CI installs SQLGlot and exercises the AST validation path as part of the declared base dependencies.

## Project structure

```text
app/
  api/routes.py             # FastAPI endpoints
  catalog.py                # Approved schema and prompt description
  config.py                 # Environment settings
  executor.py               # Read-only SQLite execution and timeout
  history.py                # Query history database
  main.py                   # FastAPI application and dashboard serving
  models.py                 # Pydantic request/response models
  safety.py                 # SQL validation policy
  seed.py                   # Synthetic dataset initialization
  service.py                # Query orchestration
  providers/
    mock.py                 # Deterministic demo provider
    openai_provider.py      # Optional OpenAI structured-output adapter
app/static/
  index.html
  assets/app.js
  assets/styles.css
scripts/
tests/
```

## Roadmap

- [ ] PostgreSQL and Snowflake/BigQuery connectors using dedicated read-only roles.
- [ ] Authentication, workspace isolation, and row-level security.
- [ ] Semantic schema descriptions and business metric definitions.
- [ ] Query clarification flow when a question is ambiguous.
- [ ] SQL query plans, cost estimation, and warehouse-specific limits.
- [ ] Saved dashboards, chart configuration, and scheduled reports.
- [ ] Query evaluation dataset with accuracy and execution success metrics.
- [ ] Audit retention, rate limits, and per-user query budgets.

## License

MIT. See [LICENSE](LICENSE).
