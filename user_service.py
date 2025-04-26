from fastapi import FastAPI, HTTPException,Header, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

# Initialize FastAPI app
app = FastAPI()

# Simulated database
users_db = {}

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "replace_this_with_a_secure_key")  # Replace this with a secure, random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# User models
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

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper functions

# Hash a password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Verify a password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Generate a JWT token
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Routes

# Register a new user
@app.post("/users/register", response_model=UserOut)
def register_user(user: User):
    # Check if the username or email already exists
    for existing_user in users_db.values():
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        if existing_user["username"] == user.username:
            raise HTTPException(status_code=400, detail="Username already taken")
    
    # Add the user to the database
    user_id = len(users_db) + 1
    users_db[user_id] = {
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password)  # Store hashed password
    }
    return {"id": user_id, "username": user.username, "email": user.email}

# Login a user and return JWT token
@app.post("/users/login", response_model=Token)
def login_user(request: LoginRequest):
    # Check if the user exists
    user = None
    for user_id, user_data in users_db.items():
        if user_data["username"] == request.username:
            user = user_data
            break
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Verify the password
    if not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create a JWT token
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route (optional: to test JWT verification)
@app.get("/users/me")
def read_users_me(token: str = Depends(lambda: "dummy")):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
@app.get("/users")
def get_all_users():
    return users_db

@app.get("/users/{user_id}")
def get_user_by_id(user_id: int):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user_id, "username": user["username"], "email": user["email"]}