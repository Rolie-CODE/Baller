from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from database import engine, SessionLocal
import models
from schemas import (
    UserCreate,
    UserLogin,
    UserOut,
    Token,
    SchoolCreate,
    SchoolUpdate,
    SchoolOut,
    PlayerProfileCreate,
    PlayerProfileUpdate,
    PlayerProfileOut,
    PositionEnum,
)
from security import hash_password, verify_password, create_access_token, decode_access_token


def seed_initial_schools():
    db = SessionLocal()
    try:
        initial_schools = [
            "University of Ghana",
            "Kwame Nkrumah University of Science and Technology",
            "University of Cape Coast",
        ]
        for school_name in initial_schools:
            exists = db.query(models.School).filter(models.School.name == school_name).first()
            if not exists:
                school = models.School(name=school_name)
                db.add(school)
        db.commit()
    finally:
        db.close()


models.Base.metadata.create_all(bind=engine)
seed_initial_schools()

app = FastAPI(title="Basketball Platform API", version="1.0.0")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    return current_user


@app.get("/")
def home():
    return {"message": "Hello Rolie - Basketball Platform API"}


# ==========================================
# Authentication Endpoints
# ==========================================

@app.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    existing_username = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken"
        )

    hashed_password = hash_password(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/auth/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    identifier = user.get_identifier()
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is required"
        )

    existing_user = db.query(models.User).filter(
        or_(models.User.username == identifier, models.User.email == identifier)
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password"
        )

    if not verify_password(user.password, existing_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password"
        )

    if not existing_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        data={
            "sub": str(existing_user.id),
            "email": existing_user.email,
            "role": existing_user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.get("/auth/me", response_model=UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# ==========================================
# School Endpoints
# ==========================================

@app.post("/schools", response_model=SchoolOut, status_code=status.HTTP_201_CREATED)
def create_school(
    school_in: SchoolCreate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    existing = db.query(models.School).filter(models.School.name == school_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A school with this name already exists"
        )

    new_school = models.School(
        name=school_in.name,
        location=school_in.location,
        description=school_in.description,
        logo_url=school_in.logo_url
    )
    db.add(new_school)
    db.commit()
    db.refresh(new_school)
    return new_school


@app.get("/schools", response_model=list[SchoolOut])
def list_schools(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    return db.query(models.School).offset(offset).limit(limit).all()


@app.get("/schools/{school_id}", response_model=SchoolOut)
def get_school(school_id: int, db: Session = Depends(get_db)):
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    return school


@app.patch("/schools/{school_id}", response_model=SchoolOut)
def update_school(
    school_id: int,
    school_in: SchoolUpdate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")

    if school_in.name is not None and school_in.name != school.name:
        dup = db.query(models.School).filter(models.School.name == school_in.name).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A school with this name already exists"
            )
        school.name = school_in.name

    if school_in.location is not None:
        school.location = school_in.location
    if school_in.description is not None:
        school.description = school_in.description
    if school_in.logo_url is not None:
        school.logo_url = school_in.logo_url

    db.commit()
    db.refresh(school)
    return school


@app.delete("/schools/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(
    school_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")

    db.delete(school)
    db.commit()
    return None


# ==========================================
# Player Profile Endpoints
# ==========================================

@app.post("/players", response_model=PlayerProfileOut, status_code=status.HTTP_201_CREATED)
def create_player_profile(
    player_in: PlayerProfileCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["PLAYER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only players can create a basketball profile"
        )

    existing_profile = db.query(models.PlayerProfile).filter(
        models.PlayerProfile.user_id == current_user.id
    ).first()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A basketball profile already exists for this user"
        )

    if player_in.school_id is not None:
        school = db.query(models.School).filter(models.School.id == player_in.school_id).first()
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="School not found"
            )

    new_profile = models.PlayerProfile(
        user_id=current_user.id,
        first_name=player_in.first_name,
        last_name=player_in.last_name,
        date_of_birth=player_in.date_of_birth,
        height=player_in.height,
        weight=player_in.weight,
        position=player_in.position.value,
        jersey_number=player_in.jersey_number,
        school_id=player_in.school_id,
        bio=player_in.bio,
        profile_image_url=player_in.profile_image_url
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile


@app.get("/players", response_model=list[PlayerProfileOut])
def list_players(
    position: PositionEnum | None = None,
    school_id: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(models.PlayerProfile).options(joinedload(models.PlayerProfile.school))
    if position:
        query = query.filter(models.PlayerProfile.position == position.value)
    if school_id is not None:
        query = query.filter(models.PlayerProfile.school_id == school_id)

    offset = (page - 1) * limit
    return query.offset(offset).limit(limit).all()


@app.get("/players/{player_id}", response_model=PlayerProfileOut)
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.query(models.PlayerProfile).options(
        joinedload(models.PlayerProfile.school)
    ).filter(models.PlayerProfile.id == player_id).first()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return player


@app.patch("/players/{player_id}", response_model=PlayerProfileOut)
def update_player_profile(
    player_id: int,
    player_in: PlayerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    profile = db.query(models.PlayerProfile).options(
        joinedload(models.PlayerProfile.school)
    ).filter(models.PlayerProfile.id == player_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    if current_user.role != "ADMIN" and profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile"
        )

    if player_in.school_id is not None:
        school = db.query(models.School).filter(models.School.id == player_in.school_id).first()
        if not school:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
        profile.school_id = player_in.school_id

    if player_in.first_name is not None:
        profile.first_name = player_in.first_name
    if player_in.last_name is not None:
        profile.last_name = player_in.last_name
    if player_in.date_of_birth is not None:
        profile.date_of_birth = player_in.date_of_birth
    if player_in.height is not None:
        profile.height = player_in.height
    if player_in.weight is not None:
        profile.weight = player_in.weight
    if player_in.position is not None:
        profile.position = player_in.position.value
    if player_in.jersey_number is not None:
        profile.jersey_number = player_in.jersey_number
    if player_in.bio is not None:
        profile.bio = player_in.bio
    if player_in.profile_image_url is not None:
        profile.profile_image_url = player_in.profile_image_url

    db.commit()
    db.refresh(profile)
    return profile


@app.delete("/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player_profile(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    profile = db.query(models.PlayerProfile).filter(models.PlayerProfile.id == player_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    if current_user.role != "ADMIN" and profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this profile"
        )

    db.delete(profile)
    db.commit()
    return None
