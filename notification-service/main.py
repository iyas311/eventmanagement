from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, get_db
from models import NotificationLog
from schemas import NotificationCreate, NotificationOut
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="notification-service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )

@app.get("/")
def read_root():
    return {"service": "notification-service", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/notify", response_model=NotificationOut)
def send_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    logging.info(f"Sending notification to {notification.recipient}: {notification.message}")
    
    new_log = NotificationLog(
        user_id=notification.user_id,
        recipient=notification.recipient,
        message=notification.message,
        status="SENT"
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

@app.get("/notifications/{user_id}", response_model=list[NotificationOut])
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    return db.query(NotificationLog).filter(NotificationLog.user_id == user_id).order_by(NotificationLog.id.desc()).all()

@app.delete("/notifications/user/{user_id}")
def clear_notifications(user_id: int, db: Session = Depends(get_db)):
    db.query(NotificationLog).filter(NotificationLog.user_id == user_id).delete()
    db.commit()
    return {"message": "Notifications cleared"}
