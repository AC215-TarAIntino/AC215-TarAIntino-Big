# 🎬 TarAIntino - Interactive Movie Quiz Demo

An ultra-premium, mobile-first interactive quiz demo showcasing the TarAIntino AI movie generation concept for AC215 at Harvard.

## ✨ Features

### Interactive Quiz Experience
- **Rating-based tag quiz** - Rate movie tags from 1-10
  - 1 = Not at all interested
  - 10 = Absolutely must have
- **Single question view** with animated transitions
- **Bayesian-optimized questions** - Backend selects most informative tags
- **5 questions per session** for optimal taste vector calculation
- **Progress ring** showing quiz completion
- **Real-time API integration** with quiz-vector backend

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
# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Start development server
npm run dev
```

Open **http://localhost:3000** in your browser

### Environment Configuration

```bash
# For local development (quiz-vector running on host)
NEXT_PUBLIC_QUIZ_API_URL=http://localhost:8082

# For Docker deployment (using service name)
NEXT_PUBLIC_QUIZ_API_URL=http://quiz-service:8082
```

## 📱 How to Use

1. **Open the app** - Quiz initializes by connecting to backend
2. **Rate tags from 1-10:**
   - Backend returns one tag at a time
   - Select a rating based on preference
   - Click "Next Tag" to submit
3. **Complete 5 questions** (Bayesian-optimized selection)
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
│   ├── SwipeCard.tsx          # Rating card (1-10 scale)
│   └── ProgressRing.tsx       # Circular progress indicator
├── result/
│   ├── VideoPlayer.tsx        # Mock video player
│   └── TasteProfile.tsx       # Taste visualization
└── effects/
    └── GradientBackground.tsx # Animated gradient

lib/
├── api/
│   ├── types.ts               # TypeScript API types
│   └── quizService.ts         # Quiz-vector API client
├── data/
│   └── tags.ts                # Tag Genome data
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

- **Quiz connects to real backend** - quiz-vector service must be running
- Session ID stored in **sessionStorage** (page refresh clears)
- 5 questions per session (Bayesian-optimized by backend)
- Generating/result pages show **mock UI** while backend pipeline runs
- Generated movie title is randomly selected (placeholder)
- Download button shows alert (no actual file yet)
- Optimized for modern browsers (Chrome, Safari, Firefox, Edge)

## 🔌 API Integration

The quiz page connects to the quiz-vector backend:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/quiz/start` | POST | Start session, get first question |
| `/quiz/answer` | POST | Submit rating, get next question |
| `/health` | GET | Service health check |

The backend uses these ratings to build a taste vector via Bayesian optimization,
which is then used by the pipeline to generate personalized movie recommendations.

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
