"use client";

import { motion, useMotionValue, useTransform } from "framer-motion";
import { useGesture } from "@use-gesture/react";
import { Movie } from "@/lib/data/movies";
import { Heart, X, TrendingUp, TrendingDown } from "lucide-react";
import { useState } from "react";
import Image from "next/image";

interface SwipeCardProps {
  movie: Movie;
  onSwipe: (direction: "left" | "right" | "up" | "down") => void;
  style?: React.CSSProperties;
  index: number;
}

export function SwipeCard({ movie, onSwipe, style, index }: SwipeCardProps) {
  const [isDragging, setIsDragging] = useState(false);
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  // Rotation based on horizontal drag
  const rotate = useTransform(x, [-200, 200], [-30, 30]);

  // Opacity for direction indicators
  const opacityLeft = useTransform(x, [-150, -50, 0], [1, 0.5, 0]);
  const opacityRight = useTransform(x, [0, 50, 150], [0, 0.5, 1]);
  const opacityUp = useTransform(y, [-150, -50, 0], [1, 0.5, 0]);
  const opacityDown = useTransform(y, [0, 50, 150], [0, 0.5, 1]);

  const bind = useGesture({
    onDrag: ({ movement: [mx, my], velocity: [vx, vy], dragging }) => {
      setIsDragging(dragging);
      x.set(mx);
      y.set(my);
    },
    onDragEnd: ({ movement: [mx, my], velocity: [vx, vy] }) => {
      setIsDragging(false);

      const threshold = 100;
      const velocityThreshold = 0.5;

      // Check for strong vertical swipes first
      if (Math.abs(my) > Math.abs(mx)) {
        if (my < -threshold || vy < -velocityThreshold) {
          // Swipe up - Love it!
          onSwipe("up");
          return;
        } else if (my > threshold || vy > velocityThreshold) {
          // Swipe down - Hate it!
          onSwipe("down");
          return;
        }
      }

      // Check horizontal swipes
      if (mx < -threshold || vx < -velocityThreshold) {
        // Swipe left - Dislike
        onSwipe("left");
      } else if (mx > threshold || vx > velocityThreshold) {
        // Swipe right - Like
        onSwipe("right");
      } else {
        // Return to center
        x.set(0);
        y.set(0);
      }
    },
  });

  return (
    <motion.div
      {...bind()}
      style={{
        x,
        y,
        rotate,
        ...style,
        touchAction: "none",
      }}
      className="absolute w-full h-full cursor-grab active:cursor-grabbing"
      animate={{
        scale: isDragging ? 1.05 : 1,
      }}
      transition={{
        scale: { duration: 0.2 },
      }}
    >
      <div className="relative w-full h-full rounded-3xl overflow-hidden glass-strong grain shadow-2xl">
        {/* Movie Poster Background */}
        <div className="absolute inset-0">
          <Image
            src={movie.poster}
            alt={movie.title}
            fill
            className="object-cover"
            priority={index < 3}
          />
          {/* Gradient Overlays */}
          <div
            className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent opacity-80"
          />
          <div
            className="absolute inset-0"
            style={{
              background: `radial-gradient(circle at center, transparent 0%, ${movie.color}40 100%)`,
            }}
          />
        </div>

        {/* Swipe Direction Indicators */}
        <motion.div
          className="absolute top-8 left-8 rotate-[-20deg]"
          style={{ opacity: opacityLeft }}
        >
          <div className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-red-500/90 border-4 border-white shadow-lg">
            <X className="w-8 h-8 text-white" strokeWidth={3} />
            <span className="text-white font-bold text-2xl">NOPE</span>
          </div>
        </motion.div>

        <motion.div
          className="absolute top-8 right-8 rotate-[20deg]"
          style={{ opacity: opacityRight }}
        >
          <div className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-green-500/90 border-4 border-white shadow-lg">
            <Heart className="w-8 h-8 text-white fill-white" strokeWidth={3} />
            <span className="text-white font-bold text-2xl">LIKE</span>
          </div>
        </motion.div>

        <motion.div
          className="absolute top-8 left-1/2 -translate-x-1/2"
          style={{ opacity: opacityUp }}
        >
          <div className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-gradient-to-r from-yellow-400 to-orange-500 border-4 border-white shadow-lg">
            <TrendingUp className="w-8 h-8 text-white" strokeWidth={3} />
            <span className="text-white font-bold text-2xl">LOVE IT!</span>
          </div>
        </motion.div>

        <motion.div
          className="absolute bottom-32 left-1/2 -translate-x-1/2"
          style={{ opacity: opacityDown }}
        >
          <div className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-gray-900/90 border-4 border-red-500 shadow-lg">
            <TrendingDown className="w-8 h-8 text-red-500" strokeWidth={3} />
            <span className="text-red-500 font-bold text-2xl">HATE IT</span>
          </div>
        </motion.div>

        {/* Movie Info */}
        <div className="absolute bottom-0 left-0 right-0 p-8 space-y-4">
          <div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-2 drop-shadow-lg">
              {movie.title}
            </h2>
            <p className="text-xl text-white/90 drop-shadow">
              {movie.director} • {movie.year}
            </p>
          </div>

          {/* Tags */}
          <div className="flex flex-wrap gap-2">
            {movie.tags.slice(0, 6).map((tag) => (
              <motion.span
                key={tag}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: Math.random() * 0.3 }}
                className="px-3 py-1 rounded-full text-sm font-medium glass border border-white/20 text-white"
              >
                {tag}
              </motion.span>
            ))}
          </div>
        </div>

        {/* Touch Hint (shows on first card) */}
        {index === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: isDragging ? 0 : 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none"
          >
            <div className="glass-strong px-8 py-4 rounded-2xl">
              <p className="text-white text-lg font-medium">
                👆 Drag to rate
              </p>
              <p className="text-white/70 text-sm mt-1">
                ← Dislike | Like → | ↑ Love | ↓ Hate
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
