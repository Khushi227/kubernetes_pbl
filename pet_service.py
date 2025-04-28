from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional
from jose import jwt, JWTError
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
import requests
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Enable Foreign Key Constraints in SQLite
if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "replace_this_with_a_secure_key")
ALGORITHM = "HS256"
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "https://pet-service-ra5g.onrender.com/users")

# Database Models
class PetDB(Base):
    __tablename__ = "pets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    species = Column(String, index=True)
    age = Column(Integer)
    adopted = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

class AdoptionHistoryDB(Base):
    __tablename__ = "adoption_history"
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)

# Pydantic Models
class Pet(BaseModel):
    name: str
    species: str
    age: int
    adopted: bool = False
    user_id: Optional[int] = None

class PetOut(BaseModel):
    id: int
    name: str
    species: str
    age: int
    adopted: bool
    user_id: Optional[int] = None

class AdoptionHistory(BaseModel):
    pet_id: int
    user_id: int
    username: str
    timestamp: str

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to validate the JWT token
def validate_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

# Helper function to validate user
def validate_user(user_id: int):
    try:
        response = requests.get(f"{USER_SERVICE_URL}/{user_id}")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"User service error: {e}")
        raise HTTPException(status_code=503, detail="User service unavailable")
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="User not found")
    return response.json()

# Routes

# Add a new pet
@app.post("/pets", response_model=PetOut)
def add_pet(pet: Pet, db: Session = Depends(get_db)):
    logger.info(f"Adding a new pet: {pet.name}")
    new_pet = PetDB(
        name=pet.name,
        species=pet.species,
        age=pet.age,
        adopted=pet.adopted
    )
    db.add(new_pet)
    db.commit()
    db.refresh(new_pet)
    return new_pet

# Get all pets
@app.get("/pets", response_model=List[PetOut])
def list_pets(db: Session = Depends(get_db)):
    logger.info("Fetching all pets")
    pets = db.query(PetDB).all()
    return pets

# Adopt a pet
@app.post("/pets/{pet_id}/adopt")
def adopt_pet(pet_id: int, user_id: UserDB = Depends(get_current_user), authorization: str = Header(None), db: Session = Depends(get_db)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    token = authorization.split(" ")[1]
    username = validate_token(token)
    validate_user(user_id)
    pet = db.query(PetDB).filter(PetDB.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if pet.adopted:
        raise HTTPException(status_code=400, detail="Pet already adopted")
    pet.adopted = True
    pet.user_id = user_id
    db.commit()
    adoption_record = AdoptionHistoryDB(
        pet_id=pet_id,
        user_id=user_id,
        username=username,
        timestamp=datetime.utcnow().isoformat()
    )
    db.add(adoption_record)
    db.commit()
    logger.info(f"Pet {pet.name} has been adopted by user {username}")
    return {"message": f"Pet {pet.name} has been adopted by user {username}"}

# Get pets adopted by a specific user
@app.get("/users/{user_id}/pets", response_model=List[PetOut])
def get_pets_by_user(user_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching pets adopted by user {user_id}")
    pets = db.query(PetDB).filter(PetDB.user_id == user_id).all()
    if not pets:
        raise HTTPException(status_code=404, detail="No pets found for this user")
    return pets

# Delete a pet
@app.delete("/pets/{pet_id}")
def delete_pet(pet_id: int, db: Session = Depends(get_db)):
    logger.info(f"Deleting pet with ID {pet_id}")
    pet = db.query(PetDB).filter(PetDB.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    db.delete(pet)
    db.commit()
    return {"message": f"Pet with ID {pet_id} has been deleted"}

# Update a pet
@app.put("/pets/{pet_id}", response_model=PetOut)
def update_pet(pet_id: int, pet: Pet, authorization: str = Header(None), db: Session = Depends(get_db)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    token = authorization.split(" ")[1]
    validate_token(token)
    logger.info(f"Updating pet with ID {pet_id}")

    existing_pet = db.query(PetDB).filter(PetDB.id == pet_id).first()
    if not existing_pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    # Update the attributes of the existing pet object
    existing_pet.name = pet.name
    existing_pet.species = pet.species
    existing_pet.age = pet.age
    existing_pet.adopted = pet.adopted

    # Add the existing pet to the session.  This should already be the case, but adding it explicitly
    #  makes it clear that we want to update this object within the current session.
    db.add(existing_pet)

    # Commit the changes to the database.  This is what persists the updates.
    db.commit()

    # Refresh the existing_pet object to get the latest data from the database.  This is good practice,
    #  especially if there are any database-side triggers or default values that might have changed.
    db.refresh(existing_pet)

    # Return the updated pet object.
    return existing_pet

# Search pets
@app.get("/pets/search", response_model=List[PetOut])
def search_pets(species: Optional[str] = None, adopted: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(PetDB)
    if species:
        query = query.filter(PetDB.species == species)
    if adopted is not None:
        query = query.filter(PetDB.adopted == adopted)
    logger.info(f"Searching pets with filters: species={species}, adopted={adopted}")
    return query.all()

# Get adoption history for a pet
@app.get("/pets/{pet_id}/history", response_model=List[AdoptionHistory])
def get_adoption_history(pet_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching adoption history for pet ID {pet_id}")
    pet = db.query(PetDB).filter(PetDB.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    history = db.query(AdoptionHistoryDB).filter(AdoptionHistoryDB.pet_id == pet_id).all()
    return history

# Recommend pets for a user
@app.get("/users/{user_id}/recommendations", response_model=List[PetOut])
def recommend_pets(user_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching pet recommendations for user {user_id}")
    user_pets = db.query(PetDB).filter(PetDB.user_id == user_id).all()
    if not user_pets:
        raise HTTPException(status_code=404, detail="No recommendations available")
    preferred_species = {pet.species for pet in user_pets}
    recommended_pets = db.query(PetDB).filter(PetDB.species.in_(preferred_species), PetDB.adopted == False).all()
    return recommended_pets