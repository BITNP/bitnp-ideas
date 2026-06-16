from fastapi import APIRouter

from bitnp_ideas.schemas.common import ApiMessage, IdeaCreate, IdeaRead, IdeaStatusUpdate
from bitnp_ideas.services import demo_data

router = APIRouter()


@router.get("", response_model=list[IdeaRead])
async def list_ideas(
    status: str | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> list[IdeaRead]:
    results = demo_data.ideas
    if status:
        results = [idea for idea in results if idea.status == status]
    if tag:
        results = [idea for idea in results if any(item.slug == tag for item in idea.tags)]
    if search:
        query = search.lower()
        results = [idea for idea in results if query in idea.title.lower()]
    return results


@router.post("", response_model=IdeaRead, status_code=201)
async def create_idea(payload: IdeaCreate) -> IdeaRead:
    return demo_data.ideas[0].model_copy(
        update={
            "title": payload.title,
            "description": payload.description,
            "priority": payload.priority,
        }
    )


@router.get("/{idea_id}", response_model=IdeaRead)
async def get_idea(idea_id: str) -> IdeaRead:
    return next((idea for idea in demo_data.ideas if idea.id == idea_id), demo_data.ideas[0])


@router.patch("/{idea_id}", response_model=IdeaRead)
async def update_idea(idea_id: str, payload: IdeaCreate) -> IdeaRead:
    idea = await get_idea(idea_id)
    return idea.model_copy(update=payload.model_dump(exclude_unset=True))


@router.delete("/{idea_id}", response_model=ApiMessage)
async def archive_idea(idea_id: str) -> ApiMessage:
    return ApiMessage(message=f"idea {idea_id} archived")


@router.post("/{idea_id}/status", response_model=ApiMessage)
async def update_idea_status(idea_id: str, payload: IdeaStatusUpdate) -> ApiMessage:
    return ApiMessage(message=f"idea {idea_id} status changed to {payload.status}")


@router.get("/{idea_id}/history")
async def get_idea_history(idea_id: str) -> list[dict[str, str]]:
    return [{"idea_id": idea_id, "from_status": "active", "to_status": "in_progress"}]


@router.post("/{idea_id}/tags", response_model=ApiMessage)
async def add_idea_tags(idea_id: str, tag_ids: list[str]) -> ApiMessage:
    return ApiMessage(message=f"added {len(tag_ids)} tags to idea {idea_id}")


@router.delete("/{idea_id}/tags/{tag_id}", response_model=ApiMessage)
async def remove_idea_tag(idea_id: str, tag_id: str) -> ApiMessage:
    return ApiMessage(message=f"removed tag {tag_id} from idea {idea_id}")
