from __future__ import annotations

from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, Field


class VehicleQuery(BaseModel):
    query: str = Field(..., description="Free-form vehicle query, e.g., 'Toyota Camry 2024 India'")
    make: Optional[str] = Field(None, description="Manufacturer, if parsed/known")
    model: Optional[str] = Field(None, description="Model name, if parsed/known")
    year: Optional[int] = Field(None, description="Model year if known")
    trim: Optional[str] = Field(None, description="Trim/variant if known")
    market: Optional[str] = Field(None, description="Market/country, e.g., US, India")

    def pretty(self) -> str:
        return self.query.strip()


class Source(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None
    source_type: Optional[Literal["cache", "web"]] = None


class ResearchBrief(BaseModel):
    vehicle: VehicleQuery
    overview: Optional[str] = None

    engine: Optional[str] = None
    power: Optional[Union[str, float, int]] = None
    torque: Optional[Union[str, float, int]] = None
    transmission: Optional[str] = None
    drivetrain: Optional[str] = None

    fuel_economy: Optional[str] = None
    dimensions: Optional[Union[str, dict]] = None
    weight: Optional[Union[str, float, int]] = None

    pricing: Optional[Union[str, dict]] = None
    safety: Optional[Union[str, dict]] = None
    key_features: list[str] = Field(default_factory=list)

    sources: list[Source] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    notes: list[str] = Field(default_factory=list)


class WriterOutput(BaseModel):
    title: str
    markdown_report: str
    brief: ResearchBrief
    citations: list[Source]
    meta: dict[str, Any] = Field(default_factory=dict)

