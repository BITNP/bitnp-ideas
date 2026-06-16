import json
from datetime import UTC, datetime
from uuid import uuid4

from bitnp_ideas.security.api_keys import (
    body_sha256_hex,
    build_canonical_request,
    canonical_query_string,
    sign_canonical_request,
)


def sign_headers(
    *,
    key_id: str,
    secret: str,
    method: str,
    path: str,
    body: dict | None = None,
    nonce: str | None = None,
) -> dict[str, str]:
    timestamp = datetime.now(UTC).isoformat()
    body_bytes = json.dumps(body, separators=(",", ":")).encode() if body is not None else b""
    canonical = build_canonical_request(
        method=method,
        path=path,
        canonical_query_string=canonical_query_string(b""),
        body_hash=body_sha256_hex(body_bytes),
        timestamp=timestamp,
        nonce=nonce or f"nonce-{uuid4()}",
    )
    return {
        "X-Api-Key": key_id,
        "X-Api-Timestamp": timestamp,
        "X-Api-Nonce": canonical.rsplit("\n", 1)[-1],
        "X-Api-Signature-Version": "v1",
        "X-Api-Signature": sign_canonical_request(secret, canonical),
    }


def create_project(api_context, key: str = "API") -> dict:
    api_context.set_user(api_context.users.administrator)
    response = api_context.client.post(
        "/projects",
        json={
            "key": key,
            "name": f"{key} Project",
            "owner_id": api_context.users.developer.id,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_task(api_context, project_id: str, title: str) -> dict:
    response = api_context.client.post(
        f"/projects/{project_id}/tasks",
        json={
            "title": title,
            "assignee_id": api_context.users.developer.id,
            "start_date": "2026-07-01",
            "end_date": "2026-07-03",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_users_rbac_endpoints(api_context) -> None:
    response = api_context.client.get("/users")
    assert response.status_code == 200
    assert {user["email"] for user in response.json()} >= {
        "administrator@example.test",
        "developer@example.test",
    }

    response = api_context.client.patch(
        f"/users/{api_context.users.developer.id}/role",
        params={"role": "administrator"},
    )
    assert response.status_code == 403

    api_context.set_user(api_context.users.superuser)
    response = api_context.client.patch(
        f"/users/{api_context.users.developer.id}/role",
        params={"role": "developer"},
    )
    assert response.status_code == 200

    api_context.set_user(api_context.users.administrator)
    response = api_context.client.patch(
        f"/users/{api_context.users.developer.id}/active",
        params={"is_active": False},
    )
    assert response.status_code == 200


def test_ideas_tags_status_history_and_filters(api_context) -> None:
    tag_response = api_context.client.post(
        "/idea-tags",
        json={"name": "Backend", "color": "#1976D2", "description": "Backend work"},
    )
    assert tag_response.status_code == 201
    tag = tag_response.json()
    assert tag["name"] == "backend"

    api_context.set_user(api_context.users.developer)
    idea_response = api_context.client.post(
        "/ideas",
        json={
            "title": "Add workflow intake",
            "description": "Let external tools submit ideas.",
            "tag_names": ["backend"],
        },
    )
    assert idea_response.status_code == 201
    idea = idea_response.json()
    assert idea["tags"][0]["slug"] == "backend"

    filtered_response = api_context.client.get(
        "/ideas", params={"tag": "backend", "search": "workflow"}
    )
    assert filtered_response.status_code == 200
    assert [item["id"] for item in filtered_response.json()] == [idea["id"]]

    blocked_response = api_context.client.post(
        f"/ideas/{idea['id']}/status",
        json={"status": "in_progress"},
    )
    assert blocked_response.status_code == 422

    status_response = api_context.client.post(
        f"/ideas/{idea['id']}/status",
        json={
            "status": "in_progress",
            "linked_project_url": "https://github.com/BITNP/ideas",
            "note": "Ready to execute.",
        },
    )
    assert status_response.status_code == 200

    history_response = api_context.client.get(f"/ideas/{idea['id']}/history")
    assert history_response.status_code == 200
    assert [item["to_status"] for item in history_response.json()] == ["in_progress", "active"]

    remove_response = api_context.client.delete(f"/ideas/{idea['id']}/tags/{tag['id']}")
    assert remove_response.status_code == 200

    archive_response = api_context.client.delete(f"/ideas/{idea['id']}")
    assert archive_response.status_code == 200
    assert api_context.client.get(f"/ideas/{idea['id']}").status_code == 404


def test_projects_tasks_gantt_dependencies_and_activity(api_context) -> None:
    api_context.set_user(api_context.users.developer)
    denied_project = api_context.client.post("/projects", json={"key": "NO", "name": "Denied"})
    assert denied_project.status_code == 403

    project = create_project(api_context, "EXEC")
    api_context.set_user(api_context.users.outsider)
    assert api_context.client.get(f"/projects/{project['id']}").status_code == 403

    api_context.set_user(api_context.users.developer)
    assert api_context.client.get(f"/projects/{project['id']}").status_code == 200

    invalid_task = api_context.client.post(
        f"/projects/{project['id']}/tasks",
        json={"title": "Bad dates", "start_date": "2026-07-10", "end_date": "2026-07-01"},
    )
    assert invalid_task.status_code == 422

    first_task = create_task(api_context, project["id"], "Design API")
    second_task = create_task(api_context, project["id"], "Build UI")

    conflict_response = api_context.client.patch(
        f"/tasks/{first_task['id']}",
        json={"version": 999, "progress": 10},
    )
    assert conflict_response.status_code == 409

    bulk_response = api_context.client.patch(
        f"/projects/{project['id']}/gantt/bulk",
        json={
            "changes": [
                {
                    "task_id": first_task["id"],
                    "version": first_task["version"],
                    "start_date": "2026-07-02",
                    "end_date": "2026-07-05",
                    "progress": 40,
                    "status": "in_progress",
                }
            ]
        },
    )
    assert bulk_response.status_code == 200

    dependency_response = api_context.client.post(
        f"/projects/{project['id']}/task-dependencies",
        json={
            "predecessor_task_id": first_task["id"],
            "successor_task_id": second_task["id"],
        },
    )
    assert dependency_response.status_code == 200

    duplicate_response = api_context.client.post(
        f"/projects/{project['id']}/task-dependencies",
        json={
            "predecessor_task_id": first_task["id"],
            "successor_task_id": second_task["id"],
        },
    )
    assert duplicate_response.status_code == 409

    cycle_response = api_context.client.post(
        f"/projects/{project['id']}/task-dependencies",
        json={
            "predecessor_task_id": second_task["id"],
            "successor_task_id": first_task["id"],
        },
    )
    assert cycle_response.status_code == 422

    gantt_response = api_context.client.get(f"/projects/{project['id']}/gantt")
    assert gantt_response.status_code == 200
    gantt = gantt_response.json()
    assert len(gantt["tasks"]) == 2
    assert len(gantt["dependencies"]) == 1

    activity_response = api_context.client.get(
        f"/projects/{project['id']}/activity",
        params={"entity_type": "task", "limit": 5},
    )
    assert activity_response.status_code == 200
    assert {item["action_type"] for item in activity_response.json()} >= {
        "task.created",
        "task.rescheduled",
    }

    dependency_id = gantt["dependencies"][0]["id"]
    delete_response = api_context.client.delete(
        f"/projects/{project['id']}/task-dependencies/{dependency_id}"
    )
    assert delete_response.status_code == 200

    archive_response = api_context.client.delete(f"/tasks/{second_task['id']}")
    assert archive_response.status_code == 200


def test_project_idea_links_and_external_links(api_context) -> None:
    project = create_project(api_context, "LINK")

    idea_response = api_context.client.post("/ideas", json={"title": "Connect planning"})
    assert idea_response.status_code == 201
    idea = idea_response.json()

    link_response = api_context.client.post(
        f"/projects/{project['id']}/ideas",
        json={"idea_id": idea["id"], "relation_type": "origin"},
    )
    assert link_response.status_code == 200

    project_ideas = api_context.client.get(f"/projects/{project['id']}/ideas")
    assert project_ideas.status_code == 200
    assert [item["id"] for item in project_ideas.json()] == [idea["id"]]

    external_link = api_context.client.post(
        f"/project/{project['id']}/links",
        json={
            "url": "https://github.com/BITNP/ideas",
            "title": "Repository",
            "link_type": "github_repo",
        },
    )
    assert external_link.status_code == 201
    external_link_id = external_link.json()["id"]

    preview = api_context.client.post(
        "/links/preview",
        json={"url": "https://github.com/BITNP/ideas", "title": "Repository"},
    )
    assert preview.status_code == 200
    assert preview.json()["title"] == "Repository"

    invalid_entity = api_context.client.get(f"/unknown/{project['id']}/links")
    assert invalid_entity.status_code == 422

    assert api_context.client.delete(f"/links/{external_link_id}").status_code == 200
    unlink_response = api_context.client.delete(f"/projects/{project['id']}/ideas/{idea['id']}")
    assert unlink_response.status_code == 200


def test_api_keys_management_and_signed_idea_only_access(api_context) -> None:
    api_context.set_user(api_context.users.developer)
    create_response = api_context.client.post("/api-keys", json={"name": "Workflow"})
    assert create_response.status_code == 201
    created = create_response.json()
    api_key = created["api_key"]
    secret = created["secret"]
    assert secret.endswith(api_key["secret_last4"])
    assert api_key["allowed_entities"] == ["idea"]

    listed = api_context.client.get("/api-keys")
    assert listed.status_code == 200
    assert "secret" not in listed.json()[0]

    rejected_scope = api_context.client.post(
        "/api-keys",
        json={"name": "Bad scope", "scopes": ["ideas:read", "projects:write"]},
    )
    assert rejected_scope.status_code == 422

    update_response = api_context.client.patch(
        f"/api-keys/{api_key['id']}",
        json={"name": "Workflow readonly", "scopes": ["ideas:read"]},
    )
    assert update_response.status_code == 200

    rotate_response = api_context.client.post(f"/api-keys/{api_key['id']}/rotate")
    assert rotate_response.status_code == 200
    rotated = rotate_response.json()
    secret = rotated["secret"]
    key_id = rotated["api_key"]["key_id"]

    api_context.use_real_auth()
    signed_ideas = api_context.client.get(
        "/ideas",
        headers=sign_headers(key_id=key_id, secret=secret, method="GET", path="/ideas"),
    )
    assert signed_ideas.status_code == 200

    signed_projects = api_context.client.get(
        "/projects",
        headers=sign_headers(key_id=key_id, secret=secret, method="GET", path="/projects"),
    )
    assert signed_projects.status_code == 403
    api_context.use_stub_auth()

    revoke_response = api_context.client.delete(f"/api-keys/{api_key['id']}")
    assert revoke_response.status_code == 200
