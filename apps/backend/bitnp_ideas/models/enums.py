from enum import StrEnum


class GlobalRole(StrEnum):
    SUPERUSER = "superuser"
    ADMINISTRATOR = "administrator"
    DEVELOPER = "developer"


class IdeaStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProjectStatus(StrEnum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class ProjectIdeaRelation(StrEnum):
    ORIGIN = "origin"
    RELATED = "related"
    INSPIRED_BY = "inspired_by"


class DependencyType(StrEnum):
    FINISH_TO_START = "finish_to_start"


class EntityType(StrEnum):
    IDEA = "idea"
    PROJECT = "project"
    TASK = "task"


class ExternalLinkType(StrEnum):
    GITHUB_REPO = "github_repo"
    WEBSITE = "website"
    DOC = "doc"
    OTHER = "other"
