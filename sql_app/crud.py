# sql_app/crud.py

from sqlalchemy.orm import Session
from . import models, schemas, security

# --- User CRUD --- 
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Habit CRUD ---

def get_habits(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Habit).filter(models.Habit.owner_id == user_id).offset(skip).limit(limit).all()

def create_user_habit(db: Session, habit: schemas.HabitCreate, user_id: int):
    db_habit = models.Habit(**habit.dict(), owner_id=user_id)
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit

def delete_habit(db: Session, habit_id: int):
    db_habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if db_habit:
        db.delete(db_habit)
        db.commit()
    return db_habit

def update_habit(db: Session, habit_id: int, habit_update: schemas.HabitUpdate):
    db_habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if db_habit:
        # Get the update data as a dictionary
        update_data = habit_update.dict(exclude_unset=True)
        # Iterate over the provided data and update the habit object
        for key, value in update_data.items():
            setattr(db_habit, key, value)
        db.commit()
        db.refresh(db_habit)
    return db_habit
