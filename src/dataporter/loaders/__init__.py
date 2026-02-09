# dataporter/loaders/__init__.py

import importlib
from dataporter.loaders.base import LoaderStrategy


_LOADER_MAP = {
    ("mysql", "local"): "dataporter.loaders.mysql_local_infile.MySQLLocalInfileLoader",
    ("mysql", "cloud"): "dataporter.loaders.mysql_to_sql.MySQLToSqlLoader",
    ("postgresql", "local"): "dataporter.loaders.postgres_copy.PostgresCopyLoader",
    ("postgresql", "cloud"): "dataporter.loaders.postgres_copy.PostgresCopyLoader",
    ("sqlserver", "local"): "dataporter.loaders.sqlserver_bulk_insert.SQLServerBulkInsertLoader",
    ("sqlserver", "cloud"): "dataporter.loaders.sqlserver_bcp.SQLServerBcpLoader",
    ("bigquery", "any"): "dataporter.loaders.bigquery_load.BigQueryLoadLoader",
}


def get_loader(engine, engine_name: str, server_type: str) -> LoaderStrategy:
    key = (engine_name, server_type)
    fallback_key = (engine_name, "any")

    path = _LOADER_MAP.get(key) or _LOADER_MAP.get(fallback_key)

    if not path:
        raise ValueError(f"Unsupported engine/server combination: {engine_name}/{server_type}")

    module_path, class_name = path.rsplit(".", 1)

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as e:
        raise ImportError(
            f"Optional dependency for '{engine_name}' is not installed.\n"
            f"Install it using: pip install dataporter[{engine_name}]"
        ) from e

    loader_cls = getattr(module, class_name)
    return loader_cls(engine)


__all__ = ["LoaderStrategy", "get_loader"]
