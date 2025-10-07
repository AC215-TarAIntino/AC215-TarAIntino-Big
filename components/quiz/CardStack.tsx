"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SwipeCard } from "./SwipeCard";
import { Movie } from "@/lib/data/movies";

interface CardStackProps {
  movies: Movie[];
  onSwipe: (movie: Movie, direction: "left" | "right" | "up" | "down") => void;
  onComplete: () => void;
}

export function CardStack({ movies, onSwipe, onComplete }: CardStackProps) {
  const [cards, setCards] = useState(movies);
  const [removedCards, setRemovedCards] = useState<number[]>([]);

  const handleSwipe = (direction: "left" | "right" | "up" | "down") => {
    if (cards.length === 0) return;

    const currentCard = cards[0];
    onSwipe(currentCard, direction);

    // Remove the card with animation
    setRemovedCards([...removedCards, currentCard.id]);

    setTimeout(() => {
      const newCards = cards.slice(1);
      setCards(newCards);

      if (newCards.length === 0) {
        // All cards swiped, quiz complete
        setTimeout(onComplete, 300);
      }
    }, 300);
  };

  // Show top 3 cards for depth effect
  const visibleCards = cards.slice(0, 3);

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <div className="relative w-full max-w-md aspect-[3/4]" style={{ perspective: "1500px" }}>
        <AnimatePresence>
          {visibleCards.map((movie, index) => {
            const isTop = index === 0;
            const zIndex = visibleCards.length - index;
            const scale = 1 - index * 0.05;
            const yOffset = index * 10;
            const opacity = 1 - index * 0.2;

            return (
              <motion.div
                key={movie.id}
                initial={{
                  scale: 0.8,
                  opacity: 0,
                  y: 50,
                }}
                animate={{
                  scale: isTop ? 1 : scale,
                  y: yOffset,
                  opacity: opacity,
                  rotateX: index * 2,
                }}
                exit={{
                  scale: 1.1,
                  opacity: 0,
                  transition: { duration: 0.3 },
                }}
                transition={{
                  type: "spring",
                  stiffness: 260,
                  damping: 20,
                }}
                style={{
                  zIndex,
                  transformStyle: "preserve-3d",
                }}
                className="absolute inset-0"
              >
                {isTop ? (
                  <SwipeCard
                    movie={movie}
                    onSwipe={handleSwipe}
                    index={index}
                  />
                ) : (
                  // Non-interactive cards behind
                  <div className="w-full h-full rounded-3xl overflow-hidden glass-strong shadow-2xl pointer-events-none">
                    <div
                      className="absolute inset-0 bg-cover bg-center"
                      style={{
                        backgroundImage: `url(${movie.poster})`,
                        filter: "blur(2px) brightness(0.7)",
                      }}
                    />
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
              <div className="text-6xl mb-4">🎬</div>
              <h3 className="text-2xl font-bold text-white mb-2">
                All Done!
              </h3>
              <p className="text-white/70">
                Generating your personalized trailer...
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
