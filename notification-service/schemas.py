from pydantic import BaseModel

class NotificationCreate(BaseModel):
    user_id: int
    recipient: str
    message: str

class NotificationOut(BaseModel):
    id: int
    user_id: int
    recipient: str
    message: str
    status: str
    created_at: str
    
    class Config:
        from_attributes = True
