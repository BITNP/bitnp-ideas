from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from bitnp_ideas.models.enums import GlobalRole, IdeaStatus, Priority, ProjectStatus, TaskStatus


class ApiMessage(BaseModel):
    message: str


class PageMeta(BaseModel):
    limit: int = 50
    cursor: str | None = None
    next_cursor: str | None = None


class EntityRef(BaseModel):
    id: str
    name: str


class CurrentUser(BaseModel):
    id: str
    email: str
    display_name: str
    global_role: GlobalRole
    is_active: bool = True


class IdeaTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    color: str | None = None
    description: str | None = None
    is_active: bool = True
    usage_count: int = 0


class IdeaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None = None
    status: IdeaStatus
    priority: Priority | None = None
    tags: list[IdeaTagRead] = Field(default_factory=list)
    creator: EntityRef
    linked_project: EntityRef | None = None
    linked_project_url: str | None = None
    created_at: datetime
    updated_at: datetime


class IdeaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = None
    priority: Priority | None = Priority.MEDIUM
    tag_names: list[str] = Field(default_factory=list)


class IdeaStatusUpdate(BaseModel):
    status: IdeaStatus
    note: str | None = None
    linked_project_id: str | None = None
    linked_project_url: str | None = None


class ProjectRead(BaseModel):
    id: str
    key: str
    name: str
    description: str | None = None
    status: ProjectStatus
    owner: EntityRef | None = None
    progress: int = 0
    start_date: date | None = None
    target_end_date: date | None = None
    members: list[EntityRef] = Field(default_factory=list)


class ProjectCreate(BaseModel):
    key: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    owner_id: str | None = None


class TaskRead(BaseModel):
    id: str
    project_id: str
    title: str
    description: str | None = None
    status: TaskStatus
    assignee: EntityRef | None = None
    start_date: date | None = None
    end_date: date | None = None
    progress: int
    version: int


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = None
    assignee_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class GanttDependency(BaseModel):
    id: str
    predecessor_task_id: str
    successor_task_id: str
    dependency_type: str = "finish_to_start"


class GanttRead(BaseModel):
    project: ProjectRead
    tasks: list[TaskRead]
    dependencies: list[GanttDependency]


class GanttBulkChange(BaseModel):
    task_id: str
    version: int
    start_date: date | None = None
    end_date: date | None = None
    assignee_id: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)


class GanttBulkUpdate(BaseModel):
    changes: list[GanttBulkChange]


class ApiKeyRead(BaseModel):
    id: str
    name: str
    key_id: str
    secret_last4: str
    scopes: list[str]
    allowed_entities: list[str]
    is_active: bool
    last_used_at: datetime | None = None


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(default_factory=lambda: ["ideas:read", "ideas:write"])


class ActivityRead(BaseModel):
    id: str
    project_id: str
    actor: EntityRef | None = None
    action_type: str
    entity_type: str
    entity_id: str
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    created_at: datetime


class ExternalLinkRead(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    url: str
    title: str | None = None
    link_type: str | None = None


class ExternalLinkCreate(BaseModel):
    url: str
    title: str | None = None
    link_type: str | None = "website"
