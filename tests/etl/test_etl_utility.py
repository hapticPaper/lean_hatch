"""Tests for the ETL utility package."""

import pytest
import json
import pandas as pd
from datetime import datetime, date
from pathlib import Path
import tempfile
import os

# Import ETL modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from etl.schema_loader import SchemaLoader, TableSchema, ColumnSchema
from etl.sql_types import SQLType, TypeHandler
from etl.data_caster import DataCaster
from etl.parquet_exporter import ParquetExporter


class TestSchemaLoader:
    """Test the SchemaLoader class."""
    
    def test_load_from_dict(self):
        """Test loading schema from a dictionary."""
        schema_dict = {
            "name": "test_table",
            "description": "Test table schema",
            "columns": [
                {
                    "name": "id",
                    "type": "INTEGER",
                    "mode": "REQUIRED",
                    "description": "Primary key"
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "mode": "NULLABLE"
                }
            ]
        }
        
        schema = SchemaLoader.load_from_dict(schema_dict)
        
        assert schema.name == "test_table"
        assert len(schema.columns) == 2
        assert schema.columns[0].name == "id"
        assert schema.columns[0].type == SQLType.INTEGER
        assert schema.columns[0].mode == "REQUIRED"
    
    def test_load_from_json_string(self):
        """Test loading schema from a JSON string."""
        json_string = '''
        {
            "name": "users",
            "columns": [
                {"name": "user_id", "type": "INT64", "mode": "REQUIRED"},
                {"name": "email", "type": "STRING", "mode": "REQUIRED"}
            ]
        }
        '''
        
        schema = SchemaLoader.load_from_json_string(json_string)
        
        assert schema.name == "users"
        assert len(schema.columns) == 2
    
    def test_invalid_mode(self):
        """Test that invalid mode raises an error."""
        schema_dict = {
            "name": "test",
            "columns": [
                {"name": "id", "type": "INTEGER", "mode": "INVALID"}
            ]
        }
        
        with pytest.raises(ValueError):
            SchemaLoader.load_from_dict(schema_dict)
    
    def test_empty_columns(self):
        """Test that empty columns list raises an error."""
        schema_dict = {
            "name": "test",
            "columns": []
        }
        
        with pytest.raises(ValueError):
            SchemaLoader.load_from_dict(schema_dict)


class TestTypeHandler:
    """Test the TypeHandler class."""
    
    def test_to_string(self):
        """Test string conversion."""
        assert TypeHandler.to_string("hello") == "hello"
        assert TypeHandler.to_string(123) == "123"
        assert TypeHandler.to_string(None) is None
        assert TypeHandler.to_string(pd.NA) is None
    
    def test_to_integer(self):
        """Test integer conversion."""
        assert TypeHandler.to_integer("123") == 123
        assert TypeHandler.to_integer(123.7) == 123
        assert TypeHandler.to_integer("") is None
        assert TypeHandler.to_integer(None) is None
        assert TypeHandler.to_integer("abc") is None
    
    def test_to_float(self):
        """Test float conversion."""
        assert TypeHandler.to_float("123.45") == 123.45
        assert TypeHandler.to_float(123) == 123.0
        assert TypeHandler.to_float("") is None
        assert TypeHandler.to_float(None) is None
    
    def test_to_boolean(self):
        """Test boolean conversion."""
        assert TypeHandler.to_boolean("true") is True
        assert TypeHandler.to_boolean("1") is True
        assert TypeHandler.to_boolean("yes") is True
        assert TypeHandler.to_boolean("false") is False
        assert TypeHandler.to_boolean("0") is False
        assert TypeHandler.to_boolean("") is False
        assert TypeHandler.to_boolean(None) is None
    
    def test_to_timestamp(self):
        """Test timestamp conversion."""
        ts = TypeHandler.to_timestamp("2024-01-01 12:00:00")
        assert isinstance(ts, pd.Timestamp)
        assert ts.tz is not None  # Should be UTC
        
        assert TypeHandler.to_timestamp(None) is None
        assert TypeHandler.to_timestamp("") is None
    
    def test_to_date(self):
        """Test date conversion."""
        d = TypeHandler.to_date("2024-01-01")
        assert isinstance(d, date)
        assert d.year == 2024
        assert d.month == 1
        assert d.day == 1
        
        assert TypeHandler.to_date(None) is None
        assert TypeHandler.to_date("") is None


class TestDataCaster:
    """Test the DataCaster class."""
    
    @pytest.fixture
    def sample_schema(self):
        """Create a sample schema for testing."""
        schema_dict = {
            "name": "test_data",
            "columns": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"},
                {"name": "name", "type": "STRING", "mode": "NULLABLE"},
                {"name": "amount", "type": "FLOAT", "mode": "NULLABLE"},
                {"name": "is_active", "type": "BOOLEAN", "mode": "NULLABLE"},
                {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"}
            ]
        }
        return SchemaLoader.load_from_dict(schema_dict)
    
    def test_cast_value(self, sample_schema):
        """Test casting individual values."""
        caster = DataCaster(sample_schema)
        
        col = sample_schema.columns[0]  # id - INTEGER
        assert caster.cast_value("123", col) == 123
        
        col = sample_schema.columns[2]  # amount - FLOAT
        assert caster.cast_value("45.67", col) == 45.67
    
    def test_cast_row(self, sample_schema):
        """Test casting a dictionary row."""
        caster = DataCaster(sample_schema)
        
        row = {
            "id": "1",
            "name": "Test User",
            "amount": "100.50",
            "is_active": "true",
            "created_at": "2024-01-01 12:00:00"
        }
        
        casted = caster.cast_row(row)
        
        assert casted["id"] == 1
        assert casted["name"] == "Test User"
        assert casted["amount"] == 100.50
        assert casted["is_active"] is True
        assert isinstance(casted["created_at"], pd.Timestamp)
    
    def test_cast_dataframe(self, sample_schema):
        """Test casting a DataFrame."""
        caster = DataCaster(sample_schema)
        
        df = pd.DataFrame([
            {"id": "1", "name": "User 1", "amount": "100", "is_active": "true", 
             "created_at": "2024-01-01"},
            {"id": "2", "name": "User 2", "amount": "200", "is_active": "false", 
             "created_at": "2024-01-02"}
        ])
        
        casted_df = caster.cast_dataframe(df)
        
        assert casted_df["id"].dtype == "Int64"
        assert casted_df["amount"].dtype == "float64"
        assert len(casted_df) == 2
    
    def test_required_field_validation(self):
        """Test that required fields are validated."""
        schema_dict = {
            "name": "test",
            "columns": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"}
            ]
        }
        schema = SchemaLoader.load_from_dict(schema_dict)
        caster = DataCaster(schema)
        
        df = pd.DataFrame([{"id": None}])
        
        with pytest.raises(ValueError, match="Required column"):
            caster.cast_dataframe(df)


class TestParquetExporter:
    """Test the ParquetExporter class."""
    
    @pytest.fixture
    def sample_schema(self):
        """Create a sample schema for testing."""
        schema_dict = {
            "name": "export_test",
            "columns": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"},
                {"name": "value", "type": "FLOAT", "mode": "NULLABLE"},
                {"name": "timestamp", "type": "TIMESTAMP", "mode": "NULLABLE"}
            ]
        }
        return SchemaLoader.load_from_dict(schema_dict)
    
    def test_export_and_read_dataframe(self, sample_schema):
        """Test exporting and reading a DataFrame."""
        exporter = ParquetExporter(sample_schema)
        
        df = pd.DataFrame([
            {"id": 1, "value": 10.5, "timestamp": "2024-01-01 12:00:00"},
            {"id": 2, "value": 20.5, "timestamp": "2024-01-02 12:00:00"}
        ])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.parquet"
            
            # Export
            exporter.export_dataframe(df, output_path)
            
            assert output_path.exists()
            
            # Read back
            df_read = exporter.read_parquet(output_path)
            
            assert len(df_read) == 2
            assert list(df_read.columns) == ["id", "value", "timestamp"]
    
    def test_export_records(self, sample_schema):
        """Test exporting records."""
        exporter = ParquetExporter(sample_schema)
        
        records = [
            {"id": 1, "value": 10.5, "timestamp": "2024-01-01"},
            {"id": 2, "value": 20.5, "timestamp": "2024-01-02"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_records.parquet"
            
            exporter.export_records(records, output_path)
            
            assert output_path.exists()
            
            df = pd.read_parquet(output_path)
            assert len(df) == 2


class TestEndToEnd:
    """End-to-end tests for the ETL utility."""
    
    def test_complete_etl_workflow(self):
        """Test a complete ETL workflow."""
        # Load schema from JSON
        schema_json = '''
        {
            "name": "sales_data",
            "description": "Sales transaction data",
            "columns": [
                {"name": "sale_id", "type": "STRING", "mode": "REQUIRED"},
                {"name": "amount", "type": "FLOAT", "mode": "REQUIRED"},
                {"name": "sale_date", "type": "TIMESTAMP", "mode": "REQUIRED"},
                {"name": "is_completed", "type": "BOOLEAN", "mode": "NULLABLE"}
            ]
        }
        '''
        
        schema = SchemaLoader.load_from_json_string(schema_json)
        
        # Create sample data
        raw_data = [
            {"sale_id": "S001", "amount": "150.50", "sale_date": "2024-01-01 10:30:00", 
             "is_completed": "true"},
            {"sale_id": "S002", "amount": "275.00", "sale_date": "2024-01-02 14:15:00", 
             "is_completed": "false"},
        ]
        
        # Cast data
        caster = DataCaster(schema)
        casted_data = caster.cast_records(raw_data)
        
        assert casted_data[0]["amount"] == 150.50
        assert casted_data[1]["is_completed"] is False
        
        # Export to parquet
        exporter = ParquetExporter(schema)
        df = pd.DataFrame(raw_data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sales.parquet"
            exporter.export_dataframe(df, output_path, cast_types=True)
            
            # Read back and verify
            df_result = exporter.read_parquet(output_path)
            assert len(df_result) == 2
            assert df_result["sale_id"].iloc[0] == "S001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
