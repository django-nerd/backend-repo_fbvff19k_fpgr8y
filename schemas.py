"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Example schemas (you can keep these for reference):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Baby Names App Schemas
# --------------------------------------------------

class Preference(BaseModel):
    """User preferences for baby name generation"""
    surname: str = Field(..., description="Family surname to check flow/compatibility")
    cultures: List[str] = Field(default_factory=list, description="Cultural backgrounds to draw names from")
    languages: List[str] = Field(default_factory=list, description="Languages spoken in the family")
    beliefs: List[str] = Field(default_factory=list, description="Belief or theme preferences (nature, virtue, religious, mythology)")
    family_origins: List[str] = Field(default_factory=list, description="Family geographic/ethnic origins")
    parent_names: List[str] = Field(default_factory=list, description="Parents' first names")
    sibling_names: List[str] = Field(default_factory=list, description="Existing siblings' names")
    gender: Optional[str] = Field(None, description="Gender preference: boy, girl, unisex")
    style: Optional[str] = Field(None, description="Style preference: classic, modern, nature, virtue, myth, religious")
    starts_with: Optional[str] = Field(None, description="Preferred starting letter")
    max_length: Optional[int] = Field(None, description="Maximum name length in characters")
    uniqueness: Optional[str] = Field(None, description="How common or unique should the name be: common, balanced, unique")

class Suggestion(BaseModel):
    name: str
    gender: Optional[str] = None
    origin: Optional[str] = None
    meaning: Optional[str] = None
    themes: List[str] = Field(default_factory=list)
    score: float = 0.0
    rationale: Optional[str] = None

class Generation(BaseModel):
    """A generation event that stores preferences and suggested names"""
    preference: Preference
    suggestions: List[Suggestion]
    notes: Optional[str] = None

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
