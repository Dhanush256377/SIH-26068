from sqlalchemy.orm import Session
from app.models.user import User
from app.models.weather import Location, WeatherRecord
from app.models.alert import Alert


# USER

def create_user(db: Session, name, email, password):
    user = User(
        name=name,
        email=email,
        password=password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_email(db: Session, email):
    return db.query(User).filter(User.email == email).first()


def get_user(db: Session, user_id):
    return db.query(User).filter(User.id == user_id).first()


# LOCATION

def create_location(db: Session, user_id, city, latitude, longitude):
    location = Location(
        user_id=user_id,
        city=city,
        latitude=latitude,
        longitude=longitude
    )

    db.add(location)
    db.commit()
    db.refresh(location)

    return location


def get_locations(db: Session, user_id):
    return db.query(Location).filter(
        Location.user_id == user_id
    ).all()


def delete_location(db: Session, location_id):
    location = db.query(Location).filter(
        Location.id == location_id
    ).first()

    if location:
        db.delete(location)
        db.commit()

    return location


# WEATHER

def create_weather_record(
    db: Session,
    location_id,
    temperature,
    humidity,
    rainfall,
    wind_speed,
    weather_condition
):
    weather = WeatherRecord(
        location_id=location_id,
        temperature=temperature,
        humidity=humidity,
        rainfall=rainfall,
        wind_speed=wind_speed,
        weather_condition=weather_condition
    )

    db.add(weather)
    db.commit()
    db.refresh(weather)

    return weather


def get_weather_records(db: Session, location_id):
    return db.query(WeatherRecord).filter(
        WeatherRecord.location_id == location_id
    ).all()


# ALERT

def create_alert(
    db: Session,
    user_id,
    location_id,
    alert_type,
    message,
    severity
):
    alert = Alert(
        user_id=user_id,
        location_id=location_id,
        alert_type=alert_type,
        message=message,
        severity=severity
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


def get_alerts(db: Session, user_id):
    return db.query(Alert).filter(
        Alert.user_id == user_id
    ).all()


# CHAT HISTORY

def create_chat(
    db: Session,
    user_id,
    location_id,
    question,
    response
):
    chat = ChatHistory(
        user_id=user_id,
        location_id=location_id,
        question=question,
        response=response
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat


def get_chat_history(db: Session, user_id):
    return db.query(ChatHistory).filter(
        ChatHistory.user_id == user_id
    ).all()


# ACTIVITY RISK

def create_activity_risk(
    db: Session,
    location_id,
    activity,
    risk_level,
    rain_probability,
    recommendation
):
    risk = ActivityRisk(
        location_id=location_id,
        activity=activity,
        risk_level=risk_level,
        rain_probability=rain_probability,
        recommendation=recommendation
    )

    db.add(risk)
    db.commit()
    db.refresh(risk)

    return risk


def get_activity_risks(db: Session, location_id):
    return db.query(ActivityRisk).filter(
        ActivityRisk.location_id == location_id
    ).all()