from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="tester")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sessions = relationship("Session", back_populates="user",cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    status = Column(String, nullable=False, default="active")
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")
    tasks = relationship("Task", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session(session_id='{self.session_id}', status='{self.status}')>"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=False)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)

    round_number = Column(Integer, nullable=False)

    target_index = Column(Integer, nullable=False)
    target_filename = Column(String, nullable=False)
    target_sha256 = Column(String, nullable=True)

    ground_truth = Column(Text, nullable=True)

    model_type = Column(String, nullable=False, default="qwen")

    user_difficulty_rating = Column(String, nullable=True)

    admin_difficulty_rating = Column(Float, nullable=True)

    difficulty = Column(String, nullable=True)

    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="tasks")
    image_versions = relationship("ImageVersion", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(task_id='{self.task_id}', round={self.round_number}, model='{self.model_type}', status='{self.status}')>"

class ImageVersion(Base):
    __tablename__ = 'image_versions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(String(36), unique=True, nullable=False, index=True)
    task_id = Column(String(36), ForeignKey('tasks.task_id'), nullable=False, index=True)

    version_number = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    prompt_time_seconds = Column(Integer, nullable=True, default=0)

    image_path = Column(String(255), nullable=False)
    generation_type = Column(String(20), nullable=False)

    model_type = Column(String, nullable=False, default="qwen")

    user_manual_score = Column(Integer, nullable=True)

    expert_score_1 = Column(Integer, nullable=True)
    expert_score_2 = Column(Integer, nullable=True)

    dino_score = Column(Float, nullable=True)
    hsv_score = Column(Float, nullable=True)
    structure_score = Column(Float, nullable=True)
    clip_score = Column(Float, nullable=True)

    ai_similarity_score = Column(Float, nullable=True)
    ai_similarity_details = Column(Text, nullable=True)

    wise_suggestions = Column(JSON, nullable=True)
    wise_generated = Column(Boolean, default=False)
    wise_error = Column(Text, nullable=True)

    is_final = Column(Boolean, default=False)
    locked = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="image_versions")
    rating = relationship("Rating", back_populates="version", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ImageVersion(version={self.version_number}, model='{self.model_type}', task={self.task_id})>"

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    rating_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, ForeignKey("image_versions.version_id"), nullable=False)

    style_score = Column(Integer, nullable=False)
    object_count_score = Column(Integer, nullable=False)
    perspective_score = Column(Integer, nullable=False)
    depth_background_score = Column(Integer, nullable=False)

    detailed_review = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    version = relationship("ImageVersion", back_populates="rating")

    def __repr__(self):
        avg = round((self.style_score + self.object_count_score + self.perspective_score + self.depth_background_score) / 4, 1)
        return f"<Rating(version_id='{self.version_id}', avg={avg})>"
