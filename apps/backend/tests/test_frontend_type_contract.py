import re
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from bitnp_ideas.main import app

FRONTEND_API_TYPES = Path(__file__).resolve().parents[2] / "frontend" / "src" / "types" / "api.ts"
READ_MODEL_CONTRACTS = {
    "ActivityRead": "ActivityRead",
    "ApiKeyRead": "ApiKeyRead",
    "AuditLogRead": "AuditLogRead",
    "CurrentUser": "CurrentUser",
    "EntityRef": "EntityRef",
    "ExternalLinkRead": "ExternalLinkRead",
    "IdeaRead": "IdeaRead",
    "IdeaStatusHistoryRead": "IdeaStatusHistoryRead",
    "IdeaTagRead": "TagRead",
    "ProjectRead": "ProjectRead",
    "TaskRead": "TaskRead",
}
WRITE_MODEL_CONTRACTS = {
    "ApiKeyCreate": "ApiKeyCreate",
    "ApiKeyUpdate": "ApiKeyUpdate",
    "ExternalLinkCreate": "ExternalLinkCreate",
    "GanttBulkChange": "GanttBulkChange",
    "GanttBulkUpdate": "GanttBulkUpdate",
    "IdeaCreate": "IdeaCreate",
    "IdeaStatusUpdate": "IdeaStatusUpdate",
    "IdeaTagCreate": "TagCreate",
    "IdeaTagUpdate": "TagUpdate",
    "IdeaUpdate": "IdeaUpdate",
    "ProjectCreate": "ProjectCreate",
    "ProjectUpdate": "ProjectUpdate",
    "TaskCreate": "TaskCreate",
    "TaskDependencyCreate": "TaskDependencyCreate",
    "TaskUpdate": "TaskUpdate",
}


def openapi_schema() -> dict[str, Any]:
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


def frontend_interfaces() -> dict[str, dict[str, str]]:
    source = FRONTEND_API_TYPES.read_text(encoding="utf-8")
    interfaces: dict[str, dict[str, str]] = {}
    for match in re.finditer(r"export interface (?P<name>\w+) \{(?P<body>.*?)\n\}", source, re.S):
        fields: dict[str, str] = {}
        for line in match.group("body").splitlines():
            field_match = re.match(r"\s*(?P<name>\w+)(?P<optional>\?)?: (?P<type>.+)", line)
            if field_match is None:
                continue
            fields[field_match.group("name")] = field_match.group("type").rstrip()
        interfaces[match.group("name")] = fields
    return interfaces


def schema_allows_null(schema: dict[str, Any]) -> bool:
    if schema.get("type") == "null":
        return True
    if "anyOf" in schema:
        return any(schema_allows_null(option) for option in schema["anyOf"])
    return False


def schema_ref_name(schema: dict[str, Any]) -> str | None:
    ref = schema.get("$ref")
    if not isinstance(ref, str):
        return None
    return ref.rsplit("/", 1)[-1]


def request_body_ref(schema: dict[str, Any], path: str, method: str) -> str:
    request_schema = schema["paths"][path][method]["requestBody"]["content"]["application/json"][
        "schema"
    ]
    ref_name = schema_ref_name(request_schema)
    assert ref_name is not None
    return ref_name


def test_frontend_read_interfaces_match_openapi_fields_and_nullability() -> None:
    schema = openapi_schema()
    components = schema["components"]["schemas"]
    interfaces = frontend_interfaces()

    assert set(READ_MODEL_CONTRACTS.values()) <= interfaces.keys()

    failures: list[str] = []
    for model_name, interface_name in sorted(READ_MODEL_CONTRACTS.items()):
        backend_properties = components[model_name]["properties"]
        frontend_fields = interfaces[interface_name]
        if set(frontend_fields) != set(backend_properties):
            failures.append(
                f"{model_name}/{interface_name}: fields differ; "
                f"frontend={sorted(frontend_fields)}, backend={sorted(backend_properties)}"
            )
            continue

        for field_name, field_schema in backend_properties.items():
            frontend_type = frontend_fields[field_name]
            if schema_allows_null(field_schema) and "| null" not in frontend_type:
                failures.append(
                    f"{model_name}.{field_name}: OpenAPI allows null but frontend type is "
                    f"{frontend_type!r}"
                )
            if not schema_allows_null(field_schema) and "| null" in frontend_type:
                failures.append(
                    f"{model_name}.{field_name}: frontend allows null but OpenAPI does not"
                )

    assert failures == []


def test_frontend_write_interfaces_match_openapi_fields_and_nullability() -> None:
    schema = openapi_schema()
    components = schema["components"]["schemas"]
    interfaces = frontend_interfaces()

    assert set(WRITE_MODEL_CONTRACTS.values()) <= interfaces.keys()

    expected_request_models = {
        "ApiKeyCreate": request_body_ref(schema, "/api-keys", "post"),
        "ApiKeyUpdate": request_body_ref(schema, "/api-keys/{api_key_id}", "patch"),
        "ExternalLinkCreate": request_body_ref(schema, "/{entity_type}/{entity_id}/links", "post"),
        "GanttBulkUpdate": request_body_ref(schema, "/projects/{project_id}/gantt/bulk", "patch"),
        "IdeaCreate": request_body_ref(schema, "/ideas", "post"),
        "IdeaStatusUpdate": request_body_ref(schema, "/ideas/{idea_id}/status", "post"),
        "IdeaUpdate": request_body_ref(schema, "/ideas/{idea_id}", "patch"),
        "IdeaTagCreate": request_body_ref(schema, "/idea-tags", "post"),
        "IdeaTagUpdate": request_body_ref(schema, "/idea-tags/{tag_id}", "patch"),
        "ProjectCreate": request_body_ref(schema, "/projects", "post"),
        "ProjectUpdate": request_body_ref(schema, "/projects/{project_id}", "patch"),
        "TaskCreate": request_body_ref(schema, "/projects/{project_id}/tasks", "post"),
        "TaskDependencyCreate": request_body_ref(
            schema, "/projects/{project_id}/task-dependencies", "post"
        ),
        "TaskUpdate": request_body_ref(schema, "/tasks/{task_id}", "patch"),
    }
    assert expected_request_models == {
        backend_name: backend_name
        for backend_name in WRITE_MODEL_CONTRACTS
        if backend_name != "GanttBulkChange"
    }

    failures: list[str] = []
    for model_name, interface_name in sorted(WRITE_MODEL_CONTRACTS.items()):
        backend_properties = components[model_name]["properties"]
        frontend_fields = interfaces[interface_name]
        if set(frontend_fields) != set(backend_properties):
            failures.append(
                f"{model_name}/{interface_name}: fields differ; "
                f"frontend={sorted(frontend_fields)}, backend={sorted(backend_properties)}"
            )
            continue

        for field_name, field_schema in backend_properties.items():
            frontend_type = frontend_fields[field_name]
            if schema_allows_null(field_schema) and "| null" not in frontend_type:
                failures.append(
                    f"{model_name}.{field_name}: OpenAPI allows null but frontend type is "
                    f"{frontend_type!r}"
                )
            if not schema_allows_null(field_schema) and "| null" in frontend_type:
                failures.append(
                    f"{model_name}.{field_name}: frontend allows null but OpenAPI does not"
                )

    assert failures == []
