from fastapi import APIRouter

from bitnp_ideas.schemas.common import ApiKeyCreate, ApiKeyRead, ApiMessage
from bitnp_ideas.services import demo_data

router = APIRouter()


@router.get("", response_model=list[ApiKeyRead])
async def list_api_keys() -> list[ApiKeyRead]:
    return demo_data.api_keys


@router.post("", status_code=201)
async def create_api_key(payload: ApiKeyCreate) -> dict[str, object]:
    key = demo_data.api_keys[0].model_copy(update={"name": payload.name, "scopes": payload.scopes})
    return {"api_key": key, "secret": "shown-once-demo-secret"}


@router.patch("/{api_key_id}", response_model=ApiMessage)
async def update_api_key(api_key_id: str, is_active: bool) -> ApiMessage:
    return ApiMessage(message=f"api key {api_key_id} active={is_active}")


@router.delete("/{api_key_id}", response_model=ApiMessage)
async def revoke_api_key(api_key_id: str) -> ApiMessage:
    return ApiMessage(message=f"api key {api_key_id} revoked")


@router.post("/{api_key_id}/rotate")
async def rotate_api_key(api_key_id: str) -> dict[str, str]:
    return {"api_key_id": api_key_id, "secret": "rotated-shown-once-demo-secret"}
