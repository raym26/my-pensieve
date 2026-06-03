from fastapi import APIRouter, Query
from services.vault_service import VaultService
from services.digest_service import DigestService
from config import VAULT_PATH

router = APIRouter()
vault = VaultService(VAULT_PATH)
digester = DigestService(vault)


@router.get("/")
def get_digest(days: int = Query(1, ge=1, le=30)):
    return digester.generate(days=days)
