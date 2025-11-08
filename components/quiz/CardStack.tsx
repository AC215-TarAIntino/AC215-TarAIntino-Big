"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SwipeCard } from "./SwipeCard";

interface CardStackProps {
  tags: string[];
  onRating: (tag: string, rating: number) => void;
  onComplete: () => void;
}

export function CardStack({ tags, onRating, onComplete }: CardStackProps) {
  const [cards, setCards] = useState(tags);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleRating = (rating: number) => {
    if (cards.length === 0 || isProcessing) return;

    setIsProcessing(true);
    const currentTag = cards[0];
    onRating(currentTag, rating);

    // Remove the card with animation
    setTimeout(() => {
      const newCards = cards.slice(1);
      setCards(newCards);
      setIsProcessing(false);

      if (newCards.length === 0) {
        // All tags rated, quiz complete
        setTimeout(onComplete, 300);
      }
    }, 300);
  };

  // Show top 3 cards for depth effect
  const visibleCards = cards.slice(0, 3);

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <div className="relative w-full max-w-sm aspect-[2/3]" style={{ perspective: "1200px" }}>
        <AnimatePresence mode="popLayout">
          {visibleCards.map((tag, index) => {
            const isTop = index === 0;
            const zIndex = visibleCards.length - index;
            const scale = 1 - index * 0.04;
            const yOffset = index * 12;
            const opacity = 1 - index * 0.15;

            return (
              <motion.div
                key={tag}
                initial={{
                  scale: 0.9,
                  opacity: 0,
                  y: 30,
                }}
                animate={{
                  scale: isTop ? 1 : scale,
                  y: yOffset,
                  opacity: opacity,
                  rotateX: index * 1.5,
                }}
                exit={{
                  scale: 1.05,
                  opacity: 0,
                  transition: {
                    duration: 0.25,
                    ease: "easeOut",
                  },
                }}
                transition={{
                  type: "spring",
                  stiffness: 300,
                  damping: 25,
                }}
                style={{
                  zIndex,
                  transformStyle: "preserve-3d",
                }}
                className="absolute inset-0"
              >
                {isTop ? (
                  <SwipeCard
                    tag={tag}
                    onRating={handleRating}
                    index={index}
                    disabled={isProcessing}
                  />
                ) : (
                  // Non-interactive cards behind showing tag preview
                  <div className="w-full h-full rounded-3xl overflow-hidden glass-strong shadow-2xl pointer-events-none flex items-center justify-center">
                    <p className="text-white/30 text-2xl font-bold px-8 text-center capitalize">
                      {tag}
                    </p>
                  </div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>

        {/* Empty state */}
        {cards.length === 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <div className="glass-strong rounded-3xl p-12 text-center">
              <div className="text-6xl mb-4">✨</div>
              <h3 className="text-2xl font-bold text-white mb-2">
                All Set!
              </h3>
              <p className="text-white/70">
                Creating your personalized recommendations...
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
