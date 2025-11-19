"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { SwipeCard } from "@/components/quiz/SwipeCard";
import { ProgressRing } from "@/components/quiz/ProgressRing";
import { GradientBackground } from "@/components/effects/GradientBackground";
import { motion, AnimatePresence } from "framer-motion";
import { startQuiz, submitAnswer } from "@/lib/api/quizService";
import type { Question, Progress } from "@/lib/api/types";

export default function QuizPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [progress, setProgress] = useState<Progress>({ asked: 0, total: 5 });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totalQuestions = 5;

  // Initialize quiz on mount
  useEffect(() => {
    const initializeQuiz = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await startQuiz(totalQuestions);
        setSessionId(response.session_id);
        setCurrentQuestion(response.question);
        setProgress({ asked: 0, total: totalQuestions });
        // Store session ID for downstream pages
        sessionStorage.setItem("quizSessionId", response.session_id);
      } catch (err) {
        console.error("Failed to start quiz:", err);
        setError(
          err instanceof Error ? err.message : "Failed to connect to quiz service"
        );
      } finally {
        setIsLoading(false);
      }
    };

    initializeQuiz();
  }, []);

  const handleRating = useCallback(
    async (rating: number) => {
      if (!sessionId || !currentQuestion || isSubmitting) return;

      try {
        setIsSubmitting(true);
        setError(null);

        const response = await submitAnswer(
          sessionId,
          currentQuestion.question_id,
          rating
        );

        setProgress(response.progress);

        if (response.status === "complete" || response.next_question === null) {
          // Quiz complete - navigate to generating page
          router.push("/generating");
        } else {
          // Show next question
          setCurrentQuestion(response.next_question);
        }
      } catch (err) {
        console.error("Failed to submit answer:", err);
        setError(
          err instanceof Error ? err.message : "Failed to submit answer"
        );
      } finally {
        setIsSubmitting(false);
      }
    },
    [sessionId, currentQuestion, isSubmitting, router]
  );

  // Loading state
  if (isLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <GradientBackground />
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="text-6xl mb-4">🎬</div>
          <h2 className="text-2xl font-bold text-white">
            Preparing your preference quiz...
          </h2>
          <p className="text-white/60 mt-2">Connecting to quiz service</p>
        </motion.div>
      </main>
    );
  }

  // Error state
  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center p-6">
        <GradientBackground />
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md"
        >
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-white mb-2">
            Connection Error
          </h2>
          <p className="text-white/70 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="glass-strong px-6 py-3 rounded-xl text-white font-semibold hover:scale-105 active:scale-95 transition-all"
          >
            Try Again
          </button>
        </motion.div>
      </main>
    );
  }

  const currentQuestionNumber = progress.asked + 1;

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
            <p className="text-white/60 text-sm mt-1">Tag Preference Quiz</p>
          </motion.div>

          {/* Progress Ring */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <ProgressRing current={progress.asked} total={progress.total} />
          </motion.div>
        </div>
      </motion.header>

      {/* Main Quiz Area - Single Question View */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.4 }}
        className="relative z-20 flex-1 flex items-center justify-center px-6 py-4 min-h-0"
      >
        <div className="w-full max-w-lg h-full max-h-[500px] relative">
          <AnimatePresence mode="wait">
            {currentQuestion && (
              <SwipeCard
                key={currentQuestion.question_id}
                tag={currentQuestion.tag_label}
                onRating={handleRating}
                index={0}
                disabled={isSubmitting}
              />
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Footer Controls */}
      <motion.footer
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="relative z-10 pb-6 px-6 flex-shrink-0"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-4">
          {/* Tag Counter */}
          <div className="glass-strong px-8 py-3 rounded-2xl">
            <p className="text-white text-lg font-medium">
              Tag{" "}
              <span className="text-gradient-gold font-bold">
                {currentQuestionNumber > totalQuestions
                  ? totalQuestions
                  : currentQuestionNumber}
              </span>{" "}
              of <span className="font-bold">{totalQuestions}</span>
            </p>
          </div>
        </div>

        {/* Rating Instructions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-3 text-center text-white/50 text-sm"
        >
          <p>Rate how much you want this in your movie recommendations</p>
          <p className="text-xs text-white/30 mt-1">
            1 = Not at all &bull; 10 = Absolutely must have
          </p>
        </motion.div>
      </motion.footer>
    </main>
  );
}
