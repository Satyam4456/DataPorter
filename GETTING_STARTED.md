# Getting Started with DataPorter

This guide helps you get DataPorter up and running in **15 minutes**.

By the end, you will:
- Create a database profile
- Preview a schema from a CSV file
- Import data into a database successfully


## What Is DataPorter?

**DataPorter** is a Python-based data ingestion tool that imports large CSV/TSV files into databases efficiently and safely.

It automatically:
- Reads files in chunks (no memory crashes)
- Infers schemas from real data
- Selects the fastest loading strategy per database
- Handles differences between database engines


## Prerequisites

Before starting, ensure you have:

### 1️⃣ Python 3.8+ and pip

```bash
python --version
```

### 2️⃣ A Running Database

You need access to at least one supported database:
| Database   | Default Port |
| ---------- | ------------ |
| PostgreSQL | 5432         |
| MySQL      | 3306         |
| SQL Server with ODBC driver | 1433         |

Local databases are recommended for first use, but you can use cloud database also.

- Note: If you want to use SQL server then ODBC Driver is compulsory for both Local and Cloud server, otherwise not.

### 3️⃣ Git

- You need git to install package directly from GitHub.

### 4️⃣ A Sample Csv File (optional)
Create a Sample.csv for testing or  
You can use the Sample data provided in this repository also.

## Installation
Recomended to use a virtual environment, as your environment depedencies may create conflict.

Step 1: Core installation  
Install the package directly from GitHub:

```bash
pip install git+https://github.com/Satyam4456/DataPorter.git
```

Step 2: Database-Specific Support  
Now, install the required package for the databases you want to use, you don't need all of them:

- For PostgreSQL
```bash
pip install "dataporter[postgres] @ git+https://github.com/Satyam4456/DataPorter.git"
```

- For MySQL
```bash
pip install "dataporter[mysql] @ git+https://github.com/Satyam4456/DataPorter.git"
```

- For SQL Server
```bash
pip install "dataporter[sqlserver] @ git+https://github.com/Satyam4456/DataPorter.git"
```

- For Google BigQuery
```bash
pip install "dataporter[gcp] @ git+https://github.com/Satyam4456/DataPorter.git"
```

Step 3: Verify Installation
```bash
python -c "import dataporter; print(dataporter.__file__)"        # Output: .../src/dataporter/__init__.py

# Then

python -c "import dataporter; print(dataporter.__version__)"    # Output: 0.1.0

# Then

from dataporter import DataPorter
print("✓ DataPorter installed successfully")

```

## Your First Import
Step 1: Create a Database Profile

A profile stores database connection details.

```bash
from dataporter import DataPorter

DataPorter.create_profile(
    name="local_db",
    engine="postgresql",
    host="localhost",
    port=5432,
    user="postgres",
    database="test_db",
    password="your_password",
    prompt_password=False,
)

print("✓ Profile created")
```
Profiles are saved in profiles.yaml and reused automatically.


Step 2: Initialize DataPorter
```bash
porter = DataPorter(profile="local_db")

if porter.test_connection():
    print("✓ Database connection successful")
```


Step 3: Preview the Schema

Before loading data, inspect how DataPorter interprets your file:
```bash
porter.preview_schema(
    file_path="sample_data.csv",
    delimiter=","
)
```

- This shows:

    - column names

    - inferred data types

    - nullability

    - confidence score


Step 4: Import the Data
```bash
report = porter.import_file(
    file_path="sample_data.csv",
    table="users",
    if_exists="replace"
)

print(f"Rows Loaded: {report.rows_loaded}")
print(f"Time Taken: {report.elapsed_seconds:.2f}s")
```

🎉 That’s it — your data is now in the database.

# Common Issues:
## Profile Not Found
```bash
DataPorter.list_profiles()
```

If empty, create a profile first.

## File Not Found

Ensure your CSV path is correct:
```bash
import os
print(os.getcwd())
print(os.listdir("."))
```

## Connection Failed

- Check:

    - Database is running
    
    - Host and port are correct
    
    - Username and password are valid

# Common Questions
## Q: What if the package has inferred wrong column type for my CSV?

Override them:
```python
report = porter.import_file(
    file_path="data.csv",
    table="mytable",
    server_type="local",
    schema_overrides={
        "date_column": "datetime",    # Override to datetime
        "amount": "float",             # Override to float
        "is_active": "bool",           # Override to boolean
    },
)
```

## Q: How big of a file can I import?

Very large! DataPorter processes files in chunks, so memory usage is constant:
```python
# This works even if file is 10GB (uses constant memory)
report = porter.import_file(
    file_path="huge_10gb_file.csv",
    table="large_table",
    server_type="local",
    chunksize=500000,  # 500K rows per chunk
)
```

## Q: Where is my password stored?

In `profiles.yaml` in the DataPorter project root. It's plaintext, so:
- ✅ Good for local/dev: Store in `profiles.yaml`
- ⚠️ Production: Use environment variables instead
```python
import os

DataPorter.create_profile(
    name="prod_db",
    engine="postgresql",
    host="prod.db.com",
    user="admin",
    database="prod_db",
    password=os.getenv("DB_PASSWORD"),  # From environment variable
    prompt_password=False,
)
```

# Key Commands Reference

```python
from dataporter import DataPorter

# Profile Management
DataPorter.create_profile(name="db1", engine="postgresql", ...)
DataPorter.update_profile(name="db1", host="newhost.com")
DataPorter.delete_profile(name="db1")
DataPorter.list_profiles()
DataPorter.get_profile(name="db1")
DataPorter.get_profiles_path()

# Initialize
porter = DataPorter(profile="db1")

# Connection
porter.test_connection()
porter.get_profile()
porter.close_connection()

# Schema
porter.infer_schema(file_path="data.csv")
porter.preview_schema(file_path="data.csv")

# Import
porter.import_file(file_path="data.csv", table="t1", server_type="local")
porter.import_folder(folder_path="data/", server_type="cloud/local", pattern="*.csv")
porter.import_folder_with_callbacks(folder_path="data/", server_type="cloud/local", on_success=func)

# Configuration
porter.set_log_level(logging.DEBUG)
porter.get_config()
porter.print_config()
```

# What’s Next?

Now that you’ve completed your first import:

🔧 Customize schema using overrides

📂 Import entire folders of CSV files

⚡ Tune performance with chunk sizes

☁️ Load data into cloud databases

👉 For deeper usage and advanced scenarios, explore all options available in API.py file.


# Success Checklist

✅ Python installed

✅ Database running

✅ DataPorter installed

✅ Profile created

✅ Schema previewed

✅ Data imported

If all are checked — you’re ready to use DataPorter.
