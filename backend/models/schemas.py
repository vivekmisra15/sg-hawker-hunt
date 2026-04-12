"""
Pydantic models for all agent inputs and outputs.
"""
from pydantic import BaseModel
from typing import Optional


class SearchRequest(BaseModel):
    query: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class HygieneResult(BaseModel):
    stall_name: str
    centre_name: str
    grade: str  # A, B, C, D
    demerit_points: int
    suspended: bool


class LocationResult(BaseModel):
    centre_name: str
    address: str
    lat: float
    lng: float
    distance_km: float
    is_open: bool
    google_rating: Optional[float]
    review_count: Optional[int]
    reviews_summary: Optional[str]


class RankedRecommendation(BaseModel):
    stall_name: str
    centre_name: str
    rank: int
    reasoning: str
    hygiene_grade: str
    is_michelin: bool
    is_halal: bool
    is_open: bool
    distance_km: float
    google_rating: Optional[float] = None


class CentreInfo(BaseModel):
    centre_id: str
    name: str
    address: str
    lat: float
    lng: float


class WeatherResult(BaseModel):
    description: str
    temp_c: float
    is_raining: bool
    outdoor_recommendation: str


class AgentEvent(BaseModel):
    type: str
    agent: Optional[str] = None
    message: str
    data: dict = {}


class SearchResponse(BaseModel):
    query: str
    recommendations: list[RankedRecommendation]
    centres_checked: int
    agent_events: list[AgentEvent] = []
