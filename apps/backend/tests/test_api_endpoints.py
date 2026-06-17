import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from bitnp_ideas.models.entities import ApiKey
from bitnp_ideas.security.api_keys import (
    PROTECTED_SECRET_PREFIX,
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
    user_page = response.json()
    assert set(user_page) == {"data", "total"}
    assert {user["email"] for user in user_page["data"]} >= {
        "administrator@example.test",
        "developer@example.test",
    }
    paged_response = api_context.client.get("/users", params={"offset": 1, "limit": 2})
    assert paged_response.status_code == 200
    paged_user_page = paged_response.json()
    assert len(paged_user_page["data"]) == 2
    assert paged_user_page["total"] >= 4

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

    tags_response = api_context.client.get("/idea-tags", params={"offset": 0, "limit": 10})
    assert tags_response.status_code == 200
    tag_page = tags_response.json()
    assert set(tag_page) == {"data", "total"}
    assert [item["slug"] for item in tag_page["data"]] == ["backend"]
    assert tag_page["total"] == 1

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
    filtered_page = filtered_response.json()
    assert set(filtered_page) == {"data", "total"}
    assert [item["id"] for item in filtered_page["data"]] == [idea["id"]]
    assert filtered_page["total"] == 1

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
    history_page = history_response.json()
    assert set(history_page) == {"data", "total"}
    assert [item["to_status"] for item in history_page["data"]] == ["in_progress", "active"]
    assert history_page["total"] == 2
    paged_history = api_context.client.get(
        f"/ideas/{idea['id']}/history", params={"offset": 1, "limit": 1}
    )
    assert paged_history.status_code == 200
    paged_history_page = paged_history.json()
    assert set(paged_history_page) == {"data", "total"}
    assert [item["to_status"] for item in paged_history_page["data"]] == ["active"]
    assert paged_history_page["total"] == 2

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
    projects_response = api_context.client.get("/projects", params={"offset": 0, "limit": 1})
    assert projects_response.status_code == 200
    project_page = projects_response.json()
    assert set(project_page) == {"data", "total"}
    assert len(project_page["data"]) == 1
    assert project_page["total"] >= 1

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

    tasks_response = api_context.client.get(
        f"/projects/{project['id']}/tasks", params={"offset": 0, "limit": 1}
    )
    assert tasks_response.status_code == 200
    task_page = tasks_response.json()
    assert set(task_page) == {"data", "total"}
    assert len(task_page["data"]) == 1
    assert task_page["total"] == 2

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
    activity_page = activity_response.json()
    assert set(activity_page) == {"data", "total"}
    assert {item["action_type"] for item in activity_page["data"]} >= {
        "task.created",
        "task.rescheduled",
    }
    assert activity_page["total"] >= 2

    dependency_id = gantt["dependencies"][0]["id"]
    delete_response = api_context.client.delete(
        f"/projects/{project['id']}/task-dependencies/{dependency_id}"
    )
    assert delete_response.status_code == 200

    archive_response = api_context.client.delete(f"/tasks/{second_task['id']}")
    assert archive_response.status_code == 200


def test_audit_logs_are_superuser_only_and_filterable(api_context) -> None:
    project = create_project(api_context, "AUDIT")

    api_context.set_user(api_context.users.administrator)
    denied = api_context.client.get("/audit-logs")
    assert denied.status_code == 403

    api_context.set_user(api_context.users.superuser)
    response = api_context.client.get(
        "/audit-logs",
        params={"action": "project.created", "entity_type": "project"},
    )
    assert response.status_code == 200
    audit_page = response.json()
    assert set(audit_page) == {"data", "total"}
    assert audit_page["total"] >= 1
    logs = audit_page["data"]
    assert any(log["entity_id"] == project["id"] for log in logs)
    assert {log["action"] for log in logs} == {"project.created"}


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
    project_ideas_page = project_ideas.json()
    assert set(project_ideas_page) == {"data", "total"}
    assert [item["id"] for item in project_ideas_page["data"]] == [idea["id"]]
    assert project_ideas_page["total"] == 1

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

    links_response = api_context.client.get(f"/project/{project['id']}/links")
    assert links_response.status_code == 200
    link_page = links_response.json()
    assert set(link_page) == {"data", "total"}
    assert [link["id"] for link in link_page["data"]] == [external_link_id]
    assert link_page["total"] == 1

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
    stored_secret = api_context.run(stored_api_key_secret(api_context, api_key["id"]))
    assert stored_secret != secret
    assert stored_secret.startswith(PROTECTED_SECRET_PREFIX)

    listed = api_context.client.get("/api-keys")
    assert listed.status_code == 200
    listed_page = listed.json()
    assert set(listed_page) == {"data", "total"}
    assert "secret" not in listed_page["data"][0]
    assert listed_page["total"] == 1

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
    rotated_stored_secret = api_context.run(stored_api_key_secret(api_context, api_key["id"]))
    assert rotated_stored_secret != secret
    assert rotated_stored_secret.startswith(PROTECTED_SECRET_PREFIX)

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


async def stored_api_key_secret(api_context, api_key_id: str) -> str:
    async with api_context.sessionmaker() as session:
        stored = await session.scalar(select(ApiKey).where(ApiKey.id == api_key_id))
        assert stored is not None
        return stored.secret_hash
