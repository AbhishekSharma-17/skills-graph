# Cognitive Load

Cognitive load is the total mental effort required to use an interface. Overloaded users make mistakes, get frustrated, and leave. This reference helps identify and fix cognitive overload.

## Table of Contents

- [Three Types of Cognitive Load](#three-types-of-cognitive-load)
- [8-Item Checklist](#8-item-checklist)
- [The Working Memory Rule](#the-working-memory-rule)
- [8 Common Violations](#8-common-violations)

---

## Three Types of Cognitive Load

### Intrinsic Load -- The Task Itself

Complexity inherent to what the user is trying to do. You cannot eliminate this, but you can structure it.

**Management strategies**:
- Break complex tasks into discrete steps
- Provide scaffolding (templates, defaults, examples)
- Progressive disclosure -- show what is needed now, hide the rest
- Group related decisions together

### Extraneous Load -- Bad Design

Mental effort caused by poor design choices. **Eliminate this ruthlessly** -- it is pure waste.

**Common sources**:
- Confusing navigation that requires mental mapping
- Unclear labels that force users to guess meaning
- Visual clutter competing for attention
- Inconsistent patterns that prevent learning
- Unnecessary steps between user intent and result

### Germane Load -- Learning Effort

Mental effort spent building understanding. This is good cognitive load -- it leads to mastery.

**Support it by**:
- Progressive disclosure that reveals complexity gradually
- Consistent patterns that reward learning
- Feedback that confirms correct understanding
- Onboarding that teaches through action, not walls of text

---

## 8-Item Checklist

Evaluate the interface against these 8 items:

1. **Single focus**: Can the user complete their primary task without distraction from competing elements?
2. **Chunking**: Is information presented in digestible groups (4 items or fewer per group)?
3. **Grouping**: Are related items visually grouped together (proximity, borders, shared background)?
4. **Visual hierarchy**: Is it immediately clear what is most important on the screen?
5. **One thing at a time**: Can the user focus on a single decision before moving to the next?
6. **Minimal choices**: Are decisions simplified (4 or fewer visible options at any decision point)?
7. **Working memory**: Does the user need to remember information from a previous screen to act on the current one?
8. **Progressive disclosure**: Is complexity revealed only when the user needs it?

### Scoring

Count the failed items:

| Failures | Level | Action |
|----------|-------|--------|
| 0-1 | Low cognitive load | Good -- no immediate action needed |
| 2-3 | Moderate cognitive load | Address soon -- users are working harder than necessary |
| 4+ | High/critical cognitive load | Critical fix needed -- users will abandon or make errors |

---

## The Working Memory Rule

**Humans can hold 4 items or fewer in working memory at once** (Miller's Law revised by Cowan, 2001).

At any decision point, count the number of distinct options, actions, or pieces of information a user must simultaneously consider:

- **4 or fewer items**: Within working memory limits -- manageable
- **5-7 items**: Pushing the boundary -- consider grouping or progressive disclosure
- **8+ items**: Overloaded -- users will skip, misclick, or abandon

### Practical Applications

| Element | Limit | Rationale |
|---------|-------|-----------|
| Navigation menus | 5 or fewer top-level items | Group the rest under clear categories |
| Form sections | 4 or fewer fields visible per group | Add visual breaks between groups |
| Action buttons | 1 primary + 1-2 secondary | Group the rest in a menu or overflow |
| Dashboard widgets | 4 or fewer key metrics visible | Without scrolling; progressive disclosure for the rest |
| Pricing tiers | 3 or fewer options | More causes analysis paralysis |

---

## 8 Common Violations

### 1. The Wall of Options

**Problem**: Presenting 10+ choices at once with no hierarchy.

**Fix**: Group into categories, highlight the recommended option, use progressive disclosure to hide advanced options.

### 2. The Memory Bridge

**Problem**: User must remember information from step 1 to complete step 3.

**Fix**: Keep relevant context visible, or repeat it where it is needed. Never force users to hold data across screens.

### 3. The Hidden Navigation

**Problem**: User must build a mental map of where things are.

**Fix**: Always show current location with breadcrumbs, active states, and progress indicators. Make the structure visible.

### 4. The Jargon Barrier

**Problem**: Technical or domain language forces translation effort.

**Fix**: Use plain language. If domain terms are unavoidable, define them inline with tooltips or parenthetical explanations.

### 5. The Visual Noise Floor

**Problem**: Every element has the same visual weight -- nothing stands out.

**Fix**: Establish clear hierarchy: one primary element, 2-3 secondary, everything else muted. Use size, color, and weight to differentiate.

### 6. The Inconsistent Pattern

**Problem**: Similar actions work differently in different places.

**Fix**: Standardize interaction patterns. Same type of action = same type of UI. Users should not have to relearn behaviors.

### 7. The Multi-Task Demand

**Problem**: Interface requires processing multiple simultaneous inputs (reading + deciding + navigating).

**Fix**: Sequence the steps. Let the user do one thing at a time. Break compound screens into focused steps.

### 8. The Context Switch

**Problem**: User must jump between screens, tabs, or modals to gather information for a single decision.

**Fix**: Co-locate the information needed for each decision. Reduce back-and-forth. Use inline expansion or side panels instead of navigation.
