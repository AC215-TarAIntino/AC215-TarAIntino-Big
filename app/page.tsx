"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { CardStack } from "@/components/quiz/CardStack";
import { ProgressRing } from "@/components/quiz/ProgressRing";
import { GradientBackground } from "@/components/effects/GradientBackground";
import { getRandomMovies, getRandomQuestionCount, Movie } from "@/lib/data/movies";
import { motion } from "framer-motion";
import { Undo2 } from "lucide-react";

type SwipeData = {
  movie: Movie;
  direction: "left" | "right" | "up" | "down";
};

export default function QuizPage() {
  const router = useRouter();
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [movies, setMovies] = useState<Movie[]>([]);
  const [swipeHistory, setSwipeHistory] = useState<SwipeData[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Initialize quiz with random number of questions
    const questionCount = getRandomQuestionCount(); // 5-10
    const randomMovies = getRandomMovies(questionCount);
    setTotalQuestions(questionCount);
    setMovies(randomMovies);
    setIsInitialized(true);
  }, []);

  const handleSwipe = (movie: Movie, direction: "left" | "right" | "up" | "down") => {
    setSwipeHistory([...swipeHistory, { movie, direction }]);
  };

  const handleUndo = () => {
    if (swipeHistory.length === 0) return;

    const lastSwipe = swipeHistory[swipeHistory.length - 1];
    setSwipeHistory(swipeHistory.slice(0, -1));
    setMovies([lastSwipe.movie, ...movies]);
  };

  const handleComplete = () => {
    // Store preferences in sessionStorage for the result page
    sessionStorage.setItem("quizResults", JSON.stringify(swipeHistory));
    router.push("/generating");
  };

  const currentQuestion = totalQuestions - movies.length + 1;

  if (!isInitialized) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <GradientBackground />
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="text-6xl mb-4">🎬</div>
          <h2 className="text-2xl font-bold text-white">Loading quiz...</h2>
        </motion.div>
      </main>
    );
  }

  return (
    <main className="h-screen relative overflow-hidden flex flex-col">
      <GradientBackground />

      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 pt-4 px-6 flex-shrink-0"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo/Title */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h1 className="text-3xl md:text-4xl font-bold text-gradient-gold">
              TarAIntino
            </h1>
            <p className="text-white/60 text-sm mt-1">
              AI-Powered Movie Quiz
            </p>
          </motion.div>

          {/* Progress Ring */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <ProgressRing
              current={movies.length === 0 ? totalQuestions : currentQuestion - 1}
              total={totalQuestions}
            />
          </motion.div>
        </div>
      </motion.header>

      {/* Main Quiz Area */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.4 }}
        className="relative z-10 flex-1 flex items-center justify-center px-6 py-4 min-h-0"
      >
        <CardStack
          movies={movies}
          onSwipe={handleSwipe}
          onComplete={handleComplete}
        />
      </motion.div>

      {/* Footer Controls */}
      <motion.footer
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="relative z-10 pb-4 px-6 flex-shrink-0"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-4">
          {/* Undo Button */}
          <button
            onClick={handleUndo}
            disabled={swipeHistory.length === 0}
            className="glass-strong px-6 py-3 rounded-2xl flex items-center gap-2 text-white font-medium hover:scale-105 active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            <Undo2 className="w-5 h-5" />
            <span>Undo</span>
          </button>

          {/* Question Counter */}
          <div className="glass-strong px-8 py-3 rounded-2xl">
            <p className="text-white text-lg font-medium">
              Question{" "}
              <span className="text-gradient-gold font-bold">
                {currentQuestion > totalQuestions ? totalQuestions : currentQuestion}
              </span>
              {" "}of{" "}
              <span className="font-bold">{totalQuestions}</span>
            </p>
          </div>
        </div>

        {/* Swipe Instructions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-3 text-center text-white/40 text-xs"
        >
          <p>
            <span className="text-red-400">← Dislike</span> •{" "}
            <span className="text-green-400">Like →</span> •{" "}
            <span className="text-yellow-400">↑ Love</span> •{" "}
            <span className="text-gray-400">↓ Hate</span>
          </p>
        </motion.div>
      </motion.footer>
    </main>
  );
}
