"use client";

import { motion } from "framer-motion";

interface TasteProfileProps {
  tags: { name: string; score: number }[];
}

export function TasteProfile({ tags }: TasteProfileProps) {
  // Sort by score and take top 8
  const topTags = tags.sort((a, b) => b.score - a.score).slice(0, 8);

  return (
    <div className="glass-strong rounded-2xl p-6 space-y-6">
      <div className="text-center">
        <h3 className="text-2xl font-bold text-white mb-2">
          Your Taste Profile
        </h3>
        <p className="text-white/60 text-sm">
          Your cinematic DNA based on preferences
        </p>
      </div>

      {/* Tag Cloud */}
      <div className="grid grid-cols-2 gap-3">
        {topTags.map((tag, index) => {
          const intensity = tag.score;
          const size = 0.8 + intensity * 0.4; // Scale from 0.8 to 1.2

          return (
            <motion.div
              key={tag.name}
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1, type: "spring" }}
              whileHover={{ scale: size * 1.1 }}
              className="relative overflow-hidden rounded-xl p-4 text-center"
              style={{
                transform: `scale(${size})`,
              }}
            >
              {/* Animated background */}
              <motion.div
                animate={{
                  opacity: [0.3, 0.5, 0.3],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="absolute inset-0 bg-gradient-to-br from-gold/20 via-neon-magenta/20 to-neon-cyan/20"
              />

              {/* Content */}
              <div className="relative z-10">
                <div className="text-sm font-semibold text-white capitalize mb-1">
                  {tag.name}
                </div>
                <div className="flex items-center justify-center gap-1">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className={`w-2 h-2 rounded-full ${
                        i < Math.ceil(intensity * 5)
                          ? "bg-gold"
                          : "bg-white/20"
                      }`}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Radar Chart Visualization (simplified) */}
      <div className="relative aspect-square max-w-xs mx-auto">
        <svg viewBox="0 0 200 200" className="w-full h-full">
          {/* Background grid */}
          <g opacity="0.1">
            {[...Array(5)].map((_, i) => {
              const radius = ((i + 1) * 80) / 5;
              return (
                <circle
                  key={i}
                  cx="100"
                  cy="100"
                  r={radius}
                  fill="none"
                  stroke="white"
                  strokeWidth="1"
                />
              );
            })}
          </g>

          {/* Axes */}
          <g opacity="0.2">
            {topTags.slice(0, 6).map((_, i) => {
              const angle = (i * 360) / 6 - 90;
              const rad = (angle * Math.PI) / 180;
              const x = 100 + Math.cos(rad) * 80;
              const y = 100 + Math.sin(rad) * 80;
              return (
                <line
                  key={i}
                  x1="100"
                  y1="100"
                  x2={x}
                  y2={y}
                  stroke="white"
                  strokeWidth="1"
                />
              );
            })}
          </g>

          {/* Data polygon */}
          <motion.polygon
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5, type: "spring" }}
            points={topTags
              .slice(0, 6)
              .map((tag, i) => {
                const angle = (i * 360) / 6 - 90;
                const rad = (angle * Math.PI) / 180;
                const radius = tag.score * 80;
                const x = 100 + Math.cos(rad) * radius;
                const y = 100 + Math.sin(rad) * radius;
                return `${x},${y}`;
              })
              .join(" ")}
            fill="url(#radarGradient)"
            stroke="url(#radarStroke)"
            strokeWidth="2"
            opacity="0.7"
          />

          {/* Gradient definitions */}
          <defs>
            <linearGradient id="radarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#667eea" stopOpacity="0.6" />
              <stop offset="50%" stopColor="#f093fb" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#ffd700" stopOpacity="0.6" />
            </linearGradient>
            <linearGradient id="radarStroke" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#667eea" />
              <stop offset="50%" stopColor="#f093fb" />
              <stop offset="100%" stopColor="#ffd700" />
            </linearGradient>
          </defs>

          {/* Data points */}
          {topTags.slice(0, 6).map((tag, i) => {
            const angle = (i * 360) / 6 - 90;
            const rad = (angle * Math.PI) / 180;
            const radius = tag.score * 80;
            const x = 100 + Math.cos(rad) * radius;
            const y = 100 + Math.sin(rad) * radius;
            return (
              <motion.circle
                key={i}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.5 + i * 0.1 }}
                cx={x}
                cy={y}
                r="4"
                fill="#ffd700"
                stroke="white"
                strokeWidth="2"
              />
            );
          })}
        </svg>
      </div>
    </div>
  );
}
