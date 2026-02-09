# Database Engines

This module contains database-specific engine implementations.

Each engine is responsible for:
- Creating SQLAlchemy connections
- Handling database-specific behavior
- Supporting schema creation and execution

| File           | Purpose                 |
| -------------- | ----------------------- |
| `sqlserver.py` | SQL Server engine logic |
| `mysql.py`     | MySQL engine logic      |
| `postgres.py`  | PostgreSQL engine logic |
| `bigquery.py`  | BigQuery engine logic   |
| `base.py`      | Shared engine interface |
