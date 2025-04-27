from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# User database model
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # Relationship to reference pets owned by the user
    pets = relationship("PetDB", back_populates="owner", cascade="all, delete-orphan")


# Pet database model
class PetDB(Base):
    __tablename__ = "pets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    species = Column(String, index=True)
    age = Column(Integer)
    adopted = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationship to reference the owner of the pet
    owner = relationship("UserDB", back_populates="pets")


# Adoption history database model
class AdoptionHistoryDB(Base):
    __tablename__ = "adoption_history"
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    user_id = Column(Integer, nullable=False)  # Not a foreign key to allow historical logging
    username = Column(String, nullable=False)  # Store username for historical purposes
    timestamp = Column(String, nullable=False)