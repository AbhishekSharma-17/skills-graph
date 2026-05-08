# shadcn/ui — Form Components

> Source: [ui.shadcn.com/docs/components](https://ui.shadcn.com/docs/components)

## Table of Contents
- [Input](#input)
- [Textarea](#textarea)
- [Select](#select)
- [Checkbox](#checkbox)
- [Radio Group](#radio-group)
- [Switch](#switch)
- [Slider](#slider)
- [Date Picker](#date-picker)
- [Combobox](#combobox)
- [Input OTP](#input-otp)
- [Label](#label)
- [Field](#field)

## Input

Text input field with consistent styling.

```bash
npx shadcn@latest add input
```

```tsx
import { Input } from "@/components/ui/input";

// Basic
<Input type="text" placeholder="Email" />

// With label
<div className="grid w-full max-w-sm gap-1.5">
  <Label htmlFor="email">Email</Label>
  <Input type="email" id="email" placeholder="Email" />
</div>

// Disabled
<Input disabled placeholder="Disabled" />

// With icon
<div className="relative">
  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
  <Input placeholder="Search..." className="pl-8" />
</div>

// File input
<Input type="file" />
```

### Input Props

| Prop | Type | Default |
|------|------|---------|
| `type` | `string` | `"text"` |
| `placeholder` | `string` | — |
| `disabled` | `boolean` | `false` |
| `className` | `string` | — |

All standard HTML input attributes are supported.

## Textarea

Multi-line text input.

```bash
npx shadcn@latest add textarea
```

```tsx
import { Textarea } from "@/components/ui/textarea";

// Basic
<Textarea placeholder="Type your message here." />

// With label
<div className="grid w-full gap-1.5">
  <Label htmlFor="message">Your message</Label>
  <Textarea id="message" placeholder="Type your message here." />
</div>

// Disabled
<Textarea disabled placeholder="Disabled" />
```

## Select

Dropdown select component built on Radix Select.

```bash
npx shadcn@latest add select
```

```tsx
import {
  Select, SelectContent, SelectGroup, SelectItem,
  SelectLabel, SelectTrigger, SelectValue,
} from "@/components/ui/select";

<Select>
  <SelectTrigger className="w-[180px]">
    <SelectValue placeholder="Select a fruit" />
  </SelectTrigger>
  <SelectContent>
    <SelectGroup>
      <SelectLabel>Fruits</SelectLabel>
      <SelectItem value="apple">Apple</SelectItem>
      <SelectItem value="banana">Banana</SelectItem>
      <SelectItem value="orange">Orange</SelectItem>
    </SelectGroup>
  </SelectContent>
</Select>

// Controlled
const [value, setValue] = useState("");
<Select value={value} onValueChange={setValue}>
  ...
</Select>

// Disabled items
<SelectItem value="grapes" disabled>Grapes (out of stock)</SelectItem>
```

### Native Select

For simpler cases or when you need standard HTML `<select>`:

```tsx
import { NativeSelect } from "@/components/ui/native-select";

<NativeSelect>
  <option value="1">Option 1</option>
  <option value="2">Option 2</option>
</NativeSelect>
```

## Checkbox

Checkbox input with optional indeterminate state.

```bash
npx shadcn@latest add checkbox
```

```tsx
import { Checkbox } from "@/components/ui/checkbox";

// With label
<div className="flex items-center space-x-2">
  <Checkbox id="terms" />
  <Label htmlFor="terms">Accept terms and conditions</Label>
</div>

// Controlled
const [checked, setChecked] = useState(false);
<Checkbox checked={checked} onCheckedChange={setChecked} />

// Disabled
<Checkbox disabled />

// With description
<div className="items-top flex space-x-2">
  <Checkbox id="terms" />
  <div className="grid gap-1.5 leading-none">
    <Label htmlFor="terms">Accept terms</Label>
    <p className="text-sm text-muted-foreground">
      You agree to our Terms of Service.
    </p>
  </div>
</div>
```

## Radio Group

Single-select radio button group.

```bash
npx shadcn@latest add radio-group
```

```tsx
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

<RadioGroup defaultValue="comfortable">
  <div className="flex items-center space-x-2">
    <RadioGroupItem value="default" id="r1" />
    <Label htmlFor="r1">Default</Label>
  </div>
  <div className="flex items-center space-x-2">
    <RadioGroupItem value="comfortable" id="r2" />
    <Label htmlFor="r2">Comfortable</Label>
  </div>
  <div className="flex items-center space-x-2">
    <RadioGroupItem value="compact" id="r3" />
    <Label htmlFor="r3">Compact</Label>
  </div>
</RadioGroup>

// Controlled
<RadioGroup value={selected} onValueChange={setSelected}>
```

## Switch

Toggle switch for on/off states.

```bash
npx shadcn@latest add switch
```

```tsx
import { Switch } from "@/components/ui/switch";

// With label
<div className="flex items-center space-x-2">
  <Switch id="airplane-mode" />
  <Label htmlFor="airplane-mode">Airplane Mode</Label>
</div>

// Controlled
const [enabled, setEnabled] = useState(false);
<Switch checked={enabled} onCheckedChange={setEnabled} />

// Disabled
<Switch disabled />
```

## Slider

Range slider for numeric input.

```bash
npx shadcn@latest add slider
```

```tsx
import { Slider } from "@/components/ui/slider";

// Basic
<Slider defaultValue={[50]} max={100} step={1} />

// Range (two thumbs)
<Slider defaultValue={[25, 75]} max={100} step={1} />

// Controlled
const [value, setValue] = useState([33]);
<Slider value={value} onValueChange={setValue} max={100} step={1} />

// With label
<div className="space-y-2">
  <Label>Volume: {value[0]}%</Label>
  <Slider value={value} onValueChange={setValue} max={100} />
</div>
```

## Date Picker

Date picker using Calendar component with Popover.

```bash
npx shadcn@latest add calendar popover button
```

```tsx
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { format } from "date-fns";

function DatePicker() {
  const [date, setDate] = useState<Date>();

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "w-[280px] justify-start text-left font-normal",
            !date && "text-muted-foreground"
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {date ? format(date, "PPP") : <span>Pick a date</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0">
        <Calendar mode="single" selected={date} onSelect={setDate} />
      </PopoverContent>
    </Popover>
  );
}

// Date range picker
function DateRangePicker() {
  const [range, setRange] = useState<DateRange>();

  return (
    <Calendar mode="range" selected={range} onSelect={setRange} numberOfMonths={2} />
  );
}
```

## Combobox

Searchable select built with Command and Popover.

```bash
npx shadcn@latest add command popover button
```

```tsx
import {
  Command, CommandEmpty, CommandGroup,
  CommandInput, CommandItem, CommandList,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

const frameworks = [
  { value: "next.js", label: "Next.js" },
  { value: "remix", label: "Remix" },
  { value: "astro", label: "Astro" },
];

function Combobox() {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" role="combobox" aria-expanded={open} className="w-[200px] justify-between">
          {value ? frameworks.find((f) => f.value === value)?.label : "Select framework..."}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0">
        <Command>
          <CommandInput placeholder="Search framework..." />
          <CommandList>
            <CommandEmpty>No framework found.</CommandEmpty>
            <CommandGroup>
              {frameworks.map((f) => (
                <CommandItem
                  key={f.value}
                  value={f.value}
                  onSelect={(v) => { setValue(v); setOpen(false); }}
                >
                  <Check className={cn("mr-2 h-4 w-4", value === f.value ? "opacity-100" : "opacity-0")} />
                  {f.label}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
```

## Input OTP

One-time password input with individual digit slots.

```bash
npx shadcn@latest add input-otp
```

```tsx
import {
  InputOTP, InputOTPGroup, InputOTPSeparator, InputOTPSlot,
} from "@/components/ui/input-otp";

// 6-digit OTP
<InputOTP maxLength={6}>
  <InputOTPGroup>
    <InputOTPSlot index={0} />
    <InputOTPSlot index={1} />
    <InputOTPSlot index={2} />
  </InputOTPGroup>
  <InputOTPSeparator />
  <InputOTPGroup>
    <InputOTPSlot index={3} />
    <InputOTPSlot index={4} />
    <InputOTPSlot index={5} />
  </InputOTPGroup>
</InputOTP>

// Controlled
<InputOTP maxLength={6} value={otp} onChange={setOtp}>
```

## Label

Accessible label component that pairs with form controls.

```bash
npx shadcn@latest add label
```

```tsx
import { Label } from "@/components/ui/label";

<Label htmlFor="email">Email</Label>
<Input id="email" type="email" />
```

## Field

Container component that groups a label, input, and description/error message.

```bash
npx shadcn@latest add field
```

```tsx
import { Field, FieldLabel, FieldDescription, FieldError } from "@/components/ui/field";

<Field>
  <FieldLabel>Username</FieldLabel>
  <Input placeholder="Enter username" />
  <FieldDescription>This is your public display name.</FieldDescription>
  <FieldError>Username is required.</FieldError>
</Field>
```
