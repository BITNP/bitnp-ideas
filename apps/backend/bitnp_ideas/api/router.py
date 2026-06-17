from fastapi import APIRouter

from bitnp_ideas.api.routes import (
    activity,
    api_keys,
    audit_logs,
    auth,
    external_links,
    gantt,
    health,
    idea_tags,
    ideas,
    projects,
    tasks,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(ideas.router, prefix="/ideas", tags=["ideas"])
api_router.include_router(idea_tags.router, prefix="/idea-tags", tags=["idea-tags"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks.router, tags=["tasks"])
api_router.include_router(gantt.router, tags=["gantt"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(activity.router, tags=["activity"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
api_router.include_router(external_links.router, tags=["external-links"])
