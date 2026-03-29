from fastapi import FastAPI, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, get_db
from models import Booking
from schemas import BookingCreate, BookingOut
import requests
import json
import pika
import os
from dotenv import load_dotenv

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="booking-service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"service": "booking-service", "status": "running"}

EVENTS_SERVICE_URL = os.getenv("EVENTS_SERVICE_URL", "http://localhost:8002")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

def publish_notification(payload):
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.exchange_declare(exchange='notifications', exchange_type='fanout', durable=False)
        channel.basic_publish(exchange='notifications', routing_key='', body=json.dumps(payload))
        connection.close()
    except Exception as e:
        print(f"RabbitMQ publish failed: {e}")

@app.post("/bookings", response_model=BookingOut)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    try:
        response = requests.get(f"{EVENTS_SERVICE_URL}/events/{booking.event_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Event not found")
        event_data = response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Events service unavailable")
        
    if event_data.get("capacity", 0) < booking.quantity:
        raise HTTPException(status_code=400, detail="Not enough tickets available")
        
    try:
        cap_response = requests.put(f"{EVENTS_SERVICE_URL}/events/{booking.event_id}/capacity?amount={booking.quantity}")
        if cap_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to reduce capacity")
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Events service unavailable")

    new_booking = Booking(
        user_id=booking.user_id,
        event_id=booking.event_id,
        status="PENDING",
        amount=event_data.get("price", 0.0) * booking.quantity,
        quantity=booking.quantity,
        attendee_name=booking.attendee_name,
        email=booking.email
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    # Send notification to Attendee
    publish_notification({
        "user_id": new_booking.user_id,
        "recipient": new_booking.email or f"User {new_booking.user_id}",
        "message": f"Booking successful! You've secured a spot for '{event_data.get('title')}'. 🎉"
    })

    # Send notification to Organizer
    organizer_id = event_data.get("organizer_id")
    if organizer_id:
        publish_notification({
            "user_id": organizer_id,
            "recipient": f"Organizer {organizer_id}",
            "message": f"Great news! A new booking has been made for your event '{event_data.get('title')}'. 📈"
        })

    return new_booking

@app.get("/bookings", response_model=List[BookingOut])
def get_all_bookings(db: Session = Depends(get_db)):
    return db.query(Booking).all()

@app.get("/bookings/user/{user_id}", response_model=List[BookingOut])
def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    return db.query(Booking).filter(Booking.user_id == user_id).all()

@app.get("/bookings/event/{event_id}", response_model=List[BookingOut])
def get_event_bookings(event_id: int, db: Session = Depends(get_db)):
    return db.query(Booking).filter(Booking.event_id == event_id).all()

@app.get("/bookings/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@app.put("/bookings/{booking_id}/pay", response_model=BookingOut)
def pay_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = "PAID"
    db.commit()
    db.refresh(booking)

    # Send notification for payment
    try:
        ev_res = requests.get(f"{EVENTS_SERVICE_URL}/events/{booking.event_id}")
        event_data = ev_res.json() if ev_res.status_code == 200 else {}
        
        publish_notification({
            "user_id": booking.user_id,
            "recipient": booking.email or f"User {booking.user_id}",
            "message": f"Payment successful! Your ticket for '{event_data.get('title')}' is now confirmed. 🎟️"
        })
        
        organizer_id = event_data.get("organizer_id")
        if organizer_id:
            publish_notification({
                "user_id": organizer_id,
                "recipient": f"Organizer {organizer_id}",
                "message": f"Success! A booking for '{event_data.get('title')}' has been paid and confirmed. 💰"
            })
    except Exception as e:
        print(f"Failed to send payment notifications: {e}")

    return booking
