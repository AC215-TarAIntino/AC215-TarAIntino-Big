"""
Trailer Generator - Microservice for generating movie trailer scene breakdowns.
"""

__version__ = "0.1.0"

from .schemas import (
    TrailerRequest,
    TrailerScene,
    TrailerBreakdown,
    TrailerGenerationResponse,
    CharacterDesign,
)

__all__ = [
    "TrailerRequest",
    "TrailerScene",
    "TrailerBreakdown",
    "TrailerGenerationResponse",
    "CharacterDesign",
]
