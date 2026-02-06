# Copilot Instructions for purrrr

## Project Overview

**purrrr** is a dual-mode audit log analyzer for Microsoft 365:
- **CLI mode**: Analyzes Purview audit logs (CSV exports) for SharePoint/OneDrive file operations, Exchange activity, and suspicious patterns
- **Web mode**: Flask-based interface for the same analysis with file uploads and session management

**Core value**: Security intelligence via comprehensive audit log filtering, user mapping, IP analysis, and anomaly detection.

## Architecture Patterns

### Modular Analyzer Design

All analysis modules inherit from `AuditAnalyzer` base class (defined in [src/purrrr/tools.py](src/purrrr/tools.py)):
- `FileOperations` ([src/purrrr/files/file_ops.py](src/purrrr/files/file_ops.py)) — file/SharePoint operations
- `ExchangeOperations` ([src/purrrr/exchange/exchange_ops.py](src/purrrr/exchange/exchange_ops.py)) — email activity
- `EntraSignInOperations` ([src/purrrr/entra/entra_ops.py](src/purrrr/entra/entra_ops.py)) — sign-in logs
- `NetworkOperations` ([src/purrrr/network/network_ops.py](src/purrrr/network/network_ops.py)) — IP/geolocation analysis
- `UserActions` ([src/purrrr/users/user_actions.py](src/purrrr/users/user_actions.py)) — user-centric views

**Key dependency**: Each analyzer receives `config: AuditConfig`, `out: OutputFormatter`, and `logger` in constructor. **Never instantiate these directly in analyzers** — they're injected in [main.py](src/purrrr/main.py#L32-L37).

### Data Flow

1. CSV import → pandas DataFrame
2. Apply `AuditConfig` filters (excluded file types, SharePoint paths, actions)
3. Pass filtered data to specialized analyzers
4. Format output via `OutputFormatter` or `JSONOutputFormatter` based on `--text` flag
5. Print or export (CSV for Exchange, JSON for CLI, HTML for web)

### Configuration System

`AuditConfig` ([src/purrrr/tools.py](src/purrrr/tools.py#L27-L74)) centralizes settings:
- **Domain mappings**: `sharepoint_domains`, `email_domain` (inferred from audit log when absent)
- **Exclusions**: `excluded_file_types`, `excluded_sharepoint_paths`, `excluded_actions`
- **User mapping**: `user_mapping` dict (populated from `--user-map` CSV)
- **Output limits**: `max_users`, `max_files` (top N results)
- **Exchange/Entra field configs**: Define which fields to extract and skip criteria

**Pattern**: All analyzers read config dynamically — modifications to `config` object propagate to all analyzers without re-instantiation.

## Key Workflows

### CLI Analysis (main.py)

```bash
python -m purrrr.main audit_log.csv --user alice@company.com --start-date 2024-01-01 --full-urls --text
```

Execution flow:
1. [parse_arguments()](src/purrrr/main.py#L42-L155) builds arg namespace
2. Load CSV with pandas, infer column types
3. Initialize `AuditConfig()`, instantiate all analyzers
4. Call analyzer methods matching user intent (`get_user_activity()`, `analyze_suspicious_patterns()`, etc.)
5. `OutputFormatter` or `JSONOutputFormatter` handles formatting
6. Print to stdout or export to CSV

**Key pattern**: Args like `--actions`, `--user`, `--ips` filter the DataFrame **before** passing to analyzers, not within them.

### Web Mode (flask_app.py)

1. User uploads CSV + optional user-map CSV
2. `AnalysisSession` class ([src/purrrr/flask_app.py](src/purrrr/flask_app.py#L66-L95)) holds DataFrame and config in session
3. Routes in [flask_app.py](src/purrrr/flask_app.py#L100-) accept JSON payloads, apply filters, call analyzers
4. Return JSON responses to frontend ([static/app.js](src/purrrr/static/app.js))
5. Redis stores sessions (or filesystem fallback if Redis unavailable)

**Deployment**: Docker Compose with Flask + Redis; configure `REDIS_URL` env var.

## Important Conventions

### Column Names (Case-Sensitive)

Audit logs must have these columns (exact case):
- **SharePoint**: `SourceFileName`, `UserID`, `Operation`, `CreationTime`, `ClientIP`, `UserAgent`
- **Exchange**: `MailboxOwnerUPN`, `Operation`, `ClientIP`, `ClientInfoString`, `CreationTime`
- **Entra**: Device, UserPrincipalName, CreatedDateTime, etc. (config-driven via `entra_field_config`)

**Gotcha**: File path parsing assumes SharePoint format (`/sites/sitename/Shared Documents/file.txt`). Non-standard paths may fail extraction.

### Output Formats

- **Default (JSON)**: Machine-readable, includes raw counts/stats
- **`--text` flag**: Human-readable colored output (via `polykit.text` utilities)
- **Exchange export (`--export-exchange-csv`)**: CSV with all extracted fields
- **Web mode**: Always JSON to frontend

**Important**: When changing output format at runtime, all analyzers' `out` attribute must be updated to use the selected formatter (see [main.py line 533+](src/purrrr/main.py#L533) for the pattern).

### User Mapping

Two approaches:
1. **CLI**: `--user-map users.csv` (UPN, display name pairs)
2. **Web**: Upload user-map CSV alongside audit log; `AnalysisSession` applies mapping to all queries

User IDs in output default to UPN if no mapping provided.

## Development Patterns

### Adding a New Analyzer

1. Create file in [src/purrrr/{module}/](src/purrrr/) inheriting from `AuditAnalyzer`
2. Implement public methods that accept DataFrame and return formatted output
3. Use `self.out.print_header()`, `self.out.format_table()` for consistent styling
4. Instantiate in [main.py](src/purrrr/main.py#L32-L37) and add CLI args in `parse_arguments()`
5. Call analyzer methods in main analysis logic (around [line 300+](src/purrrr/main.py#L300))

**Example**:
```python
# src/purrrr/newmodule/ops.py
class NewAnalyzer(AuditAnalyzer):
    def analyze(self, df: DataFrame) -> None:
        # Use self.config, self.logger, self.out
        pass
```

### Handling Missing Columns

Always validate DataFrame columns before analysis:
```python
if "ColumnName" not in df.columns:
    self.logger.warning("ColumnName not in audit log")
    return
```

### Performance Considerations

- Large CSVs (500MB+) load into memory — pandas DataFrames may consume 2-3x file size
- IP geolocation (`--do-ip-lookups`) is slow; cache results in production
- Redis session limits to 2GB (`docker-compose.yml` line 16); adjust for production

## Testing & Debugging

### CLI Testing

```bash
# Test file analysis
python -m purrrr.main test_log.csv --details --text

# Test with user mapping
python -m purrrr.main test_log.csv --user-map users.csv --text

# JSON output (default)
python -m purrrr.main test_log.csv | jq .
```

### Web Testing

```bash
# Run locally (no Docker)
python run_web.py --debug

# Run with Docker
docker-compose up --build

# Test upload at http://localhost:5000
```

### Common Issues

- **"No CSV file found"**: Ensure `log_csv` is first positional arg, not a flag
- **Empty results**: Check `excluded_actions`, `excluded_file_types` — they may filter all rows
- **Redis connection fails**: Flask falls back to filesystem sessions (logged as warning)
- **File encoding**: CSV must be UTF-8; exotic encodings cause pandas to fail silently

## External Dependencies

- **polykit** (>= 0.14.6): Logging, CLI parsing, text formatting — **never print directly, use `polykit.text.print_color()`**
- **pandas**: DataFrame operations — **avoid `.copy()` on large DataFrames; use views**
- **flask**: Web framework — session management is automatic via `AnalysisSession`
- **redis** (optional): Production session store; graceful fallback if unavailable

## File Structure Quick Reference

- **[src/purrrr/](src/purrrr/)** — Main package
  - **[tools.py](src/purrrr/tools.py)** — Config, formatters, base analyzer class
  - **[main.py](src/purrrr/main.py)** — CLI entry point with arg parsing
  - **[flask_app.py](src/purrrr/flask_app.py)** — Web interface
  - **[files/](src/purrrr/files/)**, **[exchange/](src/purrrr/exchange/)**, **[entra/](src/purrrr/entra/)**, **[network/](src/purrrr/network/)**, **[users/](src/purrrr/users/)** — Domain-specific analyzers
- **[static/](src/purrrr/static/)**, **[templates/](src/purrrr/templates/)** — Web UI (app.js, style.css, index.html)
- **[Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml)** — Container setup with Redis
- **[run_web.py](run_web.py)** — Web server launcher with host/port config

---

When stuck, check [README.md](README.md) for usage examples and feature list.
