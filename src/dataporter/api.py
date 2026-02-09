from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Iterator, List, Callable, TYPE_CHECKING
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
from getpass import getpass

from dataporter.profiles.loader import ProfileLoader, get_global_profiles_path, save_profile, delete_profile, profile_exists, get_profile_dict
from dataporter.profiles.validators import validate_profile_name, validate_engine, validate_profile_dict, normalize_profile_dict
from dataporter.readers.delimited import DelimitedReader
from dataporter.schema.infer_pandas import PandasSchemaInferencer
from dataporter.schema.user_override import SchemaOverrideManager
from dataporter.schema.model import TableSchema
from dataporter.engines import create_engine
from dataporter.loaders import get_loader
from dataporter.utils.timing import Timer
from dataporter.utils.logging import configure_logging
from dataporter.exceptions import DataPorterError, ProfileError, ProfileExistsError, ProfileNotFoundError

# Import Profile only for type checking (avoids circular import at runtime)
if TYPE_CHECKING:
    from dataporter.profiles.model import Profile

logger = logging.getLogger(__name__)


@dataclass
class ImportReport:
    """Report from data import operation."""
    file_path: str
    engine: str
    server_type: str
    table: str
    schema_used: Optional[TableSchema] = None
    rows_total: int = 0
    rows_loaded: int = 0
    rows_failed: int = 0
    elapsed_seconds: float = 0
    rows_per_second: float = 0
    load_method_used: str = ""
    errors: list = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            'file_path': str(self.file_path),
            'engine': self.engine,
            'server_type': self.server_type,
            'table': self.table,
            'rows_total': self.rows_total,
            'rows_loaded': self.rows_loaded,
            'rows_failed': self.rows_failed,
            'elapsed_seconds': self.elapsed_seconds,
            'rows_per_second': self.rows_per_second,
            'load_method_used': self.load_method_used,
            'errors': self.errors[:10],
            'started_at': self.started_at,
            'completed_at': self.completed_at,
        }


class DataPorter:
    """
    High-level API for data ingestion into multiple database engines.
    """
    
    # ========== Profile Management (Class Methods) ========= =
    
    @staticmethod
    def create_profile(
        name: str,
        engine: str,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        database: str = None,
        project_id: str = None,
        dataset: str = None,
        credentials_path: str = None,
        prompt_password: bool = True,
    ) -> "Profile":
        """
        Create a new database profile.
        
        Args:
            name: Profile name
            engine: Database engine (mysql, postgresql, sqlserver, bigquery)
            host: Database host (for SQL databases)
            port: Database port
            user: Database user (for SQL databases)
            password: Database password (for SQL databases)
            database: Database name (for SQL databases)
            project_id: Google Cloud project ID (for BigQuery)
            dataset: BigQuery dataset ID (for BigQuery)
            credentials_path: Path to service account JSON (for BigQuery)
            prompt_password: Whether to prompt for password interactively
        """
        from dataporter.profiles.manager import create_profile
        
        if engine == 'bigquery':
            # BigQuery profile
            profile_data = {
                'project_id': project_id,
                'dataset': dataset,
                'credentials_path': credentials_path,
            }
        else:
            # SQL databases
            profile_data = {
                'host': host,
                'port': port,
                'user': user,
                'password': password,
                'database': database,
            }
        
        return create_profile(name, engine, **profile_data)
    
    @classmethod
    def update_profile(cls, name: str, **kwargs) -> "Profile":
        """Update an existing profile."""
        from dataporter.profiles.model import Profile
        
        if not profile_exists(name):
            raise ProfileNotFoundError(f"Profile '{name}' not found")
        
        # Load existing
        existing = get_profile_dict(name)
        
        # Merge
        engine = kwargs.pop('engine', existing['engine'])
        config = dict(existing)
        
        # Update with provided values
        for key, value in kwargs.items():
            if value is not None:
                config[key] = value
        
        # Validate
        validate_profile_dict(engine, config)
        
        # Normalize
        config['engine'] = engine
        config = normalize_profile_dict(engine, config)
        
        # Save
        save_profile(name, config)
        logger.info(f"Updated profile '{name}'")
        
        return Profile.from_dict(name, config)
    
    @classmethod
    def delete_profile(cls, name: str) -> None:
        """Delete a profile."""
        delete_profile(name)
        logger.info(f"Deleted profile '{name}'")
    
    @classmethod
    def get_profile_by_name(cls, name: str) -> "Profile":
        """
        Get a profile by name (class method).
        
        Args:
            name: Profile name
            
        Returns:
            Profile object
            
        Raises:
            ProfileNotFoundError: If profile not found
        """
        from dataporter.profiles.model import Profile
        
        config = get_profile_dict(name)
        return Profile.from_dict(name, config)
    
    @classmethod
    def list_profiles(cls) -> Dict[str, str]:
        """List all profiles."""
        from dataporter.profiles.loader import load_profiles
        
        data = load_profiles()
        profiles = data.get("profiles", {})
        return {name: config.get('engine', 'unknown') for name, config in profiles.items()}
    
    @classmethod
    def get_profiles_path(cls) -> Path:
        """Get path to global profiles.yaml."""
        return get_global_profiles_path()
    
    # ========== Instance Initialization ==========
    
    def __init__(
        self,
        profile: str,
        profiles_path: Optional[str] = None,
        log_level: int = logging.INFO,
    ):
        """Initialize DataPorter instance."""
        configure_logging(log_level)
        
        self._log_level = log_level
        self._profile_name = profile
        self._profile = None
        self._profiles_path = profiles_path
        self.engine = None
        self.server_type = None
        
        # Use global path if not specified
        if self._profiles_path is None:
            self._profiles_path = str(get_global_profiles_path())
        
        try:
            # Load profile
            logger.info(f"Initializing DataPorter with profile '{profile}'")
            profile_loader = ProfileLoader(self._profiles_path)
            self._profile = profile_loader.get_profile(profile)
            logger.info(f"Loaded profile: {self._profile.name} (engine: {self._profile.engine})")
        except Exception as e:
            logger.error(f"Failed to load profile '{profile}': {e}")
            raise
    
    @property
    def profile(self) -> "Profile":
        """Get the current profile (property)."""
        if self._profile is None:
            raise RuntimeError("Profile not initialized")
        return self._profile
    
    @property
    def profiles_path(self) -> str:
        """Get profiles path."""
        return self._profiles_path
    
    # ========== Connection Control ==========
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            engine = create_engine(self.profile)
            result = engine.test_connection()
            logger.info(f"✓ Connection test successful for {self.profile.engine}")
            engine.close()
            return result
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
    
    def get_engine(self):
        """Get database engine instance."""
        if self.engine is None:
            self.engine = create_engine(self.profile)
        return self.engine
    
    def get_profile(self) -> "Profile":
        """
        Get current profile (instance method).
        
        Returns:
            Profile object of this instance
        """
        return self.profile
    
    def close_connection(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.close()
            self.engine = None
            logger.info("Connection closed")
    
    # ========== Schema Control ==========
    
    def infer_schema(
        self,
        file_path: str,
        delimiter: str = ",",
        encoding: str = "utf-8",
        skip_rows: int = 0,
        sample_chunks: int = 10,
        confidence_threshold: float = 0.85,
    ) -> TableSchema:
        """Infer schema from file without importing."""
        logger.info(f"Inferring schema from {file_path}")
        
        reader = DelimitedReader(
            delimiter=delimiter,
            encoding=encoding,
            skip_rows=skip_rows,
        )
        
        chunk_iterator = reader.read_chunks(file_path, chunksize=100000)
        inferencer = PandasSchemaInferencer()
        
        schema = inferencer.infer(
            table_name=Path(file_path).stem,
            chunk_iterator=chunk_iterator,
            sample_chunks=sample_chunks,
            confidence_threshold=confidence_threshold,
        )
        
        logger.info(f"Inferred {len(schema.columns)} columns")
        return schema
    
    def preview_schema(
        self,
        file_path: str,
        delimiter: str = ",",
        encoding: str = "utf-8",
        skip_rows: int = 0,
    ) -> None:
        """Preview inferred schema in formatted output."""
        schema = self.infer_schema(
            file_path=file_path,
            delimiter=delimiter,
            encoding=encoding,
            skip_rows=skip_rows,
        )
        
        print("\n" + "="*70)
        print(f"SCHEMA PREVIEW: {schema.table_name}")
        print("="*70)
        
        for col in schema.columns:
            confidence_str = f"({col.confidence:.0%} confident)" if col.confidence < 1.0 else ""
            nullable_str = "nullable" if col.nullable else "NOT NULL"
            
            print(
                f"  {col.name:25} {col.inferred_kind:12} {nullable_str:15} {confidence_str}"
            )
        
        print("="*70 + "\n")
    
    # ========== Single File Import ==========
    
    def import_file(
        self,
        file_path: str,
        table: str,
        server_type: str,
        delimiter: str = ",",
        encoding: str = "utf-8",
        skip_rows: int = 0,
        if_exists: str = "fail",
        sample_chunks: int = 10,
        confidence_threshold: float = 0.85,
        schema_overrides: Optional[Dict[str, str]] = None,
        interactive: bool = False,
        chunksize: int = 100000,
    ) -> ImportReport:
        """Import single delimited file into database."""
        self.server_type = server_type
        
        report = ImportReport(
            file_path=file_path,
            engine=self.profile.engine,
            server_type=server_type,
            table=table,
            started_at=datetime.now().isoformat(),
        )
        
        timer = Timer(f"Import {file_path} to {table}")
        timer.start()
        
        try:
            logger.info(
                f"Starting import: file={file_path}, table={table}, "
                f"engine={self.profile.engine}, server_type={server_type}"
            )
            
            logger.info("Step 1: Creating file reader")
            reader = DelimitedReader(
                delimiter=delimiter,
                encoding=encoding,
                skip_rows=skip_rows,
            )
            
            logger.info("Step 2: Testing database connection")
            engine = self.get_engine()
            engine.test_connection()
            
            logger.info("Step 3: Inferring schema from file")
            chunk_iterator = reader.read_chunks(file_path, chunksize=chunksize)
            inferencer = PandasSchemaInferencer()
            schema = inferencer.infer(
                table_name=table,
                chunk_iterator=chunk_iterator,
                sample_chunks=sample_chunks,
                confidence_threshold=confidence_threshold,
            )
            report.schema_used = schema
            
            logger.info(f"Inferred schema: {len(schema.columns)} columns")
            
            if schema_overrides or interactive:
                logger.info("Step 4: Applying schema overrides")
                override_manager = SchemaOverrideManager(schema)
                
                if schema_overrides:
                    override_manager.apply_overrides(
                        schema_overrides,
                        self.profile.engine,
                    )
                
                if interactive:
                    override_manager.interactive_override(self.profile.engine)
                
                schema = override_manager.schema
            
            logger.info("Step 5: Creating table")
            engine.create_table(schema, if_exists=if_exists)
            
            logger.info("Step 6: Loading data")
            chunk_iterator = reader.read_chunks(file_path, chunksize=chunksize)
            
            loader = get_loader(
                engine,
                self.profile.engine,
                server_type,
            )
            report.load_method_used = loader.strategy_name
            
            rows_loaded = loader.load(table, schema, chunk_iterator)
            report.rows_loaded = rows_loaded
            
            logger.info(f"✓ Successfully loaded {rows_loaded} rows using {loader.strategy_name}")
            
        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            report.errors.append(str(e))
            report.rows_failed = report.rows_total
            raise
        
        finally:
            elapsed = timer.stop()
            report.elapsed_seconds = elapsed
            report.completed_at = datetime.now().isoformat()
            
            if report.rows_loaded > 0:
                report.rows_per_second = report.rows_loaded / elapsed
            
            logger.info(f"Import completed in {elapsed:.2f}s")
        
        return report
    
    # ========== Batch Import ==========
    
    def import_folder(
        self,
        folder_path: str,
        pattern: str = "*.csv",
        delimiter: str = ",",
        encoding: str = "utf-8",
        skip_rows: int = 0,
        if_exists: str = "replace",
        sample_chunks: int = 10,
        confidence_threshold: float = 0.85,
        schema_overrides: Optional[Dict[str, Dict[str, str]]] = None,
        interactive: bool = False,
        chunksize: int = 100000,
        name_mapping: Optional[Dict[str, str]] = None,
        skip_files: Optional[List[str]] = None,
    ) -> Dict[str, ImportReport]:
        """Import all matching files from a folder."""
        from dataporter.batch import BatchImporter
        
        batch_importer = BatchImporter(
            profile=self._profile_name,
            server_type=self.server_type or "local",
            profiles_path=self._profiles_path,
            log_level=self._log_level,
        )
        
        return batch_importer.import_folder(
            folder_path=folder_path,
            pattern=pattern,
            delimiter=delimiter,
            encoding=encoding,
            skip_rows=skip_rows,
            if_exists=if_exists,
            sample_chunks=sample_chunks,
            confidence_threshold=confidence_threshold,
            schema_overrides=schema_overrides,
            interactive=interactive,
            chunksize=chunksize,
            name_mapping=name_mapping,
            skip_files=skip_files,
        )
    
    def import_folder_with_callbacks(
        self,
        folder_path: str,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        **kwargs,
    ) -> Dict[str, ImportReport]:
        """Import folder with callback functions."""
        from dataporter.batch import BatchImporter
        
        batch_importer = BatchImporter(
            profile=self._profile_name,
            server_type=self.server_type or "local",
            profiles_path=self._profiles_path,
            log_level=self._log_level,
        )
        
        return batch_importer.import_folder(
            folder_path=folder_path,
            on_success=on_success,
            on_error=on_error,
            **kwargs,
        )
    
    # ========== Configuration Control ==========
    
    def set_log_level(self, level: int) -> None:
        """Set logging level."""
        self._log_level = level
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)
        logger.info(f"Log level set to {logging.getLevelName(level)}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            'profile_name': self.profile.name,
            'engine': self.profile.engine,
            'host': self.profile.host,
            'port': self.profile.port,
            'database': self.profile.database,
            'schema': self.profile.schema,
            'profiles_path': str(self._profiles_path),
            'log_level': logging.getLevelName(self._log_level),
        }
    
    def print_config(self) -> None:
        """Print current configuration in formatted output."""
        config = self.get_config()
        
        print("\n" + "="*70)
        print("DATAPORTER CONFIGURATION")
        print("="*70)
        
        for key, value in config.items():
            if value is not None:
                print(f"  {key:20} : {value}")
        
        print("="*70 + "\n")