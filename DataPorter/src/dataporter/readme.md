# dataporter Package

This is the main application package containing the public API and orchestration logic.

It coordinates:
- File reading
- Schema inference
- Table creation
- Data loading
- Error handling


# API.py
Entry point for programmatic usage.

Exposes the `DataPorter` class, which provides high-level methods such as:
- import_file()
- profile-based execution
- end-to-end ETL orchestration 


# batch.py
Implements batch execution logic.

Used for:
- Running DataPorter jobs from scripts or schedulers
- Non-interactive and automated executions


# config.py
Handles global configuration settings such as defaults, constants, and environment-related options.


# exceptions.py
Defines custom exception classes used throughout the project to provide clearer error handling and debugging.
