from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import os

# Initialize FastAPI app
app = FastAPI()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # Use SQLite for local testing, replace for production
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "replace_this_with_a_secure_key")  # Replace with a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Models
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

Base.metadata.create_all(bind=engine)  # Create the database tables

# Pydantic Models
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

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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
def register_user(user: User, db: Session = Depends(get_db)):
    # Check if the username or email already exists
    if db.query(UserDB).filter(UserDB.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(UserDB).filter(UserDB.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Add the user to the database
    new_user = UserDB(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email}

# Login a user and return JWT token
@app.post("/users/login", response_model=Token)
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    # Validate user
    user = db.query(UserDB).filter(UserDB.username == request.username).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create a JWT token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route to get user details using JWT
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

# Fetch all users
@app.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(UserDB).all()
    return [{"id": user.id, "username": user.username, "email": user.email} for user in users]

# Fetch a user by ID
@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username, "email": user.email}

PET_SERVICE_URL = os.getenv("PET_SERVICE_URL", "http://127.0.0.1:8001")

def get_user_pets_from_pet_service(user_id: int) -> List[dict]:
    """
    Fetches the pets adopted by a specific user from the Pet Service.

    Args:
        user_id: The ID of the user.

    Returns:
        A list of pet dictionaries, or an empty list if no pets are found
        or an error occurs.  Raises HTTPException on error.
    """
    try:
        response = requests.get(f"{PET_SERVICE_URL}/users/{user_id}/pets")
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()  # Expecting a JSON list of pets
    except requests.exceptions.RequestException as e:
        # Log the error for debugging
        print(f"Error fetching pets from Pet Service: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve pets from Pet Service"
        ) from e  # Wrap the original exception for context

