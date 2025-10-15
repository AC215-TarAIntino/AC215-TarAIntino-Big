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

  // Rotation based on horizontal drag (more subtle)
  const rotate = useTransform(x, [-200, 200], [-15, 15]);

  // Opacity for direction indicators
  const opacityLeft = useTransform(x, [-120, -40, 0], [1, 0.3, 0]);
  const opacityRight = useTransform(x, [0, 40, 120], [0, 0.3, 1]);
  const opacityUp = useTransform(y, [-120, -40, 0], [1, 0.3, 0]);
  const opacityDown = useTransform(y, [0, 40, 120], [0, 0.3, 1]);

  const bind = useGesture({
    onDrag: ({ movement: [mx, my], velocity: [vx, vy], dragging }) => {
      setIsDragging(dragging);
      x.set(mx);
      y.set(my);
    },
    onDragEnd: ({ movement: [mx, my], velocity: [vx, vy] }) => {
      setIsDragging(false);

      const threshold = 80;
      const velocityThreshold = 0.4;

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
        // Return to center with spring animation
        const spring = {
          type: "spring",
          stiffness: 500,
          damping: 30,
        };
        x.set(0, spring as any);
        y.set(0, spring as any);
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
        scale: isDragging ? 1.02 : 1,
      }}
      transition={{
        scale: {
          type: "spring",
          stiffness: 400,
          damping: 30,
        },
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
          className="absolute top-6 left-6 rotate-[-15deg]"
          style={{ opacity: opacityLeft }}
        >
          <div className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-red-500/90 border-2 border-white shadow-lg">
            <X className="w-5 h-5 text-white" strokeWidth={3} />
            <span className="text-white font-bold text-lg">NOPE</span>
          </div>
        </motion.div>

        <motion.div
          className="absolute top-6 right-6 rotate-[15deg]"
          style={{ opacity: opacityRight }}
        >
          <div className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-green-500/90 border-2 border-white shadow-lg">
            <Heart className="w-5 h-5 text-white fill-white" strokeWidth={3} />
            <span className="text-white font-bold text-lg">LIKE</span>
          </div>
        </motion.div>

        <motion.div
          className="absolute top-6 left-1/2 -translate-x-1/2"
          style={{ opacity: opacityUp }}
        >
          <div className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-yellow-400 to-orange-500 border-2 border-white shadow-lg">
            <TrendingUp className="w-5 h-5 text-white" strokeWidth={3} />
            <span className="text-white font-bold text-lg">LOVE!</span>
          </div>
        </motion.div>

        <motion.div
          className="absolute bottom-24 left-1/2 -translate-x-1/2"
          style={{ opacity: opacityDown }}
        >
          <div className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gray-900/90 border-2 border-red-500 shadow-lg">
            <TrendingDown className="w-5 h-5 text-red-500" strokeWidth={3} />
            <span className="text-red-500 font-bold text-lg">HATE</span>
          </div>
        </motion.div>

        {/* Movie Info */}
        <div className="absolute bottom-0 left-0 right-0 p-6 space-y-3">
          <div>
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-1 drop-shadow-lg line-clamp-2">
              {movie.title}
            </h2>
            <p className="text-sm text-white/90 drop-shadow">
              {movie.director} • {movie.year}
            </p>
          </div>

          {/* Tags */}
          <div className="flex flex-wrap gap-1.5">
            {movie.tags.slice(0, 5).map((tag) => (
              <motion.span
                key={tag}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: Math.random() * 0.2 }}
                className="px-2.5 py-0.5 rounded-full text-xs font-medium glass border border-white/20 text-white/90"
              >
                {tag}
              </motion.span>
            ))}
          </div>
        </div>

        {/* Touch Hint (shows on first card) */}
        {index === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: isDragging ? 0 : 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none"
          >
            <div className="glass-strong px-6 py-3 rounded-xl">
              <p className="text-white text-base font-medium">
                👆 Drag to rate
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
