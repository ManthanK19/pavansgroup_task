"""Export the OpenAPI specification to a JSON file.
Works without a running database by mocking the connection pool."""
import json
import sys
import types

# Mock the database module so importing app.main doesn't need a live MySQL
mock_db = types.ModuleType("app.database")
mock_db.get_db = lambda: None
sys.modules["app.database"] = mock_db

from app.main import app  # noqa: E402

with open("openapi.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)

print("Exported openapi.json")
