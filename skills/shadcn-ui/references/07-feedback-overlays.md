# shadcn/ui — Feedback & Overlay Components

> Source: [ui.shadcn.com/docs/components](https://ui.shadcn.com/docs/components)

## Table of Contents
- [Dialog](#dialog)
- [Alert Dialog](#alert-dialog)
- [Sheet](#sheet)
- [Drawer](#drawer)
- [Toast (Sonner)](#toast-sonner)
- [Popover](#popover)
- [Tooltip](#tooltip)
- [Hover Card](#hover-card)
- [Alert](#alert)
- [Choosing the Right Overlay](#choosing-the-right-overlay)

## Dialog

Modal dialog for focused interactions. Traps focus and blocks background interaction.

```bash
npx shadcn@latest add dialog
```

```tsx
import {
  Dialog, DialogContent, DialogDescription,
  DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";

<Dialog>
  <DialogTrigger asChild>
    <Button variant="outline">Edit Profile</Button>
  </DialogTrigger>
  <DialogContent className="sm:max-w-[425px]">
    <DialogHeader>
      <DialogTitle>Edit profile</DialogTitle>
      <DialogDescription>Make changes to your profile here.</DialogDescription>
    </DialogHeader>
    <div className="grid gap-4 py-4">
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="name" className="text-right">Name</Label>
        <Input id="name" defaultValue="Pedro Duarte" className="col-span-3" />
      </div>
    </div>
    <DialogFooter>
      <Button type="submit">Save changes</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Controlled Dialog

```tsx
const [open, setOpen] = useState(false);

<Dialog open={open} onOpenChange={setOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Confirm</DialogTitle>
    </DialogHeader>
    <DialogFooter>
      <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
      <Button onClick={() => { handleSave(); setOpen(false); }}>Save</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>

// Open programmatically
<Button onClick={() => setOpen(true)}>Open</Button>
```

### Dialog with Form

```tsx
<Dialog>
  <DialogTrigger asChild>
    <Button>Create Item</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Create new item</DialogTitle>
    </DialogHeader>
    <form onSubmit={handleSubmit}>
      <div className="grid gap-4 py-4">
        <Input name="title" placeholder="Title" />
        <Textarea name="description" placeholder="Description" />
      </div>
      <DialogFooter>
        <DialogClose asChild>
          <Button variant="outline">Cancel</Button>
        </DialogClose>
        <Button type="submit">Create</Button>
      </DialogFooter>
    </form>
  </DialogContent>
</Dialog>
```

## Alert Dialog

Confirmation dialog that requires explicit user action. Cannot be dismissed by clicking outside.

```bash
npx shadcn@latest add alert-dialog
```

```tsx
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

<AlertDialog>
  <AlertDialogTrigger asChild>
    <Button variant="destructive">Delete Account</Button>
  </AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
      <AlertDialogDescription>
        This action cannot be undone. This will permanently delete your account.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction onClick={handleDelete}>Continue</AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

**Dialog vs AlertDialog:** Use Dialog for general content (forms, info). Use AlertDialog for destructive confirmations — it can't be dismissed by clicking the overlay or pressing Escape.

## Sheet

Slide-out panel anchored to a screen edge. Used for navigation, settings, or supplementary content.

```bash
npx shadcn@latest add sheet
```

```tsx
import {
  Sheet, SheetContent, SheetDescription,
  SheetHeader, SheetTitle, SheetTrigger, SheetFooter, SheetClose,
} from "@/components/ui/sheet";

// Right side (default)
<Sheet>
  <SheetTrigger asChild>
    <Button variant="outline">Open</Button>
  </SheetTrigger>
  <SheetContent>
    <SheetHeader>
      <SheetTitle>Settings</SheetTitle>
      <SheetDescription>Configure your preferences.</SheetDescription>
    </SheetHeader>
    <div className="py-4">
      {/* Content */}
    </div>
    <SheetFooter>
      <SheetClose asChild>
        <Button>Save</Button>
      </SheetClose>
    </SheetFooter>
  </SheetContent>
</Sheet>

// Side variants
<SheetContent side="left">   {/* Left panel */}
<SheetContent side="top">    {/* Top panel */}
<SheetContent side="bottom"> {/* Bottom panel */}
<SheetContent side="right">  {/* Right panel (default) */}
```

### Sheet Sizes

```tsx
// Custom width
<SheetContent className="w-[400px] sm:w-[540px]">

// Full width on mobile
<SheetContent className="w-full sm:max-w-lg">
```

## Drawer

Bottom sheet component for mobile-friendly interactions. Uses `vaul` library.

```bash
npx shadcn@latest add drawer
```

```tsx
import {
  Drawer, DrawerClose, DrawerContent, DrawerDescription,
  DrawerFooter, DrawerHeader, DrawerTitle, DrawerTrigger,
} from "@/components/ui/drawer";

<Drawer>
  <DrawerTrigger asChild>
    <Button variant="outline">Open Drawer</Button>
  </DrawerTrigger>
  <DrawerContent>
    <div className="mx-auto w-full max-w-sm">
      <DrawerHeader>
        <DrawerTitle>Move Goal</DrawerTitle>
        <DrawerDescription>Set your daily activity goal.</DrawerDescription>
      </DrawerHeader>
      <div className="p-4">
        <Slider defaultValue={[350]} max={1000} step={10} />
      </div>
      <DrawerFooter>
        <Button>Submit</Button>
        <DrawerClose asChild>
          <Button variant="outline">Cancel</Button>
        </DrawerClose>
      </DrawerFooter>
    </div>
  </DrawerContent>
</Drawer>
```

### Responsive Dialog/Drawer

Use Dialog on desktop, Drawer on mobile:

```tsx
import { useMediaQuery } from "@/hooks/use-media-query";

function ResponsiveDialog({ children, ...props }) {
  const isDesktop = useMediaQuery("(min-width: 768px)");

  if (isDesktop) {
    return <Dialog {...props}>{children}</Dialog>;
  }

  return <Drawer {...props}>{children}</Drawer>;
}
```

## Toast (Sonner)

Toast notifications using the Sonner library.

```bash
npx shadcn@latest add sonner
```

### Setup

Add the `Toaster` component to your root layout:

```tsx
// app/layout.tsx
import { Toaster } from "@/components/ui/sonner";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
```

### Usage

```tsx
import { toast } from "sonner";

// Basic
toast("Event has been created.");

// Success
toast.success("Profile updated successfully.");

// Error
toast.error("Failed to save changes.");

// With description
toast("Event Created", {
  description: "Monday, January 3rd at 6:00pm",
});

// With action
toast("File deleted", {
  action: {
    label: "Undo",
    onClick: () => restoreFile(),
  },
});

// Promise toast
toast.promise(saveData(), {
  loading: "Saving...",
  success: "Data saved!",
  error: "Could not save.",
});

// Custom duration
toast("Quick message", { duration: 2000 });

// Dismiss
const toastId = toast("Loading...");
toast.dismiss(toastId);
```

### Toaster Configuration

```tsx
<Toaster
  position="bottom-right"   // top-left, top-center, top-right, bottom-left, bottom-center, bottom-right
  richColors                // Colored success/error backgrounds
  expand                    // Expand all toasts
  closeButton              // Show close button
/>
```

## Popover

Floating content triggered by a button. Non-modal — doesn't trap focus.

```bash
npx shadcn@latest add popover
```

```tsx
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

<Popover>
  <PopoverTrigger asChild>
    <Button variant="outline">Open</Button>
  </PopoverTrigger>
  <PopoverContent className="w-80">
    <div className="grid gap-4">
      <div className="space-y-2">
        <h4 className="font-medium leading-none">Dimensions</h4>
        <p className="text-sm text-muted-foreground">Set the dimensions.</p>
      </div>
      <div className="grid gap-2">
        <div className="grid grid-cols-3 items-center gap-4">
          <Label htmlFor="width">Width</Label>
          <Input id="width" defaultValue="100%" className="col-span-2" />
        </div>
      </div>
    </div>
  </PopoverContent>
</Popover>
```

### Alignment and Offset

```tsx
<PopoverContent align="start" sideOffset={5}>  {/* align: start | center | end */}
<PopoverContent side="right" alignOffset={10}>   {/* side: top | right | bottom | left */}
```

## Tooltip

Informational popup on hover/focus. For labels and hints, not interactive content.

```bash
npx shadcn@latest add tooltip
```

```tsx
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "@/components/ui/tooltip";

// Wrap your app (or a section) with TooltipProvider
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild>
      <Button variant="outline" size="icon">
        <Plus className="h-4 w-4" />
      </Button>
    </TooltipTrigger>
    <TooltipContent>
      <p>Add new item</p>
    </TooltipContent>
  </Tooltip>
</TooltipProvider>
```

### TooltipProvider in Layout

```tsx
// app/layout.tsx — provide once for the whole app
<TooltipProvider delayDuration={300}>
  {children}
</TooltipProvider>
```

## Hover Card

Rich preview card that appears on hover. Useful for user profiles, link previews.

```bash
npx shadcn@latest add hover-card
```

```tsx
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";

<HoverCard>
  <HoverCardTrigger asChild>
    <Button variant="link">@shadcn</Button>
  </HoverCardTrigger>
  <HoverCardContent className="w-80">
    <div className="flex justify-between space-x-4">
      <Avatar>
        <AvatarImage src="https://github.com/shadcn.png" />
        <AvatarFallback>SC</AvatarFallback>
      </Avatar>
      <div className="space-y-1">
        <h4 className="text-sm font-semibold">@shadcn</h4>
        <p className="text-sm">Creator of shadcn/ui</p>
      </div>
    </div>
  </HoverCardContent>
</HoverCard>
```

## Alert

Static alert banners for important messages. Not a popup — renders inline.

```bash
npx shadcn@latest add alert
```

```tsx
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

// Default
<Alert>
  <Terminal className="h-4 w-4" />
  <AlertTitle>Heads up!</AlertTitle>
  <AlertDescription>You can add components using the CLI.</AlertDescription>
</Alert>

// Destructive
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Error</AlertTitle>
  <AlertDescription>Your session has expired.</AlertDescription>
</Alert>
```

## Choosing the Right Overlay

| Component | Use For | Modal? | Dismissal |
|-----------|---------|--------|-----------|
| **Dialog** | Forms, content, settings | Yes | Click outside, Escape |
| **AlertDialog** | Destructive confirmations | Yes | Only via buttons |
| **Sheet** | Side panels, navigation | Yes | Click outside, Escape |
| **Drawer** | Mobile bottom sheets | Yes | Drag down, click outside |
| **Popover** | Small forms, pickers | No | Click outside |
| **Tooltip** | Labels, hints | No | Move mouse away |
| **HoverCard** | Rich previews | No | Move mouse away |
| **Alert** | Inline banners | No | Stays until removed |
| **Toast** | Notifications | No | Auto-dismiss, swipe |
