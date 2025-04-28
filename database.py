from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from models import Base, UserDB, PetDB, AdoptionHistoryDB
import os

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Create the engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # Number of connections to keep in the pool
    max_overflow=20,  # Maximum number of connections allowed beyond pool_size
    pool_recycle=3600,  # Recycle connections after this many seconds (e.g., 1 hour)
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)


# Enable SQLite Foreign Key Constraints
if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to initialize the database
def initialize_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)  # Drop existing tables, if any

    print("Creating tables in specific order...")
    UserDB.__table__.create(bind=engine)  # Create the 'users' table first
    PetDB.__table__.create(bind=engine)   # Create the 'pets' table next
    AdoptionHistoryDB.__table__.create(bind=engine)  # Create the 'adoption_history' table last
    print("Database tables created successfully.")

if __name__ == "__main__":
    initialize_database()