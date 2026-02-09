from google.cloud import bigquery
from google.oauth2 import service_account
from dataporter.engines.base import Engine
from dataporter.schema.model import TableSchema
from dataporter.exceptions import EngineConnectionError
import logging

logger = logging.getLogger(__name__)


class BigQueryEngine(Engine):
    """Google BigQuery database engine."""
    
    def __init__(self, profile):
        """Initialize BigQuery engine."""
        if hasattr(profile, '__dict__'):
            self.config = {
                'project_id': profile.project_id,
                'dataset': profile.dataset,
                'credentials_path': profile.credentials_path,
            }
        else:
            self.config = profile
        
        self._client = None
        logger.debug("BigQueryEngine initialized")
    
    def test_connection(self) -> bool:
        """Test BigQuery connection."""
        try:
            client = self._get_client()
            # Test by listing datasets
            list(client.list_datasets(max_results=1))
            logger.info("BigQuery connection successful")
            return True
        except Exception as e:
            logger.error(f"BigQuery connection failed: {e}")
            raise EngineConnectionError(f"BigQuery connection failed: {e}") from e
    
    def _get_client(self):
        """Get BigQuery client."""
        if self._client is None:
            credentials_path = self.config.get('credentials_path')
            project_id = self.config.get('project_id')
            
            # Load credentials from JSON key file
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            
            self._client = bigquery.Client(
                credentials=credentials,
                project=project_id
            )
            logger.debug("BigQuery client created")
        
        return self._client
    
    def create_table(self, schema: TableSchema, if_exists: str = "fail") -> None:
        """Create table in BigQuery."""
        client = self._get_client()
        project_id = self.config.get('project_id')
        dataset = self.config.get('dataset')
        table_id = schema.table_name
        
        table_ref = f"{project_id}.{dataset}.{table_id}"
        
        # Check if table exists
        try:
            client.get_table(table_ref)
            exists = True
        except Exception:
            exists = False
        
        if exists:
            if if_exists == 'fail':
                raise Exception(f"Table {table_ref} already exists")
            elif if_exists == 'replace':
                self.drop_table(table_id)
                logger.info(f"Dropped table {table_id}")
            elif if_exists == 'append':
                logger.info(f"Table {table_id} exists, will append data")
                return
        
        # Build schema for BigQuery
        bq_schema = self._get_bigquery_schema(schema)
        
        # Create table
        table = bigquery.Table(table_ref, schema=bq_schema)
        table = client.create_table(table)
        
        logger.info(f"Created table {table_ref}")
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        client = self._get_client()
        project_id = self.config.get('project_id')
        dataset = self.config.get('dataset')
        table_ref = f"{project_id}.{dataset}.{table_name}"
        
        try:
            client.get_table(table_ref)
            return True
        except Exception:
            return False
    
    def drop_table(self, table_name: str) -> None:
        """Drop table from BigQuery."""
        client = self._get_client()
        project_id = self.config.get('project_id')
        dataset = self.config.get('dataset')
        table_ref = f"{project_id}.{dataset}.{table_name}"
        
        client.delete_table(table_ref, not_found_ok=True)
        logger.info(f"Dropped table {table_name}")
    
    def close(self) -> None:
        """Close BigQuery client."""
        if self._client:
            self._client.close()
            logger.info("BigQuery client closed")
    
    def _get_bigquery_schema(self, schema: TableSchema):
        """Convert TableSchema to BigQuery schema."""
        from google.cloud.bigquery import SchemaField
        
        bq_schema = []
        
        for col in schema.columns:
            col_kind = col.inferred_kind
            
            if col_kind == 'int':
                bq_type = 'INTEGER'
            elif col_kind == 'float':
                bq_type = 'FLOAT64'
            elif col_kind == 'bool':
                bq_type = 'BOOLEAN'
            elif col_kind == 'datetime':
                if 'time' in col.name.lower() and 'date' not in col.name.lower():
                    bq_type = 'TIME'
                else:
                    bq_type = 'TIMESTAMP'
            else:
                bq_type = 'STRING'
            
            mode = 'NULLABLE' if col.nullable else 'REQUIRED'
            
            bq_schema.append(
                SchemaField(col.name, bq_type, mode=mode)
            )
        
        return bq_schema