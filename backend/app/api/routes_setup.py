from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.config import settings
from app.services.nebius_client import NebiusClient
from app.security.redaction import mask_api_key

router = APIRouter(prefix="/setup", tags=["Setup & Connection"])

class SetupStatusResponse(BaseModel):
    configured: bool
    base_url: str
    model: str
    key_status: str
    setup_instructions: str

class TestConnectionRequest(BaseModel):
    base_url: Optional[str] = None
    model: Optional[str] = None

@router.get("/status", response_model=SetupStatusResponse)
def get_setup_status():
    has_key = bool(settings.nebius_api_key and settings.nebius_api_key.strip())
    masked = mask_api_key(settings.nebius_api_key)
    return SetupStatusResponse(
        configured=has_key,
        base_url=settings.nebius_base_url,
        model=settings.nebius_model,
        key_status=f"Configured ({masked})" if has_key else "Missing",
        setup_instructions=(
            "Add your NEBIUS_API_KEY into your local .env file. "
            "Never share or commit this key to Git or public chats."
        )
    )

@router.post("/test-connection")
def test_connection(req: Optional[TestConnectionRequest] = None):
    custom_base_url = req.base_url if req and req.base_url else settings.nebius_base_url
    custom_model = req.model if req and req.model else settings.nebius_model
    
    client = NebiusClient(
        base_url=custom_base_url,
        api_key=settings.nebius_api_key,
        model=custom_model
    )
    return client.test_connection()
