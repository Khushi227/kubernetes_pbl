from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Simulated database
users = {}
user_id_counter = 1

# Data Models
class User(BaseModel):
    username: str
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str

class LoginRequest(BaseModel):
    username: str
    password: str

# Routes

# Register a new user
@app.post("/users/register", response_model=UserOut)
def register_user(user: User):
    global user_id_counter
    # Check if email is already registered
    for existing_user in users.values():
        if existing_user.email == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Register the user
    user_id = user_id_counter
    users[user_id] = user
    user_id_counter += 1
    return {"id": user_id, "username": user.username, "email": user.email}

# Login a user
@app.post("/users/login")
def login_user(request: LoginRequest):
    # Authenticate the user
    for user_id, user in users.items():
        if user.username == request.username and user.password == request.password:
            return {"message": f"Welcome back, {request.username}!"}
    
    # If authentication fails
    raise HTTPException(status_code=401, detail="Invalid username or password")

# Get user by ID
@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    user = users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"id": user_id, "username": user.username, "email": user.email}

# List all users
@app.get("/users", response_model=List[UserOut])
def list_users():
    return [{"id": user_id, "username": user.username, "email": user.email} for user_id, user in users.items()]