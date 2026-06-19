from datetime import UTC, date, datetime

from bitnp_ideas.models.enums import GlobalRole, IdeaStatus, Priority, ProjectStatus, TaskStatus
from bitnp_ideas.schemas.common import (
    ActivityRead,
    ApiKeyRead,
    CurrentUser,
    EntityRef,
    ExternalLinkRead,
    GanttDependency,
    GanttRead,
    IdeaRead,
    IdeaTagRead,
    ProjectRead,
    TaskRead,
)

now = datetime.now(UTC)

alice = EntityRef(id="usr_alice", name="Alice Admin")
devon = EntityRef(id="usr_devon", name="Devon Developer")

current_user = CurrentUser(
    id="usr_alice",
    email="alice@bitnp.local",
    display_name="Alice Admin",
    global_role=GlobalRole.SUPERUSER,
)

tags = [
    IdeaTagRead(id="tag_ai", name="ai", slug="ai", color="#3F51B5", usage_count=8),
    IdeaTagRead(id="tag_backend", name="backend", slug="backend", color="#00897B", usage_count=6),
    IdeaTagRead(id="tag_gantt", name="gantt", slug="gantt", color="#F4511E", usage_count=3),
]

ideas = [
    IdeaRead(
        id="idea_ai_ingestion",
        title="Add AI workflow idea ingestion",
        description="Allow signed API clients to submit ideas into the intake board.",
        status=IdeaStatus.ACTIVE,
        priority=Priority.HIGH,
        tags=[tags[0], tags[1]],
        creator=devon,
        created_at=now,
        updated_at=now,
    ),
    IdeaRead(
        id="idea_dependency_drag",
        title="Drag dependency lines on the Gantt view",
        description="Create finish-to-start task dependencies directly from the schedule canvas.",
        status=IdeaStatus.IN_PROGRESS,
        priority=Priority.MEDIUM,
        tags=[tags[2]],
        creator=alice,
        linked_project=EntityRef(id="prj_ideas", name="IDEAS MVP"),
        created_at=now,
        updated_at=now,
    ),
]

projects = [
    ProjectRead(
        id="prj_ideas",
        key="IDEAS",
        name="IDEAS MVP",
        description="Phase 0-2 bootstrap for the internal execution system.",
        status=ProjectStatus.ACTIVE,
        owner=alice,
        progress=38,
        start_date=date(2026, 6, 16),
        target_end_date=date(2026, 8, 1),
        members=[alice, devon],
    )
]

tasks = [
    TaskRead(
        id="task_bootstrap",
        project_id="prj_ideas",
        title="Bootstrap monorepo",
        status=TaskStatus.DONE,
        assignee=alice,
        start_date=date(2026, 6, 16),
        end_date=date(2026, 6, 18),
        progress=100,
        version=2,
    ),
    TaskRead(
        id="task_idea_api",
        project_id="prj_ideas",
        title="Implement idea and tag API",
        status=TaskStatus.IN_PROGRESS,
        assignee=devon,
        start_date=date(2026, 6, 19),
        end_date=date(2026, 6, 26),
        progress=45,
        version=4,
    ),
    TaskRead(
        id="task_gantt",
        project_id="prj_ideas",
        title="Build Gantt scheduling surface",
        status=TaskStatus.TODO,
        assignee=devon,
        start_date=date(2026, 6, 27),
        end_date=date(2026, 7, 8),
        progress=10,
        version=1,
    ),
]

dependencies = [
    GanttDependency(
        id="dep_bootstrap_api",
        predecessor_task_id="task_bootstrap",
        successor_task_id="task_idea_api",
    )
]

gantt = GanttRead(project=projects[0], tasks=tasks, dependencies=dependencies)

activities = [
    ActivityRead(
        id="act_reschedule",
        project_id="prj_ideas",
        actor=devon,
        action_type="task.rescheduled",
        entity_type="task",
        entity_id="task_idea_api",
        before={"end_date": "2026-06-24"},
        after={"end_date": "2026-06-26"},
        created_at=now,
    ),
    ActivityRead(
        id="act_linked",
        project_id="prj_ideas",
        actor=alice,
        action_type="idea.linked",
        entity_type="idea",
        entity_id="idea_dependency_drag",
        created_at=now,
    ),
]

api_keys = [
    ApiKeyRead(
        id="key_demo",
        name="AI intake workflow",
        key_id="bitnp_ideasdemo_01",
        secret_last4="2f9a",
        scopes=["ideas:read", "ideas:write"],
        allowed_entities=["idea"],
        is_active=True,
        revoked_at=None,
    )
]

links = [
    ExternalLinkRead(
        id="link_keycloak",
        entity_type="project",
        entity_id="prj_ideas",
        url="https://github.com/BITNP/keycloak-account-service",
        title="BITNP Keycloak Account Service",
        link_type="github_repo",
    )
]
