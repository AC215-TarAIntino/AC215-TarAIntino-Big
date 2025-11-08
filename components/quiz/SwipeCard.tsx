"use client";

import { motion, AnimatePresence } from "framer-motion";
import { formatTagForDisplay } from "@/lib/data/tags";
import { useState, useEffect } from "react";
import { Minus, Plus, ChevronRight, Sparkles } from "lucide-react";

interface SwipeCardProps {
  tag: string;
  onRating: (rating: number) => void;
  style?: React.CSSProperties;
  index: number;
}

export function SwipeCard({ tag, onRating, style, index }: SwipeCardProps) {
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // Detect mobile viewport
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const handleRatingSelect = (rating: number) => {
    setSelectedRating(rating);
  };

  const handleStepperChange = (delta: number) => {
    const newRating = Math.max(0, Math.min(10, (selectedRating ?? 5) + delta));
    setSelectedRating(newRating);
  };

  const handleNext = () => {
    if (selectedRating !== null) {
      onRating(selectedRating);
    }
  };

  // Get color based on rating (0=cool blue, 10=hot magenta)
  const getRatingColor = (rating: number) => {
    const colors = [
      "#3b82f6", // 0 - blue-500
      "#60a5fa", // 1 - blue-400
      "#6366f1", // 2 - indigo-500
      "#8b5cf6", // 3 - violet-500
      "#a855f7", // 4 - purple-500
      "#c026d3", // 5 - fuchsia-600
      "#d946ef", // 6 - fuchsia-500
      "#e879f9", // 7 - fuchsia-400
      "#f0abfc", // 8 - fuchsia-300
      "#f9a8d4", // 9 - pink-300
      "#ec4899", // 10 - pink-500
    ];
    return colors[rating];
  };

  const getRatingGradient = (rating: number) => {
    if (rating <= 3) return "from-blue-500 to-indigo-500";
    if (rating <= 6) return "from-purple-500 to-fuchsia-500";
    return "from-fuchsia-500 to-pink-500";
  };

  const formattedTag = formatTagForDisplay(tag);

  return (
    <motion.div
      style={style}
      className="absolute w-full h-full"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
    >
      <div className="relative w-full h-full rounded-3xl overflow-hidden glass-strong grain shadow-2xl flex flex-col">
        {/* Animated gradient background based on rating */}
        <AnimatePresence mode="wait">
          {selectedRating !== null && (
            <motion.div
              key={selectedRating}
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.15 }}
              exit={{ opacity: 0 }}
              className={`absolute inset-0 bg-gradient-to-br ${getRatingGradient(selectedRating)}`}
            />
          )}
        </AnimatePresence>

        {/* Content */}
        <div className="relative z-10 flex flex-col h-full p-8">
          {/* Tag Display */}
          <div className="flex-1 flex flex-col items-center justify-center text-center space-y-6">
            {/* Decorative icon */}
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: "spring", delay: 0.2 }}
            >
              <Sparkles className="w-12 h-12 text-gradient-gold" />
            </motion.div>

            {/* Tag name */}
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-4xl sm:text-5xl md:text-6xl font-bold text-white drop-shadow-lg px-4"
            >
              {formattedTag}
            </motion.h2>

            {/* Rating prompt */}
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-white/70 text-base sm:text-lg max-w-md"
            >
              How important is this in your movies?
            </motion.p>

            {/* Selected rating display */}
            <AnimatePresence mode="wait">
              {selectedRating !== null && (
                <motion.div
                  key={selectedRating}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  className="flex items-center gap-3"
                >
                  <div
                    className="w-20 h-20 rounded-full flex items-center justify-center text-3xl font-bold text-white shadow-xl"
                    style={{
                      background: `linear-gradient(135deg, ${getRatingColor(selectedRating)}, ${getRatingColor(Math.min(10, selectedRating + 1))})`,
                    }}
                  >
                    {selectedRating}
                  </div>
                  <div className="text-left">
                    <p className="text-white font-semibold text-lg">
                      {selectedRating === 0 && "Not at all"}
                      {selectedRating >= 1 && selectedRating <= 3 && "Slightly"}
                      {selectedRating >= 4 && selectedRating <= 6 && "Moderately"}
                      {selectedRating >= 7 && selectedRating <= 9 && "Very important"}
                      {selectedRating === 10 && "Essential!"}
                    </p>
                    <p className="text-white/50 text-sm">Rating: {selectedRating}/10</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Rating Input */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="space-y-4"
          >
            {isMobile ? (
              // Mobile: Stepper UI
              <div className="flex items-center justify-center gap-4">
                <button
                  onClick={() => handleStepperChange(-1)}
                  disabled={selectedRating === 0}
                  className="glass-strong p-4 rounded-2xl text-white hover:scale-105 active:scale-95 transition-all disabled:opacity-30 disabled:hover:scale-100"
                >
                  <Minus className="w-6 h-6" />
                </button>

                <div className="glass-strong px-8 py-4 rounded-2xl min-w-[100px] text-center">
                  <p className="text-4xl font-bold text-white">
                    {selectedRating ?? "—"}
                  </p>
                </div>

                <button
                  onClick={() => handleStepperChange(1)}
                  disabled={selectedRating === 10}
                  className="glass-strong p-4 rounded-2xl text-white hover:scale-105 active:scale-95 transition-all disabled:opacity-30 disabled:hover:scale-100"
                >
                  <Plus className="w-6 h-6" />
                </button>
              </div>
            ) : (
              // Desktop: Number buttons grid
              <div className="grid grid-cols-11 gap-2">
                {Array.from({ length: 11 }, (_, i) => (
                  <motion.button
                    key={i}
                    onClick={() => handleRatingSelect(i)}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.6 + i * 0.03 }}
                    className={`aspect-square rounded-xl font-bold text-lg transition-all ${
                      selectedRating === i
                        ? "text-white shadow-xl scale-110"
                        : "glass-strong text-white/70 hover:text-white hover:scale-105 active:scale-95"
                    }`}
                    style={
                      selectedRating === i
                        ? {
                            background: `linear-gradient(135deg, ${getRatingColor(i)}, ${getRatingColor(Math.min(10, i + 1))})`,
                          }
                        : {}
                    }
                  >
                    {i}
                  </motion.button>
                ))}
              </div>
            )}

            {/* Scale labels */}
            <div className="flex items-center justify-between text-xs text-white/50 px-1">
              <span>Not at all</span>
              <span>Essential</span>
            </div>

            {/* Next button */}
            <motion.button
              onClick={handleNext}
              disabled={selectedRating === null}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="w-full glass-strong py-4 rounded-2xl flex items-center justify-center gap-2 text-white font-semibold text-lg hover:scale-[1.02] active:scale-98 transition-all disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              <span>Next Tag</span>
              <ChevronRight className="w-5 h-5" />
            </motion.button>
          </motion.div>
        </div>

        {/* First card hint */}
        {index === 0 && selectedRating === null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="absolute top-4 left-1/2 -translate-x-1/2 glass-strong px-4 py-2 rounded-xl pointer-events-none"
          >
            <p className="text-white/80 text-sm font-medium flex items-center gap-2">
              <span>👇</span>
              <span>Select a rating below</span>
            </p>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
