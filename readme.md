# DataPorter

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)


**DataPorter** is a scalable Python-based data ingestion framework for importing large CSV/TSV files into relational databases **without loading the entire dataset into memory**.

It is designed to handle **real-world, messy data** and work reliably across **PostgreSQL, MySQL, SQL Server, and Google BigQuery**.

---

## Why DataPorter?

Moving large flat files into databases sounds simple—until it isn’t.

Without DataPorter, you usually deal with:
- Manual INSERT scripts
- Memory crashes on large files
- Database-specific syntax
- Schema mismatches
- Slow and unreliable imports
- Manual table creation in the database
- Hard to handle multiple files at once

DataPorter solves this by providing:
- **Chunk-based ingestion** (constant memory usage)
- **Automatic schema inference And table creation database**
- **Database-specific bulk loading strategies**
- **Profile-driven configuration**
- **One unified API across databases**
- ** Able to handle multiple files at once**

---

## Key Features

- 🚀 **Chunked Processing** – Import millions of rows efficiently
- 🧠 **Schema Inference** – Intelligent type detection with confidence scoring
- 🔄 **Multi-Database Support** – PostgreSQL, MySQL, SQL Server, BigQuery
- ⚡ **Smart Loader Selection** – Automatically picks the fastest load method
- 🧩 **Extensible Architecture** – Pluggable readers, loaders, engines
- ✍️ **Schema Overrides** – Full control when inference is uncertain

---

## Supported Databases

| Database | Loading Strategy |
|--------|------------------|
| PostgreSQL | COPY |
| MySQL | LOAD DATA LOCAL INFILE / SQLAlchemy fallback |
| SQL Server | BULK INSERT / BCP |
| BigQuery | GCS upload + load job |

---

## Quick Start (2 Minutes)

### 1️⃣ Install

```bash
pip install git+https://github.com/Satyam4456/DataPorter.git
```

### 2️⃣ Create a Database Profile

```bash
from dataporter import DataPorter

DataPorter.create_profile(
    name="my_db",
    engine="postgresql",
    host="localhost",
    port=5432,
    user="postgres",
    database="test_db",
    password="your_password",
    prompt_password=False,
)
```

### 3️⃣ Import a CSV

```bash
porter = DataPorter(profile="my_db")

porter.import_file(
    file_path="data.csv",
    table="users",
    if_exists="replace"
)
```

That’s it.
Your data is now in the database.


# Getting Started (Recommended)

For a step-by-step beginner guide, including:

Environment setup

Schema preview

First full import

Common errors and fixes

👉 Read the full guide here:
📘 GETTING_STARTED.md


## Project Structure (High Level)
```bash
DataPorter/
├── src/ dataporter/
│       ├── engines/     # Database engines
│       ├── loaders/     # Bulk loading strategies
│       ├── readers/     # File readers
│       ├── schema/      # Schema inference & mapping
│       ├── profiles/    # Profile management
│       └── utils/       # Shared utilities
├── tests/
├── profiles.yaml
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

# Who Is This For?

Data Analysts moving CSVs into databases

Data Engineers building ingestion pipelines

Anyone tired of writing custom import scripts

Projects that must support multiple databases


# Status

This project is actively developed and designed as:

A reusable ingestion library

A learning-grade ETL framework

A portfolio-quality data engineering project


#Next Steps

📘 Read the full onboarding guide → GETTING_STARTED.md

🔧 Explore schema overrides

🧪 Run tests to understand behavior

🚀 Extend loaders or engines
