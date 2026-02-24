from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    
    # One-to-many relationship: A user can have many photos
    photos = relationship("Photo", back_populates="owner")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    google_photo_id = Column(String, unique=True, index=True)
    thumbnail_url = Column(String)
    
    # Metadata
    creation_time = Column(DateTime, default=datetime.datetime.utcnow)
    lat = Column(Float, nullable=True) # Latitude
    lon = Column(Float, nullable=True) # Longitude
    
    # Google Gemini multimodal embeddings use 1408 dimensions
    image_embedding = Column(Vector(1408), nullable=True)
    
    # Back-reference to the user
    owner = relationship("User", back_populates="photos")
