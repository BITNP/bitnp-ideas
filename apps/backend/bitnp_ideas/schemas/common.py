from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from bitnp_ideas.models.enums import (
    DependencyType,
    EntityType,
    ExternalLinkType,
    GlobalRole,
    IdeaStatus,
    Priority,
    ProjectIdeaRelation,
    ProjectStatus,
    TaskStatus,
)


class ApiMessage(BaseModel):
    message: str


class LoginResponse(BaseModel):
    authorization_url: str
    state: str


class Page[T](BaseModel):
    data: list[T]
    total: int


class EntityRef(BaseModel):
    id: str
    name: str


class CurrentUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    global_role: GlobalRole
    is_active: bool = True


class CallbackResponse(BaseModel):
    access_token: str
    token_type: str
    user: CurrentUser


class IdeaTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    color: str | None = None
    description: str | None = None
    is_active: bool = True
    usage_count: int = 0
    created_at: datetime


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


class IdeaUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = None
    priority: Priority | None = None
    linked_project_id: str | None = None
    linked_project_url: str | None = None


class IdeaStatusUpdate(BaseModel):
    status: IdeaStatus
    note: str | None = None
    linked_project_id: str | None = None
    linked_project_url: str | None = None


class IdeaTagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    color: str | None = Field(default=None, max_length=16)
    description: str | None = None


class IdeaTagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    color: str | None = Field(default=None, max_length=16)
    description: str | None = None
    is_active: bool | None = None


class IdeaTagAttach(BaseModel):
    tag_ids: list[str] = Field(min_length=1)


class IdeaStatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    idea_id: str
    from_status: str | None = None
    to_status: str
    actor_id: str | None = None
    note: str | None = None
    linked_project_id: str | None = None
    linked_project_url: str | None = None
    created_at: datetime


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    key: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    owner_id: str | None = None


class ProjectUpdate(BaseModel):
    key: str | None = Field(default=None, min_length=2, max_length=32)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: ProjectStatus | None = None
    owner_id: str | None = None
    start_date: date | None = None
    target_end_date: date | None = None


class ProjectMemberCreate(BaseModel):
    user_id: str


class ProjectIdeaLinkCreate(BaseModel):
    idea_id: str
    relation_type: ProjectIdeaRelation = ProjectIdeaRelation.RELATED


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = None
    assignee_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = None
    status: TaskStatus | None = None
    assignee_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    parent_task_id: str | None = None
    version: int | None = None


class GanttDependency(BaseModel):
    id: str
    predecessor_task_id: str
    successor_task_id: str
    dependency_type: DependencyType = DependencyType.FINISH_TO_START


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
    status: TaskStatus | None = None


class GanttBulkUpdate(BaseModel):
    changes: list[GanttBulkChange]


class TaskDependencyCreate(BaseModel):
    predecessor_task_id: str
    successor_task_id: str
    dependency_type: DependencyType = DependencyType.FINISH_TO_START


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    key_id: str
    secret_last4: str
    scopes: list[str]
    allowed_entities: list[str]
    is_active: bool
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(default_factory=lambda: ["ideas:read", "ideas:write"])


class ApiKeyCreateResponse(BaseModel):
    api_key: ApiKeyRead
    secret: str


class ApiKeyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None
    scopes: list[str] | None = None


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


class AuditLogRead(BaseModel):
    id: str
    actor_user_id: str | None = None
    actor_api_key_id: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class ExternalLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: EntityType
    entity_id: str
    url: str
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    site_name: str | None = None
    link_type: ExternalLinkType | None = None
    created_at: datetime


class ExternalLinkCreate(BaseModel):
    url: str
    title: str | None = None
    description: str | None = None
    link_type: ExternalLinkType | None = ExternalLinkType.WEBSITE


class LinkPreview(BaseModel):
    url: str
    title: str | None = None
    description: str | None = None
    image: str | None = None
