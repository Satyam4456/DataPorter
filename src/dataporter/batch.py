"""
Batch import functionality for processing multiple files.
"""

import glob
from pathlib import Path
from typing import Dict, List, Optional, Callable, TYPE_CHECKING
import logging

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from dataporter.api import DataPorter, ImportReport
else:
    ImportReport = None

logger = logging.getLogger(__name__)


class BatchImporter:
    """Import multiple files from a folder."""
    
    def __init__(
        self,
        profile: str,
        server_type: str,
        profiles_path: Optional[str] = None,
        log_level: int = logging.INFO,
    ):
        """
        Initialize batch importer.
        
        Args:
            profile: Profile name
            server_type: 'local' or 'cloud'
            profiles_path: Path to profiles.yaml (uses global if not specified)
            log_level: Logging level
        """
        # Import here to avoid circular imports
        from dataporter.api import DataPorter
        
        self.profile = profile
        self.server_type = server_type
        self.profiles_path = profiles_path
        self.log_level = log_level
        self.porter = DataPorter(
            profile=profile,
            profiles_path=profiles_path,
            log_level=log_level,
        )
    
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
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> Dict:
        """
        Import all matching files from a folder.
        
        Args:
            folder_path: Path to folder containing files
            pattern: File pattern to match (e.g., "*.csv", "sales_*.csv")
            delimiter: Field delimiter
            encoding: File encoding
            skip_rows: Rows to skip at start
            if_exists: 'fail', 'replace', or 'append'
            sample_chunks: Chunks for schema inference
            confidence_threshold: Min confidence for types
            schema_overrides: Dict mapping filename -> {column -> type}
            interactive: Ask user for uncertain columns
            chunksize: Rows per chunk
            name_mapping: Dict mapping filename -> table_name
            skip_files: List of filenames to skip
            on_success: Callback function on successful import
            on_error: Callback function on error
            
        Returns:
            Dict mapping filename -> ImportReport or error message
        """
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # Find matching files
        files = sorted(glob.glob(str(folder / pattern)))
        logger.info(f"Found {len(files)} files matching '{pattern}' in {folder}")
        
        if not files:
            logger.warning(f"No files found matching pattern '{pattern}'")
            return {}
        
        skip_files = skip_files or []
        schema_overrides = schema_overrides or {}
        name_mapping = name_mapping or {}
        
        results = {}
        
        for file_path in files:
            file_name = Path(file_path).name
            
            # Check if should skip
            if file_name in skip_files:
                logger.info(f"Skipping {file_name}")
                continue
            
            # Determine table name
            if file_name in name_mapping:
                table_name = name_mapping[file_name]
            else:
                table_name = Path(file_path).stem  # Filename without extension
            
            try:
                logger.info(f"Importing {file_name} → {table_name}")
                
                # Get schema overrides for this file if provided
                file_overrides = schema_overrides.get(file_name)
                
                # Import
                report = self.porter.import_file(
                    file_path=file_path,
                    table=table_name,
                    server_type=self.server_type,
                    delimiter=delimiter,
                    encoding=encoding,
                    skip_rows=skip_rows,
                    if_exists=if_exists,
                    sample_chunks=sample_chunks,
                    confidence_threshold=confidence_threshold,
                    schema_overrides=file_overrides,
                    interactive=interactive,
                    chunksize=chunksize,
                )
                
                results[file_name] = report
                
                logger.info(
                    f"✓ {file_name}: {report.rows_loaded} rows in {report.elapsed_seconds:.2f}s"
                )
                
                # Call success callback
                if on_success:
                    on_success(file_name, report)
            
            except Exception as e:
                logger.error(f"✗ {file_name}: {e}")
                results[file_name] = str(e)
                
                # Call error callback
                if on_error:
                    on_error(file_name, str(e))
        
        # Summary
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: Dict) -> None:
        """Print summary of batch import."""
        print("\n" + "="*70)
        print("BATCH IMPORT SUMMARY")
        print("="*70)
        
        success_count = 0
        failed_count = 0
        total_rows = 0
        total_time = 0.0
        
        for filename, result in results.items():
            # Check if result is an ImportReport (has rows_loaded attribute)
            if hasattr(result, 'rows_loaded'):
                success_count += 1
                total_rows += result.rows_loaded
                total_time += result.elapsed_seconds
                status = "✓ SUCCESS"
                details = f"{result.rows_loaded} rows"
            else:
                failed_count += 1
                status = "✗ FAILED"
                details = str(result)[:50]
            
            print(f"{status:15} {filename:30} {details}")
        
        print("-"*70)
        print(
            f"Total: {success_count} succeeded, {failed_count} failed | "
            f"{total_rows} rows in {total_time:.2f}s"
        )
        print("="*70)
