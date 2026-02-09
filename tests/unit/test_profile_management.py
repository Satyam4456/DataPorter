import pytest
import tempfile
from pathlib import Path
from dataporter import DataPorter
from dataporter.exceptions import (
    ProfileError,
    ProfileExistsError,
    ProfileNotFoundError,
)
from dataporter.profiles import (
    get_global_profiles_path,
    load_profiles,
    save_profiles,
    profile_exists,
)


class TestProfileCreation:
    """Test profile creation."""
    
    def test_create_profile_saves_to_global_path(self):
        """Test that new profile is saved to global profiles.yaml."""
        global_path = get_global_profiles_path()
        
        # Create profile
        profile = DataPorter.create_profile(
            name="test_pg",
            engine="postgresql",
            host="localhost",
            user="postgres",
            database="testdb",
            password="testpass",
            prompt_password=False,
        )
        
        # Check it exists
        assert profile_exists("test_pg")
        
        # Verify file location
        assert global_path.exists()
        
        # Load and verify
        data = load_profiles()
        assert "test_pg" in data["profiles"]
        assert data["profiles"]["test_pg"]["engine"] == "postgresql"
        
        # Cleanup
        DataPorter.delete_profile("test_pg")
    
    def test_create_mysql_profile(self):
        """Test creating MySQL profile."""
        profile = DataPorter.create_profile(
            name="test_mysql",
            engine="mysql",
            host="localhost",
            user="root",
            database="mydb",
            password="pass",
            prompt_password=False,
        )
        
        assert profile.engine == "mysql"
        assert profile.port == 3306
        assert profile_exists("test_mysql")
        
        DataPorter.delete_profile("test_mysql")
    
    def test_create_sqlserver_profile(self):
        """Test creating SQL Server profile."""
        profile = DataPorter.create_profile(
            name="test_sqlserver",
            engine="sqlserver",
            host="server.database.windows.net",
            user="admin",
            database="mydb",
            password="pass",
            prompt_password=False,
        )
        
        assert profile.engine == "sqlserver"
        assert profile.schema == "dbo"
        assert profile.driver == "ODBC Driver 18 for SQL Server"
        
        DataPorter.delete_profile("test_sqlserver")
    
    def test_create_bigquery_profile(self):
        """Test creating BigQuery profile."""
        profile = DataPorter.create_profile(
            name="test_bq",
            engine="bigquery",
            project_id="my-project",
            dataset="my_dataset",
            gcs_bucket="my-bucket",
            credentials_path="/path/to/key.json",
        )
        
        assert profile.engine == "bigquery"
        assert profile.gcs_prefix == "dataporter_uploads/"
        
        DataPorter.delete_profile("test_bq")


class TestProfileValidation:
    """Test profile validation."""
    
    def test_invalid_profile_name(self):
        """Test that invalid profile names are rejected."""
        with pytest.raises(ProfileError):
            DataPorter.create_profile(
                name="test-invalid",  # Hyphen not allowed
                engine="postgresql",
                host="localhost",
                user="user",
                database="db",
                password="pass",
                prompt_password=False,
            )
    
    def test_invalid_engine(self):
        """Test that invalid engine is rejected."""
        with pytest.raises(ProfileError):
            DataPorter.create_profile(
                name="test_invalid",
                engine="invalid_engine",
                host="localhost",
                user="user",
                database="db",
                password="pass",
                prompt_password=False,
            )
    
    def test_missing_required_postgresql_fields(self):
        """Test that PostgreSQL profile requires host, user, database."""
        with pytest.raises(ProfileError):
            DataPorter.create_profile(
                name="test_missing",
                engine="postgresql",
                # Missing host, user, database
                password="pass",
                prompt_password=False,
            )
    
    def test_missing_required_bigquery_fields(self):
        """Test that BigQuery profile requires project_id, dataset, gcs_bucket."""
        with pytest.raises(ProfileError):
            DataPorter.create_profile(
                name="test_bq_missing",
                engine="bigquery",
                # Missing required fields
            )
    
    def test_invalid_port(self):
        """Test that invalid port is rejected."""
        with pytest.raises(ProfileError):
            DataPorter.create_profile(
                name="test_invalid_port",
                engine="postgresql",
                host="localhost",
                port=99999,  # Invalid
                user="user",
                database="db",
                password="pass",
                prompt_password=False,
            )


class TestProfileOverwrite:
    """Test profile overwrite behavior."""
    
    def test_overwrite_false_raises_error(self):
        """Test that creating existing profile raises error by default."""
        # Create first profile
        DataPorter.create_profile(
            name="test_overwrite",
            engine="postgresql",
            host="localhost",
            user="user",
            database="db",
            password="pass",
            prompt_password=False,
        )
        
        # Try to create again
        with pytest.raises(ProfileExistsError):
            DataPorter.create_profile(
                name="test_overwrite",
                engine="postgresql",
                host="newhost",
                user="newuser",
                database="newdb",
                password="pass",
                prompt_password=False,
            )
        
        # Cleanup
        DataPorter.delete_profile("test_overwrite")
    
    def test_overwrite_true_replaces_profile(self):
        """Test that overwrite=True replaces profile."""
        # Create first profile
        DataPorter.create_profile(
            name="test_overwrite2",
            engine="postgresql",
            host="localhost",
            user="user",
            database="db",
            password="pass",
            prompt_password=False,
        )
        
        # Overwrite with different values
        profile = DataPorter.create_profile(
            name="test_overwrite2",
            engine="postgresql",
            host="newhost",
            user="newuser",
            database="newdb",
            password="newpass",
            prompt_password=False,
            overwrite=True,
        )
        
        # Verify new values
        assert profile.host == "newhost"
        assert profile.user == "newuser"
        
        DataPorter.delete_profile("test_overwrite2")


class TestProfileUpdate:
    """Test profile update."""
    
    def test_update_profile(self):
        """Test updating a profile."""
        # Create
        DataPorter.create_profile(
            name="test_update",
            engine="postgresql",
            host="localhost",
            user="user",
            database="db",
            password="pass",
            prompt_password=False,
        )
        
        # Update
        profile = DataPorter.update_profile(
            name="test_update",
            host="newhost",
            user="newuser",
        )
        
        assert profile.host == "newhost"
        assert profile.user == "newuser"
        assert profile.database == "db"  # Unchanged
        
        DataPorter.delete_profile("test_update")
    
    def test_update_nonexistent_profile(self):
        """Test that updating nonexistent profile raises error."""
        with pytest.raises(ProfileNotFoundError):
            DataPorter.update_profile(name="nonexistent", host="newhost")


class TestProfileDelete:
    """Test profile deletion."""
    
    def test_delete_profile(self):
        """Test deleting a profile."""
        # Create
        DataPorter.create_profile(
            name="test_delete",
            engine="postgresql",
            host="localhost",
            user="user",
            database="db",
            password="pass",
            prompt_password=False,
        )
        
        assert profile_exists("test_delete")
        
        # Delete
        DataPorter.delete_profile("test_delete")
        
        assert not profile_exists("test_delete")
    
    def test_delete_nonexistent_profile(self):
        """Test that deleting nonexistent profile raises error."""
        with pytest.raises(ProfileNotFoundError):
            DataPorter.delete_profile("nonexistent")


class TestProfileQuery:
    """Test profile querying."""
    
    def test_get_profile(self):
        """Test getting a specific profile."""
        # Create
        DataPorter.create_profile(
            name="test_get",
            engine="postgresql",
            host="localhost",
            user="user",
            database="db",
            password="pass",
            prompt_password=False,
        )
        
        # Get
        profile = DataPorter.get_profile("test_get")
        
        assert profile.name == "test_get"
        assert profile.engine == "postgresql"
        assert profile.host == "localhost"
        
        DataPorter.delete_profile("test_get")
    
    def test_get_nonexistent_profile(self):
        """Test that getting nonexistent profile raises error."""
        with pytest.raises(ProfileNotFoundError):
            DataPorter.get_profile("nonexistent")
    
    def test_list_profiles(self):
        """Test listing all profiles."""
        # Create multiple
        DataPorter.create_profile(
            name="test_list1",
            engine="postgresql",
            host="localhost",
            user="user",
            database="db",
            password="pass",
            prompt_password=False,
        )
        
        DataPorter.create_profile(
            name="test_list2",
            engine="mysql",
            host="localhost",
            user="user",
            database="db",
            password="pass",
            prompt_password=False,
        )
        
        # List
        profiles = DataPorter.list_profiles()
        
        assert "test_list1" in profiles
        assert "test_list2" in profiles
        assert profiles["test_list1"] == "postgresql"
        assert profiles["test_list2"] == "mysql"
        
        # Cleanup
        DataPorter.delete_profile("test_list1")
        DataPorter.delete_profile("test_list2")
    
    def test_get_profiles_path(self):
        """Test getting profiles.yaml path."""
        path = DataPorter.get_profiles_path()
        
        assert isinstance(path, Path)
        assert path.name == "profiles.yaml"
        assert "DataPorter" in str(path) or "dataporter" in str(path.parent)
