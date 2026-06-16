from typing import Annotated

from fastapi import APIRouter, Depends

from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import ApiMessage, CurrentUser, ProjectCreate, ProjectRead
from bitnp_ideas.security.rbac import require_roles
from bitnp_ideas.services import demo_data

router = APIRouter()
ProjectAdminDep = Annotated[
    CurrentUser, Depends(require_roles(GlobalRole.SUPERUSER, GlobalRole.ADMINISTRATOR))
]


@router.get("", response_model=list[ProjectRead])
async def list_projects() -> list[ProjectRead]:
    return demo_data.projects


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(
    payload: ProjectCreate,
    _: ProjectAdminDep,
) -> ProjectRead:
    return demo_data.projects[0].model_copy(update=payload.model_dump(exclude_unset=True))


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: str) -> ProjectRead:
    return next(
        (project for project in demo_data.projects if project.id == project_id),
        demo_data.projects[0],
    )


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(project_id: str, payload: ProjectCreate) -> ProjectRead:
    project = await get_project(project_id)
    return project.model_copy(update=payload.model_dump(exclude_unset=True))


@router.delete("/{project_id}", response_model=ApiMessage)
async def archive_project(project_id: str) -> ApiMessage:
    return ApiMessage(message=f"project {project_id} archived")


@router.post("/{project_id}/members", response_model=ApiMessage)
async def add_project_member(project_id: str, user_id: str) -> ApiMessage:
    return ApiMessage(message=f"user {user_id} added to project {project_id}")


@router.delete("/{project_id}/members/{user_id}", response_model=ApiMessage)
async def remove_project_member(project_id: str, user_id: str) -> ApiMessage:
    return ApiMessage(message=f"user {user_id} removed from project {project_id}")


@router.get("/{project_id}/ideas")
async def list_project_ideas(project_id: str):
    return [
        idea
        for idea in demo_data.ideas
        if idea.linked_project and idea.linked_project.id == project_id
    ]


@router.post("/{project_id}/ideas", response_model=ApiMessage)
async def link_project_idea(project_id: str, idea_id: str) -> ApiMessage:
    return ApiMessage(message=f"idea {idea_id} linked to project {project_id}")


@router.delete("/{project_id}/ideas/{idea_id}", response_model=ApiMessage)
async def unlink_project_idea(project_id: str, idea_id: str) -> ApiMessage:
    return ApiMessage(message=f"idea {idea_id} unlinked from project {project_id}")
