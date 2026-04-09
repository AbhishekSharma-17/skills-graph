# Shape & Discovery

## Philosophy

Most AI-generated UIs fail not because of bad code, but because of skipped thinking. They jump to "here's a card grid" without asking "what is the user trying to accomplish?" Shape inverts that: understand deeply first, so implementation is precise.

This process produces a **design brief** — a structured artifact that guides implementation through discovery, not guesswork. The brief can be handed off to any implementation process and ensures that code serves a clear design intent.

**Scope**: Design planning only. This process does not write code. It produces the thinking that makes code good.

---

## When to Shape

- **Always for new features.** Any feature that involves new UI surface area benefits from shaping. The 20 minutes spent in discovery saves hours of rework.
- **Always for redesigns.** If existing UI is being rethought, shape first to understand why the current version fails and what the new version must accomplish.
- **Optional for small tweaks.** Bug fixes, copy changes, and minor adjustments to existing patterns can skip shaping if the intent is already clear.
- **Required if you are uncertain.** If you are not sure whether to shape, shape. The cost of unnecessary shaping is low. The cost of skipping it when it was needed is high.

---

## Phase 1: Discovery Interview

Do not write any code or make any design decisions during this phase. Your only job is to understand the feature deeply enough to make excellent design decisions later.

Ask these questions in conversation, adapting based on answers. Have a natural dialogue — do not dump all questions at once. Ask the user directly to clarify what you cannot infer.

### Purpose & Context

- What is this feature for? What problem does it solve?
- Who specifically will use it? (Not "users" — be specific: role, context, frequency)
- What does success look like? How will you know this feature is working?
- What is the user's state of mind when they reach this feature? (Rushed? Exploring? Anxious? Focused?)

### Content & Data

- What content or data does this feature display or collect?
- What are the realistic ranges? (Minimum, typical, maximum — e.g., 0 items, 5 items, 500 items)
- What are the edge cases? (Empty state, error state, first-time use, power user)
- Is any content dynamic? What changes and how often?

### Design Goals

- What is the single most important thing a user should do or understand here?
- What should this feel like? (Fast/efficient? Calm/trustworthy? Fun/playful? Premium/refined?)
- Are there existing patterns in the product this should be consistent with?
- Are there specific examples (inside or outside the product) that capture what you are going for?

### Constraints

- Are there technical constraints? (Framework, performance budget, browser support)
- Are there content constraints? (Localization, dynamic text length, user-generated content)
- Mobile/responsive requirements?
- Accessibility requirements beyond WCAG AA?

### Anti-Goals

- What should this NOT be? What would be a wrong direction?
- What is the biggest risk of getting this wrong?

---

## Phase 2: Design Brief

After the interview, synthesize everything into a structured design brief. Present it to the user for confirmation before considering shaping complete.

### Brief Structure

**1. Feature Summary** (2-3 sentences)

What this is, who it is for, and what it needs to accomplish. Concise enough to orient anyone picking up the brief.

**2. Primary User Action**

The single most important thing a user should do or understand on this surface. Everything else is secondary to this action. If the design makes this action harder, the design is wrong.

**3. Design Direction**

How this should feel. What aesthetic approach fits. Reference the project's design context and explain how this feature should express it. Include specific mood words and, if helpful, reference points.

**4. Layout Strategy**

High-level spatial approach: what gets emphasis, what is secondary, how information flows. Describe the visual hierarchy and rhythm, not specific CSS. Think in terms of regions, focal points, and reading order.

**5. Key States**

List every state the feature needs:

- **Default**: The normal, happy-path view
- **Empty**: No data yet — what does the user see and what should they do?
- **Loading**: Data is being fetched — how does the user know?
- **Error**: Something went wrong — what does the user need to understand and do?
- **Success**: An action completed — what confirmation does the user get?
- **Edge cases**: Overflow, first-run, power-user scenarios, permission states

For each state, note what the user needs to see and feel.

**6. Interaction Model**

How users interact with this feature. What happens on click, hover, scroll? What feedback do they get? What is the flow from entry to completion? Note any progressive disclosure — what is revealed and when.

**7. Content Requirements**

What copy, labels, empty state messages, error messages, and microcopy are needed. Note any dynamic content and its realistic ranges. Flag content that needs to be written vs. content that already exists.

**8. Recommended References**

Based on the brief, list which reference files would be most valuable during implementation:

- `spatial-design` for complex layouts
- `typography` for type-heavy features
- `motion-design` for animated features
- `interaction-design` for form-heavy features
- `color-and-contrast` for themed or color-intensive features
- `responsive-design` for multi-viewport features
- `ux-writing` for copy-heavy features

**9. Open Questions**

Anything unresolved that the implementer should resolve during build. Be explicit about what you do not know — hidden assumptions cause more rework than open questions.

---

## After Shaping

Get explicit confirmation of the brief from the user before finishing. If the user disagrees with any part, revisit the relevant discovery questions.

Once confirmed, the brief is complete. It serves as the blueprint for implementation — every design decision during build should trace back to something in the brief. If a question arises during implementation that the brief does not answer, that is a sign the brief needs updating, not that the question should be guessed at.
