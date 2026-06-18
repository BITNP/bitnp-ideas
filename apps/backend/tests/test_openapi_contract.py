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


def operation_success_schema(schema: dict[str, Any], path: str, method: str, status: str) -> dict:
    return schema["paths"][path][method]["responses"][status]["content"]["application/json"][
        "schema"
    ]


def response_ref_name(schema: dict[str, Any], path: str, method: str, status: str) -> str | None:
    success_schema = operation_success_schema(schema, path, method, status)
    ref = success_schema.get("$ref")
    return ref.rsplit("/", 1)[-1] if isinstance(ref, str) else None


def resolved_success_schema(schema: dict[str, Any], path: str, method: str, status: str) -> dict:
    success_schema = operation_success_schema(schema, path, method, status)
    ref_name = response_ref_name(schema, path, method, status)
    if ref_name is not None:
        return component(schema, ref_name)
    return success_schema


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


def test_gantt_read_uses_task_read_items() -> None:
    schema = openapi_schema()

    tasks_schema = component(schema, "GanttRead")["properties"]["tasks"]

    assert tasks_schema["items"]["$ref"].endswith("/TaskRead")


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


def test_auth_responses_match_frontend_contract() -> None:
    schema = openapi_schema()

    login_response = schema["paths"]["/auth/login"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    login_schema = component(schema, login_response["$ref"].rsplit("/", 1)[-1])
    assert {"authorization_url", "state"} <= set(login_schema["required"])

    callback_response = schema["paths"]["/auth/callback"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    callback_schema = component(schema, callback_response["$ref"].rsplit("/", 1)[-1])
    assert {"access_token", "token_type", "user"} <= set(callback_schema["required"])
    user_schema = callback_schema["properties"]["user"]
    assert user_schema["$ref"].endswith("/CurrentUser")


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


def test_frontend_api_module_routes_exist_in_openapi() -> None:
    schema = openapi_schema()

    expected_routes = [
        ("get", "/auth/login", "200", "LoginResponse"),
        ("get", "/auth/callback", "200", "CallbackResponse"),
        ("get", "/auth/me", "200", "CurrentUser"),
        ("post", "/auth/logout", "200", "ApiMessage"),
        ("get", "/users", "200", None),
        ("get", "/users/{user_id}", "200", "CurrentUser"),
        ("patch", "/users/{user_id}/role", "200", "ApiMessage"),
        ("patch", "/users/{user_id}/active", "200", "ApiMessage"),
        ("get", "/idea-tags", "200", None),
        ("post", "/idea-tags", "201", "IdeaTagRead"),
        ("get", "/idea-tags/{tag_id}", "200", "IdeaTagRead"),
        ("patch", "/idea-tags/{tag_id}", "200", "IdeaTagRead"),
        ("delete", "/idea-tags/{tag_id}", "200", "ApiMessage"),
        ("get", "/ideas", "200", None),
        ("post", "/ideas", "201", "IdeaRead"),
        ("get", "/ideas/{idea_id}", "200", "IdeaRead"),
        ("patch", "/ideas/{idea_id}", "200", "IdeaRead"),
        ("delete", "/ideas/{idea_id}", "200", "ApiMessage"),
        ("post", "/ideas/{idea_id}/status", "200", "ApiMessage"),
        ("get", "/ideas/{idea_id}/history", "200", None),
        ("post", "/ideas/{idea_id}/tags", "200", "ApiMessage"),
        ("delete", "/ideas/{idea_id}/tags/{tag_id}", "200", "ApiMessage"),
        ("get", "/projects", "200", None),
        ("post", "/projects", "201", "ProjectRead"),
        ("get", "/projects/{project_id}", "200", "ProjectRead"),
        ("patch", "/projects/{project_id}", "200", "ProjectRead"),
        ("delete", "/projects/{project_id}", "200", "ApiMessage"),
        ("post", "/projects/{project_id}/members", "200", "ApiMessage"),
        ("delete", "/projects/{project_id}/members/{user_id}", "200", "ApiMessage"),
        ("get", "/projects/{project_id}/ideas", "200", None),
        ("post", "/projects/{project_id}/ideas", "200", "ApiMessage"),
        ("delete", "/projects/{project_id}/ideas/{idea_id}", "200", "ApiMessage"),
        ("get", "/projects/{project_id}/tasks", "200", None),
        ("post", "/projects/{project_id}/tasks", "201", "TaskRead"),
        ("get", "/tasks/{task_id}", "200", "TaskRead"),
        ("patch", "/tasks/{task_id}", "200", "TaskRead"),
        ("delete", "/tasks/{task_id}", "200", "ApiMessage"),
        ("get", "/projects/{project_id}/gantt", "200", "GanttRead"),
        ("patch", "/projects/{project_id}/gantt/bulk", "200", "ApiMessage"),
        ("post", "/projects/{project_id}/task-dependencies", "200", "ApiMessage"),
        (
            "delete",
            "/projects/{project_id}/task-dependencies/{dependency_id}",
            "200",
            "ApiMessage",
        ),
        ("get", "/projects/{project_id}/activity", "200", None),
        ("get", "/api-keys", "200", None),
        ("post", "/api-keys", "201", "ApiKeyCreateResponse"),
        ("patch", "/api-keys/{api_key_id}", "200", "ApiMessage"),
        ("delete", "/api-keys/{api_key_id}", "200", "ApiMessage"),
        ("post", "/api-keys/{api_key_id}/rotate", "200", "ApiKeyCreateResponse"),
        ("get", "/audit-logs", "200", None),
        ("get", "/{entity_type}/{entity_id}/links", "200", None),
        ("post", "/{entity_type}/{entity_id}/links", "201", "ExternalLinkRead"),
        ("delete", "/links/{link_id}", "200", "ApiMessage"),
        ("post", "/links/preview", "200", "LinkPreview"),
    ]

    missing: list[str] = []
    schema_mismatches: list[str] = []

    for method, path, status_code, expected_ref in expected_routes:
        operation = schema["paths"].get(path, {}).get(method)
        if operation is None:
            missing.append(f"{method.upper()} {path}")
            continue
        if status_code not in operation.get("responses", {}):
            missing.append(f"{method.upper()} {path} response {status_code}")
            continue
        if expected_ref is not None:
            actual_ref = response_ref_name(schema, path, method, status_code)
            if actual_ref != expected_ref:
                schema_mismatches.append(
                    f"{method.upper()} {path}: expected {expected_ref}, got {actual_ref}"
                )
        else:
            properties = resolved_success_schema(schema, path, method, status_code).get(
                "properties", {}
            )
            if not {"data", "total"} <= set(properties):
                schema_mismatches.append(f"{method.upper()} {path}: expected Page response")

    assert missing == []
    assert schema_mismatches == []
