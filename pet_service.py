from fastapi import FastAPI, HTTPException, Header, Depends,File, UploadFile
from pydantic import BaseModel
from typing import List, Optional
from jose import jwt, JWTError
import requests
import os
from datetime import datetime

app = FastAPI()

# Simulated database
pets = {}
pet_id_counter = 1

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "replace_this_with_a_secure_key")  # Use the same key as in the User Service
ALGORITHM = "HS256"
USER_SERVICE_URL = "http://127.0.0.1:8000/users"  # Update this URL to the deployed User Service

# Data Models
class Pet(BaseModel):
    name: str
    species: str
    age: int
    adopted: bool = False
    user_id: Optional[int] = None  # Tracks the user who adopted the pet

class PetOut(BaseModel):
    id: int
    name: str
    species: str
    age: int
    adopted: bool
    user_id: Optional[int] = None

# Helper function to validate the JWT token
def validate_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes

# Add a new pet
@app.post("/pets", response_model=PetOut)
def add_pet(pet: Pet):
    global pet_id_counter
    pet_id = pet_id_counter
    pets[pet_id] = pet
    pet_id_counter += 1
    return {"id": pet_id, **pet.dict()}

# Get all pets
@app.get("/pets", response_model=List[PetOut])
def list_pets():
    return [{"id": pet_id, **pet.dict()} for pet_id, pet in pets.items()]

# Adopt a pet
adoption_history = {}

@app.post("/pets/{pet_id}/adopt")
def adopt_pet(pet_id: int, user_id: int, authorization: str = Header(None)):
    global adoption_history  # Access the global adoption history

    # Ensure the Authorization header is present
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    # Extract token and validate
    token = authorization.split(" ")[1]
    username = validate_token(token)

    # Validate the user ID by calling the User Service (optional but recommended)
    response = requests.get(f"{USER_SERVICE_URL}/{user_id}")
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="User not found")

    # Handle pet adoption logic
    pet = pets.get(pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if pet.adopted:
        raise HTTPException(status_code=400, detail="Pet already adopted")

    # Update the pet's adoption status
    pet.adopted = True
    pet.user_id = user_id

    # Record adoption history
    adoption_history.setdefault(pet_id, []).append(
        {"user_id": user_id, "username": username, "timestamp": datetime.utcnow().isoformat()}
    )

    return {"message": f"Pet {pet.name} has been adopted by user {username}"}

# Get pets adopted by a specific user
@app.get("/users/{user_id}/pets", response_model=List[PetOut])
def get_pets_by_user(user_id: int):
    user_pets = [pet for pet in pets.values() if pet.user_id == user_id]
    if not user_pets:
        raise HTTPException(status_code=404, detail="No pets found for this user")
    return [{"id": pet_id, **pet.dict()} for pet_id, pet in pets.items() if pet.user_id == user_id]

@app.delete("/pets/{pet_id}")
def delete_pet(pet_id: int):
    if pet_id not in pets:
        raise HTTPException(status_code=404, detail="Pet not found")
    del pets[pet_id]
    return {"message": f"Pet with ID {pet_id} has been deleted"}

@app.put("/pets/{pet_id}", response_model=PetOut)
def update_pet(pet_id: int, pet: Pet):
    if pet_id not in pets:
        raise HTTPException(status_code=404, detail="Pet not found")
    pets[pet_id] = pet
    return {"id": pet_id, **pet.dict()}

@app.get("/pets/search", response_model=List[PetOut])
def search_pets(species: Optional[str] = None, adopted: Optional[bool] = None):
    filtered_pets = [
        {"id": pet_id, **pet.dict()}
        for pet_id, pet in pets.items()
        if (species is None or pet.species == species)
        and (adopted is None or pet.adopted == adopted)
    ]
    return filtered_pets

@app.get("/pets/{pet_id}/history")
def get_adoption_history(pet_id: int):
    global adoption_history  # Access the global dictionary
    if pet_id not in pets:
        raise HTTPException(status_code=404, detail="Pet not found")
    return adoption_history.get(pet_id, [])

@app.get("/users/{user_id}/recommendations", response_model=List[PetOut])
def recommend_pets(user_id: int):
    # Example logic: Recommend pets of the same species as previously adopted pets
    user_pets = [pet for pet in pets.values() if pet.user_id == user_id]
    if not user_pets:
        raise HTTPException(status_code=404, detail="No recommendations available")
    preferred_species = {pet.species for pet in user_pets}
    recommended_pets = [
        {"id": pet_id, **pet.dict()}
        for pet_id, pet in pets.items()
        if pet.species in preferred_species and not pet.adopted
    ]
    return recommended_pets

