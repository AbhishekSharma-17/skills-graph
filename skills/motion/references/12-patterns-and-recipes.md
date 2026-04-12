# Patterns and Recipes

> Source: https://motion.dev/examples | Version: 12.x

## Table of Contents
- [Page Transitions](#page-transitions)
- [Modal Dialog](#modal-dialog)
- [Tabs with Indicator](#tabs-with-indicator)
- [Toast Notifications](#toast-notifications)
- [Staggered List](#staggered-list)
- [Accordion](#accordion)
- [Animated Counter](#animated-counter)
- [Card Hover Effect](#card-hover-effect)
- [Skeleton Loader](#skeleton-loader)
- [Animated Toggle](#animated-toggle)
- [Scroll Progress Bar](#scroll-progress-bar)
- [Floating Action Button](#floating-action-button)

## Page Transitions

```tsx
import { AnimatePresence, motion } from "motion/react"

function PageTransition({ children, pathname }) {
  return (
    <AnimatePresence mode="wait">
      <motion.main
        key={pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.25, ease: "easeInOut" }}
      >
        {children}
      </motion.main>
    </AnimatePresence>
  )
}

// Next.js App Router usage
function Layout({ children }) {
  const pathname = usePathname()
  return <PageTransition pathname={pathname}>{children}</PageTransition>
}
```

## Modal Dialog

```tsx
function Modal({ isOpen, onClose, children }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          key="modal-wrapper"
          style={{
            position: "fixed",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 50,
          }}
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            style={{
              position: "absolute",
              inset: 0,
              backgroundColor: "rgba(0, 0, 0, 0.5)",
            }}
          />
          {/* Content */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", duration: 0.5, bounce: 0.2 }}
            style={{
              position: "relative",
              backgroundColor: "#fff",
              borderRadius: 12,
              padding: 24,
              maxWidth: 480,
              width: "90%",
              boxShadow: "0 25px 50px rgba(0, 0, 0, 0.25)",
            }}
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
```

## Tabs with Indicator

```tsx
function Tabs({ tabs, activeTab, onTabChange }) {
  return (
    <div style={{ display: "flex", gap: 4, position: "relative" }}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          style={{
            position: "relative",
            padding: "8px 16px",
            background: "none",
            border: "none",
            cursor: "pointer",
            color: activeTab === tab.id ? "#1e40af" : "#6b7280",
            fontWeight: activeTab === tab.id ? 600 : 400,
          }}
        >
          {tab.label}
          {activeTab === tab.id && (
            <motion.div
              layoutId="tab-indicator"
              style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                right: 0,
                height: 2,
                backgroundColor: "#3b82f6",
                borderRadius: 1,
              }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            />
          )}
        </button>
      ))}
    </div>
  )
}
```

## Toast Notifications

```tsx
function ToastStack({ toasts, onDismiss }) {
  return (
    <div style={{
      position: "fixed",
      bottom: 16,
      right: 16,
      display: "flex",
      flexDirection: "column",
      gap: 8,
      zIndex: 100,
    }}>
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            layout
            initial={{ opacity: 0, x: 100, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 100, scale: 0.95 }}
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            onDragEnd={(_, info) => {
              if (info.offset.x > 80) onDismiss(toast.id)
            }}
            style={{
              padding: "12px 16px",
              backgroundColor: "#fff",
              borderRadius: 8,
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
              minWidth: 280,
            }}
          >
            {toast.message}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
```

## Staggered List

```tsx
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring", stiffness: 300, damping: 24 },
  },
}

function StaggeredList({ items }) {
  return (
    <motion.ul
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      style={{ listStyle: "none", padding: 0 }}
    >
      {items.map((item) => (
        <motion.li
          key={item.id}
          variants={itemVariants}
          style={{ padding: "12px 0", borderBottom: "1px solid #e5e7eb" }}
        >
          {item.label}
        </motion.li>
      ))}
    </motion.ul>
  )
}
```

## Accordion

```tsx
function Accordion({ items }) {
  const [openId, setOpenId] = useState(null)

  return (
    <div>
      {items.map((item) => (
        <div key={item.id}>
          <motion.button
            onClick={() => setOpenId(openId === item.id ? null : item.id)}
            style={{ width: "100%", textAlign: "left", padding: "12px 0" }}
            whileHover={{ color: "#3b82f6" }}
          >
            {item.title}
            <motion.span
              animate={{ rotate: openId === item.id ? 180 : 0 }}
              style={{ float: "right" }}
            >
              ▼
            </motion.span>
          </motion.button>
          <AnimatePresence>
            {openId === item.id && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                style={{ overflow: "hidden" }}
              >
                <div style={{ padding: "8px 0 16px" }}>
                  {item.content}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  )
}
```

## Animated Counter

```tsx
function AnimatedCounter({ value }) {
  const motionValue = useMotionValue(0)
  const rounded = useTransform(motionValue, (v) => Math.round(v))

  useEffect(() => {
    const controls = animate(motionValue, value, {
      duration: 1.5,
      ease: "easeOut",
    })
    return controls.stop
  }, [value])

  return <motion.span>{rounded}</motion.span>
}
```

## Card Hover Effect

```tsx
function HoverCard({ title, description, image }) {
  return (
    <motion.article
      whileHover="hover"
      initial="rest"
      style={{
        position: "relative",
        overflow: "hidden",
        borderRadius: 12,
        cursor: "pointer",
      }}
    >
      <motion.img
        src={image}
        variants={{
          rest: { scale: 1 },
          hover: { scale: 1.05 },
        }}
        transition={{ duration: 0.4 }}
        style={{ width: "100%", display: "block" }}
      />
      <motion.div
        variants={{
          rest: { y: "100%" },
          hover: { y: 0 },
        }}
        transition={{ type: "spring", stiffness: 300, damping: 25 }}
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          padding: 16,
          background: "linear-gradient(transparent, rgba(0,0,0,0.8))",
          color: "#fff",
        }}
      >
        <h3>{title}</h3>
        <p>{description}</p>
      </motion.div>
    </motion.article>
  )
}
```

## Skeleton Loader

```tsx
function Skeleton({ width = "100%", height = 20 }) {
  return (
    <motion.div
      style={{
        width,
        height,
        borderRadius: 4,
        backgroundColor: "#e5e7eb",
      }}
      animate={{ opacity: [0.5, 1, 0.5] }}
      transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
    />
  )
}
```

## Animated Toggle

```tsx
function Toggle({ isOn, onToggle }) {
  return (
    <motion.button
      onClick={onToggle}
      animate={{ backgroundColor: isOn ? "#22c55e" : "#d1d5db" }}
      style={{
        width: 56,
        height: 32,
        borderRadius: 16,
        border: "none",
        cursor: "pointer",
        display: "flex",
        alignItems: isOn ? "center" : "center",
        justifyContent: isOn ? "flex-end" : "flex-start",
        padding: 3,
      }}
    >
      <motion.div
        layout
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
        style={{
          width: 26,
          height: 26,
          borderRadius: 13,
          backgroundColor: "#fff",
          boxShadow: "0 1px 3px rgba(0, 0, 0, 0.2)",
        }}
      />
    </motion.button>
  )
}
```

## Scroll Progress Bar

```tsx
function ScrollProgress() {
  const { scrollYProgress } = useScroll()

  return (
    <motion.div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: 3,
        backgroundColor: "#3b82f6",
        transformOrigin: "left",
        scaleX: scrollYProgress,
        zIndex: 50,
      }}
    />
  )
}
```

## Floating Action Button

```tsx
function FAB({ actions }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div style={{ position: "fixed", bottom: 24, right: 24 }}>
      <AnimatePresence>
        {isOpen && actions.map((action, i) => (
          <motion.button
            key={action.id}
            initial={{ opacity: 0, y: 20, scale: 0.8 }}
            animate={{ opacity: 1, y: -(i + 1) * 56, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.8 }}
            transition={{ delay: i * 0.05 }}
            onClick={action.onClick}
            style={{
              position: "absolute",
              bottom: 0,
              right: 0,
              width: 48,
              height: 48,
              borderRadius: 24,
              border: "none",
              backgroundColor: "#fff",
              boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
              cursor: "pointer",
            }}
          >
            {action.icon}
          </motion.button>
        ))}
      </AnimatePresence>

      <motion.button
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsOpen(!isOpen)}
        animate={{ rotate: isOpen ? 45 : 0 }}
        style={{
          position: "relative",
          width: 56,
          height: 56,
          borderRadius: 28,
          border: "none",
          backgroundColor: "#3b82f6",
          color: "#fff",
          fontSize: 24,
          cursor: "pointer",
          boxShadow: "0 4px 12px rgba(59, 130, 246, 0.4)",
          zIndex: 1,
        }}
      >
        +
      </motion.button>
    </div>
  )
}
```

## Related
- [07-animate-presence](07-animate-presence.md) — Exit animation patterns
- [06-layout-animations](06-layout-animations.md) — Layout transition patterns
- [04-gestures](04-gestures.md) — Gesture interaction patterns
