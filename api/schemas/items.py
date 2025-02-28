# define schemas for items
from pydantic import BaseModel


class HeroCreate(BaseModel):
    type: str
    owner: str

class HeroRead(HeroCreate):
    id: int 
