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
        "AuditLogRead": {"actor_user_id", "actor_api_key_id", "metadata", "created_at"},
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


def test_audit_logs_route_is_exposed_without_api_version_prefix() -> None:
    schema = openapi_schema()

    assert "/audit-logs" in schema["paths"]
    assert "/api/v1/audit-logs" not in schema["paths"]


def test_paginated_get_routes_expose_offset_limit_and_page_shape() -> None:
    schema = openapi_schema()

    expected_paths = {
        "/api-keys",
        "/audit-logs",
        "/idea-tags",
        "/ideas",
        "/ideas/{idea_id}/history",
        "/projects",
        "/projects/{project_id}/activity",
        "/projects/{project_id}/ideas",
        "/projects/{project_id}/tasks",
        "/users",
        "/{entity_type}/{entity_id}/links",
    }
    paginated_routes: set[str] = set()
    invalid_page_routes: list[str] = []
    for path, methods in schema["paths"].items():
        operation = methods.get("get")
        if operation is None:
            continue
        parameter_names = {parameter["name"] for parameter in operation.get("parameters", [])}
        if not {"offset", "limit"} <= parameter_names:
            continue
        paginated_routes.add(path)
        success_response = operation.get("responses", {}).get("200", {})
        response_schema = (
            success_response.get("content", {}).get("application/json", {}).get("schema", {})
        )
        if "$ref" in response_schema:
            response_schema = component(schema, response_schema["$ref"].rsplit("/", 1)[-1])
        properties = response_schema.get("properties", {})
        data_schema = properties.get("data", {})
        required = set(response_schema.get("required", []))
        if not (
            {"data", "total"} <= properties.keys()
            and {"data", "total"} <= required
            and data_schema.get("type") == "array"
            and properties.get("total", {}).get("type") == "integer"
        ):
            invalid_page_routes.append(path)

    assert paginated_routes == expected_paths
    assert invalid_page_routes == []
