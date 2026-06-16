from fastapi import APIRouter

from bitnp_ideas.schemas.common import ApiMessage, IdeaTagRead
from bitnp_ideas.services import demo_data

router = APIRouter()


@router.get("", response_model=list[IdeaTagRead])
async def list_tags() -> list[IdeaTagRead]:
    return demo_data.tags


@router.post("", response_model=IdeaTagRead, status_code=201)
async def create_tag(
    name: str, color: str | None = None, description: str | None = None
) -> IdeaTagRead:
    return IdeaTagRead(
        id=f"tag_{name.lower()}",
        name=name,
        slug=name.lower().replace(" ", "-"),
        color=color,
        description=description,
    )


@router.get("/{tag_id}", response_model=IdeaTagRead)
async def get_tag(tag_id: str) -> IdeaTagRead:
    return next((tag for tag in demo_data.tags if tag.id == tag_id), demo_data.tags[0])


@router.patch("/{tag_id}", response_model=IdeaTagRead)
async def update_tag(tag_id: str, name: str | None = None, color: str | None = None) -> IdeaTagRead:
    tag = await get_tag(tag_id)
    return tag.model_copy(update={"name": name or tag.name, "color": color or tag.color})


@router.delete("/{tag_id}", response_model=ApiMessage)
async def disable_tag(tag_id: str) -> ApiMessage:
    return ApiMessage(message=f"tag {tag_id} disabled")
