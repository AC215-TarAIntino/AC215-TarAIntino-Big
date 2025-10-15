"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { GradientBackground } from "@/components/effects/GradientBackground";
import { VideoPlayer } from "@/components/result/VideoPlayer";
import { TasteProfile } from "@/components/result/TasteProfile";
import { Download, RotateCcw, Share2, Sparkles } from "lucide-react";
import JSConfetti from "js-confetti";

interface SwipeHistory {
  direction: string;
  movie: {
    poster: string;
    tags: string[];
  };
}

export default function ResultPage() {
  const router = useRouter();
  const [generatedTitle, setGeneratedTitle] = useState("");
  const [posterUrl, setPosterUrl] = useState("");
  const [tasteProfile, setTasteProfile] = useState<{ name: string; score: number }[]>([]);

  useEffect(() => {
    // Trigger confetti on load
    const jsConfetti = new JSConfetti();

    setTimeout(() => {
      jsConfetti.addConfetti({
        confettiColors: ["#ffd700", "#ff00ff", "#00ffff", "#667eea", "#f093fb"],
        confettiRadius: 6,
        confettiNumber: 500,
      });
    }, 300);

    // Additional confetti bursts
    setTimeout(() => {
      jsConfetti.addConfetti({
        emojis: ["🎬", "🎥", "⭐", "✨", "🎭"],
        emojiSize: 40,
        confettiNumber: 30,
      });
    }, 1000);

    // Load quiz results from sessionStorage
    const results = sessionStorage.getItem("quizResults");
    if (results) {
      const swipeHistory = JSON.parse(results);

      // Generate mock title based on preferences
      const titles = [
        "Neon Shadows",
        "The Crimson Odyssey",
        "Echoes of Tomorrow",
        "Midnight Reverie",
        "The Last Symphony",
        "Fractured Dreams",
        "Velocity Noir",
        "The Golden Paradox",
      ];

      const randomTitle = titles[Math.floor(Math.random() * titles.length)];
      setGeneratedTitle(randomTitle);

      // Use the first liked/loved movie's poster
      const likedMovie = swipeHistory.find(
        (s: SwipeHistory) => s.direction === "right" || s.direction === "up"
      );
      if (likedMovie) {
        setPosterUrl(likedMovie.movie.poster);
      } else {
        // Fallback poster
        setPosterUrl("https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400&h=600&fit=crop");
      }

      // Calculate taste profile
      const tagScores: { [key: string]: number } = {};
      swipeHistory.forEach((swipe: SwipeHistory) => {
        const weight =
          swipe.direction === "up" ? 2 : swipe.direction === "right" ? 1 : 0;

        if (weight > 0) {
          swipe.movie.tags.forEach((tag: string) => {
            tagScores[tag] = (tagScores[tag] || 0) + weight;
          });
        }
      });

      // Normalize scores
      const maxScore = Math.max(...Object.values(tagScores));
      const profile = Object.entries(tagScores).map(([name, score]) => ({
        name,
        score: score / maxScore,
      }));

      setTasteProfile(profile);
    }
  }, []);

  const handleDownload = () => {
    // Trigger another confetti burst
    const jsConfetti = new JSConfetti();
    jsConfetti.addConfetti({
      confettiColors: ["#ffd700", "#ff00ff", "#00ffff"],
      confettiRadius: 8,
      confettiNumber: 300,
    });

    // Mock download
    setTimeout(() => {
      alert(`🎬 Your trailer "${generatedTitle}" is downloading!\n\n(This is a mock demo - no actual video file)`);
    }, 500);
  };

  const handleCreateAnother = () => {
    sessionStorage.removeItem("quizResults");
    router.push("/");
  };

  return (
    <main className="min-h-screen relative overflow-hidden">
      <GradientBackground />

      <div className="relative z-10 min-h-screen py-12 px-6">
        <div className="max-w-5xl mx-auto space-y-8">
          {/* Success Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="text-center space-y-4"
          >
            <motion.div
              animate={{
                scale: [1, 1.2, 1],
                rotate: [0, 10, -10, 0],
              }}
              transition={{
                duration: 0.6,
                delay: 0.3,
              }}
              className="inline-block text-7xl mb-4"
            >
              🎬
            </motion.div>

            <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">
              Your AI Trailer is Ready!
            </h1>

            <p className="text-xl text-white/70">
              Generated based on your unique cinematic taste
            </p>
          </motion.div>

          {/* Video Player */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7 }}
          >
            <VideoPlayer posterUrl={posterUrl} title={generatedTitle} />
          </motion.div>

          {/* Movie Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="glass-strong rounded-2xl p-8 space-y-4"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h2 className="text-3xl font-bold text-gradient-gold mb-2">
                  {generatedTitle}
                </h2>
                <p className="text-white/70 text-lg">
                  A TarAIntino Original • 2025 • AI Generated
                </p>
              </div>

              <motion.div
                animate={{
                  rotate: [0, 360],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "linear",
                }}
              >
                <Sparkles className="w-8 h-8 text-gold" />
              </motion.div>
            </div>

            <p className="text-white/80 leading-relaxed">
              An AI-generated cinematic experience crafted from your unique preferences.
              This trailer combines elements of your favorite genres, moods, and styles
              into a personalized visual story.
            </p>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/10">
              <div className="text-center">
                <div className="text-2xl font-bold text-gold">2:00</div>
                <div className="text-sm text-white/60">Duration</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-neon-magenta">4K</div>
                <div className="text-sm text-white/60">Quality</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-neon-cyan">AI</div>
                <div className="text-sm text-white/60">Generated</div>
              </div>
            </div>
          </motion.div>

          {/* Taste Profile */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.1 }}
          >
            <TasteProfile tags={tasteProfile} />
          </motion.div>

          {/* Action Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.3 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            {/* Download Button - Primary CTA */}
            <motion.button
              onClick={handleDownload}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="relative group overflow-hidden px-8 py-4 rounded-2xl font-bold text-lg text-black bg-gradient-to-r from-gold via-gold-dark to-gold flex items-center justify-center gap-3 shadow-lg"
            >
              {/* Animated shine effect */}
              <motion.div
                animate={{
                  x: [-200, 200],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "linear",
                }}
                className="absolute inset-0 w-32 bg-gradient-to-r from-transparent via-white/40 to-transparent"
              />

              <Download className="w-6 h-6 relative z-10" />
              <span className="relative z-10">Download Your Trailer</span>
            </motion.button>

            {/* Share Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-8 py-4 rounded-2xl font-medium text-white glass-strong flex items-center justify-center gap-3 hover:border-white/30 transition-colors"
            >
              <Share2 className="w-5 h-5" />
              <span>Share</span>
            </motion.button>

            {/* Create Another */}
            <motion.button
              onClick={handleCreateAnother}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-8 py-4 rounded-2xl font-medium text-white glass-strong flex items-center justify-center gap-3 hover:border-neon-cyan/50 transition-colors"
            >
              <RotateCcw className="w-5 h-5" />
              <span>Create Another Masterpiece</span>
            </motion.button>
          </motion.div>

          {/* Footer Note */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
            className="text-center text-white/40 text-sm"
          >
            <p>
              ✨ This is a demo showcasing the TarAIntino UI/UX concept
            </p>
          </motion.div>
        </div>
      </div>
    </main>
  );
}
