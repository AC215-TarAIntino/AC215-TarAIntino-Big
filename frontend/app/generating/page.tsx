"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { GradientBackground } from "@/components/effects/GradientBackground";
import { Sparkles, Film, Wand2, Check } from "lucide-react";
import type { TrailerGenerationResponse } from "@/types/generation";

const PHASES = [
  {
    id: 1,
    title: "Analyzing your cinematic taste...",
    description: "Processing your preferences",
    icon: Sparkles,
    progress: [0, 25],
    color: "#667eea",
  },
  {
    id: 2,
    title: "Crafting your personalized story...",
    description: "Building narrative structure",
    icon: Wand2,
    progress: [25, 50],
    color: "#f093fb",
  },
  {
    id: 3,
    title: "Generating AI scenes...",
    description: "Creating visual sequences",
    icon: Film,
    progress: [50, 75],
    color: "#ffd700",
  },
  {
    id: 4,
    title: "Adding final cinematic touches...",
    description: "Polishing your trailer",
    icon: Sparkles,
    progress: [75, 100],
    color: "#00ffff",
  },
];

export default function GeneratingPage() {
  const router = useRouter();
  const [progress, setProgress] = useState(0);
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);
  const [isGenerationComplete, setIsGenerationComplete] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState(
    "Contacting the TarAIntino studio...",
  );
  const [hasNavigated, setHasNavigated] = useState(false);

  // Drive the visual progress until we either hit 95% or complete the generation.
  useEffect(() => {
    if (isGenerationComplete || generationError) {
      setProgress(100);
      return;
    }

    const duration = 8000;
    const interval = 50;
    const steps = duration / interval;
    const increment = 95 / steps;
    let currentProgress = 0;

    const timer = setInterval(() => {
      currentProgress = Math.min(currentProgress + increment, 95);
      setProgress((prev) => {
        if (prev >= 95) {
          clearInterval(timer);
          return prev;
        }
        if (currentProgress >= 95) {
          clearInterval(timer);
        }
        return Math.min(currentProgress, 95);
      });
    }, interval);

    return () => clearInterval(timer);
  }, [isGenerationComplete, generationError]);

  // Update the current phase based on progress value.
  useEffect(() => {
    if (progress >= 75) {
      setCurrentPhaseIndex(3);
    } else if (progress >= 50) {
      setCurrentPhaseIndex(2);
    } else if (progress >= 25) {
      setCurrentPhaseIndex(1);
    } else {
      setCurrentPhaseIndex(0);
    }
  }, [progress]);

  // Once the generator finishes, push to the result page.
  useEffect(() => {
    if (!isGenerationComplete || hasNavigated || generationError) {
      return;
    }

    setProgress(100);
    const timeout = setTimeout(() => {
      setHasNavigated(true);
      router.push("/result");
    }, 1200);

    return () => clearTimeout(timeout);
  }, [isGenerationComplete, hasNavigated, router, generationError]);

  useEffect(() => {
    let isCancelled = false;
    sessionStorage.removeItem("generationResult");

    const runGeneration = async () => {
      try {
        setStatusMessage("Sending your prompts to TarAIntino's AI studio...");

        const quizResultsRaw = sessionStorage.getItem("quizResults");
        let quizResults: unknown;
        if (quizResultsRaw) {
          try {
            quizResults = JSON.parse(quizResultsRaw);
          } catch (error) {
            console.warn("Unable to parse quiz results", error);
          }
        }

        const response = await fetch("/api/generate-trailer", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ quizResults }),
        });

        const text = await response.text();
        type GeneratorResponse = TrailerGenerationResponse | { error: string };
        const payload = text ? (JSON.parse(text) as GeneratorResponse) : null;

        if (!response.ok || !payload || "error" in payload) {
          const errorMessage =
            payload && "error" in payload
              ? (payload.error as string)
              : "Failed to generate trailer";
          throw new Error(errorMessage);
        }

        if (isCancelled) {
          return;
        }

        sessionStorage.setItem(
          "generationResult",
          JSON.stringify(payload as TrailerGenerationResponse),
        );
        setStatusMessage("Polishing your cinematic trailer...");
        setIsGenerationComplete(true);
      } catch (error) {
        if (isCancelled) {
          return;
        }
        console.error(error);
        setGenerationError(
          error instanceof Error
            ? error.message
            : "Unexpected error during generation",
        );
        setStatusMessage("We hit a snag while generating your trailer.");
      }
    };

    void runGeneration();
    return () => {
      isCancelled = true;
    };
  }, []);

  const handleRetry = () => {
    window.location.reload();
  };

  const currentPhase = PHASES[currentPhaseIndex];
  const CurrentIcon = currentPhase.icon;

  return (
    <main className="h-screen relative overflow-hidden flex items-center justify-center">
      <GradientBackground />

      <div className="relative z-10 w-full max-w-2xl px-6 py-8">
        {/* Main Loading Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="glass-strong rounded-3xl p-6 md:p-8 space-y-6"
        >
          {/* Phase Indicator */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentPhase.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
              className="text-center space-y-4"
            >
              {/* Icon */}
              <motion.div
                animate={{
                  rotate: [0, 360],
                  scale: [1, 1.1, 1],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "linear",
                }}
                className="inline-flex items-center justify-center w-20 h-20 rounded-full glass"
                style={{
                  boxShadow: `0 0 40px ${currentPhase.color}60`,
                }}
              >
                <CurrentIcon
                  className="w-10 h-10"
                  style={{ color: currentPhase.color }}
                  strokeWidth={2}
                />
              </motion.div>

              {/* Title */}
              <h2 className="text-3xl md:text-4xl font-bold text-white">
                {currentPhase.title}
              </h2>

              {/* Description */}
              <p className="text-white/70 text-lg">
                {currentPhase.description}
              </p>
            </motion.div>
          </AnimatePresence>

          {/* Progress Bar */}
          <div className="space-y-4">
            {/* Circular Progress */}
            <div className="flex items-center justify-center">
              <div className="relative w-48 h-48">
                <svg
                  className="transform -rotate-90"
                  width="192"
                  height="192"
                  viewBox="0 0 192 192"
                >
                  {/* Background circle */}
                  <circle
                    cx="96"
                    cy="96"
                    r="88"
                    stroke="rgba(255, 255, 255, 0.1)"
                    strokeWidth="16"
                    fill="none"
                  />

                  {/* Progress circle */}
                  <motion.circle
                    cx="96"
                    cy="96"
                    r="88"
                    stroke="url(#progressGradient)"
                    strokeWidth="16"
                    fill="none"
                    strokeLinecap="round"
                    style={{
                      strokeDasharray: 2 * Math.PI * 88,
                      strokeDashoffset: 2 * Math.PI * 88 * (1 - progress / 100),
                    }}
                    transition={{
                      duration: 0.1,
                      ease: "linear",
                    }}
                  />

                  {/* Gradient definition */}
                  <defs>
                    <linearGradient
                      id="progressGradient"
                      x1="0%"
                      y1="0%"
                      x2="100%"
                      y2="100%"
                    >
                      <stop offset="0%" stopColor="#667eea" />
                      <stop offset="50%" stopColor="#f093fb" />
                      <stop offset="100%" stopColor="#ffd700" />
                    </linearGradient>
                  </defs>
                </svg>

                {/* Percentage Text */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <motion.div
                    key={Math.floor(progress / 5)}
                    initial={{ scale: 1.2, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="text-center"
                  >
                    <div className="text-5xl font-bold text-gradient-gold">
                      {Math.floor(progress)}%
                    </div>
                  </motion.div>
                </div>
              </div>
            </div>

            {/* Linear Progress Bar */}
            <div className="relative w-full h-3 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                className="absolute inset-y-0 left-0 rounded-full"
                style={{
                  background: `linear-gradient(90deg, ${currentPhase.color} 0%, ${currentPhase.color}aa 100%)`,
                  width: `${progress}%`,
                  boxShadow: `0 0 20px ${currentPhase.color}80`,
                }}
                transition={{ duration: 0.1, ease: "linear" }}
              />

              {/* Shimmer effect */}
              <motion.div
                animate={{
                  x: [-100, 400],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "linear",
                }}
                className="absolute inset-0 w-32 bg-gradient-to-r from-transparent via-white/30 to-transparent"
              />
            </div>
          </div>

          <div className="text-center text-white/70 text-sm space-y-2 min-h-[60px] flex flex-col items-center justify-center">
            {generationError ? (
              <>
                <p className="text-red-400 font-semibold">
                  {generationError}
                </p>
                <button
                  onClick={handleRetry}
                  className="px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 text-white text-sm"
                >
                  Try again
                </button>
              </>
            ) : (
              <p>{statusMessage}</p>
            )}
          </div>

          {/* Phase Checklist */}
          <div className="space-y-3">
            {PHASES.map((phase, index) => {
              const isComplete = progress >= phase.progress[1];
              const isCurrent = index === currentPhaseIndex;
              const PhaseIcon = phase.icon;

              return (
                <motion.div
                  key={phase.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                    isCurrent
                      ? "glass-strong border border-white/20"
                      : "opacity-50"
                  }`}
                >
                  <div
                    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      isComplete
                        ? "bg-green-500"
                        : isCurrent
                        ? "glass border border-white/20"
                        : "bg-white/10"
                    }`}
                  >
                    {isComplete ? (
                      <Check className="w-5 h-5 text-white" strokeWidth={3} />
                    ) : (
                      <PhaseIcon className="w-4 h-4 text-white" />
                    )}
                  </div>

                  <span className="text-white text-sm font-medium flex-1">
                    {phase.title}
                  </span>

                  {isCurrent && (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                      className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full"
                    />
                  )}
                </motion.div>
              );
            })}
          </div>

          {/* Fun Fact / Tip */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="text-center text-white/50 text-sm italic"
          >
            <p>
              ✨ Fun fact: We&apos;re using your taste vector to find the perfect cinematic blend!
            </p>
          </motion.div>
        </motion.div>
      </div>
    </main>
  );
}
