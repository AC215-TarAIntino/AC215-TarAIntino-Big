"""
Tests for Pydantic schemas.
"""

import pytest
from pydantic import ValidationError
from movie_pipeline.schemas import (
    MovieRequest,
    CastMember,
    GeneratedMovie,
    MovieGenerationResponse
)


class TestMovieRequest:
    """Tests for MovieRequest schema."""

    def test_valid_movie_request(self):
        """Test creating a valid MovieRequest."""
        request = MovieRequest(movie_names=["Inception", "The Matrix"])
        assert request.movie_names == ["Inception", "The Matrix"]
        assert request.model is None

    def test_movie_request_with_model(self):
        """Test MovieRequest with optional model parameter."""
        request = MovieRequest(
            movie_names=["Inception"],
            model="anthropic/claude-3.5-sonnet"
        )
        assert request.movie_names == ["Inception"]
        assert request.model == "anthropic/claude-3.5-sonnet"

    def test_movie_request_empty_list(self):
        """Test that empty movie list raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            MovieRequest(movie_names=[])
        assert "too_short" in str(exc_info.value)

    def test_movie_request_too_many_movies(self):
        """Test that more than 10 movies raises validation error."""
        movies = [f"Movie{i}" for i in range(11)]
        with pytest.raises(ValidationError) as exc_info:
            MovieRequest(movie_names=movies)
        assert "too_long" in str(exc_info.value)

    def test_movie_request_single_movie(self):
        """Test MovieRequest with single movie."""
        request = MovieRequest(movie_names=["Inception"])
        assert len(request.movie_names) == 1

    def test_movie_request_exactly_ten_movies(self):
        """Test MovieRequest with exactly 10 movies (boundary)."""
        movies = [f"Movie{i}" for i in range(10)]
        request = MovieRequest(movie_names=movies)
        assert len(request.movie_names) == 10


class TestCastMember:
    """Tests for CastMember schema."""

    def test_valid_cast_member(self):
        """Test creating a valid CastMember."""
        cast = CastMember(
            actor_name="John Fictional",
            character_name="Detective Smith",
            physical_description="A tall man in his 40s with sharp features",
            personality_traits=["brave", "intelligent", "determined"],
            acting_style="Method actor with intense presence",
            role_description="Lead investigator solving a complex case"
        )
        assert cast.actor_name == "John Fictional"
        assert cast.character_name == "Detective Smith"
        assert len(cast.personality_traits) == 3

    def test_cast_member_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError):
            CastMember(
                actor_name="John Fictional",
                character_name="Detective Smith"
                # Missing other required fields
            )

    def test_cast_member_empty_traits(self):
        """Test CastMember with empty personality traits."""
        cast = CastMember(
            actor_name="Jane Fictional",
            character_name="Dr. Johnson",
            physical_description="A woman in her 30s",
            personality_traits=[],
            acting_style="Versatile character actor",
            role_description="Supporting role as medical examiner"
        )
        assert cast.personality_traits == []


class TestGeneratedMovie:
    """Tests for GeneratedMovie schema."""

    def get_valid_movie_data(self):
        """Helper to get valid movie data."""
        return {
            "title": "The Quantum Paradox",
            "tagline": "Reality is just the beginning",
            "genres": ["Sci-Fi", "Thriller"],
            "plot_summary": "A detailed plot about quantum mechanics and time travel.",
            "director_name": "Maria Filmmaker",
            "director_background": "Known for sci-fi epics with philosophical depth.",
            "writers": ["John Writer", "Jane Scriptwriter"],
            "writer_backgrounds": "Award-winning writing team specializing in complex narratives.",
            "cast": [
                {
                    "actor_name": "Alex Performer",
                    "character_name": "Dr. Chen",
                    "physical_description": "Tall Asian man in his 40s with graying hair",
                    "personality_traits": ["brilliant", "obsessive"],
                    "acting_style": "Intense method acting",
                    "role_description": "Lead physicist discovering time travel"
                }
            ],
            "runtime": "142 min",
            "rating": "PG-13",
            "release_year": 2026,
            "production_company": "Stellar Productions",
            "production_company_background": "Independent studio known for intelligent sci-fi.",
            "budget": "$80M",
            "themes": ["time", "identity", "consequences"],
            "visual_style": "Dark, moody cinematography with neon accents",
            "target_audience": "Adults 25-45 who enjoy thoughtful sci-fi"
        }

    def test_valid_generated_movie(self):
        """Test creating a valid GeneratedMovie."""
        movie_data = self.get_valid_movie_data()
        movie = GeneratedMovie(**movie_data)

        assert movie.title == "The Quantum Paradox"
        assert len(movie.genres) == 2
        assert movie.release_year == 2026
        assert len(movie.cast) == 1

    def test_generated_movie_with_optional_fields(self):
        """Test GeneratedMovie with optional fields."""
        movie_data = self.get_valid_movie_data()
        movie_data["inspiration_source"] = ["Inception", "The Matrix"]
        movie_data["unique_selling_point"] = "First film to accurately depict quantum physics"
        movie_data["similar_movies"] = ["Interstellar", "Arrival"]

        movie = GeneratedMovie(**movie_data)

        assert movie.inspiration_source == ["Inception", "The Matrix"]
        assert movie.unique_selling_point is not None
        assert len(movie.similar_movies) == 2

    def test_generated_movie_release_year_validation(self):
        """Test that release year must be between 2024-2030."""
        movie_data = self.get_valid_movie_data()

        # Test valid years
        for year in [2024, 2025, 2030]:
            movie_data["release_year"] = year
            movie = GeneratedMovie(**movie_data)
            assert movie.release_year == year

        # Test invalid years
        for year in [2023, 2031]:
            movie_data["release_year"] = year
            with pytest.raises(ValidationError) as exc_info:
                GeneratedMovie(**movie_data)
            assert "greater_than_equal" in str(exc_info.value) or "less_than_equal" in str(exc_info.value)

    def test_generated_movie_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        incomplete_data = {
            "title": "Test Movie",
            "tagline": "A test"
            # Missing many required fields
        }

        with pytest.raises(ValidationError):
            GeneratedMovie(**incomplete_data)

    def test_generated_movie_multiple_cast_members(self):
        """Test GeneratedMovie with multiple cast members."""
        movie_data = self.get_valid_movie_data()
        movie_data["cast"].append({
            "actor_name": "Sarah Star",
            "character_name": "Agent Murphy",
            "physical_description": "Athletic woman in her 30s",
            "personality_traits": ["determined", "tactical"],
            "acting_style": "Physical performance specialist",
            "role_description": "Government agent tracking the physicist"
        })

        movie = GeneratedMovie(**movie_data)
        assert len(movie.cast) == 2


class TestMovieGenerationResponse:
    """Tests for MovieGenerationResponse schema."""

    def test_successful_response(self):
        """Test a successful movie generation response."""
        movie_data = {
            "title": "Test Movie",
            "tagline": "A test",
            "genres": ["Action"],
            "plot_summary": "Test plot",
            "director_name": "Test Director",
            "director_background": "Test background",
            "writers": ["Writer 1"],
            "writer_backgrounds": "Test",
            "cast": [{
                "actor_name": "Actor 1",
                "character_name": "Character 1",
                "physical_description": "Description",
                "personality_traits": ["trait"],
                "acting_style": "Style",
                "role_description": "Role"
            }],
            "runtime": "120 min",
            "rating": "PG-13",
            "release_year": 2026,
            "production_company": "Company",
            "production_company_background": "Background",
            "budget": "$100M",
            "themes": ["theme1"],
            "visual_style": "Style",
            "target_audience": "Everyone"
        }

        response = MovieGenerationResponse(
            success=True,
            movie=GeneratedMovie(**movie_data),
            input_movies_found=2,
            input_movies_data=[{"Title": "Movie1"}, {"Title": "Movie2"}],
            model_used="test-model"
        )

        assert response.success is True
        assert response.movie is not None
        assert response.input_movies_found == 2
        assert response.error is None
        assert response.model_used == "test-model"

    def test_failed_response(self):
        """Test a failed movie generation response."""
        response = MovieGenerationResponse(
            success=False,
            movie=None,
            input_movies_found=0,
            error="API key not configured",
            model_used="test-model"
        )

        assert response.success is False
        assert response.movie is None
        assert response.error == "API key not configured"

    def test_response_without_input_data(self):
        """Test response without input movie data."""
        response = MovieGenerationResponse(
            success=True,
            movie=None,
            input_movies_found=2,
            model_used="test-model"
        )

        assert response.input_movies_data is None
