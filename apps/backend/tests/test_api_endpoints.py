import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from sqlalchemy import select

from bitnp_ideas.api.routes import auth as auth_routes
from bitnp_ideas.core.config import settings
from bitnp_ideas.models.entities import ApiKey
from bitnp_ideas.security.api_keys import (
    PROTECTED_SECRET_PREFIX,
    body_sha256_hex,
    build_canonical_request,
    canonical_query_string,
    sign_canonical_request,
)
from bitnp_ideas.security.oidc_adapter import OidcLoginRequest


def sign_headers(
    *,
    key_id: str,
    secret: str,
    method: str,
    path: str,
    body: dict | None = None,
    nonce: str | None = None,
    query_string: bytes = b"",
) -> dict[str, str]:
    timestamp = datetime.now(UTC).isoformat()
    body_bytes = json.dumps(body, separators=(",", ":")).encode() if body is not None else b""
    canonical = build_canonical_request(
        method=method,
        path=path,
        canonical_query_string=canonical_query_string(query_string),
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


def test_auth_login_returns_signed_oidc_state(api_context, monkeypatch) -> None:
    redirect_uri = "http://localhost:5173/login"

    async def fake_build_login_request(state: str, redirect_uri: str) -> OidcLoginRequest:
        return OidcLoginRequest(
            authorization_url=f"https://idp.example.test/auth?state={state}",
            state=state,
        )

    monkeypatch.setattr(auth_routes.oidc_adapter, "build_login_request", fake_build_login_request)

    response = api_context.client.get("/auth/login", params={"redirect_uri": redirect_uri})

    assert response.status_code == 200
    body = response.json()
    state_payload = jwt.decode(
        body["state"],
        settings.security.session_secret_key,
        algorithms=["HS256"],
    )
    assert state_payload["kind"] == "oidc_state"
    assert state_payload["redirect_uri"] == redirect_uri
    assert isinstance(state_payload["exp"], int)


def test_auth_callback_rejects_invalid_oidc_state_before_exchange(api_context, monkeypatch) -> None:
    exchange_called = False

    async def fake_exchange_code(code: str, redirect_uri: str) -> dict:
        nonlocal exchange_called
        exchange_called = True
        return {"access_token": "should-not-be-used"}

    monkeypatch.setattr(auth_routes.oidc_adapter, "exchange_code", fake_exchange_code)

    response = api_context.client.get(
        "/auth/callback",
        params={
            "code": "oidc-code",
            "state": "not-a-valid-state",
            "redirect_uri": "http://localhost:5173/login",
        },
    )

    assert response.status_code == 401
    assert exchange_called is False


def test_auth_callback_accepts_valid_state_and_returns_expiring_session_token(
    api_context, monkeypatch
) -> None:
    redirect_uri = "http://localhost:5173/login"
    state = api_context.run(auth_routes.create_oidc_state(redirect_uri))

    async def fake_exchange_code(code: str, redirect_uri: str) -> dict:
        return {"access_token": "oidc-access-token"}

    async def fake_userinfo(access_token: str) -> dict:
        return {
            "sub": "oidc-subject",
            "email": "oidc-user@example.test",
            "name": "OIDC User",
        }

    monkeypatch.setattr(auth_routes.oidc_adapter, "exchange_code", fake_exchange_code)
    monkeypatch.setattr(auth_routes.oidc_adapter, "userinfo", fake_userinfo)

    response = api_context.client.get(
        "/auth/callback",
        params={"code": "oidc-code", "state": state, "redirect_uri": redirect_uri},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "oidc-user@example.test"
    session_payload = jwt.decode(
        body["access_token"],
        settings.security.session_secret_key,
        algorithms=["HS256"],
    )
    assert session_payload["email"] == "oidc-user@example.test"
    assert isinstance(session_payload["jti"], str)
    assert isinstance(session_payload["exp"], int)


def test_logout_revokes_current_bearer_session_token(api_context) -> None:
    token = jwt.encode(
        {
            "sub": api_context.users.developer.id,
            "jti": f"session-{uuid4()}",
            "email": api_context.users.developer.email,
            "name": api_context.users.developer.display_name,
            "role": api_context.users.developer.global_role,
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(hours=1),
        },
        settings.security.session_secret_key,
        algorithm="HS256",
    )

    api_context.use_real_auth()
    headers = {"Authorization": f"Bearer {token}"}
    assert api_context.client.get("/auth/me", headers=headers).status_code == 200
    logout_response = api_context.client.post("/auth/logout", headers=headers)
    revoked_response = api_context.client.get("/auth/me", headers=headers)
    api_context.use_stub_auth()

    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "logged out"}
    assert revoked_response.status_code == 401


def test_expired_bearer_session_token_is_rejected(api_context) -> None:
    expired_token = jwt.encode(
        {
            "sub": api_context.users.developer.id,
            "jti": f"session-{uuid4()}",
            "email": api_context.users.developer.email,
            "name": api_context.users.developer.display_name,
            "role": api_context.users.developer.global_role,
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "exp": datetime.now(UTC) - timedelta(hours=1),
        },
        settings.security.session_secret_key,
        algorithm="HS256",
    )

    api_context.use_real_auth()
    response = api_context.client.get(
        "/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )
    api_context.use_stub_auth()

    assert response.status_code == 401


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
    second_tag_response = api_context.client.post(
        "/idea-tags",
        json={"name": "Frontend", "color": "#7C4DFF", "description": "Frontend work"},
    )
    assert second_tag_response.status_code == 201

    tags_response = api_context.client.get("/idea-tags", params={"offset": 0, "limit": 10})
    assert tags_response.status_code == 200
    tag_page = tags_response.json()
    assert set(tag_page) == {"data", "total"}
    assert {item["slug"] for item in tag_page["data"]} == {"backend", "frontend"}
    assert tag_page["total"] == 2

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
    second_idea_response = api_context.client.post("/ideas", json={"title": "Improve dashboard"})
    assert second_idea_response.status_code == 201

    filtered_response = api_context.client.get(
        "/ideas", params={"tag": "backend", "search": "workflow"}
    )
    assert filtered_response.status_code == 200
    filtered_page = filtered_response.json()
    assert set(filtered_page) == {"data", "total"}
    assert [item["id"] for item in filtered_page["data"]] == [idea["id"]]
    assert filtered_page["total"] == 1
    paged_ideas = api_context.client.get("/ideas", params={"offset": 1, "limit": 1})
    assert paged_ideas.status_code == 200
    paged_ideas_page = paged_ideas.json()
    assert set(paged_ideas_page) == {"data", "total"}
    assert len(paged_ideas_page["data"]) == 1
    assert paged_ideas_page["total"] == 2

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
    paged_tags = api_context.client.get("/idea-tags", params={"offset": 1, "limit": 1})
    assert paged_tags.status_code == 200
    paged_tag_page = paged_tags.json()
    assert set(paged_tag_page) == {"data", "total"}
    assert len(paged_tag_page["data"]) == 1
    assert paged_tag_page["total"] == 2

    api_context.set_user(api_context.users.outsider)
    denied_update = api_context.client.patch(
        f"/ideas/{idea['id']}",
        json={"title": "Outsider update"},
    )
    assert denied_update.status_code == 403
    denied_status = api_context.client.post(
        f"/ideas/{idea['id']}/status",
        json={"status": "active"},
    )
    assert denied_status.status_code == 403
    denied_tags = api_context.client.post(
        f"/ideas/{idea['id']}/tags",
        json={"tag_ids": [tag["id"]]},
    )
    assert denied_tags.status_code == 403
    denied_archive = api_context.client.delete(f"/ideas/{idea['id']}")
    assert denied_archive.status_code == 403

    api_context.set_user(api_context.users.developer)
    remove_response = api_context.client.delete(f"/ideas/{idea['id']}/tags/{tag['id']}")
    assert remove_response.status_code == 200

    archive_response = api_context.client.delete(f"/ideas/{idea['id']}")
    assert archive_response.status_code == 200
    assert api_context.client.get(f"/ideas/{idea['id']}").status_code == 404


def test_projects_tasks_gantt_dependencies_and_activity(api_context) -> None:
    api_context.set_user(api_context.users.developer)
    denied_project = api_context.client.post("/projects", json={"key": "NO", "name": "Denied"})
    assert denied_project.status_code == 403

    api_context.set_user(api_context.users.administrator)
    missing_owner = api_context.client.post(
        "/projects",
        json={"key": "MISS", "name": "Missing Owner", "owner_id": "missing-user"},
    )
    assert missing_owner.status_code == 404

    project = create_project(api_context, "EXEC")
    create_project(api_context, "EXEC2")
    projects_response = api_context.client.get("/projects", params={"offset": 0, "limit": 1})
    assert projects_response.status_code == 200
    project_page = projects_response.json()
    assert set(project_page) == {"data", "total"}
    assert len(project_page["data"]) == 1
    assert project_page["total"] >= 2
    paged_projects = api_context.client.get("/projects", params={"offset": 1, "limit": 1})
    assert paged_projects.status_code == 200
    paged_project_page = paged_projects.json()
    assert set(paged_project_page) == {"data", "total"}
    assert len(paged_project_page["data"]) == 1
    assert paged_project_page["total"] >= 2

    access_project = create_project(api_context, "ACCS")
    api_context.set_user(api_context.users.developer)
    access_task = create_task(api_context, access_project["id"], "Access check")
    api_context.set_user(api_context.users.outsider)
    assert api_context.client.get(f"/projects/{access_project['id']}").status_code == 403
    assert api_context.client.get(f"/projects/{access_project['id']}/tasks").status_code == 403
    assert api_context.client.get(f"/tasks/{access_task['id']}").status_code == 403
    assert api_context.client.get(f"/projects/{access_project['id']}/gantt").status_code == 403
    assert (
        api_context.client.get(f"/projects/{access_project['id']}/activity").status_code == 403
    )

    api_context.set_user(api_context.users.developer)
    assert api_context.client.get(f"/projects/{project['id']}").status_code == 200

    api_context.set_user(api_context.users.administrator)
    invalid_member = api_context.client.post(
        f"/projects/{project['id']}/members",
        json={"user_id": "missing-user"},
    )
    assert invalid_member.status_code == 404

    add_member = api_context.client.post(
        f"/projects/{project['id']}/members",
        json={"user_id": api_context.users.outsider.id},
    )
    assert add_member.status_code == 200

    api_context.set_user(api_context.users.developer)
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

    task_detail = api_context.client.get(f"/tasks/{first_task['id']}")
    assert task_detail.status_code == 200
    assert task_detail.json()["id"] == first_task["id"]

    conflict_response = api_context.client.patch(
        f"/tasks/{first_task['id']}",
        json={"version": 999, "progress": 10},
    )
    assert conflict_response.status_code == 409

    invalid_assignee = api_context.client.patch(
        f"/tasks/{first_task['id']}",
        json={"version": first_task["version"], "assignee_id": api_context.users.superuser.id},
    )
    assert invalid_assignee.status_code == 422

    update_response = api_context.client.patch(
        f"/tasks/{first_task['id']}",
        json={
            "version": first_task["version"],
            "status": "in_progress",
            "progress": 50,
            "assignee_id": api_context.users.outsider.id,
        },
    )
    assert update_response.status_code == 200
    updated_task = update_response.json()
    assert updated_task["status"] == "in_progress"
    assert updated_task["progress"] == 50
    assert updated_task["assignee"]["id"] == api_context.users.outsider.id

    stale_bulk_response = api_context.client.patch(
        f"/projects/{project['id']}/gantt/bulk",
        json={
            "changes": [
                {
                    "task_id": first_task["id"],
                    "version": 999,
                    "progress": 30,
                }
            ]
        },
    )
    assert stale_bulk_response.status_code == 409

    bulk_response = api_context.client.patch(
        f"/projects/{project['id']}/gantt/bulk",
        json={
            "changes": [
                {
                    "task_id": first_task["id"],
                    "version": updated_task["version"],
                    "start_date": "2026-07-02",
                    "end_date": "2026-07-05",
                    "progress": 40,
                    "status": "in_progress",
                }
            ]
        },
    )
    assert bulk_response.status_code == 200

    self_dependency_response = api_context.client.post(
        f"/projects/{project['id']}/task-dependencies",
        json={
            "predecessor_task_id": first_task["id"],
            "successor_task_id": first_task["id"],
        },
    )
    assert self_dependency_response.status_code == 422

    other_project = create_project(api_context, "CROSS")
    api_context.set_user(api_context.users.developer)
    other_task = create_task(api_context, other_project["id"], "Other project task")
    cross_project_dependency = api_context.client.post(
        f"/projects/{project['id']}/task-dependencies",
        json={
            "predecessor_task_id": first_task["id"],
            "successor_task_id": other_task["id"],
        },
    )
    assert cross_project_dependency.status_code == 422

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
    filtered_activity = api_context.client.get(
        f"/projects/{project['id']}/activity",
        params={
            "actor_user_id": api_context.users.developer.id,
            "action_type": "task.created",
        },
    )
    assert filtered_activity.status_code == 200
    filtered_activity_page = filtered_activity.json()
    assert filtered_activity_page["total"] == 2
    assert all(
        item["actor"]["id"] == api_context.users.developer.id
        and item["action_type"] == "task.created"
        for item in filtered_activity_page["data"]
    )
    empty_activity = api_context.client.get(
        f"/projects/{project['id']}/activity",
        params={"action_type": "task.never_happened"},
    )
    assert empty_activity.status_code == 200
    assert empty_activity.json() == {"data": [], "total": 0}
    paged_activity = api_context.client.get(
        f"/projects/{project['id']}/activity",
        params={"entity_type": "task", "offset": 1, "limit": 1},
    )
    assert paged_activity.status_code == 200
    paged_activity_page = paged_activity.json()
    assert set(paged_activity_page) == {"data", "total"}
    assert len(paged_activity_page["data"]) == 1
    assert paged_activity_page["total"] >= 2

    dependency_id = gantt["dependencies"][0]["id"]
    delete_response = api_context.client.delete(
        f"/projects/{project['id']}/task-dependencies/{dependency_id}"
    )
    assert delete_response.status_code == 200
    missing_dependency_delete = api_context.client.delete(
        f"/projects/{project['id']}/task-dependencies/{dependency_id}"
    )
    assert missing_dependency_delete.status_code == 404

    archive_response = api_context.client.delete(f"/tasks/{second_task['id']}")
    assert archive_response.status_code == 200
    assert api_context.client.get(f"/tasks/{second_task['id']}").status_code == 404

    api_context.set_user(api_context.users.administrator)
    remove_member = api_context.client.delete(
        f"/projects/{project['id']}/members/{api_context.users.outsider.id}"
    )
    assert remove_member.status_code == 200


def test_audit_logs_are_superuser_only_and_filterable(api_context) -> None:
    project = create_project(api_context, "AUDIT")
    create_project(api_context, "AUD2")

    api_context.set_user(api_context.users.administrator)
    denied = api_context.client.get("/audit-logs")
    assert denied.status_code == 403

    api_context.set_user(api_context.users.superuser)
    response = api_context.client.get(
        "/audit-logs",
        params={
            "action": "project.created",
            "entity_type": "project",
            "entity_id": project["id"],
            "actor_user_id": api_context.users.administrator.id,
            "created_from": datetime.now(UTC).date().isoformat(),
            "created_to": datetime.now(UTC).date().isoformat(),
        },
    )
    assert response.status_code == 200
    audit_page = response.json()
    assert set(audit_page) == {"data", "total"}
    assert audit_page["total"] >= 1
    logs = audit_page["data"]
    assert any(log["entity_id"] == project["id"] for log in logs)
    assert {log["action"] for log in logs} == {"project.created"}
    paged_response = api_context.client.get(
        "/audit-logs",
        params={"action": "project.created", "offset": 1, "limit": 1},
    )
    assert paged_response.status_code == 200
    paged_audit_page = paged_response.json()
    assert set(paged_audit_page) == {"data", "total"}
    assert len(paged_audit_page["data"]) == 1
    assert paged_audit_page["total"] >= 2

    future_response = api_context.client.get(
        "/audit-logs",
        params={
            "entity_id": project["id"],
            "created_from": (datetime.now(UTC) + timedelta(days=1)).date().isoformat(),
            "created_to": (datetime.now(UTC) + timedelta(days=1)).date().isoformat(),
        },
    )
    assert future_response.status_code == 200
    assert future_response.json() == {"data": [], "total": 0}

    invalid_range = api_context.client.get(
        "/audit-logs",
        params={"created_from": "2026-07-02", "created_to": "2026-07-01"},
    )
    assert invalid_range.status_code == 422


def test_project_idea_links_and_external_links(api_context) -> None:
    project = create_project(api_context, "LINK")

    api_context.set_user(api_context.users.developer)
    idea_response = api_context.client.post("/ideas", json={"title": "Connect planning"})
    assert idea_response.status_code == 201
    idea = idea_response.json()
    second_idea_response = api_context.client.post("/ideas", json={"title": "Connect delivery"})
    assert second_idea_response.status_code == 201
    second_idea = second_idea_response.json()

    idea_link = api_context.client.post(
        f"/idea/{idea['id']}/links",
        json={"url": "https://example.com/idea", "title": "Idea context"},
    )
    assert idea_link.status_code == 201
    idea_link_id = idea_link.json()["id"]

    api_context.set_user(api_context.users.outsider)
    denied_idea_link = api_context.client.post(
        f"/idea/{idea['id']}/links",
        json={"url": "https://example.com/denied-idea"},
    )
    assert denied_idea_link.status_code == 403
    denied_idea_link_delete = api_context.client.delete(f"/links/{idea_link_id}")
    assert denied_idea_link_delete.status_code == 403

    api_context.set_user(api_context.users.developer)
    assert api_context.client.delete(f"/links/{idea_link_id}").status_code == 200

    api_context.set_user(api_context.users.administrator)
    link_response = api_context.client.post(
        f"/projects/{project['id']}/ideas",
        json={"idea_id": idea["id"], "relation_type": "origin"},
    )
    assert link_response.status_code == 200
    second_link_response = api_context.client.post(
        f"/projects/{project['id']}/ideas",
        json={"idea_id": second_idea["id"], "relation_type": "related"},
    )
    assert second_link_response.status_code == 200

    project_ideas = api_context.client.get(
        f"/projects/{project['id']}/ideas", params={"offset": 0, "limit": 1}
    )
    assert project_ideas.status_code == 200
    project_ideas_page = project_ideas.json()
    assert set(project_ideas_page) == {"data", "total"}
    assert len(project_ideas_page["data"]) == 1
    assert project_ideas_page["total"] == 2
    paged_project_ideas = api_context.client.get(
        f"/projects/{project['id']}/ideas", params={"offset": 1, "limit": 1}
    )
    assert paged_project_ideas.status_code == 200
    paged_project_ideas_page = paged_project_ideas.json()
    assert set(paged_project_ideas_page) == {"data", "total"}
    assert len(paged_project_ideas_page["data"]) == 1
    assert paged_project_ideas_page["total"] == 2

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
    second_external_link = api_context.client.post(
        f"/project/{project['id']}/links",
        json={"url": "https://docs.example.test", "title": "Docs", "link_type": "doc"},
    )
    assert second_external_link.status_code == 201
    second_external_link_id = second_external_link.json()["id"]

    api_context.set_user(api_context.users.outsider)
    denied_links = api_context.client.get(f"/project/{project['id']}/links")
    assert denied_links.status_code == 403
    denied_create = api_context.client.post(
        f"/project/{project['id']}/links",
        json={"url": "https://example.com/denied"},
    )
    assert denied_create.status_code == 403
    denied_delete = api_context.client.delete(f"/links/{external_link_id}")
    assert denied_delete.status_code == 403

    api_context.set_user(api_context.users.administrator)
    missing_entity = api_context.client.post(
        "/project/missing-project/links",
        json={"url": "https://example.com/missing"},
    )
    assert missing_entity.status_code == 404

    links_response = api_context.client.get(
        f"/project/{project['id']}/links", params={"offset": 0, "limit": 1}
    )
    assert links_response.status_code == 200
    link_page = links_response.json()
    assert set(link_page) == {"data", "total"}
    assert len(link_page["data"]) == 1
    assert link_page["total"] == 2
    paged_links_response = api_context.client.get(
        f"/project/{project['id']}/links", params={"offset": 1, "limit": 1}
    )
    assert paged_links_response.status_code == 200
    paged_link_page = paged_links_response.json()
    assert set(paged_link_page) == {"data", "total"}
    assert len(paged_link_page["data"]) == 1
    assert paged_link_page["total"] == 2

    preview = api_context.client.post(
        "/links/preview",
        json={"url": "https://github.com/BITNP/ideas", "title": "Repository"},
    )
    assert preview.status_code == 200
    assert preview.json()["title"] == "Repository"

    invalid_entity = api_context.client.get(f"/unknown/{project['id']}/links")
    assert invalid_entity.status_code == 422

    assert api_context.client.delete(f"/links/{external_link_id}").status_code == 200
    assert api_context.client.delete(f"/links/{second_external_link_id}").status_code == 200
    links_after_delete = api_context.client.get(f"/project/{project['id']}/links")
    assert links_after_delete.status_code == 200
    deleted_link_page = links_after_delete.json()
    assert deleted_link_page["data"] == []
    assert deleted_link_page["total"] == 0
    unlink_response = api_context.client.delete(f"/projects/{project['id']}/ideas/{idea['id']}")
    assert unlink_response.status_code == 200
    second_unlink_response = api_context.client.delete(
        f"/projects/{project['id']}/ideas/{second_idea['id']}"
    )
    assert second_unlink_response.status_code == 200
    project_ideas_after_unlink = api_context.client.get(f"/projects/{project['id']}/ideas")
    assert project_ideas_after_unlink.status_code == 200
    assert project_ideas_after_unlink.json()["total"] == 0


def test_api_keys_management_and_signed_idea_only_access(api_context) -> None:
    api_context.set_user(api_context.users.developer)
    create_response = api_context.client.post("/api-keys", json={"name": "Workflow"})
    assert create_response.status_code == 201
    created = create_response.json()
    api_key = created["api_key"]
    secret = created["secret"]
    assert secret.endswith(api_key["secret_last4"])
    assert api_key["allowed_entities"] == ["idea"]
    assert api_key["revoked_at"] is None
    stored_secret = api_context.run(stored_api_key_secret(api_context, api_key["id"]))
    assert stored_secret != secret
    assert stored_secret.startswith(PROTECTED_SECRET_PREFIX)

    listed = api_context.client.get("/api-keys")
    assert listed.status_code == 200
    listed_page = listed.json()
    assert set(listed_page) == {"data", "total"}
    assert "secret" not in listed_page["data"][0]
    assert listed_page["total"] == 1
    second_create_response = api_context.client.post("/api-keys", json={"name": "Workflow 2"})
    assert second_create_response.status_code == 201
    paged_keys = api_context.client.get("/api-keys", params={"offset": 1, "limit": 1})
    assert paged_keys.status_code == 200
    paged_key_page = paged_keys.json()
    assert set(paged_key_page) == {"data", "total"}
    assert len(paged_key_page["data"]) == 1
    assert paged_key_page["total"] == 2

    api_context.set_user(api_context.users.outsider)
    outsider_keys = api_context.client.get("/api-keys")
    assert outsider_keys.status_code == 200
    assert outsider_keys.json() == {"data": [], "total": 0}
    outsider_update = api_context.client.patch(
        f"/api-keys/{api_key['id']}",
        json={"name": "Outsider update"},
    )
    assert outsider_update.status_code == 403
    outsider_revoke = api_context.client.delete(f"/api-keys/{api_key['id']}")
    assert outsider_revoke.status_code == 403
    outsider_rotate = api_context.client.post(f"/api-keys/{api_key['id']}/rotate")
    assert outsider_rotate.status_code == 403

    api_context.set_user(api_context.users.superuser)
    superuser_keys = api_context.client.get("/api-keys")
    assert superuser_keys.status_code == 200
    assert superuser_keys.json()["total"] == 2

    api_context.set_user(api_context.users.developer)

    rejected_scope = api_context.client.post(
        "/api-keys",
        json={"name": "Bad scope", "scopes": ["ideas:read", "projects:write"]},
    )
    assert rejected_scope.status_code == 422

    deactivate_response = api_context.client.patch(
        f"/api-keys/{api_key['id']}",
        json={"is_active": False},
    )
    assert deactivate_response.status_code == 200
    deactivated_keys = api_context.client.get("/api-keys").json()["data"]
    deactivated_key = next(key for key in deactivated_keys if key["id"] == api_key["id"])
    assert deactivated_key["is_active"] is False
    assert deactivated_key["revoked_at"] is None

    api_context.use_real_auth()
    paused_key_request = api_context.client.get(
        "/ideas",
        headers=sign_headers(
            key_id=api_key["key_id"],
            secret=secret,
            method="GET",
            path="/ideas",
        ),
    )
    api_context.use_stub_auth()
    assert paused_key_request.status_code == 401

    reactivate_response = api_context.client.patch(
        f"/api-keys/{api_key['id']}",
        json={"is_active": True},
    )
    assert reactivate_response.status_code == 200
    reactivated_keys = api_context.client.get("/api-keys").json()["data"]
    reactivated_key = next(key for key in reactivated_keys if key["id"] == api_key["id"])
    assert reactivated_key["is_active"] is True
    assert reactivated_key["revoked_at"] is None

    api_context.use_real_auth()
    api_created_idea_body = {"title": "API submitted idea"}
    signed_create_idea = api_context.client.post(
        "/ideas",
        json=api_created_idea_body,
        headers=sign_headers(
            key_id=api_key["key_id"],
            secret=secret,
            method="POST",
            path="/ideas",
            body=api_created_idea_body,
        ),
    )
    api_context.use_stub_auth()
    assert signed_create_idea.status_code == 201

    api_context.set_user(api_context.users.superuser)
    api_key_audit = api_context.client.get(
        "/audit-logs",
        params={"actor_api_key_id": api_key["id"], "action": "idea.created"},
    )
    assert api_key_audit.status_code == 200
    api_key_audit_page = api_key_audit.json()
    assert api_key_audit_page["total"] == 1
    assert api_key_audit_page["data"][0]["actor_api_key_id"] == api_key["id"]
    assert api_key_audit_page["data"][0]["entity_type"] == "idea"

    api_context.set_user(api_context.users.developer)

    update_response = api_context.client.patch(
        f"/api-keys/{api_key['id']}",
        json={"name": "Workflow readonly", "scopes": ["ideas:read"]},
    )
    assert update_response.status_code == 200

    paused_create_response = api_context.client.post("/api-keys", json={"name": "Paused rotate"})
    assert paused_create_response.status_code == 201
    paused_key = paused_create_response.json()["api_key"]
    assert (
        api_context.client.patch(
            f"/api-keys/{paused_key['id']}",
            json={"is_active": False},
        ).status_code
        == 200
    )
    paused_rotate_response = api_context.client.post(f"/api-keys/{paused_key['id']}/rotate")
    assert paused_rotate_response.status_code == 200
    paused_rotated = paused_rotate_response.json()["api_key"]
    assert paused_rotated["is_active"] is False
    assert paused_rotated["revoked_at"] is None

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
    assert signed_ideas.json()["total"] >= 1

    signed_filtered_ideas = api_context.client.get(
        "/ideas?search=API%20submitted",
        headers=sign_headers(
            key_id=key_id,
            secret=secret,
            method="GET",
            path="/ideas",
            query_string=b"search=API%20submitted",
        ),
    )
    assert signed_filtered_ideas.status_code == 200
    assert signed_filtered_ideas.json()["total"] == 1

    replay_nonce = f"replay-{uuid4()}"
    replay_headers = sign_headers(
        key_id=key_id,
        secret=secret,
        method="GET",
        path="/ideas",
        nonce=replay_nonce,
    )
    assert api_context.client.get("/ideas", headers=replay_headers).status_code == 200
    assert api_context.client.get("/ideas", headers=replay_headers).status_code == 401

    readonly_create_idea_body = {"title": "Readonly key should not write"}
    signed_readonly_create = api_context.client.post(
        "/ideas",
        json=readonly_create_idea_body,
        headers=sign_headers(
            key_id=key_id,
            secret=secret,
            method="POST",
            path="/ideas",
            body=readonly_create_idea_body,
        ),
    )
    assert signed_readonly_create.status_code == 403

    signed_projects = api_context.client.get(
        "/projects",
        headers=sign_headers(key_id=key_id, secret=secret, method="GET", path="/projects"),
    )
    assert signed_projects.status_code == 403
    api_context.use_stub_auth()

    revoke_response = api_context.client.delete(f"/api-keys/{api_key['id']}")
    assert revoke_response.status_code == 200
    revoked_keys = api_context.client.get("/api-keys").json()["data"]
    revoked_key = next(key for key in revoked_keys if key["id"] == api_key["id"])
    assert revoked_key["is_active"] is False
    assert revoked_key["revoked_at"] is not None
    assert (
        api_context.client.patch(
            f"/api-keys/{api_key['id']}",
            json={"is_active": True},
        ).status_code
        == 409
    )
    assert api_context.client.post(f"/api-keys/{api_key['id']}/rotate").status_code == 409
    second_revoke_response = api_context.client.delete(f"/api-keys/{api_key['id']}")
    assert second_revoke_response.status_code == 200

    api_context.use_real_auth()
    revoked_key_request = api_context.client.get(
        "/ideas",
        headers=sign_headers(key_id=key_id, secret=secret, method="GET", path="/ideas"),
    )
    api_context.use_stub_auth()
    assert revoked_key_request.status_code == 401

    tampered_create_response = api_context.client.post("/api-keys", json={"name": "Tampered"})
    assert tampered_create_response.status_code == 201
    tampered = tampered_create_response.json()
    api_context.run(
        set_api_key_allowed_entities(api_context, tampered["api_key"]["id"], ["project"])
    )
    api_context.use_real_auth()
    tampered_key_request = api_context.client.get(
        "/ideas",
        headers=sign_headers(
            key_id=tampered["api_key"]["key_id"],
            secret=tampered["secret"],
            method="GET",
            path="/ideas",
        ),
    )
    api_context.use_stub_auth()
    assert tampered_key_request.status_code == 403


async def stored_api_key_secret(api_context, api_key_id: str) -> str:
    async with api_context.sessionmaker() as session:
        stored = await session.scalar(select(ApiKey).where(ApiKey.id == api_key_id))
        assert stored is not None
        return stored.secret_hash


async def set_api_key_allowed_entities(
    api_context, api_key_id: str, allowed_entities: list[str]
) -> None:
    async with api_context.sessionmaker() as session:
        stored = await session.scalar(select(ApiKey).where(ApiKey.id == api_key_id))
        assert stored is not None
        stored.allowed_entities = allowed_entities
        await session.commit()
