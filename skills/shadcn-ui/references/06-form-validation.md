# shadcn/ui — Form Validation

> Source: [ui.shadcn.com/docs/forms/react-hook-form](https://ui.shadcn.com/docs/forms/react-hook-form)

## Table of Contents
- [Overview](#overview)
- [Setup](#setup)
- [Basic Form Pattern](#basic-form-pattern)
- [Form Component API](#form-component-api)
- [Field Types](#field-types)
- [Validation Patterns](#validation-patterns)
- [Error Handling](#error-handling)
- [Advanced Patterns](#advanced-patterns)
- [Server-Side Validation](#server-side-validation)
- [Common Pitfalls](#common-pitfalls)

## Overview

shadcn/ui's form system integrates React Hook Form for state management with Zod for schema-based validation. This gives you type-safe forms with automatic error handling.

The `Form` component wraps React Hook Form's `FormProvider` and provides a `FormField` component that connects form controls to the form state.

## Setup

```bash
# Install form component and dependencies
npx shadcn@latest add form input label

# Required peer dependencies (installed automatically)
npm install react-hook-form @hookform/resolvers zod
```

## Basic Form Pattern

Three steps: define schema, create form, build fields.

```tsx
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Form, FormControl, FormDescription,
  FormField, FormItem, FormLabel, FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

// 1. Define the schema
const formSchema = z.object({
  username: z.string().min(2, "Username must be at least 2 characters."),
  email: z.string().email("Invalid email address."),
});

type FormValues = z.infer<typeof formSchema>;

// 2. Create the form
export function ProfileForm() {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
      email: "",
    },
  });

  function onSubmit(values: FormValues) {
    console.log(values);
  }

  // 3. Build fields
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input placeholder="shadcn" {...field} />
              </FormControl>
              <FormDescription>Your public display name.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="user@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  );
}
```

## Form Component API

| Component | Purpose |
|-----------|---------|
| `Form` | Wraps `FormProvider` from React Hook Form |
| `FormField` | Connects a field to form state via `control` and `name` |
| `FormItem` | Container for label + control + description + error |
| `FormLabel` | Accessible label (auto-links to control) |
| `FormControl` | Wraps the actual input element |
| `FormDescription` | Helper text below the input |
| `FormMessage` | Validation error message (auto-populated from Zod) |

### FormField render prop

The `render` function receives `{ field }` with these properties:

| Property | Purpose |
|----------|---------|
| `field.value` | Current field value |
| `field.onChange` | Change handler |
| `field.onBlur` | Blur handler |
| `field.name` | Field name |
| `field.ref` | React ref for focus management |

Spread `{...field}` onto input components. For components with non-standard APIs (like Radix Select), map manually.

## Field Types

### Select Field

```tsx
<FormField
  control={form.control}
  name="role"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Role</FormLabel>
      <Select onValueChange={field.onChange} defaultValue={field.value}>
        <FormControl>
          <SelectTrigger>
            <SelectValue placeholder="Select a role" />
          </SelectTrigger>
        </FormControl>
        <SelectContent>
          <SelectItem value="admin">Admin</SelectItem>
          <SelectItem value="user">User</SelectItem>
        </SelectContent>
      </Select>
      <FormMessage />
    </FormItem>
  )}
/>
```

### Checkbox Field

```tsx
<FormField
  control={form.control}
  name="terms"
  render={({ field }) => (
    <FormItem className="flex items-start space-x-3 space-y-0">
      <FormControl>
        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
      </FormControl>
      <div className="space-y-1 leading-none">
        <FormLabel>Accept terms and conditions</FormLabel>
        <FormDescription>You agree to our Terms of Service.</FormDescription>
      </div>
      <FormMessage />
    </FormItem>
  )}
/>
```

### Switch Field

```tsx
<FormField
  control={form.control}
  name="notifications"
  render={({ field }) => (
    <FormItem className="flex items-center justify-between rounded-lg border p-4">
      <div className="space-y-0.5">
        <FormLabel>Email Notifications</FormLabel>
        <FormDescription>Receive emails about new features.</FormDescription>
      </div>
      <FormControl>
        <Switch checked={field.value} onCheckedChange={field.onChange} />
      </FormControl>
    </FormItem>
  )}
/>
```

### Textarea Field

```tsx
<FormField
  control={form.control}
  name="bio"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Bio</FormLabel>
      <FormControl>
        <Textarea placeholder="Tell us about yourself" className="resize-none" {...field} />
      </FormControl>
      <FormDescription>Max 160 characters.</FormDescription>
      <FormMessage />
    </FormItem>
  )}
/>
```

### Radio Group Field

```tsx
<FormField
  control={form.control}
  name="type"
  render={({ field }) => (
    <FormItem className="space-y-3">
      <FormLabel>Notification type</FormLabel>
      <FormControl>
        <RadioGroup onValueChange={field.onChange} defaultValue={field.value} className="flex flex-col space-y-1">
          <FormItem className="flex items-center space-x-3 space-y-0">
            <FormControl><RadioGroupItem value="all" /></FormControl>
            <FormLabel className="font-normal">All notifications</FormLabel>
          </FormItem>
          <FormItem className="flex items-center space-x-3 space-y-0">
            <FormControl><RadioGroupItem value="mentions" /></FormControl>
            <FormLabel className="font-normal">Mentions only</FormLabel>
          </FormItem>
        </RadioGroup>
      </FormControl>
      <FormMessage />
    </FormItem>
  )}
/>
```

## Validation Patterns

### String Validation

```typescript
const schema = z.object({
  name: z.string().min(1, "Required").max(50, "Too long"),
  email: z.string().email("Invalid email"),
  url: z.string().url("Invalid URL").optional(),
  slug: z.string().regex(/^[a-z0-9-]+$/, "Only lowercase, numbers, hyphens"),
});
```

### Number Validation

```typescript
const schema = z.object({
  age: z.coerce.number().min(18, "Must be 18+").max(120),
  price: z.coerce.number().positive("Must be positive"),
});
```

### Enum Validation

```typescript
const schema = z.object({
  role: z.enum(["admin", "user", "moderator"], {
    required_error: "Please select a role.",
  }),
});
```

### Array Validation

```typescript
const schema = z.object({
  tags: z.array(z.string()).min(1, "Select at least one tag"),
  items: z.array(
    z.object({
      name: z.string().min(1),
      quantity: z.coerce.number().positive(),
    })
  ),
});
```

### Cross-Field Validation

```typescript
const schema = z
  .object({
    password: z.string().min(8),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });
```

### Conditional Validation

```typescript
const schema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("email"),
    email: z.string().email(),
  }),
  z.object({
    type: z.literal("phone"),
    phone: z.string().min(10),
  }),
]);
```

## Error Handling

### Automatic Error Display

`FormMessage` automatically shows the Zod error for its field. No manual wiring needed.

### Manual Error Setting

```typescript
form.setError("email", {
  type: "manual",
  message: "This email is already taken.",
});
```

### Root-Level Errors

```typescript
form.setError("root", {
  type: "manual",
  message: "Something went wrong. Please try again.",
});

// Display in form
{form.formState.errors.root && (
  <p className="text-sm text-destructive">{form.formState.errors.root.message}</p>
)}
```

### Loading State

```tsx
<Button type="submit" disabled={form.formState.isSubmitting}>
  {form.formState.isSubmitting ? "Saving..." : "Submit"}
</Button>
```

## Advanced Patterns

### Dynamic Fields (useFieldArray)

```tsx
import { useFieldArray } from "react-hook-form";

const { fields, append, remove } = useFieldArray({
  control: form.control,
  name: "items",
});

{fields.map((field, index) => (
  <div key={field.id} className="flex gap-2">
    <FormField
      control={form.control}
      name={`items.${index}.name`}
      render={({ field }) => (
        <FormItem>
          <FormControl><Input {...field} /></FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
    <Button type="button" variant="destructive" onClick={() => remove(index)}>
      Remove
    </Button>
  </div>
))}
<Button type="button" variant="outline" onClick={() => append({ name: "" })}>
  Add Item
</Button>
```

### Multi-Step Forms

```tsx
const [step, setStep] = useState(1);

// Validate current step before advancing
async function nextStep() {
  const fields = step === 1 ? ["name", "email"] : ["address", "city"];
  const valid = await form.trigger(fields as any);
  if (valid) setStep(step + 1);
}
```

### Form Reset

```tsx
// Reset to defaults
form.reset();

// Reset to specific values
form.reset({ username: "new-value", email: "new@example.com" });
```

## Server-Side Validation

```tsx
async function onSubmit(values: FormValues) {
  const result = await createUser(values);

  if (result.errors) {
    for (const [field, message] of Object.entries(result.errors)) {
      form.setError(field as keyof FormValues, { message });
    }
    return;
  }

  router.push("/dashboard");
}
```

## Common Pitfalls

1. **Zod field names must match form field names** — if your schema has `username` but your `FormField` name is `user_name`, validation won't connect.

2. **Use `z.coerce.number()` for numeric inputs** — HTML inputs return strings. Without `coerce`, Zod rejects them.

3. **Don't forget `defaultValues`** — React Hook Form requires default values for controlled components. Omitting them causes uncontrolled-to-controlled warnings.

4. **Select uses `onValueChange`, not `onChange`** — Radix Select has a different API. Map `field.onChange` to `onValueChange`.

5. **Always pair client validation with server validation** — Zod schemas run client-side. Never trust client-only validation for security.
