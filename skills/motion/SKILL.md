---
name: motion
description: "Motion (formerly Framer Motion) — production-grade animation library for React with springs, gestures, layout animations, and scroll effects. MANDATORY TRIGGERS: motion, framer motion, framer-motion, motion/react, useAnimate, AnimatePresence, layout animation. Also trigger when building React animations, gesture interactions, scroll-linked effects, page transitions, or animated UI components. When in doubt about whether to use this skill for React animation tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["react", "animation", "gestures", "layout", "scroll", "springs", "ui", "framer-motion", "typescript"]
---

# Motion (React Animation Library)

> Version tracked: 12.x (v12.38.0) | Source: https://motion.dev

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview](references/00-overview.md) | Starting with Motion, installation, core concepts, migration from Framer Motion |
| [01-motion-component](references/01-motion-component.md) | Using motion components, props, custom components, SSR |
| [02-animation-fundamentals](references/02-animation-fundamentals.md) | animate/initial props, keyframes, variants, CSS variables |
| [03-transitions](references/03-transitions.md) | Spring, tween, inertia, easing, duration, orchestration |
| [04-gestures](references/04-gestures.md) | Hover, tap, drag, pan, focus, inView gestures |
| [05-scroll-animations](references/05-scroll-animations.md) | useScroll, whileInView, parallax, scroll-linked effects |
| [06-layout-animations](references/06-layout-animations.md) | layout prop, layoutId, shared transitions, LayoutGroup |
| [07-animate-presence](references/07-animate-presence.md) | Exit animations, mode prop, enter/exit orchestration |
| [08-motion-values](references/08-motion-values.md) | useMotionValue, useTransform, useSpring, useVelocity |
| [09-hooks-and-utilities](references/09-hooks-and-utilities.md) | useAnimate, useInView, useReducedMotion, MotionConfig |
| [10-svg-and-path](references/10-svg-and-path.md) | SVG animation, pathLength, morphing, line drawing |
| [11-performance](references/11-performance.md) | GPU acceleration, will-change, reduce re-renders, bundle size |
| [12-patterns-and-recipes](references/12-patterns-and-recipes.md) | Common UI patterns: modals, tabs, toasts, page transitions |

## Installation

```bash
npm install motion
# or
pnpm add motion
```

```tsx
import { motion } from "motion/react"
```

## Quick Reference

- Docs: https://motion.dev/docs
- GitHub: https://github.com/motiondivision/motion
- npm: https://www.npmjs.com/package/motion
- Examples: https://motion.dev/examples
- Migration from Framer Motion: change import from `"framer-motion"` to `"motion/react"`
