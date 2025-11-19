"""
Database Schemas for Gestor de Alta Performance com IA

Each Pydantic model below represents a MongoDB collection. The collection
name is the lowercase of the class name (e.g., Task -> "task").
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

# Base user
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")

# Agenda / Calendar
class Event(BaseModel):
    user_id: str = Field(..., description="Owner user id")
    title: str
    description: Optional[str] = None
    category: str = Field("personal", description="personal|professional|family|other")
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    all_day: bool = False

class FocusBlock(BaseModel):
    user_id: str
    title: str
    start_time: datetime
    end_time: datetime
    objective: Optional[str] = None

# Tasks
class Task(BaseModel):
    user_id: str
    title: str
    description: Optional[str] = None
    scope: str = Field("personal", description="professional|personal|family|home")
    labels: List[str] = []
    priority: str = Field("medium", description="low|medium|high|urgent")
    due_date: Optional[date] = None
    completed: bool = False

# Habits
class Habit(BaseModel):
    user_id: str
    name: str
    target_per_day: int = 1
    done_today: int = 0

# Goals
class Goal(BaseModel):
    user_id: str
    title: str
    horizon: str = Field("weekly", description="annual|quarterly|monthly|weekly")
    progress: int = Field(0, ge=0, le=100)
    actions: List[str] = []

# Health
class HealthLog(BaseModel):
    user_id: str
    type: str = Field("energy", description="energy|mood|workout|water|supplement")
    value: float = 0
    note: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Nutrition
class MealPlan(BaseModel):
    user_id: str
    date: date
    meals: List[str] = []
    objective: str = Field("energia", description="perda_peso|foco_mental|energia|bem_estar")
    shopping_list: List[str] = []

# Family / Home
class FamilyItem(BaseModel):
    user_id: str
    type: str = Field("maintenance", description="maintenance|task|recurring_purchase|document|reminder")
    title: str
    due_date: Optional[date] = None
    notes: Optional[str] = None

# Contacts
class Contact(BaseModel):
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    birthday: Optional[date] = None

# Notes
class Note(BaseModel):
    user_id: str
    title: str
    content: str
    type: str = Field("note", description="note|gratitude|idea|reflection")
    created_at: datetime = Field(default_factory=datetime.utcnow)

# AI Requests (audit)
class AIRequest(BaseModel):
    user_id: str
    kind: str
    parameters: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
