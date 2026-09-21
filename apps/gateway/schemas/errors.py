from typing import Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    message: str
    type: str
    code: str
    param: Optional[str] = None
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
