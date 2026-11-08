import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Security(api_key_header)) -> None:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    expected = settings.api_key.get_secret_value()
    if not secrets.compare_digest(api_key.strip().encode(), expected.encode()):
        raise HTTPException(status_code=403, detail="Invalid API key")
