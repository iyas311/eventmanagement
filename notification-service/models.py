from database import Base
from sqlalchemy import Column, Integer, String

from datetime import datetime

class NotificationLog(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    recipient = Column(String)
    message = Column(String)
    status = Column(String, default="SENT")
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
