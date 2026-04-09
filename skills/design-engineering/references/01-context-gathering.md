# Context Gathering

Design skills produce generic output without project context. You must have confirmed design context before doing any design work. This is not optional — it is the single most important factor determining whether output feels designed or generated.

**Why context cannot be inferred from code:** Code tells you what was built, not who it is for or what it should feel like. Only the creator can provide this information. Reading the codebase gives you technical constraints and existing patterns, but never audience, brand, or emotional goals.

---

## The 3-Step Gathering Protocol

Follow these steps in order. Stop as soon as you have the required context.

### Step 1: Check Current Instructions (Instant)

If your loaded instructions already contain a **Design Context** section, proceed immediately to design work. This is the fastest path — the context has already been captured and is available in memory.

### Step 2: Check .impeccable.md (Fast)

If current instructions do not contain design context, read `.impeccable.md` from the project root. If it exists and contains the required context (users, brand, aesthetic direction), proceed to design work.

### Step 3: Run Teach Mode (Required If Steps 1-2 Failed)

If neither source has context, you MUST run the teach flow NOW before doing anything else.

**Do not skip this step.** Do not attempt to infer context from the codebase instead. Do not proceed with design work hoping to "figure it out as you go." Context gathering is a hard prerequisite.

---

## Teach Mode — 4-Step Process

The teach flow is a one-time setup that gathers design context for the project. Run it once, and all future design work benefits.

### Step 1: Explore the Codebase

Before asking questions, thoroughly scan the project to discover what you can:

- **README and docs**: Project purpose, target audience, any stated goals
- **Package.json / config files**: Tech stack, dependencies, existing design libraries
- **Existing components**: Current design patterns, spacing, typography in use
- **Brand assets**: Logos, favicons, color values already defined
- **Design tokens / CSS variables**: Existing color palettes, font stacks, spacing scales
- **Any style guides or brand documentation**

Note what you have learned and what remains unclear. The point is to minimize the number of questions you need to ask — do not ask about things you can discover yourself.

### Step 2: Ask UX-Focused Questions

Ask the user directly to clarify what you could not infer from the codebase. Focus only on gaps. Skip questions where the answer is already clear from exploration.

Have a natural conversation — do not dump all questions at once.

#### Users & Purpose
- Who uses this? What is their context when using it?
- What job are they trying to get done?
- What emotions should the interface evoke? (confidence, delight, calm, urgency, etc.)

#### Brand & Personality
- How would you describe the brand personality in 3 words?
- Any reference sites or apps that capture the right feel? What specifically about them?
- What should this explicitly NOT look like? Any anti-references?

#### Aesthetic Preferences
- Any strong preferences for visual direction? (minimal, bold, elegant, playful, technical, organic, etc.)
- Light mode, dark mode, or both?
- Any colors that must be used or avoided?

#### Design Principles
- What 3-5 principles should guide all design decisions for this project?
- What trade-offs matter most? (Speed vs polish? Density vs breathing room? Playful vs professional?)

#### Accessibility Requirements
- Specific accessibility requirements? (WCAG level, known user needs)
- Considerations for reduced motion, color blindness, or other accommodations?

### Step 3: Write the Design Context File

Synthesize your findings and the user's answers into a structured `.impeccable.md` file in the project root.

### Step 4: Confirm

Confirm completion with the user. Summarize the key design principles that will now guide all future work. Optionally, offer to append the Design Context to `.github/copilot-instructions.md` if the user wants it available to other tools.

---

## The .impeccable.md Template

```markdown
## Design Context

### Users
[Who they are, their context, the job to be done.
Include: role, frequency of use, state of mind when using the product,
physical context (office, mobile, evening, etc.)]

### Brand Personality
[Voice, tone, 3-word personality summary, emotional goals.
Example: "Warm, precise, opinionated" — the interface should feel like
a knowledgeable friend who gives direct advice.]

### Aesthetic Direction
[Visual tone, specific references, anti-references, theme choice and why.
Example: "Dark theme — users are SREs in dim offices at 2am.
Reference: Linear's density with Vercel's restraint.
Anti-reference: Salesforce — too busy, too many competing elements."]

### Design Principles
[3-5 principles derived from the conversation.
Example:
1. Density without clutter — show more data, not more chrome
2. Speed over polish — users are in crisis mode, never block them
3. Quiet confidence — the interface should feel competent, not flashy
4. Progressive disclosure — simple surface, depth on demand]

### Accessibility Requirements
[WCAG level, specific accommodations, reduced motion support.
Example: "WCAG AA minimum. Support prefers-reduced-motion.
High contrast mode for on-call dashboards in bright server rooms."]
```

---

## Required Context — Minimum Viable

At absolute minimum, every design skill needs these three pieces of information before producing any output:

1. **Target audience**: Who uses this product and in what context?
2. **Use cases**: What jobs are they trying to get done?
3. **Brand personality/tone**: How should the interface feel?

Individual skills may require additional context. Check the skill's preparation section for specifics.

---

## Rules

- **Never skip context gathering on a new project.** The first design action on any project is always gathering context or confirming it exists.
- **Never infer brand or audience from code.** You can infer technical constraints and existing patterns, but not who the users are or how the product should feel.
- **Ask directly, not rhetorically.** When you need information, ask the user a clear question and wait for an answer. Do not make assumptions wrapped in "I assume..."
- **Write it down.** Context that lives only in conversation history is fragile. Always persist it to `.impeccable.md` so it survives across sessions.
- **Update when things change.** If the user's understanding of their audience evolves, or the brand direction shifts, update the context file. Stale context is almost as bad as no context.
