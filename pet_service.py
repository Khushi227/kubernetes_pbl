from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests

app = FastAPI()

# Simulated database
pets = {}
pet_id_counter = 1

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
@app.post("/pets/{pet_id}/adopt")
def adopt_pet(pet_id: int, user_id: int):
    # Check if the pet exists
    pet = pets.get(pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if pet.adopted:
        raise HTTPException(status_code=400, detail="Pet is already adopted")

    # Validate the user ID by calling the User Service
    user_service_url = f"http://127.0.0.1:8000/users/{user_id}"
    try:
        response = requests.get(user_service_url, timeout=5)
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500, detail="User Service is unreachable")

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="User not found")

    # Mark the pet as adopted and associate it with the user
    pet.adopted = True
    pet.user_id = user_id
    return {"message": f"Pet {pet.name} has been adopted by user {user_id}"}

# Get pets adopted by a specific user
@app.get("/users/{user_id}/pets", response_model=List[PetOut])
def get_pets_by_user(user_id: int):
    user_pets = [pet for pet in pets.values() if pet.user_id == user_id]
    if not user_pets:
        raise HTTPException(status_code=404, detail="No pets found for this user")
    return [{"id": pet_id, **pet.dict()} for pet_id, pet in pets.items() if pet.user_id == user_id]