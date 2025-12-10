"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Movie {
  title: string;
  duration: number;
  narration: string;
  scenes_count: number;
  characters: string[];
  visual_style: string;
  aspect_ratio: string;
  created_at: string;
  filename: string;
  video_url: string;
  thumbnail_url: string;
}

interface GalleryManifest {
  version: string;
  created_at: string;
  total_movies: number;
  movies: Movie[];
}

export default function MovieGallery() {
  const [manifest, setManifest] = useState<GalleryManifest | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);

  useEffect(() => {
    fetchGallery();
  }, []);

  const fetchGallery = async () => {
    try {
      setIsLoading(true);
      const response = await fetch("/api/gallery");
      if (!response.ok) {
        throw new Error("Failed to fetch gallery");
      }
      const data = await response.json();
      setManifest(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="w-full p-6">
        <div className="text-center text-white/60">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          <p className="mt-2">Loading gallery...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full p-6">
        <div className="glass-strong rounded-lg p-6 text-center">
          <p className="text-red-400">Error loading gallery: {error}</p>
        </div>
      </div>
    );
  }

  if (!manifest || manifest.movies.length === 0) {
    return (
      <div className="w-full p-6">
        <div className="glass-strong rounded-lg p-6 text-center">
          <p className="text-white/60">No movies available yet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gradient-gold mb-2">
          Featured Movies
        </h2>
        <p className="text-white/60">
          {manifest.total_movies === 1
            ? "Watch our featured Tarantino-style movie trailer"
            : `${manifest.total_movies} Tarantino-style movies created by our community`
          }
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {manifest.movies.map((movie, index) => (
          <motion.div
            key={movie.filename}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="glass-strong rounded-lg overflow-hidden cursor-pointer hover:scale-105 transition-transform"
            onClick={() => setSelectedMovie(movie)}
          >
            <div className="aspect-video bg-gradient-to-br from-purple-900/20 to-pink-900/20 flex items-center justify-center">
              <div className="text-center p-4">
                <h3 className="text-lg font-bold text-white line-clamp-2">
                  {movie.title}
                </h3>
                <p className="text-sm text-white/60 mt-2">
                  {movie.scenes_count} scenes • {movie.duration}s
                </p>
              </div>
            </div>
            <div className="p-3">
              <p className="text-xs text-white/50 line-clamp-2">
                {movie.narration}
              </p>
            </div>
          </motion.div>
        ))}
      </div>

      <AnimatePresence>
        {selectedMovie && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedMovie(null)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="glass-strong rounded-lg max-w-3xl w-full p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-2xl font-bold text-gradient-gold">
                    {selectedMovie.title}
                  </h3>
                  <p className="text-white/60 mt-1">
                    {selectedMovie.visual_style} • {selectedMovie.duration} seconds
                  </p>
                </div>
                <button
                  onClick={() => setSelectedMovie(null)}
                  className="text-white/60 hover:text-white text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="mb-4">
                <p className="text-white/80">{selectedMovie.narration}</p>
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-semibold text-white/80 mb-2">Characters:</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedMovie.characters.map((char) => (
                    <span
                      key={char}
                      className="px-3 py-1 bg-purple-500/20 rounded-full text-sm text-white/80"
                    >
                      {char}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    const videoUrl = selectedMovie.video_url.replace(
                      "gs://",
                      "https://storage.googleapis.com/"
                    );
                    window.open(videoUrl, "_blank");
                  }}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition-all"
                >
                  Watch Trailer
                </button>
                <button
                  onClick={() => setSelectedMovie(null)}
                  className="px-6 py-3 glass-strong rounded-lg font-semibold hover:bg-white/10 transition-all"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
