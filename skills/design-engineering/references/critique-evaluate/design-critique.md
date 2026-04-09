# Design Critique

Comprehensive design evaluation methodology combining human-like assessment with systematic detection to produce actionable, prioritized feedback.

## Table of Contents

- [Two-Assessment Methodology](#two-assessment-methodology)
  - [Assessment A: LLM Design Review](#assessment-a-llm-design-review)
  - [Assessment B: Automated Detection](#assessment-b-automated-detection)
- [Combined Report Format](#combined-report-format)
  - [Design Health Score](#design-health-score)
  - [Anti-Patterns Verdict](#anti-patterns-verdict)
  - [Overall Impression](#overall-impression)
  - [What's Working Well](#whats-working-well)
  - [Priority Issues](#priority-issues)
  - [Persona Red Flags](#persona-red-flags)
  - [Minor Observations](#minor-observations)
  - [Open Questions](#open-questions)
- [Post-Critique Flow](#post-critique-flow)

---

## Two-Assessment Methodology

Run two independent assessments. Neither should see the other's output to avoid bias. The assessments complement each other: the LLM review catches subjective design quality issues while automated detection catches systematic, measurable problems.

### Assessment A: LLM Design Review

Think like a design director. Read the source files (HTML, CSS, JS/TS) and visually inspect the live page if possible. Evaluate these dimensions:

#### Visual Hierarchy

- Eye flow: Where does the eye go first, second, third?
- Primary action clarity: Is the most important action immediately obvious?
- Composition: Balance, whitespace, rhythm across the layout
- Typography hierarchy: Are heading levels, weights, and sizes creating clear structure?

#### Information Architecture

- Structure: Is content organized logically?
- Grouping: Are related items together? Are unrelated items separated?
- Navigation: Can users find what they need? Is current location clear?
- Labeling: Are categories and sections named in user-friendly terms?

#### Emotional Resonance

- Brand match: Does the interface feel appropriate for the brand and audience?
- Emotional journey: What emotion does this evoke? Is that intentional?
- Peak-end rule: Is the most intense moment positive? Does the experience end well?
- Emotional valleys: Are high-stakes moments (payment, delete, commit) handled with care -- progress indicators, reassurance copy, undo options?

#### Cognitive Load

Consult `references/critique-evaluate/cognitive-load.md` for the full framework.

- Run the 8-item cognitive load checklist
- Report failure count: 0-1 = low (good), 2-3 = moderate, 4+ = critical
- Count visible options at each decision point. Flag if more than 4
- Check for progressive disclosure: is complexity revealed only when needed?

#### Overall Quality

- Discoverability: Are interactive elements obvious?
- Color: Purposeful use, cohesion, accessibility
- States and edge cases: Empty, loading, error, success states handled?
- Microcopy: Clarity, tone, helpfulness of UI text

#### AI Slop Detection (Critical)

Does this look like every other AI-generated interface? Check for:

- AI color palette (indigo-to-purple gradients, teal accents)
- Gradient text effects
- Dark glows and glassmorphism
- Hero metric layouts with big numbers
- Identical card grids with icons
- Generic system fonts or overused display fonts
- Excessive rounded corners and shadows
- Generic stock-photo aesthetic

**The test**: If someone said "AI made this," would you believe them immediately?

#### Output from Assessment A

Return structured findings covering:
- AI slop verdict (pass/fail with specific tells)
- Heuristic scores (10 heuristics, 0-4 each)
- Cognitive load assessment (checklist failures, decision point counts)
- What's working (2-3 specific items)
- Priority issues (3-5 with what/why/fix)
- Minor observations
- Provocative questions

### Assessment B: Automated Detection

Run systematic, deterministic checks that flag specific measurable patterns. This catches issues the subjective review might miss.

**What to scan for**:
- AI slop tells (25 specific patterns including color, layout, typography, and interaction anti-patterns)
- Component quality issues (missing states, incomplete interactions)
- Accessibility basics (contrast, labels, keyboard support)
- General design anti-patterns (gray-on-color, nested cards, bounce easing, redundant copy)

**Output from Assessment B**:
- Pattern matches with counts and file locations
- False positives noted
- Issues the LLM review may have missed

---

## Combined Report Format

Synthesize both assessments into a single report. Do not simply concatenate. Weave findings together, noting where the assessments agree, where automated detection caught issues the review missed, and where detector findings are false positives.

### Design Health Score

Consult `references/critique-evaluate/heuristics-scoring.md` for full scoring criteria.

Present Nielsen's 10 heuristics as a table:

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | ? | [specific finding or "n/a"] |
| 2 | Match System / Real World | ? | |
| 3 | User Control and Freedom | ? | |
| 4 | Consistency and Standards | ? | |
| 5 | Error Prevention | ? | |
| 6 | Recognition Rather Than Recall | ? | |
| 7 | Flexibility and Efficiency | ? | |
| 8 | Aesthetic and Minimalist Design | ? | |
| 9 | Error Recovery | ? | |
| 10 | Help and Documentation | ? | |
| **Total** | | **??/40** | **[Rating band]** |

Be honest with scores. A 4 means genuinely excellent. Most real interfaces score 20-32.

**Score ranges**: 36-40 Excellent, 28-35 Good, 20-27 Acceptable, 12-19 Poor, 0-11 Critical.

### Anti-Patterns Verdict

Start here. Does this look AI-generated?

- **LLM assessment**: Overall aesthetic feel, layout sameness, generic composition, missed opportunities for personality
- **Automated scan**: What the detector found, with counts and file locations. Note issues the detector caught that the LLM missed. Flag false positives.

### Overall Impression

A brief gut reaction: what works, what doesn't, and the single biggest opportunity for improvement.

### What's Working Well

Highlight 2-3 things done well. Be specific about why they work. Celebrate good practices so they get replicated.

### Priority Issues

The 3-5 most impactful design problems, ordered by importance.

For each issue, tag with P0-P3 severity (see `references/critique-evaluate/heuristics-scoring.md` for severity definitions):

- **[P?] What**: Name the problem clearly
- **Why it matters**: How this hurts users or undermines goals
- **Fix**: What to do about it (be concrete)
- **Recommended reference**: Which skill or reference can address this

**Severity levels**:
- **P0 Blocking** -- Prevents task completion. Fix immediately.
- **P1 Major** -- Significant difficulty or confusion. Fix before release.
- **P2 Minor** -- Annoyance, workaround exists. Fix in next pass.
- **P3 Polish** -- Nice-to-fix, no real user impact. Fix if time permits.

### Persona Red Flags

Consult `references/critique-evaluate/personas.md` for the full persona framework.

Auto-select 2-3 personas most relevant to the interface type (use the selection table in the personas reference). For each selected persona, walk through the primary user action and list specific red flags found.

Example format:

> **Alex (Power User)**: No keyboard shortcuts detected. Form requires 8 clicks for primary action. Forced modal onboarding. High abandonment risk.

> **Jordan (First-Timer)**: Icon-only nav in sidebar. Technical jargon in error messages ("404 Not Found"). No visible help. Will abandon at step 2.

Be specific. Name exact elements and interactions that fail each persona. Do not write generic persona descriptions -- write what broke for them.

### Minor Observations

Quick notes on smaller issues worth addressing but not critical enough for the priority list.

### Open Questions

Provocative questions that might unlock better solutions:

- "What if the primary action were more prominent?"
- "Does this need to feel this complex?"
- "What would a confident version of this look like?"
- "What happens when there are 0 items? 1000 items?"

---

## Post-Critique Flow

### Ask the User

After presenting findings, ask targeted questions based on what was actually found:

1. **Priority direction**: "I found problems with [X], [Y], and [Z]. Which area should we tackle first?" Offer the top 2-3 issue categories as options.
2. **Design intent**: If tonal mismatch was found, ask whether intentional. Offer 2-3 tonal directions as options.
3. **Scope**: "I found N issues. Want to address everything, or focus on the top 3?" Offer scope options.
4. **Constraints** (only if relevant): "Should any sections stay as-is?"

Rules for questions:
- Every question must reference specific findings from the report
- Maximum 2-4 questions. Respect the user's time.
- Offer concrete options, not open-ended prompts
- If findings are straightforward (1-2 clear issues), skip questions and go directly to recommendations

### Recommended Action Sequence

After receiving answers, present a prioritized action summary reflecting the user's priorities and scope:

1. List recommended actions/references in priority order
2. Order by user's stated priorities first, then by impact
3. Each item's description should carry enough context for focused work
4. Map each Priority Issue to the appropriate reference or skill
5. Skip actions that address zero issues
6. End with a polish pass as the final step if any fixes were recommended

### Feedback Principles

- Be direct. Vague feedback wastes everyone's time.
- Be specific. "The submit button," not "some elements."
- Say what's wrong AND why it matters to users.
- Give concrete suggestions, not just "consider exploring..."
- Prioritize ruthlessly. If everything is important, nothing is.
- Do not soften criticism. Honest feedback leads to great design.
