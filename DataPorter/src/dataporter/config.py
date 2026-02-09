from typing import Dict, Tuple

# Schema inference defaults
DEFAULT_SAMPLE_CHUNKS = 10
DEFAULT_CONFIDENCE_THRESHOLD = 0.85
DEFAULT_CHUNK_SIZE = 100000

# Type inference patterns (regex for object refinement)
BOOLEAN_PATTERNS = (r'^(true|false|yes|no|1|0|t|f|y|n)$',)
NULL_PATTERNS = ('', 'null', 'none', 'na', 'n/a', '<null>')

# MySQL default options
MYSQL_DEFAULT_CHUNKSIZE = 5000

# BCP and subprocess defaults
BCP_TIMEOUT = 3600  # 1 hour for large loads
COPY_TIMEOUT = 3600

# Encoding defaults
DEFAULT_ENCODING = 'utf-8'

# BigQuery defaults
BIGQUERY_JOB_TIMEOUT = 3600

# Supported engines
SUPPORTED_ENGINES = ('postgresql', 'mysql', 'sqlserver', 'bigquery')

# Supported server types
SUPPORTED_SERVER_TYPES = ('local', 'cloud')

# Engine to driver mapping
ENGINE_DRIVER_MAP: Dict[str, str] = {
    'postgresql': 'postgresql',
    'mysql': 'mysql+pymysql',
    'sqlserver': 'mssql+pyodbc',
    'bigquery': 'bigquery',
}

# Type kind definitions (canonical types)
TYPE_KINDS = ('int', 'float', 'bool', 'datetime', 'string')