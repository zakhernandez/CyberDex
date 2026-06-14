from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field



class PingCreate(BaseModel):

    message: str = Field(min_length=1, max_length=200)



class PingRead(BaseModel):

    id: int
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)