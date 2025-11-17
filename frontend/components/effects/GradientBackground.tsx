"use client";

import { motion } from "framer-motion";

export function GradientBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      {/* Animated gradient blobs */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          rotate: [0, 90, 0],
          x: [0, 100, 0],
          y: [0, -100, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute top-0 left-0 w-[600px] h-[600px] rounded-full blur-3xl opacity-30"
        style={{
          background: "radial-gradient(circle, #667eea 0%, transparent 70%)",
        }}
      />

      <motion.div
        animate={{
          scale: [1, 1.3, 1],
          rotate: [0, -90, 0],
          x: [0, -100, 0],
          y: [0, 100, 0],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute top-1/4 right-0 w-[700px] h-[700px] rounded-full blur-3xl opacity-30"
        style={{
          background: "radial-gradient(circle, #f093fb 0%, transparent 70%)",
        }}
      />

      <motion.div
        animate={{
          scale: [1, 1.1, 1],
          rotate: [0, 45, 0],
          x: [0, 50, 0],
          y: [0, -50, 0],
        }}
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute bottom-0 left-1/4 w-[500px] h-[500px] rounded-full blur-3xl opacity-30"
        style={{
          background: "radial-gradient(circle, #ffd700 0%, transparent 70%)",
        }}
      />

      <motion.div
        animate={{
          scale: [1, 1.15, 1],
          rotate: [0, -45, 0],
          x: [0, -50, 0],
          y: [0, 50, 0],
        }}
        transition={{
          duration: 22,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute bottom-1/4 right-1/4 w-[550px] h-[550px] rounded-full blur-3xl opacity-30"
        style={{
          background: "radial-gradient(circle, #00ffff 0%, transparent 70%)",
        }}
      />

      {/* Noise texture overlay */}
      <div
        className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='3' numOctaves='5' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />
    </div>
  );
}
