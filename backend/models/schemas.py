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
    grade: str  # A, B, C, D, or UNKNOWN
    demerit_points: int
    suspended: bool
    is_closed_today: bool = False
    reasoning_trace: str = ""


class LocationResult(BaseModel):
    centre_name: str
    address: str
    lat: float
    lng: float
    distance_km: float
    is_open: bool
    google_rating: Optional[float] = None
    review_count: Optional[int] = None
    reviews_summary: Optional[str] = None
    crowd_level: str = "unknown"  # quiet | busy | unknown
    reasoning_trace: str = ""


class SentimentResult(BaseModel):
    sentiment_score: float = 0.0   # -1.0 (negative) to +1.0 (positive)
    hygiene_concerns: bool = False
    queue_signal: str = "unknown"  # "short" | "long" | "unknown"
    standout_quote: str = ""


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
    standout_quote: Optional[str] = None
    score: float = 0.0


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
