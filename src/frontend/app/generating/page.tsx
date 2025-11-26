"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { GradientBackground } from "@/components/effects/GradientBackground";
import { Sparkles, Film, Wand2, Check } from "lucide-react";

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
    description: "Creating visual sequences (this may take 5-15 minutes)",
    icon: Film,
    progress: [50, 90],
    color: "#ffd700",
  },
  {
    id: 4,
    title: "Finalizing your trailer...",
    description: "Polishing and uploading to GCS",
    icon: Sparkles,
    progress: [90, 100],
    color: "#00ffff",
  },
];

export default function GeneratingPage() {
  const router = useRouter();
  const [progress, setProgress] = useState(0);
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState("15-20 minutes");

  useEffect(() => {
    // Start elapsed time counter
    const startTime = Date.now();
    const timeInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      setElapsedTime(elapsed);
    }, 1000);

    const startGeneration = async () => {
      try {
        // Get session data from sessionStorage
        const sessionId = sessionStorage.getItem("sessionId");
        const tasteVectorStr = sessionStorage.getItem("tasteVector");

        if (!sessionId || !tasteVectorStr) {
          console.error("Missing session data");
          setError("Session expired. Please start the quiz again.");
          setTimeout(() => router.push("/"), 3000);
          clearInterval(timeInterval);
          return;
        }

        const tasteVector = JSON.parse(tasteVectorStr);
        console.log("Starting video generation for session:", sessionId);

        // Import the video service dynamically
        const { startVideoGeneration, pollForVideo } = await import("@/lib/api/videoService");

        setStatusMessage("Initiating pipeline...");
        setProgress(5);

        // Start video generation (triggers backend pipeline)
        setStatusMessage("🎬 Connecting to AI services...");
        const result = await startVideoGeneration(sessionId, tasteVector);

        if (!result.success) {
          clearInterval(timeInterval);
          throw new Error(result.error || "Failed to start video generation");
        }

        setStatusMessage("✅ Pipeline started! Getting movie recommendations...");
        setProgress(10);
        setCurrentPhaseIndex(0);
        setEstimatedTimeRemaining("15-20 minutes");

        // Poll for completion
        const videoStatus = await pollForVideo(sessionId, {
          maxAttempts: 360, // 30 minutes at 5 second intervals (increased from 15 min)
          intervalMs: 5000,
          onProgress: (status) => {
            console.log("Video status:", status);

            // Update progress based on status
            if (status.progress !== undefined) {
              setProgress(status.progress);

              // Update phase based on progress with detailed messages
              if (status.progress < 25) {
                setCurrentPhaseIndex(0);
                setStatusMessage("🔍 Analyzing your taste preferences and finding matching movies...");
                setEstimatedTimeRemaining("12-18 minutes");
              } else if (status.progress < 50) {
                setCurrentPhaseIndex(1);
                setStatusMessage("✍️ AI is writing your personalized movie concept...");
                setEstimatedTimeRemaining("10-15 minutes");
              } else if (status.progress < 90) {
                setCurrentPhaseIndex(2);
                setStatusMessage("🎥 Generating AI video scenes (this is the longest step - please be patient)...");
                setEstimatedTimeRemaining("8-12 minutes");
              } else {
                setCurrentPhaseIndex(3);
                setStatusMessage("☁️ Finalizing and uploading to cloud storage...");
                setEstimatedTimeRemaining("1-2 minutes");
              }
            } else {
              // Estimate progress based on time
              const elapsed = Math.floor((Date.now() - startTime) / 1000);
              let estimatedProgress = 50; // Default to middle of video generation

              if (elapsed < 60) {
                estimatedProgress = Math.min(10 + elapsed / 2, 25);
                setCurrentPhaseIndex(0);
                setStatusMessage("🔍 Getting movie recommendations from your taste profile...");
              } else if (elapsed < 180) {
                estimatedProgress = Math.min(25 + (elapsed - 60) / 5, 50);
                setCurrentPhaseIndex(1);
                setStatusMessage("✍️ AI is crafting your unique movie story...");
              } else if (elapsed < 900) {
                estimatedProgress = Math.min(50 + (elapsed - 180) / 20, 85);
                setCurrentPhaseIndex(2);
                setStatusMessage(`🎥 Generating video with AI (${Math.floor(elapsed / 60)} min elapsed - hang tight!)...`);
              } else {
                estimatedProgress = Math.min(85 + (elapsed - 900) / 30, 95);
                setCurrentPhaseIndex(3);
                setStatusMessage("☁️ Almost done! Uploading your trailer...");
              }

              setProgress(estimatedProgress);
            }
          },
        });

        // Video is ready!
        if (videoStatus.videoUrl) {
          clearInterval(timeInterval);
          setProgress(100);
          setCurrentPhaseIndex(3);
          setStatusMessage("🎉 Success! Your trailer is ready!");

          // Store video URL for result page
          sessionStorage.setItem("videoUrl", videoStatus.videoUrl);
          if (videoStatus.gcsUrl) {
            sessionStorage.setItem("gcsUrl", videoStatus.gcsUrl);
          }

          // Navigate to result page
          setTimeout(() => {
            router.push("/result");
          }, 1500);
        }
      } catch (error) {
        clearInterval(timeInterval);
        console.error("Video generation error:", error);
        setError(
          error instanceof Error
            ? error.message
            : "Video generation failed. Please try again."
        );
        setStatusMessage("An error occurred");
      }
    };

    startGeneration();

    return () => {
      clearInterval(timeInterval);
    };
  }, [router]);

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
          {/* Error Display */}
          {error && (
            <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-4 text-center">
              <p className="text-red-200 font-medium">❌ {error}</p>
            </div>
          )}

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

              {/* Status Message */}
              {statusMessage && (
                <p className="text-white/50 text-sm italic">
                  {statusMessage}
                </p>
              )}
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
                      duration: 0.5,
                      ease: "easeInOut",
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
                transition={{ duration: 0.5, ease: "easeInOut" }}
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

                  {isCurrent && !error && (
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

          {/* Info Message with Elapsed Time */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="text-center space-y-3"
          >
            {/* Elapsed Time */}
            <div className="glass-strong px-6 py-4 rounded-xl inline-block">
              <div className="flex items-center gap-4">
                <div className="text-left">
                  <p className="text-white/50 text-xs uppercase tracking-wide">Elapsed Time</p>
                  <p className="text-white text-2xl font-bold font-mono">
                    {Math.floor(elapsedTime / 60)}:{(elapsedTime % 60).toString().padStart(2, '0')}
                  </p>
                </div>
                <div className="h-12 w-px bg-white/20" />
                <div className="text-left">
                  <p className="text-white/50 text-xs uppercase tracking-wide">Est. Remaining</p>
                  <p className="text-white text-lg font-medium">
                    {estimatedTimeRemaining}
                  </p>
                </div>
              </div>
            </div>

            {/* Message */}
            <p className="text-white/50 text-sm italic">
              ✨ Using AI to create your personalized trailer...
            </p>
            {progress < 50 && (
              <p className="text-white/40 text-xs">
                This takes 15-20 minutes. Feel free to grab a coffee! ☕
              </p>
            )}
            {progress >= 50 && progress < 85 && (
              <p className="text-white/40 text-xs">
                🎥 Video generation is the slowest step - thank you for your patience!
              </p>
            )}
          </motion.div>
        </motion.div>
      </div>
    </main>
  );
}
