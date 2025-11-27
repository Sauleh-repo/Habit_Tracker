# sql_app/main.py

from datetime import timedelta, date
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import crud, models, schemas, security
from .database import SessionLocal, engine

# This line is commented out as per our previous fix to prevent server lock-ups
# models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# This is the CORS middleware configuration
origins = [
    "http://localhost:3000",                # For local development
    "http://34.54.156.38",                  # Your GCP Load Balancer IP (no trailing slash)
    "http://storage.googleapis.com",        # The origin for GCS (no path or filename)
    "https://storage.googleapis.com",       # Adding https as well, just in case
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Authentication Dependency ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# --- API Endpoints ---

@app.post("/users/register", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user

@app.post("/habits/", response_model=schemas.Habit)
def create_habit_for_user(
    habit: schemas.HabitCreate,
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.create_user_habit(db=db, habit=habit, user_id=current_user.id)

@app.get("/habits/", response_model=List[schemas.Habit])
def read_habits(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    habits = db.query(models.Habit).filter(models.Habit.owner_id == current_user.id).offset(skip).limit(limit).all()
    return habits

@app.put("/habits/{habit_id}/toggle", response_model=schemas.Habit)
def toggle_habit_completion(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    db_habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()

    if db_habit is None:
        raise HTTPException(status_code=44, detail="Habit not found")

    if db_habit.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this habit")

    today = date.today()
    if db_habit.last_completed_at == today:
        db_habit.last_completed_at = None
    else:
        db_habit.last_completed_at = today

    db.commit()
    db.refresh(db_habit)
    return db_habit

@app.delete("/habits/{habit_id}", response_model=schemas.Habit)
def delete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    db_habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()

    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    if db_habit.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this habit")
    
    deleted_habit = crud.delete_habit(db=db, habit_id=habit_id)
    return deleted_habit

@app.put("/habits/{habit_id}", response_model=schemas.Habit)
def update_habit_details(
    habit_id: int,
    habit_update: schemas.HabitUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    db_habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()

    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    if db_habit.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this habit")
    
    updated_habit = crud.update_habit(db=db, habit_id=habit_id, habit_update=habit_update)
    return updated_habit