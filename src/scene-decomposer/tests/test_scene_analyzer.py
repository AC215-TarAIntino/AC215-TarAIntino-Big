"""
Comprehensive tests for scene_analyzer.py - MovieAnalyzer class.
"""

import sys
from pathlib import Path
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trailer_generator.scene_analyzer import MovieAnalyzer
from trailer_generator.schemas import GeneratedMovie, CastMember, MovieAnalysis


@pytest.fixture
def sample_cast():
    """Create sample cast members for testing."""
    return [
        CastMember(
            actor_name="Emma Stone",
            character_name="Dr. Sarah Chen",
            physical_description="A woman in her early 30s with short auburn hair and green eyes, athletic build",
            personality_traits=["intelligent", "determined", "cautious"],
            acting_style="naturalistic",
            role_description="Brilliant scientist who discovers an anomaly"
        ),
        CastMember(
            actor_name="Oscar Isaac",
            character_name="Marcus Vale",
            physical_description="A man in his 40s with dark hair and brown eyes, rugged appearance",
            personality_traits=["brave", "impulsive", "loyal"],
            acting_style="intense",
            role_description="Former military officer turned security consultant"
        ),
        CastMember(
            actor_name="Tilda Swinton",
            character_name="Dr. Helena Pierce",
            physical_description="A woman in her 50s with silver hair and piercing blue eyes",
            personality_traits=["mysterious", "calculating", "wise"],
            acting_style="ethereal",
            role_description="Senior researcher with hidden agenda"
        ),
        CastMember(
            actor_name="John Boyega",
            character_name="Alex Turner",
            physical_description="A man in his late 20s with short black hair",
            personality_traits=["optimistic", "tech-savvy", "energetic"],
            acting_style="dynamic",
            role_description="Young programmer caught in the conspiracy"
        ),
    ]


@pytest.fixture
def sample_movie(sample_cast):
    """Create a sample movie for testing."""
    return GeneratedMovie(
        title="The Quantum Paradox",
        tagline="Reality is just the beginning",
        genres=["Sci-Fi", "Thriller", "Mystery"],
        plot_summary="When a brilliant physicist discovers a way to observe quantum phenomena at the macro scale, she unwittingly opens a door to parallel realities. As alternate versions of herself begin to bleed through, she must race against time to close the rift before all of reality collapses. But the deeper she goes, the more she questions which version of herself is real.",
        director_name="Denis Villeneuve",
        director_background="Acclaimed director known for cerebral science fiction",
        writers=["Charlie Kaufman", "Emma Thomas"],
        writer_backgrounds="Known for complex, mind-bending narratives",
        cast=sample_cast,
        runtime="142 minutes",
        rating="PG-13",
        release_year=2024,
        production_company="A24 Films",
        production_company_background="Independent studio known for auteur-driven films",
        budget="$85 million",
        themes=["identity", "reality", "quantum physics", "existentialism"],
        visual_style="Sleek and minimalist with desaturated colors, emphasizing blues and grays. Sterile laboratory environments contrast with chaotic parallel realities.",
        target_audience="Adults 25-45 who enjoy intellectual sci-fi",
        unique_selling_point="A mind-bending exploration of quantum mechanics meets personal identity crisis",
        inspiration_source=["Primer", "Arrival", "Coherence"],
        similar_movies=["Interstellar", "Inception", "Annihilation"]
    )


class TestMovieAnalyzer:
    """Tests for the MovieAnalyzer class."""

    def test_initialization(self, sample_movie):
        """Test that MovieAnalyzer initializes correctly."""
        analyzer = MovieAnalyzer(sample_movie)
        assert analyzer.movie == sample_movie

    def test_analyze_returns_movie_analysis(self, sample_movie):
        """Test that analyze() returns a MovieAnalysis object."""
        analyzer = MovieAnalyzer(sample_movie)
        analysis = analyzer.analyze()

        assert isinstance(analysis, MovieAnalysis)
        assert hasattr(analysis, "main_characters")
        assert hasattr(analysis, "key_themes")
        assert hasattr(analysis, "visual_style_summary")
        assert hasattr(analysis, "tone")
        assert hasattr(analysis, "hook_elements")

    def test_extract_main_characters(self, sample_movie):
        """Test that main characters are extracted correctly."""
        analyzer = MovieAnalyzer(sample_movie)
        characters = analyzer._extract_main_characters()

        # Should return top 4 cast members
        assert len(characters) == 4
        assert characters[0]["name"] == "Dr. Sarah Chen"
        assert characters[0]["actor"] == "Emma Stone"
        assert "auburn hair" in characters[0]["physical_description"]
        assert "scientist" in characters[0]["role"].lower()
        assert "intelligent, determined, cautious" in characters[0]["traits"]

    def test_extract_main_characters_fewer_than_four(self):
        """Test extraction when movie has fewer than 4 cast members."""
        small_cast = [
            CastMember(
                actor_name="Actor One",
                character_name="Character One",
                physical_description="Description one",
                personality_traits=["trait1"],
                acting_style="style1",
                role_description="role1"
            ),
            CastMember(
                actor_name="Actor Two",
                character_name="Character Two",
                physical_description="Description two",
                personality_traits=["trait2"],
                acting_style="style2",
                role_description="role2"
            )
        ]

        movie = GeneratedMovie(
            title="Small Cast Movie",
            tagline="test",
            genres=["Drama"],
            plot_summary="test plot",
            director_name="test director",
            director_background="test",
            writers=["writer"],
            writer_backgrounds="test",
            cast=small_cast,
            runtime="90 minutes",
            rating="PG",
            release_year=2024,
            production_company="test",
            production_company_background="test",
            budget="$1M",
            themes=["test"],
            visual_style="test style",
            target_audience="test"
        )

        analyzer = MovieAnalyzer(movie)
        characters = analyzer._extract_main_characters()

        assert len(characters) == 2

    def test_extract_key_themes(self, sample_movie):
        """Test that key themes are extracted correctly."""
        analyzer = MovieAnalyzer(sample_movie)
        themes = analyzer._extract_key_themes()

        # Should return top 4 themes
        assert len(themes) == 4
        assert "identity" in themes
        assert "reality" in themes
        assert "quantum physics" in themes
        assert "existentialism" in themes

    def test_extract_key_themes_fewer_than_four(self, sample_movie):
        """Test theme extraction when movie has fewer than 4 themes."""
        movie_data = sample_movie.model_dump()
        movie_data["themes"] = ["survival", "hope"]
        movie = GeneratedMovie(**movie_data)

        analyzer = MovieAnalyzer(movie)
        themes = analyzer._extract_key_themes()

        assert len(themes) == 2
        assert "survival" in themes
        assert "hope" in themes

    def test_summarize_visual_style(self, sample_movie):
        """Test that visual style is summarized correctly."""
        analyzer = MovieAnalyzer(sample_movie)
        visual_style = analyzer._summarize_visual_style()

        assert visual_style == sample_movie.visual_style
        assert "minimalist" in visual_style.lower()
        assert "blue" in visual_style.lower()

    def test_determine_tone_thriller(self, sample_movie):
        """Test tone determination for thriller genre."""
        analyzer = MovieAnalyzer(sample_movie)
        tone = analyzer._determine_tone()

        # Movie has Thriller and Mystery genres
        assert "tense" in tone.lower() or "suspenseful" in tone.lower()

    def test_determine_tone_action(self):
        """Test tone determination for action genre."""
        movie_data = {
            "title": "Action Movie",
            "tagline": "test",
            "genres": ["Action", "Adventure"],
            "plot_summary": "test",
            "director_name": "test",
            "director_background": "test",
            "writers": ["test"],
            "writer_backgrounds": "test",
            "cast": [],
            "runtime": "90 min",
            "rating": "PG-13",
            "release_year": 2024,
            "production_company": "test",
            "production_company_background": "test",
            "budget": "$1M",
            "themes": ["test"],
            "visual_style": "test",
            "target_audience": "test"
        }
        movie = GeneratedMovie(**movie_data)
        analyzer = MovieAnalyzer(movie)
        tone = analyzer._determine_tone()

        assert "high-energy" in tone.lower() or "exciting" in tone.lower()

    def test_determine_tone_drama(self):
        """Test tone determination for drama genre."""
        movie_data = {
            "title": "Drama Movie",
            "tagline": "test",
            "genres": ["Drama"],
            "plot_summary": "test",
            "director_name": "test",
            "director_background": "test",
            "writers": ["test"],
            "writer_backgrounds": "test",
            "cast": [],
            "runtime": "90 min",
            "rating": "PG-13",
            "release_year": 2024,
            "production_company": "test",
            "production_company_background": "test",
            "budget": "$1M",
            "themes": ["test"],
            "visual_style": "test",
            "target_audience": "test"
        }
        movie = GeneratedMovie(**movie_data)
        analyzer = MovieAnalyzer(movie)
        tone = analyzer._determine_tone()

        assert "emotionally gripping" in tone.lower()

    def test_determine_tone_sci_fi(self, sample_movie):
        """Test tone determination for sci-fi genre."""
        analyzer = MovieAnalyzer(sample_movie)
        tone = analyzer._determine_tone()

        # Sample movie has Sci-Fi genre
        assert "visually spectacular" in tone.lower()

    def test_determine_tone_comedy(self):
        """Test tone determination for comedy genre."""
        movie_data = {
            "title": "Comedy Movie",
            "tagline": "test",
            "genres": ["Comedy"],
            "plot_summary": "test",
            "director_name": "test",
            "director_background": "test",
            "writers": ["test"],
            "writer_backgrounds": "test",
            "cast": [],
            "runtime": "90 min",
            "rating": "PG-13",
            "release_year": 2024,
            "production_company": "test",
            "production_company_background": "test",
            "budget": "$1M",
            "themes": ["test"],
            "visual_style": "test",
            "target_audience": "test"
        }
        movie = GeneratedMovie(**movie_data)
        analyzer = MovieAnalyzer(movie)
        tone = analyzer._determine_tone()

        assert "humorous" in tone.lower() or "entertaining" in tone.lower()

    def test_determine_tone_horror(self):
        """Test tone determination for horror genre."""
        movie_data = {
            "title": "Horror Movie",
            "tagline": "test",
            "genres": ["Horror"],
            "plot_summary": "test",
            "director_name": "test",
            "director_background": "test",
            "writers": ["test"],
            "writer_backgrounds": "test",
            "cast": [],
            "runtime": "90 min",
            "rating": "R",
            "release_year": 2024,
            "production_company": "test",
            "production_company_background": "test",
            "budget": "$1M",
            "themes": ["test"],
            "visual_style": "test",
            "target_audience": "test"
        }
        movie = GeneratedMovie(**movie_data)
        analyzer = MovieAnalyzer(movie)
        tone = analyzer._determine_tone()

        assert "tense" in tone.lower() or "suspenseful" in tone.lower()

    def test_determine_tone_romance(self):
        """Test tone determination for romance genre."""
        movie_data = {
            "title": "Romance Movie",
            "tagline": "test",
            "genres": ["Romance"],
            "plot_summary": "test",
            "director_name": "test",
            "director_background": "test",
            "writers": ["test"],
            "writer_backgrounds": "test",
            "cast": [],
            "runtime": "90 min",
            "rating": "PG-13",
            "release_year": 2024,
            "production_company": "test",
            "production_company_background": "test",
            "budget": "$1M",
            "themes": ["test"],
            "visual_style": "test",
            "target_audience": "test"
        }
        movie = GeneratedMovie(**movie_data)
        analyzer = MovieAnalyzer(movie)
        tone = analyzer._determine_tone()

        assert "heartwarming" in tone.lower()

    def test_determine_tone_crime(self):
        """Test tone determination for crime genre."""
        movie_data = {
            "title": "Crime Movie",
            "tagline": "test",
            "genres": ["Crime"],
            "plot_summary": "test",
            "director_name": "test",
            "director_background": "test",
            "writers": ["test"],
            "writer_backgrounds": "test",
            "cast": [],
            "runtime": "90 min",
            "rating": "R",
            "release_year": 2024,
            "production_company": "test",
            "production_company_background": "test",
            "budget": "$1M",
            "themes": ["test"],
            "visual_style": "test",
            "target_audience": "test"
        }
        movie = GeneratedMovie(**movie_data)
        analyzer = MovieAnalyzer(movie)
        tone = analyzer._determine_tone()

        assert "gritty" in tone.lower() or "intense" in tone.lower()

    def test_determine_tone_unknown_genre(self):
        """Test tone determination for unknown genre."""
        movie_data = {
            "title": "Unknown Movie",
            "tagline": "test",
            "genres": ["UnknownGenre"],
            "plot_summary": "test",
            "director_name": "test",
            "director_background": "test",
            "writers": ["test"],
            "writer_backgrounds": "test",
            "cast": [],
            "runtime": "90 min",
            "rating": "PG-13",
            "release_year": 2024,
            "production_company": "test",
            "production_company_background": "test",
            "budget": "$1M",
            "themes": ["test"],
            "visual_style": "test",
            "target_audience": "test"
        }
        movie = GeneratedMovie(**movie_data)
        analyzer = MovieAnalyzer(movie)
        tone = analyzer._determine_tone()

        # Should return generic description
        assert "compelling" in tone.lower() or "atmospheric" in tone.lower()

    def test_identify_hooks(self, sample_movie):
        """Test that hook elements are identified correctly."""
        analyzer = MovieAnalyzer(sample_movie)
        hooks = analyzer._identify_hooks()

        assert len(hooks) > 0
        # Should include unique selling point
        assert any("mind-bending" in hook.lower() for hook in hooks)
        # Should include tagline
        assert any("Reality is just the beginning" in hook for hook in hooks)
        # Should include genre appeal
        assert any("Sci-Fi" in hook for hook in hooks)

    def test_identify_hooks_without_usp(self, sample_movie):
        """Test hook identification when unique_selling_point is None."""
        movie_data = sample_movie.model_dump()
        movie_data["unique_selling_point"] = None
        movie = GeneratedMovie(**movie_data)

        analyzer = MovieAnalyzer(movie)
        hooks = analyzer._identify_hooks()

        # Should still have hooks from other sources
        assert len(hooks) > 0
        assert any("tagline" in hook.lower() for hook in hooks)

    def test_get_character_consistency_guide(self, sample_movie):
        """Test character consistency guide generation."""
        analyzer = MovieAnalyzer(sample_movie)
        guide = analyzer.get_character_consistency_guide()

        assert "CHARACTER CONSISTENCY GUIDE" in guide
        assert sample_movie.title in guide
        assert "Dr. Sarah Chen" in guide
        assert "Emma Stone" in guide
        assert "auburn hair" in guide
        assert sample_movie.visual_style in guide

    def test_format_for_llm_context(self, sample_movie):
        """Test LLM context formatting."""
        analyzer = MovieAnalyzer(sample_movie)
        context = analyzer.format_for_llm_context()

        # Check all major sections are present
        assert sample_movie.title in context
        assert sample_movie.tagline in context
        assert "PLOT SUMMARY" in context
        assert "MAIN CHARACTERS" in context
        assert "VISUAL STYLE" in context
        assert "THEMES" in context
        assert "TONE" in context
        assert "DIRECTOR" in context

        # Check character details
        assert "Dr. Sarah Chen" in context
        assert "auburn hair" in context

    def test_format_character_designs_for_llm(self, sample_movie):
        """Test character designs formatting for LLM."""
        analyzer = MovieAnalyzer(sample_movie)
        designs = analyzer.format_character_designs_for_llm()

        assert "CHARACTER DESIGNS TO GENERATE" in designs
        assert "character_name" in designs
        assert "image_generation_prompt" in designs
        assert "brief_identifier" in designs
        assert "visual_style" in designs

        # Check all 4 main characters are included
        assert "Dr. Sarah Chen" in designs
        assert "Marcus Vale" in designs
        assert "Dr. Helena Pierce" in designs
        assert "Alex Turner" in designs

        # Check their descriptions
        assert "auburn hair" in designs
        assert "dark hair" in designs

    def test_analyze_complete_workflow(self, sample_movie):
        """Test the complete analysis workflow."""
        analyzer = MovieAnalyzer(sample_movie)
        analysis = analyzer.analyze()

        # Verify all fields are populated
        assert len(analysis.main_characters) == 4
        assert len(analysis.key_themes) == 4
        assert analysis.visual_style_summary
        assert analysis.tone
        assert len(analysis.hook_elements) > 0

        # Verify content quality
        assert analysis.main_characters[0]["name"] == "Dr. Sarah Chen"
        assert "identity" in analysis.key_themes
        assert "Sleek" in analysis.visual_style_summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
