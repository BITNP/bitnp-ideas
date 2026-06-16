from typing import Any

from fastapi.testclient import TestClient

from bitnp_ideas.main import app


def openapi_schema() -> dict[str, Any]:
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


def component(schema: dict[str, Any], name: str) -> dict[str, Any]:
    return schema["components"]["schemas"][name]


def test_frontend_read_models_expose_timestamps() -> None:
    schema = openapi_schema()

    expected_fields = {
        "IdeaTagRead": {"created_at"},
        "ProjectRead": {"created_at", "updated_at"},
        "TaskRead": {"created_at", "updated_at"},
        "ApiKeyRead": {"created_at"},
        "ExternalLinkRead": {"created_at", "description", "image_url", "site_name"},
    }

    for schema_name, fields in expected_fields.items():
        properties = component(schema, schema_name)["properties"]
        assert fields <= properties.keys()


def test_gantt_bulk_change_accepts_status() -> None:
    schema = openapi_schema()

    properties = component(schema, "GanttBulkChange")["properties"]

    expected = {
        "task_id",
        "version",
        "start_date",
        "end_date",
        "assignee_id",
        "progress",
        "status",
    }

    assert expected <= properties.keys()


def test_link_preview_has_preview_shape() -> None:
    schema = openapi_schema()

    preview_response = schema["paths"]["/links/preview"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    properties = component(schema, preview_response["$ref"].rsplit("/", 1)[-1])["properties"]

    assert {"url", "title", "description", "image"} <= properties.keys()
