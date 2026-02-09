from typing import Dict, Optional
from pathlib import Path
import yaml
import logging

from dataporter.profiles.model import Profile
from dataporter.profiles.validators import validate_profile_dict
from dataporter.profiles.loader import get_global_profiles_path

logger = logging.getLogger(__name__)


# ---------- Internal helpers ----------

def _get_profiles_path() -> Path:
    """
    Get the global profiles.yaml path and ensure parent directory exists.
    """
    path = get_global_profiles_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_all_profiles() -> Dict[str, dict]:
    """
    Load the full profiles.yaml content.
    Returns a dict with structure: {"profiles": {...}}
    """
    profiles_path = _get_profiles_path()

    if not profiles_path.exists():
        return {"profiles": {}}

    with open(profiles_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if "profiles" not in data:
        data["profiles"] = {}

    return data


def _save_all_profiles(data: Dict[str, dict]) -> None:
    """
    Save the full profiles.yaml content.
    """
    profiles_path = _get_profiles_path()

    with open(profiles_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False,
        )


# ---------- Core profile operations ----------

def create_profile(name: str, engine: str, **kwargs) -> Profile:
    """
    Create and persist a new profile.
    """
    validate_profile_dict(engine, kwargs)

    if engine == "bigquery":
        profile = Profile(
            name=name,
            engine=engine,
            project_id=kwargs.get("project_id"),
            dataset=kwargs.get("dataset"),
            credentials_path=kwargs.get("credentials_path"),
        )
        profile_data = {
            "engine": engine,
            "project_id": profile.project_id,
            "dataset": profile.dataset,
            "credentials_path": profile.credentials_path,
        }
    else:
        profile = Profile(
            name=name,
            engine=engine,
            host=kwargs.get("host"),
            port=kwargs.get("port"),
            user=kwargs.get("user"),
            password=kwargs.get("password"),
            database=kwargs.get("database"),
        )
        profile_data = {
            "engine": engine,
            "host": profile.host,
            "port": profile.port,
            "user": profile.user,
            "password": profile.password,
            "database": profile.database,
        }

    data = _load_all_profiles()
    data["profiles"][name] = profile_data
    _save_all_profiles(data)

    logger.info("Created profile '%s'", name)
    return profile


def get_profile(name: str) -> Optional[Profile]:
    """
    Load a profile by name.
    """
    data = _load_all_profiles()
    profile_data = data["profiles"].get(name)

    if not profile_data:
        return None

    engine = profile_data.get("engine")

    if engine == "bigquery":
        return Profile(
            name=name,
            engine=engine,
            project_id=profile_data.get("project_id"),
            dataset=profile_data.get("dataset"),
            credentials_path=profile_data.get("credentials_path"),
        )

    return Profile(
        name=name,
        engine=engine,
        host=profile_data.get("host"),
        port=profile_data.get("port"),
        user=profile_data.get("user"),
        password=profile_data.get("password"),
        database=profile_data.get("database"),
    )


def list_profiles() -> Dict[str, str]:
    """
    List all profiles as {name: engine}.
    """
    data = _load_all_profiles()
    return {
        name: cfg.get("engine", "unknown")
        for name, cfg in data["profiles"].items()
    }


def delete_profile(name: str) -> bool:
    """
    Delete a profile by name.
    """
    data = _load_all_profiles()

    if name not in data["profiles"]:
        return False

    del data["profiles"][name]
    _save_all_profiles(data)

    logger.info("Deleted profile '%s'", name)
    return True


def get_profile_fields(engine: str) -> dict:
    """
    Return required fields and prompts for a given engine.
    """
    if engine == "bigquery":
        return {
            "required": ["project_id", "dataset", "credentials_path"],
            "prompts": {
                "project_id": "Google Cloud Project ID",
                "dataset": "BigQuery Dataset ID",
                "credentials_path": "Path to service account JSON key file",
            },
        }

    if engine in {"mysql", "postgresql", "sqlserver"}:
        return {
            "required": ["host", "port", "user", "password", "database"],
            "prompts": {
                "host": "Database host",
                "port": "Database port",
                "user": "Database username",
                "password": "Database password",
                "database": "Database name",
            },
        }

    raise ValueError(f"Unsupported engine: {engine}")
