# 🎬 TarAIntino - Interactive Movie Quiz Demo

An ultra-premium, mobile-first interactive quiz demo showcasing the TarAIntino AI movie generation concept for AC215 at Harvard.

## ✨ Features

### Interactive Quiz Experience
- **Tinder-style swipe gestures** - Drag cards left/right/up/down
  - Swipe **right** → Like (green glow)
  - Swipe **left** → Dislike (red glow)
  - Pull **up** → Love it! (gold explosion)
  - Pull **down** → Hate it (dark effect)
- **3D card stack** with perspective depth
- **Undo functionality** to go back to previous movies
- **Dynamic question count** (randomly 5-10 questions per session)
- **Progress ring** showing quiz completion

### Loading Animation
- **Multi-phase progress animation** (8 seconds total)
  - Phase 1: Analyzing taste (0-25%)
  - Phase 2: Crafting story (25-50%)
  - Phase 3: Generating scenes (50-75%)
  - Phase 4: Final touches (75-100%)
- **Circular and linear progress bars** with gradient animations
- **Phase checklist** with animated checkmarks
- **Rotating icons** and shimmer effects

### Result Page
- **Confetti celebration** on load (using js-confetti)
- **Mock video player** with custom controls
  - Play/pause, volume, progress bar
  - Film strip border decoration
  - Hover interactions
- **Generated movie title** based on preferences
- **Taste profile visualization** with:
  - Tag cloud with intensity scaling
  - Radar chart showing top 6 preferences
  - Animated data points
- **Download button** with shine animation
- **Share and Create Another** actions

### Premium Design
- **Cinematic color palette** (blacks, golds, neon accents)
- **Glass morphism** effects throughout
- **Animated gradient backgrounds** with morphing blobs
- **Film grain texture** overlays
- **Smooth page transitions** using Framer Motion
- **Responsive design** (mobile-first, works on all devices)

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ installed
- npm

### Quick Start

```bash
# Start development server
npm run dev
```

Open **http://localhost:3000** in your browser

## 📱 How to Use

1. **Open the app** - Quiz starts immediately (no landing page)
2. **Swipe through movies:**
   - Drag right if you like it
   - Drag left if you dislike it
   - Pull up if you love it
   - Pull down if you hate it
3. **Complete 5-10 questions** (random each time)
4. **Watch the loading animation** (8 seconds)
5. **See your results:**
   - Mock video player with your "generated" trailer
   - Your taste profile visualization
   - Download button (triggers confetti!)

## 🎨 Tech Stack

- **Next.js 15** (App Router, TypeScript)
- **Tailwind CSS** (v4 with custom design system)
- **Framer Motion** - Smooth animations and gestures
- **@use-gesture/react** - Advanced swipe/drag handling
- **GSAP** - Timeline animations
- **React Spring** - Spring physics
- **js-confetti** - Celebration effects
- **Lucide React** - Icon system

## 📂 Project Structure

```
app/
├── page.tsx                    # Quiz page (main entry)
├── generating/page.tsx         # Loading animation
├── result/page.tsx            # Result with video player
├── layout.tsx                 # Root layout
└── globals.css                # Custom styles

components/
├── quiz/
│   ├── CardStack.tsx          # 3D card stack manager
│   ├── SwipeCard.tsx          # Individual swipeable card
│   └── ProgressRing.tsx       # Circular progress indicator
├── result/
│   ├── VideoPlayer.tsx        # Mock video player
│   └── TasteProfile.tsx       # Taste visualization
└── effects/
    └── GradientBackground.tsx # Animated gradient

lib/
├── data/
│   └── movies.ts              # 45 mock movies with metadata
└── utils/
    └── cn.ts                  # Utility function
```

## 🎯 Mock Data

- **45 diverse movies** including:
  - Blade Runner, Inception, Pulp Fiction, Parasite
  - The Grand Budapest Hotel, Mad Max, Amélie
  - Drive, Her, Interstellar, Moonlight
  - And many more across all genres!

- **Tag system** with 30+ cinematic attributes:
  - Visual: noir, vibrant, gritty, whimsical
  - Mood: dark, uplifting, melancholic, thrilling
  - Themes: dystopian, romantic, philosophical, violent
  - Genre: sci-fi, horror, action, drama

## 🎓 AC215 Project Context

This is a **mock front-end demo** for the TarAIntino project - an AI movie generation infrastructure. The full system includes:
- Adaptive quiz engine (this demo)
- Tag Genome-based taste vector calculation
- LLM-based story generation
- AI video generation APIs
- Orchestrated workflow system

This demo showcases the **user experience** and **interaction design** without requiring backend infrastructure.

## 🎨 Design Philosophy

- **Premium over quick** - Beautiful animations and smooth UX
- **Mobile-first** - Optimized for touch gestures
- **Cinematic aesthetic** - Deep blacks, gold accents, film grain
- **Delightful interactions** - Every action has visual feedback

## 📸 Key Interactions

1. **Card Swipe Physics** - Spring animations with momentum
2. **3D Stack Effect** - Cards scale and blur with depth
3. **Progress Animations** - Smooth percentage counting
4. **Confetti Bursts** - Multiple celebrations on result page
5. **Gradient Morphing** - Animated background blobs
6. **Glass Morphism** - Backdrop blur throughout
7. **Hover Effects** - Magnetic buttons, scale transforms

## 🔧 Development Commands

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

## 📝 Notes

- All data is **mock** - no real API calls or video generation
- Quiz results stored in **sessionStorage** (page refresh clears)
- Random 5-10 questions per session
- Generated movie title is randomly selected
- Download button shows alert (no actual file)
- Optimized for modern browsers (Chrome, Safari, Firefox, Edge)

## 🎉 Demo Highlights

Perfect for presenting:
- ✅ Ultra-interactive Tinder-style swipe mechanics
- ✅ Premium cinematic design system
- ✅ Multi-phase loading with percentage progress
- ✅ Confetti celebration effects
- ✅ Mock video player with custom controls
- ✅ Taste profile visualization
- ✅ Mobile-responsive throughout
- ✅ Smooth animations at 60fps

---

**Built for AC215 - Advanced Practical Data Science**
Harvard University | 2025

🎬 Made with Next.js, Framer Motion, and lots of ✨
