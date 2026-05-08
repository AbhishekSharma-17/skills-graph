# shadcn/ui — Layout Components

> Source: [ui.shadcn.com/docs/components](https://ui.shadcn.com/docs/components)

## Table of Contents
- [Card](#card)
- [Sidebar](#sidebar)
- [Scroll Area](#scroll-area)
- [Resizable](#resizable)
- [Separator](#separator)
- [Aspect Ratio](#aspect-ratio)
- [Collapsible](#collapsible)

## Card

Container component for grouping related content with optional header, footer, and actions.

```bash
npx shadcn@latest add card
```

### Subcomponents

| Component | Purpose |
|-----------|---------|
| `Card` | Root container |
| `CardHeader` | Top section (title + description) |
| `CardTitle` | Heading text |
| `CardDescription` | Subheading / summary |
| `CardContent` | Main body |
| `CardFooter` | Bottom section (actions) |

### Usage

```tsx
import {
  Card, CardContent, CardDescription,
  CardFooter, CardHeader, CardTitle,
} from "@/components/ui/card";

<Card>
  <CardHeader>
    <CardTitle>Create Project</CardTitle>
    <CardDescription>Deploy your new project in one click.</CardDescription>
  </CardHeader>
  <CardContent>
    <form>
      <Input placeholder="Project name" />
    </form>
  </CardContent>
  <CardFooter className="flex justify-between">
    <Button variant="outline">Cancel</Button>
    <Button>Deploy</Button>
  </CardFooter>
</Card>
```

### Variants via className

```tsx
// Interactive card
<Card className="cursor-pointer hover:bg-accent transition-colors">

// Bordered card
<Card className="border-2 border-primary">

// No border
<Card className="border-0 shadow-lg">
```

## Sidebar

Full-featured application sidebar with navigation groups, collapsible menus, and responsive behavior.

```bash
npx shadcn@latest add sidebar
```

### Subcomponents

| Component | Purpose |
|-----------|---------|
| `SidebarProvider` | Context provider (wraps layout) |
| `Sidebar` | Root sidebar container |
| `SidebarHeader` | Top area (logo, branding) |
| `SidebarContent` | Scrollable navigation area |
| `SidebarFooter` | Bottom area (user menu) |
| `SidebarGroup` | Groups related nav items |
| `SidebarGroupLabel` | Section label |
| `SidebarGroupContent` | Section content |
| `SidebarMenu` | Navigation menu |
| `SidebarMenuItem` | Individual menu item |
| `SidebarMenuButton` | Clickable nav button |
| `SidebarMenuSub` | Submenu container |
| `SidebarMenuSubItem` | Submenu item |
| `SidebarRail` | Resize/collapse handle |
| `SidebarInset` | Main content wrapper |
| `SidebarTrigger` | Toggle button |

### Basic Layout

```tsx
import {
  Sidebar, SidebarContent, SidebarGroup,
  SidebarGroupContent, SidebarGroupLabel,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem,
  SidebarProvider, SidebarInset, SidebarTrigger,
} from "@/components/ui/sidebar";

export default function Layout({ children }) {
  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Application</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <a href="/dashboard">
                      <Home className="h-4 w-4" />
                      <span>Dashboard</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
      </Sidebar>
      <SidebarInset>
        <header className="flex items-center gap-2 p-4">
          <SidebarTrigger />
          <h1>Page Title</h1>
        </header>
        <main className="p-4">{children}</main>
      </SidebarInset>
    </SidebarProvider>
  );
}
```

### Sidebar Variants

```tsx
// Collapsible icon-only mode
<Sidebar collapsible="icon">

// Fixed (non-collapsible)
<Sidebar collapsible="none">

// Side (default) or floating
<Sidebar variant="floating">
<Sidebar variant="inset">
```

### Responsive Behavior

On mobile (`<768px`), Sidebar renders as a Sheet (slide-over drawer). SidebarTrigger opens/closes it. On desktop, it behaves as a persistent sidebar.

### Config-Driven Navigation

```tsx
const navItems = [
  { title: "Dashboard", url: "/dashboard", icon: Home },
  { title: "Settings", url: "/settings", icon: Settings },
  { title: "Users", url: "/users", icon: Users },
];

<SidebarMenu>
  {navItems.map((item) => (
    <SidebarMenuItem key={item.title}>
      <SidebarMenuButton asChild isActive={pathname === item.url}>
        <a href={item.url}>
          <item.icon className="h-4 w-4" />
          <span>{item.title}</span>
        </a>
      </SidebarMenuButton>
    </SidebarMenuItem>
  ))}
</SidebarMenu>
```

## Scroll Area

Custom scrollbar component wrapping Radix ScrollArea.

```bash
npx shadcn@latest add scroll-area
```

```tsx
import { ScrollArea } from "@/components/ui/scroll-area";

// Vertical scroll
<ScrollArea className="h-72 w-48 rounded-md border">
  <div className="p-4">
    {items.map((item) => (
      <div key={item} className="text-sm">{item}</div>
    ))}
  </div>
</ScrollArea>

// Horizontal scroll
<ScrollArea className="w-96 whitespace-nowrap rounded-md border">
  <div className="flex w-max space-x-4 p-4">
    {images.map((img) => (
      <img key={img} src={img} className="h-32 w-32 rounded-md" />
    ))}
  </div>
  <ScrollBar orientation="horizontal" />
</ScrollArea>
```

## Resizable

Resizable panels with drag handles, built on `react-resizable-panels`.

```bash
npx shadcn@latest add resizable
```

```tsx
import {
  ResizableHandle, ResizablePanel, ResizablePanelGroup,
} from "@/components/ui/resizable";

<ResizablePanelGroup direction="horizontal" className="min-h-[200px]">
  <ResizablePanel defaultSize={25} minSize={20}>
    <div className="p-4">Sidebar</div>
  </ResizablePanel>
  <ResizableHandle withHandle />
  <ResizablePanel defaultSize={75}>
    <div className="p-4">Content</div>
  </ResizablePanel>
</ResizablePanelGroup>

// Vertical layout
<ResizablePanelGroup direction="vertical">
  <ResizablePanel defaultSize={60}>Top</ResizablePanel>
  <ResizableHandle />
  <ResizablePanel defaultSize={40}>Bottom</ResizablePanel>
</ResizablePanelGroup>
```

### Persistent Layout

```tsx
<ResizablePanelGroup
  direction="horizontal"
  onLayout={(sizes) => {
    document.cookie = `panel-layout=${JSON.stringify(sizes)}`;
  }}
>
```

## Separator

Visual divider between content sections.

```bash
npx shadcn@latest add separator
```

```tsx
import { Separator } from "@/components/ui/separator";

// Horizontal (default)
<Separator />

// Vertical
<Separator orientation="vertical" className="h-6" />

// In a toolbar
<div className="flex items-center gap-2">
  <Button>Edit</Button>
  <Separator orientation="vertical" className="h-6" />
  <Button>Share</Button>
  <Separator orientation="vertical" className="h-6" />
  <Button variant="destructive">Delete</Button>
</div>
```

## Aspect Ratio

Maintains a fixed aspect ratio for child content.

```bash
npx shadcn@latest add aspect-ratio
```

```tsx
import { AspectRatio } from "@/components/ui/aspect-ratio";

// 16:9 video container
<AspectRatio ratio={16 / 9}>
  <img src="/photo.jpg" alt="Photo" className="rounded-md object-cover" />
</AspectRatio>

// Square
<AspectRatio ratio={1}>
  <div className="flex items-center justify-center bg-muted">1:1</div>
</AspectRatio>

// 4:3
<AspectRatio ratio={4 / 3}>
  <iframe src="..." className="h-full w-full" />
</AspectRatio>
```

## Collapsible

Expandable/collapsible content section.

```bash
npx shadcn@latest add collapsible
```

```tsx
import {
  Collapsible, CollapsibleContent, CollapsibleTrigger,
} from "@/components/ui/collapsible";

function CollapsibleSection() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold">Advanced Settings</h4>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm">
            <ChevronsUpDown className="h-4 w-4" />
          </Button>
        </CollapsibleTrigger>
      </div>
      <CollapsibleContent className="space-y-2">
        <div className="rounded-md border px-4 py-3 text-sm">
          Setting 1
        </div>
        <div className="rounded-md border px-4 py-3 text-sm">
          Setting 2
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
```
