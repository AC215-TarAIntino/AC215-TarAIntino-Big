"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { GradientBackground } from "@/components/effects/GradientBackground";
import { TasteProfile } from "@/components/result/TasteProfile";
import { Download, RotateCcw, Share2, Sparkles } from "lucide-react";
import JSConfetti from "js-confetti";

interface TagRating {
  tag: string;
  rating: number;
}

export default function ResultPage() {
  const router = useRouter();
  const [generatedTitle, setGeneratedTitle] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [gcsUrl, setGcsUrl] = useState("");
  const [tasteProfile, setTasteProfile] = useState<{ name: string; score: number }[]>([]);
  const [error, setError] = useState<string | null>(null);

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

    setTimeout(() => {
      jsConfetti.addConfetti({
        emojis: ["🎬", "🎥", "⭐", "✨", "🎭"],
        emojiSize: 40,
        confettiNumber: 30,
      });
    }, 1000);

    // Load REAL video URL from sessionStorage
    const storedVideoUrl = sessionStorage.getItem("videoUrl");
    const storedGcsUrl = sessionStorage.getItem("gcsUrl");
    const movieTitle = sessionStorage.getItem("movieTitle");

    console.log("🎬 Result Page - SessionStorage Debug:");
    console.log("  videoUrl:", storedVideoUrl);
    console.log("  gcsUrl:", storedGcsUrl);
    console.log("  movieTitle:", movieTitle);

    if (!storedVideoUrl) {
      console.error("❌ No video URL found in sessionStorage");
      setError("Video URL not found. Please generate a new trailer.");
    } else {
      console.log("✅ Setting video URL:", storedVideoUrl.substring(0, 100) + "...");
      setVideoUrl(storedVideoUrl);
      setGcsUrl(storedGcsUrl || "");
    }

    // Set movie title
    if (movieTitle) {
      setGeneratedTitle(movieTitle);
    } else {
      // Fallback to mock title if not available
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
      setGeneratedTitle(titles[Math.floor(Math.random() * titles.length)]);
    }

    // Load quiz results for taste profile
    const results = sessionStorage.getItem("quizResults");
    if (results) {
      const tagRatings: TagRating[] = JSON.parse(results);

      // Calculate taste profile
      const maxScore = 10;
      const profile = tagRatings.map((rating) => ({
        name: rating.tag,
        score: rating.rating / maxScore,
      }));
      profile.sort((a, b) => b.score - a.score);
      setTasteProfile(profile);
    }
  }, []);

  const handleDownload = () => {
    // Trigger confetti
    const jsConfetti = new JSConfetti();
    jsConfetti.addConfetti({
      confettiColors: ["#ffd700", "#ff00ff", "#00ffff"],
      confettiRadius: 8,
      confettiNumber: 300,
    });

    // Download the actual video
    if (videoUrl) {
      const link = document.createElement("a");
      link.href = videoUrl;
      link.download = `${generatedTitle}.mp4`;
      link.target = "_blank"; // Open in new tab if download fails
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      alert("Video not available for download");
    }
  };

  const handleCreateAnother = () => {
    sessionStorage.clear();
    router.push("/");
  };

  // Error state
  if (error) {
    return (
      <main className="min-h-screen relative overflow-hidden flex items-center justify-center">
        <GradientBackground />
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md p-8 glass-strong rounded-2xl"
        >
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-white mb-2">Error</h2>
          <p className="text-white/70 mb-6">{error}</p>
          <button
            onClick={handleCreateAnother}
            className="glass-strong px-6 py-3 rounded-xl text-white font-semibold hover:scale-105 active:scale-95 transition-all"
          >
            Create New Trailer
          </button>
        </motion.div>
      </main>
    );
  }

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

          {/* Real Video Player */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7 }}
          >
            <div className="relative w-full aspect-video rounded-2xl overflow-hidden glass-strong">
              {videoUrl ? (
                <video
                  controls
                  autoPlay
                  className="w-full h-full object-contain bg-black"
                  src={videoUrl}
                  onError={(e) => {
                    console.error("❌ Video failed to load:", e);
                    console.error("   Video URL:", videoUrl);
                    console.error("   Error details:", (e.target as HTMLVideoElement).error);
                  }}
                  onLoadedMetadata={() => {
                    console.log("✅ Video metadata loaded successfully!");
                  }}
                  onCanPlay={() => {
                    console.log("✅ Video can play!");
                  }}
                >
                  <source src={videoUrl} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-black">
                  <p className="text-white/50">Loading video...</p>
                </div>
              )}
            </div>
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
                {gcsUrl && (
                  <p className="text-white/40 text-xs mt-2 font-mono">
                    {gcsUrl}
                  </p>
                )}
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
              An AI-generated cinematic experience crafted from your tag preferences.
              This trailer combines your favorite genres, moods, and storytelling elements
              into a personalized visual masterpiece.
            </p>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/10">
              <div className="text-center">
                <div className="text-2xl font-bold text-gold">~35s</div>
                <div className="text-sm text-white/60">Duration</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-neon-magenta">HD</div>
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
              ✨ Powered by AI • Generated using Google VEO & Gemini
            </p>
          </motion.div>
        </div>
      </div>
    </main>
  );
}
