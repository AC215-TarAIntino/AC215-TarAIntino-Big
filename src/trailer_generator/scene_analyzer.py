"""
Movie analyzer for extracting key information for trailer generation.
"""

from typing import Dict, List
from .schemas import GeneratedMovie, MovieAnalysis, CastMember


class MovieAnalyzer:
    """Analyzes movie data to extract key information for trailer generation."""

    def __init__(self, movie: GeneratedMovie):
        """
        Initialize the analyzer with a movie.

        Args:
            movie: GeneratedMovie object to analyze
        """
        self.movie = movie

    def analyze(self) -> MovieAnalysis:
        """
        Perform complete movie analysis.

        Returns:
            MovieAnalysis object with extracted information
        """
        return MovieAnalysis(
            main_characters=self._extract_main_characters(),
            key_themes=self._extract_key_themes(),
            visual_style_summary=self._summarize_visual_style(),
            tone=self._determine_tone(),
            hook_elements=self._identify_hooks()
        )

    def _extract_main_characters(self) -> List[Dict[str, str]]:
        """
        Extract main characters with their key information.

        Returns:
            List of character dictionaries with name and description
        """
        # Take top 3-4 cast members as they're usually the most important
        main_cast = self.movie.cast[:4]

        characters = []
        for member in main_cast:
            characters.append({
                "name": member.character_name,
                "actor": member.actor_name,
                "physical_description": member.physical_description,
                "role": member.role_description,
                "traits": ", ".join(member.personality_traits)
            })

        return characters

    def _extract_key_themes(self) -> List[str]:
        """
        Extract key themes from the movie.

        Returns:
            List of key themes
        """
        # Use the movie's themes directly, but limit to most important ones
        return self.movie.themes[:4]

    def _summarize_visual_style(self) -> str:
        """
        Create a concise summary of the visual style.

        Returns:
            Visual style summary string
        """
        return self.movie.visual_style

    def _determine_tone(self) -> str:
        """
        Determine the overall tone based on genres and themes.

        Returns:
            Tone description
        """
        # Analyze genres to infer tone
        genres = [g.lower() for g in self.movie.genres]

        # Map genres to tone descriptors
        tone_indicators = []

        if any(g in genres for g in ["thriller", "horror", "mystery"]):
            tone_indicators.append("tense and suspenseful")
        if any(g in genres for g in ["action", "adventure"]):
            tone_indicators.append("high-energy and exciting")
        if "drama" in genres:
            tone_indicators.append("emotionally gripping")
        if any(g in genres for g in ["sci-fi", "fantasy"]):
            tone_indicators.append("visually spectacular")
        if "comedy" in genres:
            tone_indicators.append("humorous and entertaining")
        if any(g in genres for g in ["romance", "family"]):
            tone_indicators.append("heartwarming")
        if any(g in genres for g in ["war", "crime"]):
            tone_indicators.append("gritty and intense")

        # If we couldn't determine tone from genres, use a generic description
        if not tone_indicators:
            tone_indicators.append("compelling and atmospheric")

        # Combine tone indicators
        if len(tone_indicators) == 1:
            return tone_indicators[0]
        elif len(tone_indicators) == 2:
            return f"{tone_indicators[0]} and {tone_indicators[1]}"
        else:
            return f"{', '.join(tone_indicators[:-1])}, and {tone_indicators[-1]}"

    def _identify_hooks(self) -> List[str]:
        """
        Identify compelling hook elements for the trailer.

        Returns:
            List of hook elements
        """
        hooks = []

        # Add the unique selling point as the primary hook
        if self.movie.unique_selling_point:
            hooks.append(self.movie.unique_selling_point)

        # Add tagline as a hook
        hooks.append(f"Tagline: {self.movie.tagline}")

        # Extract compelling elements from plot summary
        # (First and last sentences often contain hooks)
        plot_sentences = self.movie.plot_summary.split(". ")
        if len(plot_sentences) >= 2:
            hooks.append(f"Opening hook: {plot_sentences[0]}")
            hooks.append(f"Stakes: {plot_sentences[-1]}")

        # Add genre appeal
        hooks.append(f"Genre appeal: {', '.join(self.movie.genres)}")

        return hooks

    def get_character_consistency_guide(self) -> str:
        """
        Generate a detailed guide for maintaining character consistency.

        Returns:
            Detailed character consistency guide
        """
        guide_parts = [
            f"CHARACTER CONSISTENCY GUIDE FOR '{self.movie.title}' TRAILER\n",
            "=" * 70,
            "\nIMPORTANT: To maintain character consistency across scenes, each character",
            "should appear in ONE CONTINUOUS scene. Use the following descriptions:\n"
        ]

        for i, member in enumerate(self.movie.cast[:4], 1):
            guide_parts.extend([
                f"\n{i}. {member.character_name} (played by {member.actor_name})",
                "-" * 60,
                f"Physical: {member.physical_description}",
                f"Role: {member.role_description}",
                f"Traits: {', '.join(member.personality_traits)}\n"
            ])

        guide_parts.extend([
            "\nVISUAL STYLE:",
            "-" * 60,
            self.movie.visual_style,
            "\n\nWhen a character appears multiple times, ensure they are in a SINGLE",
            "CONTINUOUS scene that can be generated with VEO 3.1 as one video sequence.",
            "The end frame of that scene becomes the start frame of the next scene."
        ])

        return "\n".join(guide_parts)

    def format_for_llm_context(self) -> str:
        """
        Format movie information for LLM context.

        Returns:
            Formatted string with all relevant movie information
        """
        analysis = self.analyze()

        context_parts = [
            f"MOVIE: {self.movie.title}",
            f"TAGLINE: {self.movie.tagline}",
            f"GENRES: {', '.join(self.movie.genres)}",
            f"RATING: {self.movie.rating}",
            f"RUNTIME: {self.movie.runtime}",
            "\n--- PLOT SUMMARY ---",
            self.movie.plot_summary,
            "\n--- MAIN CHARACTERS ---"
        ]

        for char in analysis.main_characters:
            context_parts.extend([
                f"\nCharacter: {char['name']}",
                f"Physical: {char['physical_description']}",
                f"Role: {char['role']}",
                f"Traits: {char['traits']}"
            ])

        context_parts.extend([
            "\n--- VISUAL STYLE ---",
            self.movie.visual_style,
            "\n--- THEMES ---",
            ", ".join(self.movie.themes),
            "\n--- TONE ---",
            analysis.tone,
            "\n--- DIRECTOR ---",
            f"{self.movie.director_name}: {self.movie.director_background}"
        ])

        return "\n".join(context_parts)
