from typing import List
from pydantic import BaseModel


class ModelItem(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "crouter"


class ModelListResponse(BaseModel):
    object: str = "list"
    data: List[ModelItem]
