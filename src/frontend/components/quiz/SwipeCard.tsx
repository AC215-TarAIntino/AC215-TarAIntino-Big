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
  disabled?: boolean;
}

export function SwipeCard({ tag, onRating, style, index, disabled = false }: SwipeCardProps) {
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
    const newRating = Math.max(1, Math.min(10, (selectedRating ?? 5) + delta));
    setSelectedRating(newRating);
  };

  const handleNext = () => {
    if (selectedRating !== null && !disabled) {
      onRating(selectedRating);
    }
  };

  // Get color based on rating (1=cool blue, 10=hot magenta)
  const getRatingColor = (rating: number) => {
    const colors = [
      "#3b82f6", // 1 - blue-500
      "#60a5fa", // 2 - blue-400
      "#6366f1", // 3 - indigo-500
      "#8b5cf6", // 4 - violet-500
      "#a855f7", // 5 - purple-500
      "#c026d3", // 6 - fuchsia-600
      "#d946ef", // 7 - fuchsia-500
      "#e879f9", // 8 - fuchsia-400
      "#f0abfc", // 9 - fuchsia-300
      "#ec4899", // 10 - pink-500
    ];
    return colors[rating - 1] || colors[0];
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
      <div className="relative w-full h-full rounded-3xl overflow-hidden glass-strong grain shadow-2xl flex flex-col pointer-events-auto">
        {/* Animated gradient background based on rating */}
        <AnimatePresence mode="wait">
          {selectedRating !== null && (
            <motion.div
              key={selectedRating}
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.15 }}
              exit={{ opacity: 0 }}
              className={`absolute inset-0 bg-gradient-to-br ${getRatingGradient(selectedRating)} pointer-events-none`}
            />
          )}
        </AnimatePresence>

        {/* Content */}
        <div className="relative z-10 flex flex-col h-full p-4 sm:p-6 md:p-8">
          {/* Tag Display */}
          <div className="flex-1 flex flex-col items-center justify-center text-center space-y-3 sm:space-y-4">
            {/* Decorative icon */}
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: "spring", delay: 0.2 }}
            >
              <Sparkles className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 text-gradient-gold" />
            </motion.div>

            {/* Tag name */}
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white drop-shadow-lg px-4"
            >
              {formattedTag}
            </motion.h2>

            {/* Rating prompt */}
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-white/70 text-sm sm:text-base max-w-md"
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
                  className="flex items-center gap-2 sm:gap-3"
                >
                  <div
                    className="w-14 h-14 sm:w-16 sm:h-16 md:w-20 md:h-20 rounded-full flex items-center justify-center text-2xl sm:text-3xl font-bold text-white shadow-xl"
                    style={{
                      background: `linear-gradient(135deg, ${getRatingColor(selectedRating)}, ${getRatingColor(Math.min(10, selectedRating + 1))})`,
                    }}
                  >
                    {selectedRating}
                  </div>
                  <div className="text-left">
                    <p className="text-white font-semibold text-sm sm:text-base md:text-lg">
                      {selectedRating === 1 && "Not at all"}
                      {selectedRating >= 2 && selectedRating <= 3 && "Slightly"}
                      {selectedRating >= 4 && selectedRating <= 6 && "Moderately"}
                      {selectedRating >= 7 && selectedRating <= 9 && "Very important"}
                      {selectedRating === 10 && "Essential!"}
                    </p>
                    <p className="text-white/50 text-xs sm:text-sm">Rating: {selectedRating}/10</p>
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
            className="space-y-2 sm:space-y-3"
          >
            {isMobile ? (
              // Mobile: Stepper UI
              <div className="flex items-center justify-center gap-3">
                <button
                  onClick={() => handleStepperChange(-1)}
                  disabled={selectedRating === 1 || disabled}
                  className="glass-strong p-3 rounded-xl text-white hover:scale-105 active:scale-95 transition-all disabled:opacity-30 disabled:hover:scale-100"
                >
                  <Minus className="w-5 h-5" />
                </button>

                <div className="glass-strong px-6 py-3 rounded-xl min-w-[80px] text-center">
                  <p className="text-3xl font-bold text-white">
                    {selectedRating ?? "—"}
                  </p>
                </div>

                <button
                  onClick={() => handleStepperChange(1)}
                  disabled={selectedRating === 10 || disabled}
                  className="glass-strong p-3 rounded-xl text-white hover:scale-105 active:scale-95 transition-all disabled:opacity-30 disabled:hover:scale-100"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>
            ) : (
              // Desktop: Number buttons grid (1-10)
              <div className="grid grid-cols-10 gap-2">
                {Array.from({ length: 10 }, (_, i) => i + 1).map((rating) => (
                  <motion.button
                    key={rating}
                    onClick={() => handleRatingSelect(rating)}
                    disabled={disabled}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.6 + (rating - 1) * 0.03 }}
                    className={`aspect-square rounded-xl font-bold text-lg transition-all ${
                      selectedRating === rating
                        ? "text-white shadow-xl scale-110"
                        : "glass-strong text-white/70 hover:text-white hover:scale-105 active:scale-95"
                    } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
                    style={
                      selectedRating === rating
                        ? {
                            background: `linear-gradient(135deg, ${getRatingColor(rating)}, ${getRatingColor(Math.min(10, rating + 1))})`,
                          }
                        : {}
                    }
                  >
                    {rating}
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
              disabled={selectedRating === null || disabled}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="w-full glass-strong py-3 rounded-xl flex items-center justify-center gap-2 text-white font-semibold text-base hover:scale-[1.02] active:scale-98 transition-all disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              <span>{disabled ? "Processing..." : "Next Tag"}</span>
              <ChevronRight className="w-4 h-4" />
            </motion.button>
          </motion.div>
        </div>

        {/* First card hint */}
        {index === 0 && selectedRating === null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="absolute top-3 left-1/2 -translate-x-1/2 glass-strong px-3 py-1.5 rounded-lg pointer-events-none"
          >
            <p className="text-white/80 text-xs font-medium flex items-center gap-1.5">
              <span className="text-sm">👇</span>
              <span>Select a rating below</span>
            </p>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
