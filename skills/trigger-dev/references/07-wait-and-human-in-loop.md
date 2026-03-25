# Wait & Human-in-the-Loop

> Source: https://trigger.dev/docs — v4.4.3

## Contents

- [Wait Functions](#wait-functions)
- [Waitpoint Tokens](#waitpoint-tokens)
- [Human-in-the-Loop Workflows](#human-in-the-loop-workflows)
- [Token Management API](#token-management-api)
- [Common Patterns](#common-patterns)

## Wait Functions

Trigger.dev provides wait functions that pause task execution and release compute resources. When the wait is longer than 5 seconds, the task checkpoints and does NOT count towards compute charges.

### wait.for — Wait for a Duration

```typescript
import { task, wait } from "@trigger.dev/sdk/v3";

export const delayedTask = task({
  id: "delayed-task",
  run: async (payload) => {
    // Process first step
    await sendEmail(payload.email, "Welcome!");

    // Wait 24 hours (checkpoints, no compute charge)
    await wait.for({ hours: 24 });

    // Process second step
    await sendEmail(payload.email, "How's it going?");

    // Wait 3 days
    await wait.for({ days: 3 });

    // Third step
    await sendEmail(payload.email, "Don't forget to...");

    return { status: "sequence_complete" };
  },
});
```

### Supported Duration Formats

```typescript
await wait.for({ seconds: 30 });
await wait.for({ minutes: 15 });
await wait.for({ hours: 2 });
await wait.for({ days: 7 });
await wait.for({ weeks: 1 });

// String format also supported
await wait.for("30s");
await wait.for("15m");
await wait.for("2h");
await wait.for("7d");
```

### wait.until — Wait Until a Specific Time

```typescript
export const scheduledAction = task({
  id: "scheduled-action",
  run: async (payload: { executeAt: string }) => {
    // Wait until the specified time
    await wait.until({ date: new Date(payload.executeAt) });

    // Executes at the specified time
    await performAction(payload);
    return { executedAt: new Date().toISOString() };
  },
});
```

## Waitpoint Tokens

Tokens pause task execution until an external signal completes them. This is the foundation for human-in-the-loop workflows.

### Creating a Token

```typescript
import { wait } from "@trigger.dev/sdk/v3";

const token = await wait.createToken({
  timeout: "24h",                        // Auto-fail after 24 hours
  idempotencyKey: `approval-${orderId}`, // Prevent duplicates
  tags: ["approval", `order:${orderId}`],
});

// token.id — unique identifier (e.g., "waitpoint_xxxx")
// token.url — HTTP endpoint for external completion
// token.publicAccessToken — for client-side completion
```

### Waiting for a Token

```typescript
export const approvalTask = task({
  id: "approval-workflow",
  run: async (payload: { orderId: string; amount: number }) => {
    // Step 1: Create approval token
    const token = await wait.createToken({
      timeout: "48h",
      tags: [`order:${payload.orderId}`],
    });

    // Step 2: Notify approver (send link with token URL)
    await sendApprovalEmail({
      to: "manager@company.com",
      orderId: payload.orderId,
      amount: payload.amount,
      approvalUrl: `https://app.com/approve?token=${token.id}`,
    });

    // Step 3: Wait for approval (checkpoints, no compute charge)
    const result = await wait.forToken<{
      approved: boolean;
      approver: string;
      note?: string;
    }>(token.id);

    // Step 4: Process result
    if (result.ok) {
      if (result.output.approved) {
        await processOrder(payload.orderId);
        return { status: "approved", by: result.output.approver };
      } else {
        await cancelOrder(payload.orderId);
        return { status: "rejected", by: result.output.approver };
      }
    } else {
      // Timeout — no response within 48 hours
      await escalateOrder(payload.orderId);
      return { status: "escalated" };
    }
  },
});
```

### Completing a Token

#### Via SDK (from your backend)

```typescript
import { wait } from "@trigger.dev/sdk/v3";

// In your approval API endpoint
await wait.completeToken<{ approved: boolean; approver: string }>(
  tokenId,
  { approved: true, approver: "jane@company.com" }
);
```

#### Via HTTP POST (from any language)

```bash
curl -X POST "https://api.trigger.dev/api/v1/waitpoints/tokens/{tokenId}/complete" \
  -H "Authorization: Bearer tr_prod_xxxx" \
  -H "Content-Type: application/json" \
  -d '{"data": {"approved": true, "approver": "jane@company.com"}}'
```

#### Via Public Access Token (from client-side)

```typescript
// Use the publicAccessToken from createToken
await fetch(`https://api.trigger.dev/api/v1/waitpoints/tokens/${tokenId}/complete`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token.publicAccessToken}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ data: { approved: true } }),
});
```

### Using .unwrap()

```typescript
// Throws on timeout, returns data directly on success
const approval = await wait.forToken<ApprovalData>(tokenId).unwrap();
// approval is typed as ApprovalData
console.log(approval.approved);
```

## Human-in-the-Loop Workflows

### Approval Workflow Pattern

```typescript
export const purchaseApproval = task({
  id: "purchase-approval",
  run: async (payload: { requestId: string; amount: number; requestedBy: string }) => {
    const token = await wait.createToken({ timeout: "72h" });

    // Send notification to approver
    await slack.postMessage({
      channel: "#approvals",
      text: `Purchase request #${payload.requestId} for $${payload.amount}`,
      blocks: [
        {
          type: "actions",
          elements: [
            { type: "button", text: { text: "Approve" }, url: `${APP_URL}/approve/${token.id}` },
            { type: "button", text: { text: "Reject" }, url: `${APP_URL}/reject/${token.id}` },
          ],
        },
      ],
    });

    const result = await wait.forToken<{ decision: "approved" | "rejected" }>(token.id);

    if (!result.ok) {
      return { status: "timeout", escalated: true };
    }

    if (result.output.decision === "approved") {
      await executePurchase(payload.requestId);
      return { status: "approved" };
    }

    return { status: "rejected" };
  },
});
```

### Multi-Step Approval Chain

```typescript
export const multiApproval = task({
  id: "multi-step-approval",
  run: async (payload: { documentId: string }) => {
    // Step 1: Manager approval
    const managerToken = await wait.createToken({ timeout: "24h" });
    await notifyManager(payload.documentId, managerToken.id);
    const managerResult = await wait.forToken(managerToken.id).unwrap();

    // Step 2: Legal review (only if manager approved)
    const legalToken = await wait.createToken({ timeout: "48h" });
    await notifyLegal(payload.documentId, legalToken.id);
    const legalResult = await wait.forToken(legalToken.id).unwrap();

    // Step 3: Final sign-off
    const ceoToken = await wait.createToken({ timeout: "72h" });
    await notifyCEO(payload.documentId, ceoToken.id);
    const ceoResult = await wait.forToken(ceoToken.id).unwrap();

    return { status: "fully_approved", approvals: 3 };
  },
});
```

## Token Management API

### List Tokens

```typescript
const tokens = await wait.listTokens({
  status: "WAITING",                    // WAITING, COMPLETED, TIMED_OUT
  tags: ["order:order_123"],
  period: "7d",                         // Last 7 days
  from: new Date("2026-03-01"),
  to: new Date("2026-03-25"),
});

for (const token of tokens.data) {
  console.log(`${token.id}: ${token.status}`);
}
```

### Retrieve a Token

```typescript
const token = await wait.retrieveToken(tokenId);
console.log(token.status);    // "WAITING" | "COMPLETED" | "TIMED_OUT"
console.log(token.output);    // Completion data (if completed)
console.log(token.error);     // Error info (if timed out)
```

### Token Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `timeout` | `string` | Auto-timeout duration (e.g., "24h") |
| `idempotencyKey` | `string` | Prevent duplicate tokens |
| `idempotencyKeyTTL` | `string` | Key expiration (default: "1h") |
| `tags` | `string[]` | Filterable labels |

## Common Patterns

### Email Drip Campaign with Waits

```typescript
export const dripCampaign = task({
  id: "drip-campaign",
  run: async (payload: { userId: string; email: string }) => {
    // Day 0: Welcome email
    await sendEmail(payload.email, "welcome");

    // Day 1: Feature introduction
    await wait.for({ days: 1 });
    await sendEmail(payload.email, "features");

    // Day 3: Tips & tricks
    await wait.for({ days: 2 });
    await sendEmail(payload.email, "tips");

    // Day 7: Upgrade prompt
    await wait.for({ days: 4 });
    const user = await db.users.findById(payload.userId);
    if (!user.isPaid) {
      await sendEmail(payload.email, "upgrade");
    }

    return { completed: true, totalDays: 7 };
  },
});
```

### AI Agent with Human Review

```typescript
export const aiWithReview = task({
  id: "ai-with-review",
  run: async (payload: { prompt: string }) => {
    // Generate AI response
    const draft = await generateAIResponse(payload.prompt);

    // Create review token
    const token = await wait.createToken({ timeout: "4h" });
    await notifyReviewer(draft, token.id);

    // Wait for human review
    const review = await wait.forToken<{
      action: "approve" | "edit" | "reject";
      editedContent?: string;
    }>(token.id);

    if (!review.ok) return { status: "review_timeout" };

    switch (review.output.action) {
      case "approve":
        await publishContent(draft);
        return { status: "published" };
      case "edit":
        await publishContent(review.output.editedContent!);
        return { status: "published_with_edits" };
      case "reject":
        return { status: "rejected" };
    }
  },
});
```

## Related Topics

- Writing tasks → `01-writing-tasks.md`
- Error handling → `06-error-handling-retries.md`
- Realtime updates → `08-realtime-streaming.md`
