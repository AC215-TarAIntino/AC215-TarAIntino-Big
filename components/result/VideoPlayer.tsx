"use client";

import { motion } from "framer-motion";
import { Play, Pause, Volume2, VolumeX, Maximize2 } from "lucide-react";
import { useState } from "react";
import Image from "next/image";

interface VideoPlayerProps {
  posterUrl: string;
  title: string;
}

export function VideoPlayer({ posterUrl, title }: VideoPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);

  // Mock playback
  const togglePlay = () => {
    setIsPlaying(!isPlaying);
    if (!isPlaying) {
      // Simulate progress
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            setIsPlaying(false);
            clearInterval(interval);
            return 0;
          }
          return prev + 1;
        });
      }, 50);
    }
  };

  return (
    <div className="relative w-full aspect-video rounded-2xl overflow-hidden glass-strong group">
      {/* Film Strip Border Effect */}
      <div className="absolute inset-0 pointer-events-none z-10">
        <div className="absolute top-0 left-0 right-0 h-8 bg-gradient-to-b from-black/50 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-black/50 to-transparent" />

        {/* Film strip perforations */}
        <div className="absolute top-2 left-0 right-0 flex justify-between px-2">
          {[...Array(20)].map((_, i) => (
            <div key={i} className="w-2 h-2 bg-black/30 rounded-sm" />
          ))}
        </div>
        <div className="absolute bottom-2 left-0 right-0 flex justify-between px-2">
          {[...Array(20)].map((_, i) => (
            <div key={i} className="w-2 h-2 bg-black/30 rounded-sm" />
          ))}
        </div>
      </div>

      {/* Video Content */}
      <div className="relative w-full h-full bg-black">
        <Image
          src={posterUrl}
          alt={title}
          fill
          className="object-cover"
        />

        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent" />

        {/* Play Button Overlay */}
        <motion.button
          onClick={togglePlay}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          className="absolute inset-0 flex items-center justify-center z-20"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="w-24 h-24 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center border-4 border-white/50 hover:bg-white/30 transition-colors"
          >
            {isPlaying ? (
              <Pause className="w-12 h-12 text-white fill-white ml-0" />
            ) : (
              <Play className="w-12 h-12 text-white fill-white ml-2" />
            )}
          </motion.div>
        </motion.button>
      </div>

      {/* Video Controls */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/90 via-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity z-30">
        {/* Progress Bar */}
        <div className="mb-3">
          <div className="relative w-full h-1 bg-white/20 rounded-full overflow-hidden cursor-pointer hover:h-2 transition-all">
            <motion.div
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-gold via-neon-magenta to-neon-cyan rounded-full"
              style={{ width: `${progress}%` }}
            />

            {/* Progress dot */}
            {progress > 0 && (
              <motion.div
                className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg"
                style={{ left: `${progress}%` }}
              />
            )}
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/30 transition-colors"
            >
              {isPlaying ? (
                <Pause className="w-5 h-5 text-white fill-white" />
              ) : (
                <Play className="w-5 h-5 text-white fill-white ml-1" />
              )}
            </button>

            <button
              onClick={() => setIsMuted(!isMuted)}
              className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/30 transition-colors"
            >
              {isMuted ? (
                <VolumeX className="w-5 h-5 text-white" />
              ) : (
                <Volume2 className="w-5 h-5 text-white" />
              )}
            </button>

            <span className="text-white text-sm font-medium">
              {Math.floor(progress * 1.2)}s / 2:00
            </span>
          </div>

          <button className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/30 transition-colors">
            <Maximize2 className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}
