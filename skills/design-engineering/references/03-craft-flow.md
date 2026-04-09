# Craft Flow

Build a feature with high design quality through a structured process: shape the design, load the right references, then build and iterate visually until the result is delightful.

---

## The 5-Step Process

### Step 1: Shape

Run the shape and discovery process (see `02-shape-discovery.md`), passing along whatever feature description the user provided.

Wait for the design brief to be fully confirmed before proceeding. The brief is your blueprint — every implementation decision should trace back to it.

If the user has already completed shaping and has a confirmed design brief, skip this step and use the existing brief.

### Step 2: Load References

Based on the design brief's "Recommended References" section, consult the relevant reference files. At minimum, always consult:

- **spatial-design** — for layout and spacing
- **typography** — for type hierarchy

Then add references based on the brief's needs:

| Need | Reference to Load |
|------|-------------------|
| Complex interactions or forms | interaction-design |
| Animation or transitions | motion-design |
| Color-heavy or themed | color-and-contrast |
| Responsive requirements | responsive-design |
| Heavy on copy, labels, or errors | ux-writing |

### Step 3: Build

Implement the feature following the design brief. Work in this specific order — each step builds on the previous one:

1. **Structure first.** Semantic HTML for the primary state. No styling yet. Get the DOM right before anything visual.

2. **Layout and spacing.** Establish the spatial rhythm and visual hierarchy. Use the spacing scale, set up the grid, define regions.

3. **Typography and color.** Apply the type scale and color system. Set hierarchy through size, weight, and color contrast.

4. **Interactive states.** Hover, focus, active, disabled. Every interactive surface should feel intentional and responsive.

5. **Edge case states.** Empty, loading, error, overflow, first-run. Each state should feel designed, not like an afterthought.

6. **Motion.** Purposeful transitions and animations where appropriate. Entrances, exits, state changes. No motion for motion's sake.

7. **Responsive.** Adapt for different viewports. Do not just shrink — redesign for the context. Mobile users have different needs, not just smaller screens.

**During build:**

- Test with real (or realistic) data at every step, not placeholder text
- Check each state as you build it, not all at the end
- If you discover a design question the brief does not answer, stop and ask rather than guessing
- Every visual choice should trace back to something in the design brief

### Step 4: Visual Iteration

This step is critical. Do not stop after the first implementation pass.

Open the result in a browser. If browser automation tools are available, use them to navigate to the page and visually inspect the result. If not, ask the user to open it and provide feedback.

Iterate through these checks:

1. **Does it match the brief?** Compare the live result against every section of the design brief. Fix discrepancies.

2. **Does it pass the AI slop test?** If someone saw this and said "AI made this," would they believe it immediately? If yes, it needs more design intention. Check against the banned patterns list in `00-overview.md`.

3. **Check every state.** Navigate through empty, error, loading, and edge case states. Each one should feel intentional.

4. **Check responsive.** Resize the viewport. Does it adapt well or just shrink? Does it still serve the user at every breakpoint?

5. **Check the details.** Spacing consistency, type hierarchy clarity, color contrast, interactive feedback, motion timing. The bar is not "it works" — the bar is "this delights."

After each round of fixes, visually verify again. Repeat until you would be proud to show this to the user.

### Step 5: Present

Present the result to the user:

- Show the feature in its primary state
- Walk through the key states (empty, error, responsive)
- Explain design decisions that connect back to the design brief
- Ask: "What is working? What is not?"

Iterate based on feedback. Good design is rarely right on the first pass. The presentation step is not a hand-off — it is the beginning of a conversation that refines the work until it meets the bar.

---

## Reference Loading Guide

Quick reference for which files to load based on feature type:

| Feature Type | Always Load | Additionally Load |
|-------------|-------------|-------------------|
| Any feature | spatial-design, typography | — |
| Form or input-heavy | spatial-design, typography | interaction-design, ux-writing |
| Data dashboard | spatial-design, typography | color-and-contrast, responsive-design |
| Marketing/landing page | spatial-design, typography | motion-design, color-and-contrast, responsive-design |
| Animated feature | spatial-design, typography | motion-design |
| Multi-viewport feature | spatial-design, typography | responsive-design |
| Content/editorial | spatial-design, typography | ux-writing |
| Themed/branded | spatial-design, typography | color-and-contrast |
