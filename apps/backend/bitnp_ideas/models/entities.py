from datetime import date, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bitnp_ideas.db.base import Base, TimestampMixin, uuid_pk
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

postgres_jsonb = JSONB().with_variant(JSON(), "sqlite")
postgres_text_array = ARRAY(Text).with_variant(JSON(), "sqlite")
postgres_inet = INET().with_variant(String(45), "sqlite")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = uuid_pk()
    sso_provider: Mapped[str] = mapped_column(String(80), nullable=False)
    sso_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    global_role: Mapped[GlobalRole] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("sso_provider", "sso_subject", name="uq_users_sso_identity"),
        CheckConstraint(
            "global_role IN ('superuser', 'administrator', 'developer')",
            name="ck_users_global_role",
        ),
    )


class Idea(Base, TimestampMixin):
    __tablename__ = "ideas"

    id: Mapped[str] = uuid_pk()
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[IdeaStatus] = mapped_column(
        String(32), nullable=False, default=IdeaStatus.ACTIVE
    )
    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    linked_project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"))
    linked_project_url: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[Priority | None] = mapped_column(String(16))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tags: Mapped[list["IdeaTag"]] = relationship(
        secondary="idea_tag_links", back_populates="ideas", viewonly=True
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'paused', 'in_progress', 'completed')",
            name="ck_bitnp_ideasstatus",
        ),
        CheckConstraint("priority IN ('low', 'medium', 'high')", name="ck_bitnp_ideaspriority"),
        CheckConstraint(
            "(status NOT IN ('in_progress', 'completed')) OR "
            "(linked_project_id IS NOT NULL OR linked_project_url IS NOT NULL)",
            name="ck_bitnp_ideasprogress_requires_link",
        ),
    )


class IdeaTag(Base, TimestampMixin):
    __tablename__ = "idea_tags"

    id: Mapped[str] = uuid_pk()
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(16))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))

    ideas: Mapped[list[Idea]] = relationship(
        secondary="idea_tag_links", back_populates="tags", viewonly=True
    )


class IdeaTagLink(Base):
    __tablename__ = "idea_tag_links"

    idea_id: Mapped[str] = mapped_column(
        ForeignKey("ideas.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(
        ForeignKey("idea_tags.id", ondelete="CASCADE"), primary_key=True
    )
    added_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_idea_tag_links_tag_id", "tag_id"),
        Index("idx_idea_tag_links_idea_id", "idea_id"),
    )


class IdeaStatusHistory(Base):
    __tablename__ = "idea_status_history"

    id: Mapped[str] = uuid_pk()
    idea_id: Mapped[str] = mapped_column(ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(32))
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str | None] = mapped_column(Text)
    linked_project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"))
    linked_project_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    key: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(String(32), nullable=False)
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    start_date: Mapped[date | None] = mapped_column(Date)
    target_end_date: Mapped[date | None] = mapped_column(Date)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('planning', 'active', 'paused', 'completed', 'cancelled')",
            name="ck_projects_status",
        ),
    )


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[str] = uuid_pk()
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    added_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_members_user"),)


class ProjectIdea(Base):
    __tablename__ = "project_ideas"

    id: Mapped[str] = uuid_pk()
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    idea_id: Mapped[str] = mapped_column(ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False)
    relation_type: Mapped[ProjectIdeaRelation] = mapped_column(String(32), nullable=False)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "idea_id", name="uq_project_bitnp_ideaslink"),
        CheckConstraint(
            "relation_type IN ('origin', 'related', 'inspired_by')",
            name="ck_project_bitnp_ideasrelation_type",
        ),
    )


class ProjectTask(Base, TimestampMixin):
    __tablename__ = "project_tasks"

    id: Mapped[str] = uuid_pk()
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    parent_task_id: Mapped[str | None] = mapped_column(
        ForeignKey("project_tasks.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(String(32), nullable=False)
    assignee_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "status IN ('todo', 'in_progress', 'blocked', 'review', 'done', 'cancelled')",
            name="ck_project_tasks_status",
        ),
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_project_tasks_progress"),
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id: Mapped[str] = uuid_pk()
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    predecessor_task_id: Mapped[str] = mapped_column(
        ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False
    )
    successor_task_id: Mapped[str] = mapped_column(
        ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False
    )
    dependency_type: Mapped[DependencyType] = mapped_column(
        String(32), default=DependencyType.FINISH_TO_START, nullable=False
    )
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "predecessor_task_id", "successor_task_id", name="uq_task_dependencies_edge"
        ),
        CheckConstraint(
            "predecessor_task_id <> successor_task_id", name="ck_task_dependencies_no_self"
        ),
        CheckConstraint("dependency_type IN ('finish_to_start')", name="ck_task_dependencies_type"),
    )


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = uuid_pk()
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    key_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    secret_hash: Mapped[str] = mapped_column(Text, nullable=False)
    secret_last4: Mapped[str] = mapped_column(String(4), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(postgres_text_array, nullable=False)
    allowed_entities: Mapped[list[str]] = mapped_column(
        postgres_text_array, default=["idea"], nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ApiKeyNonce(Base):
    __tablename__ = "api_key_nonces"

    id: Mapped[str] = uuid_pk()
    key_id: Mapped[str] = mapped_column(String(80), nullable=False)
    nonce: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("key_id", "nonce", name="uq_api_key_nonces_key_nonce"),)


class ActivityStream(Base):
    __tablename__ = "activity_stream"

    id: Mapped[str] = uuid_pk()
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str] = mapped_column(nullable=False)
    before: Mapped[dict | None] = mapped_column(postgres_jsonb)
    after: Mapped[dict | None] = mapped_column(postgres_jsonb)
    metadata_: Mapped[dict | None] = mapped_column("metadata", postgres_jsonb)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = uuid_pk()
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    actor_api_key_id: Mapped[str | None] = mapped_column(ForeignKey("api_keys.id"))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str | None]
    before: Mapped[dict | None] = mapped_column(postgres_jsonb)
    after: Mapped[dict | None] = mapped_column(postgres_jsonb)
    ip_address: Mapped[str | None] = mapped_column(postgres_inet)
    user_agent: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict | None] = mapped_column("metadata", postgres_jsonb)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExternalLink(Base):
    __tablename__ = "external_links"

    id: Mapped[str] = uuid_pk()
    entity_type: Mapped[EntityType] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    site_name: Mapped[str | None] = mapped_column(Text)
    link_type: Mapped[ExternalLinkType | None] = mapped_column(String(32))
    metadata_: Mapped[dict | None] = mapped_column("metadata", postgres_jsonb)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('idea', 'project', 'task')", name="ck_external_links_entity_type"
        ),
        CheckConstraint(
            "link_type IN ('github_repo', 'website', 'doc', 'other')",
            name="ck_external_links_link_type",
        ),
    )
