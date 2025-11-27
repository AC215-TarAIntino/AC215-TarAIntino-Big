"""
Trailer Generator - Microservice for generating movie trailer scene breakdowns.
"""

__version__ = "0.1.0"

from .schemas import (
    CharacterDesign,
    TrailerBreakdown,
    TrailerGenerationResponse,
    TrailerRequest,
    TrailerScene,
)

__all__ = [
    "TrailerRequest",
    "TrailerScene",
    "TrailerBreakdown",
    "TrailerGenerationResponse",
    "CharacterDesign",
]
