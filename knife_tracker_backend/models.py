from pydantic import BaseModel
from typing import List, Optional

class RegisterDevice(BaseModel):
    deviceId: str
    pushToken: str


class UpdateFilters(BaseModel):
    categories: List[str]
    minPrice: Optional[float] = None
    maxPrice: Optional[float] = None

class UpdateNotifications(BaseModel):
    enabled: bool
