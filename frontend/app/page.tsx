"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { CardStack } from "@/components/quiz/CardStack";
import { ProgressRing } from "@/components/quiz/ProgressRing";
import { GradientBackground } from "@/components/effects/GradientBackground";
import { getRandomTags } from "@/lib/data/tags";
import { motion } from "framer-motion";

type TagRating = {
  tag: string;
  rating: number; // 0-10
};

export default function QuizPage() {
  const router = useRouter();
  const [tags, setTags] = useState<string[]>([]);
  const [ratings, setRatings] = useState<TagRating[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);

  const totalQuestions = 8; // Fixed: always 8 tags

  useEffect(() => {
    // Initialize quiz with 8 random tags
    const randomTags = getRandomTags(8);
    setTags(randomTags);
    setIsInitialized(true);
  }, []);

  const handleRating = (tag: string, rating: number) => {
    setRatings([...ratings, { tag, rating }]);
    // Remove the rated tag from the list
    setTags(tags.slice(1));
  };

  const handleComplete = () => {
    // Store tag ratings in sessionStorage for the result page
    sessionStorage.setItem("quizResults", JSON.stringify(ratings));
    router.push("/generating");
  };

  const currentQuestion = tags.length === 0 ? totalQuestions : totalQuestions - tags.length + 1;

  if (!isInitialized) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <GradientBackground />
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="text-6xl mb-4">🏷️</div>
          <h2 className="text-2xl font-bold text-white">Loading your preference quiz...</h2>
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
              Tag Preference Quiz
            </p>
          </motion.div>

          {/* Progress Ring */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <ProgressRing
              current={tags.length === 0 ? totalQuestions : currentQuestion - 1}
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
        className="relative z-20 flex-1 flex items-center justify-center px-6 py-4 min-h-0"
      >
        <CardStack
          tags={tags}
          onRating={handleRating}
          onComplete={handleComplete}
        />
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
                {currentQuestion > totalQuestions ? totalQuestions : currentQuestion}
              </span>
              {" "}of{" "}
              <span className="font-bold">{totalQuestions}</span>
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
            0 = Not at all • 10 = Absolutely must have
          </p>
        </motion.div>
      </motion.footer>
    </main>
  );
}
