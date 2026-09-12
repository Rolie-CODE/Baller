from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException
import models
from database import engine, SessionLocal
from schemas import UserCreate, UserLogin
from security import hash_password, verify_password



models.Base.metadata.create_all(bind=engine)


app = FastAPI()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {"message": "Hello Rolie"}


@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    hashed_password = hash_password(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        password=hashed_password,
        school=user.school
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(
        models.User.username == user.username
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_valid = verify_password(
        user.password,
        existing_user.password
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "message": "Login successful",
        "user_id": existing_user.id,
        "username": existing_user.username
    }