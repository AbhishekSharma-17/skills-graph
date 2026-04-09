# UX Copy & Onboarding

## Table of Contents

- [Button Labels](#button-labels)
- [Error Message Formula](#error-message-formula)
- [Empty States as Opportunities](#empty-states-as-opportunities)
- [Voice vs Tone](#voice-vs-tone)
- [Writing for Accessibility](#writing-for-accessibility)
- [Writing for Translation](#writing-for-translation)
- [Terminology Consistency](#terminology-consistency)
- [Loading State Copy](#loading-state-copy)
- [Confirmation Dialogs](#confirmation-dialogs)
- [Help Text and Tooltips](#help-text-and-tooltips)
- [Navigation and Wayfinding](#navigation-and-wayfinding)
- [Onboarding Principles](#onboarding-principles)
- [Onboarding Patterns](#onboarding-patterns)
- [Empty State Design](#empty-state-design)
- [Clarity Assessment](#clarity-assessment)
- [Copy Improvement Process](#copy-improvement-process)

---

## Button Labels

### Verb + Object Pattern

Every button should describe what will happen using a specific verb and object. Never use generic labels.

| Bad | Good | Why |
|-----|------|-----|
| OK | Save changes | Says what will happen |
| Submit | Create account | Outcome-focused |
| Yes | Delete message | Confirms the specific action |
| Cancel | Keep editing | Clarifies what "cancel" means |
| Click here | Download PDF | Describes the destination |
| Confirm | Send invitation | Names the actual operation |

### Destructive Action Labels

Name the destruction explicitly:

- "Delete" not "Remove" -- delete implies permanent, remove implies recoverable.
- "Delete 5 items" not "Delete selected" -- show the count.
- Use red/danger styling to reinforce the destructive nature.

### Paired Button Labels

When presenting a choice, make both options specific:

- "Delete project" / "Keep project" -- not "Yes" / "No"
- "Discard changes" / "Continue editing" -- not "OK" / "Cancel"
- "Sign out" / "Stay signed in" -- not "Confirm" / "Cancel"

---

## Error Message Formula

Every error message answers three questions: (1) What happened? (2) Why? (3) How to fix it?

### Error Message Templates

| Situation | Template | Example |
|-----------|----------|---------|
| **Format error** | "[Field] needs to be [format]. Example: [example]" | "Phone number needs 10 digits. Example: (555) 123-4567" |
| **Missing required** | "Please enter [what's missing]" | "Please enter your email address" |
| **Permission denied** | "You don't have access to [thing]. [What to do]" | "You don't have access to this project. Contact your admin for access." |
| **Network error** | "We couldn't reach [thing]. Check your connection and [action]." | "We couldn't reach the server. Check your connection and try again." |
| **Server error** | "Something went wrong on our end. We're looking into it. [Alternative]" | "Something went wrong on our end. Your work is saved. Try refreshing." |
| **Conflict** | "[Thing] already exists. [Options]" | "A project named 'Alpha' already exists. Choose a different name." |
| **Rate limit** | "Too many attempts. [Wait time and alternative]" | "Too many login attempts. Try again in 5 minutes or reset your password." |

### Error Message Principles

- **Do not blame the user**: "Please enter a date in MM/DD/YYYY format" not "You entered an invalid date."
- **Be specific**: "Email addresses need an @ symbol" not "Invalid input."
- **Suggest fixes**: Always tell users what to do next.
- **Include examples**: Show the expected format when relevant.
- **Link to help**: For complex errors, link to documentation or support.
- **Never use humor**: Users are already frustrated. Be empathetic, not cute.
- **No error codes alone**: "Error 403" means nothing to users. Translate to plain language.

### Placement

- Inline errors appear below the relevant field.
- Connect errors to fields with `aria-describedby`.
- Summary errors at form top should link to the specific fields.
- Toast/banner errors for system-level issues (network, server).

---

## Empty States as Opportunities

Empty states are onboarding moments, not dead ends. Every empty state should:

1. **Acknowledge**: Briefly state what is empty.
2. **Explain value**: Why filling this matters.
3. **Provide action**: Clear next step to get started.

### Examples

```
Bad:  "No items"
Good: "No projects yet. Create your first project to get started."

Bad:  "Nothing to show"
Good: "Your team's activity will appear here once members start collaborating."

Bad:  "0 results"
Good: "No results for 'widget'. Try a different search term or check your filters."
```

### Empty State Types

| Type | Tone | Content |
|------|------|---------|
| **First use** | Welcoming, encouraging | Emphasize value, offer templates |
| **User cleared** | Light, supportive | Easy path to recreate |
| **No results** | Helpful | Suggest different query, offer to clear filters |
| **No permissions** | Explanatory | Why access is restricted, how to request it |
| **Error state** | Empathetic | What failed, retry option |

---

## Voice vs Tone

**Voice** is the brand's consistent personality across all touchpoints. **Tone** adapts to the moment and the user's emotional state.

### Tone by Moment

| Moment | Tone | Example |
|--------|------|---------|
| **Success** | Brief, celebratory | "Done! Your changes are live." |
| **Error** | Empathetic, helpful | "That didn't work. Here's what to try..." |
| **Loading** | Reassuring, specific | "Saving your work..." |
| **Destructive confirm** | Serious, clear | "Delete this project? This can't be undone." |
| **Onboarding** | Welcoming, encouraging | "Let's set up your first project." |
| **Empty state** | Motivating, guiding | "Your dashboard will come alive once you add data." |
| **Upgrade prompt** | Respectful, value-focused | "You've reached the free plan limit. Upgrade for unlimited projects." |

### Voice Guidelines

- Be human, not robotic: "Oops, something went wrong" not "System error encountered."
- Be confident, not arrogant: "We recommend..." not "You must..."
- Be helpful, not condescending: Assume intelligence, provide assistance.
- Be concise, not terse: Cut unnecessary words without losing clarity.

---

## Writing for Accessibility

### Link Text

Links must have standalone meaning. Screen reader users often navigate by links alone.

- "View pricing plans" not "Click here"
- "Read the migration guide" not "Learn more"
- "Download Q4 report (PDF, 2.3 MB)" not "Download"

### Alt Text

Describe the information the image conveys, not the image itself:

- "Revenue increased 40% in Q4" not "Chart"
- "Sarah Chen, Head of Engineering" not "Photo of woman"
- Use `alt=""` for purely decorative images -- screen readers skip them.

### Icon Buttons

Buttons with only an icon need `aria-label`:

```html
<button aria-label="Close dialog">
  <svg><!-- X icon --></svg>
</button>
```

### Form Accessibility

- Every input needs a visible `<label>`.
- Group related fields with `<fieldset>` and `<legend>`.
- Error messages linked via `aria-describedby`.
- Required fields indicated with both visual marker and `aria-required="true"`.

---

## Writing for Translation

### Text Expansion Rates

Design layouts that accommodate text growth when translated:

| Language | Expansion | Impact |
|----------|-----------|--------|
| German | +30% | Buttons, labels, headings grow significantly |
| French | +20% | Moderate growth across all UI |
| Finnish | +30-40% | Compound words create very long strings |
| Chinese | -30% | Fewer characters but similar display width |
| Arabic | Varies | Right-to-left layout, different numeral systems |

### Translation-Friendly Patterns

- **Keep numbers separate**: "New messages: {count}" not "You have {count} new messages" -- word order varies by language.
- **Full sentences as single strings**: Never concatenate fragments. "5 items selected" should be one translatable string, not "5" + "items" + "selected."
- **Avoid abbreviations**: "5 minutes ago" not "5 mins ago" -- abbreviations may not exist in other languages.
- **Give translators context**: Note where strings appear and any character limits.
- **Avoid idioms and slang**: "Something went wrong" not "Looks like we hit a snag."
- **Do not embed text in images**: Use CSS or HTML text that can be translated.

### Layout Considerations

- Use flexible containers that grow with content.
- Avoid fixed-width buttons -- let text determine width.
- Test with the longest target language early.
- Right-to-left languages need mirrored layouts (not just text direction).

---

## Terminology Consistency

Pick one term for each concept and use it everywhere. Variation creates confusion.

| Inconsistent | Consistent Choice |
|--------------|-------------------|
| Delete / Remove / Trash | Delete |
| Settings / Preferences / Options | Settings |
| Sign in / Log in / Enter | Sign in |
| Create / Add / New | Create |
| Dashboard / Home / Overview | Dashboard |
| Users / Members / People | Members |

### Building a Glossary

- Document every term with its definition and usage context.
- Include terms that are NOT used (and their approved alternatives).
- Review the glossary when adding new features.
- Share the glossary with design, engineering, and content teams.

---

## Loading State Copy

### Be Specific

| Bad | Good |
|-----|------|
| Loading... | Saving your draft... |
| Please wait | Analyzing your data... this usually takes 30-60 seconds |
| Processing | Uploading 3 of 12 files... |

### Long Wait Strategies

- Set time expectations: "This usually takes 30 seconds."
- Show progress: "Uploading 3 of 12 files..."
- Explain what is happening: "Generating your report from 50,000 records."
- Offer escape: "Cancel" button for operations that can be interrupted.

---

## Confirmation Dialogs

### Use Sparingly

Most confirmation dialogs are design failures. Consider undo instead -- users click through confirmations mindlessly but actively use undo.

### When Confirmation Is Required

- Truly irreversible actions (account deletion).
- High-cost operations (billing changes).
- Batch operations affecting many items.

### Writing Confirmations

- **Name the action**: "Delete 'Project Alpha'?" not "Are you sure?"
- **State consequences**: "This can't be undone. All project data will be permanently removed."
- **Specific button labels**: "Delete project" / "Keep project" -- never "Yes" / "No"
- **Match severity to tone**: Destructive actions need serious, clear language.

---

## Help Text and Tooltips

### Help Text Principles

- Add value beyond the label: "Choose a username. You can change this later in Settings."
- Answer implicit questions: "What is this?" or "Why do you need this?"
- Keep it brief but complete.
- Place instructions before the field, not after.
- Link to detailed documentation for complex topics.

### Tooltip Guidelines

- Do not repeat the label.
- Maximum one short sentence.
- Appear on hover/focus, dismiss on blur.
- Never put essential information only in tooltips -- some users cannot hover.

---

## Navigation and Wayfinding

### Label Guidelines

- Be specific: "Your projects" not "Items"
- Use user language: "Team members" not "User management"
- Make hierarchy clear through visual and textual cues.
- Provide information scent: breadcrumbs, current location indicators.

### Breadcrumbs

Show the user's location in the hierarchy:

```
Home > Projects > Project Alpha > Settings
```

Use breadcrumbs when navigation depth exceeds two levels.

---

## Onboarding Principles

### Show, Don't Tell

- Demonstrate with working examples, not descriptions.
- Provide real functionality during onboarding, not a separate tutorial mode.
- Use progressive disclosure -- teach one concept at a time.

### Make It Optional

- Let experienced users skip onboarding entirely.
- Do not block access to the product.
- Provide "Skip" or "I'll explore on my own" at every step.

### Minimize Time to Value

- Get users to the "aha moment" as quickly as possible.
- Front-load the most important concepts.
- Teach the 20% that delivers 80% of value.
- Save advanced features for contextual discovery later.

### Context Over Ceremony

- Teach features when users need them, not all upfront.
- Empty states are onboarding opportunities.
- Tooltips and hints at the point of use are more effective than tours.

### Respect User Intelligence

- Do not patronize or over-explain standard patterns.
- Be concise and clear.
- Assume users can figure out conventional UI patterns.

---

## Onboarding Patterns

### Initial Product Onboarding

**Welcome screen**: Clear value proposition, what users will accomplish, honest time estimate, option to skip.

**Account setup**: Minimal required information (collect more later), explain why each piece is needed, smart defaults, social login when appropriate.

**Core concept introduction**: Introduce 1-3 core concepts (not everything), use simple language, make it interactive (do, don't just read), show progress (step 1 of 3).

**First success**: Guide users to accomplish something real, offer pre-populated examples or templates, celebrate completion (without overdoing it), show clear next steps.

### Feature Discovery

**Contextual tooltips**: Appear the first time a user encounters a feature, point directly at the relevant UI element, include brief explanation plus benefit, are dismissable with "Don't show again", include optional "Learn more" link.

**Feature announcements**: Highlight new features at release, explain what is new and why it matters, let users try immediately, are dismissable.

**Progressive onboarding**: Teach features when users encounter them, use badges or indicators on new/unused features, unlock complexity gradually.

### Guided Tours

Use for complex interfaces, significant product changes, or domain-specific tools.

- Spotlight specific UI elements (dim the rest of the page).
- Keep to 3-7 steps maximum per tour.
- Allow free navigation through the tour.
- Include "Skip tour" option.
- Make tours replayable from a help menu.
- Focus on workflows ("Create a project") not features ("This is the project button").
- Provide sample data so actions work during the tour.

### Interactive Tutorials

Use when users need hands-on practice or concepts are complex.

- Sandbox environment with sample data.
- Clear objectives: "Create a chart showing sales by region."
- Step-by-step guidance with validation.
- Graduation moment: "You're ready!"

---

## Empty State Design

Every empty state needs five elements:

1. **What will be here**: "Your recent projects will appear here."
2. **Why it matters**: "Projects help you organize your work and collaborate with your team."
3. **How to get started**: Clear CTA -- [Create project] or [Import from template].
4. **Visual interest**: Illustration or icon, not just text on a blank page.
5. **Contextual help**: "Need help? Watch our 2-minute tutorial."

Never show the same onboarding twice. Track completion with `localStorage` and respect dismissals.

---

## Clarity Assessment

When reviewing existing copy, check for these problems:

| Problem | Signal | Fix |
|---------|--------|-----|
| **Jargon** | Technical terms users won't understand | Replace with plain language |
| **Ambiguity** | Multiple interpretations possible | Be specific and concrete |
| **Passive voice** | "Your file has been uploaded" | Active: "We uploaded your file" |
| **Length** | Too wordy or too terse | Cut words or add necessary context |
| **Assumptions** | Presumes user knowledge | Explain or link to explanation |
| **Missing context** | Users don't know what to do or why | Add purpose and next steps |
| **Tone mismatch** | Too formal, casual, or inappropriate | Match the emotional moment |

### The Clarity Test

For every piece of copy, ask:

- Can users understand this without additional context?
- Do users know what to do next?
- Is it as short as possible while remaining clear?
- Does it match terminology used elsewhere?
- Is the tone appropriate for the situation?

---

## Copy Improvement Process

Systematically audit and improve copy across eight categories:

| Category | Check |
|----------|-------|
| **Error messages** | Explains what/why/fix? Avoids blame? Specific? |
| **Labels** | Specific, descriptive? User language? Consistent? |
| **Buttons** | Verb + object? Destructive actions named? Paired buttons descriptive? |
| **Help text** | Adds value beyond label? Answers implicit question? Brief? |
| **Empty states** | Acknowledges, explains value, provides action? |
| **Success messages** | Confirms what happened? Explains next? Appropriate tone? |
| **Loading states** | Specific about what's happening? Time expectations? Cancel option? |
| **Confirmations** | Names action? States consequences? Specific labels? Could undo replace? |

### Process

1. Audit copy against all eight categories.
2. Flag problems with specific clarity issues.
3. Rewrite: specific, concise, active, human, helpful, consistent.
4. Test for comprehension, actionability, and tone.
5. Update terminology glossary with new terms.
