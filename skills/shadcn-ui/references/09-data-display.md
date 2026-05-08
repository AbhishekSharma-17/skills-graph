# shadcn/ui — Data Display Components

> Source: [ui.shadcn.com/docs/components](https://ui.shadcn.com/docs/components)

## Table of Contents
- [Table](#table)
- [Data Table](#data-table)
- [Badge](#badge)
- [Avatar](#avatar)
- [Skeleton](#skeleton)
- [Progress](#progress)
- [Calendar](#calendar)
- [Carousel](#carousel)
- [Toggle & Toggle Group](#toggle--toggle-group)

## Table

Simple HTML table with consistent styling.

```bash
npx shadcn@latest add table
```

```tsx
import {
  Table, TableBody, TableCaption, TableCell,
  TableFooter, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

<Table>
  <TableCaption>A list of recent invoices.</TableCaption>
  <TableHeader>
    <TableRow>
      <TableHead className="w-[100px]">Invoice</TableHead>
      <TableHead>Status</TableHead>
      <TableHead>Method</TableHead>
      <TableHead className="text-right">Amount</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {invoices.map((invoice) => (
      <TableRow key={invoice.id}>
        <TableCell className="font-medium">{invoice.id}</TableCell>
        <TableCell>{invoice.status}</TableCell>
        <TableCell>{invoice.method}</TableCell>
        <TableCell className="text-right">{invoice.amount}</TableCell>
      </TableRow>
    ))}
  </TableBody>
  <TableFooter>
    <TableRow>
      <TableCell colSpan={3}>Total</TableCell>
      <TableCell className="text-right">$2,500.00</TableCell>
    </TableRow>
  </TableFooter>
</Table>
```

## Data Table

Full-featured data table built on TanStack Table (React Table).

```bash
npx shadcn@latest add table
npm install @tanstack/react-table
```

### Column Definitions

```tsx
import { ColumnDef } from "@tanstack/react-table";

type Payment = {
  id: string;
  amount: number;
  status: "pending" | "processing" | "success" | "failed";
  email: string;
};

const columns: ColumnDef<Payment>[] = [
  {
    accessorKey: "status",
    header: "Status",
  },
  {
    accessorKey: "email",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Email
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
  },
  {
    accessorKey: "amount",
    header: () => <div className="text-right">Amount</div>,
    cell: ({ row }) => {
      const amount = parseFloat(row.getValue("amount"));
      const formatted = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      }).format(amount);
      return <div className="text-right font-medium">{formatted}</div>;
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const payment = row.original;
      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => navigator.clipboard.writeText(payment.id)}>
              Copy ID
            </DropdownMenuItem>
            <DropdownMenuItem>View details</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];
```

### DataTable Component

```tsx
"use client";

import {
  flexRender, getCoreRowModel, getFilteredRowModel,
  getPaginationRowModel, getSortedRowModel,
  useReactTable, type SortingState, type ColumnFiltersState,
} from "@tanstack/react-table";

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
}

export function DataTable<TData, TValue>({
  columns, data,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: { sorting, columnFilters },
  });

  return (
    <div>
      {/* Filter */}
      <div className="flex items-center py-4">
        <Input
          placeholder="Filter emails..."
          value={(table.getColumn("email")?.getFilterValue() as string) ?? ""}
          onChange={(e) => table.getColumn("email")?.setFilterValue(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder ? null :
                      flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} data-state={row.getIsSelected() && "selected"}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-end space-x-2 py-4">
        <Button variant="outline" size="sm" onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}>Previous</Button>
        <Button variant="outline" size="sm" onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}>Next</Button>
      </div>
    </div>
  );
}
```

### Row Selection

```tsx
import { Checkbox } from "@/components/ui/checkbox";

// Add select column
const selectColumn: ColumnDef<Payment> = {
  id: "select",
  header: ({ table }) => (
    <Checkbox
      checked={table.getIsAllPageRowsSelected()}
      onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
      aria-label="Select all"
    />
  ),
  cell: ({ row }) => (
    <Checkbox
      checked={row.getIsSelected()}
      onCheckedChange={(value) => row.toggleSelected(!!value)}
      aria-label="Select row"
    />
  ),
};

// In useReactTable config
const table = useReactTable({
  // ...
  onRowSelectionChange: setRowSelection,
  state: { rowSelection },
});
```

## Badge

Small status indicator or label.

```bash
npx shadcn@latest add badge
```

```tsx
import { Badge } from "@/components/ui/badge";

<Badge>Default</Badge>
<Badge variant="secondary">Secondary</Badge>
<Badge variant="outline">Outline</Badge>
<Badge variant="destructive">Destructive</Badge>

// As a link
<Badge asChild>
  <a href="/new">New Feature</a>
</Badge>

// Custom colors via className
<Badge className="bg-green-500 hover:bg-green-600">Active</Badge>
```

## Avatar

User profile image with fallback.

```bash
npx shadcn@latest add avatar
```

```tsx
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

<Avatar>
  <AvatarImage src="https://github.com/shadcn.png" alt="@shadcn" />
  <AvatarFallback>CN</AvatarFallback>
</Avatar>

// Sizes via className
<Avatar className="h-6 w-6">   {/* Small */}
<Avatar className="h-10 w-10"> {/* Medium (default) */}
<Avatar className="h-16 w-16"> {/* Large */}

// Avatar group
<div className="flex -space-x-2">
  {users.map((user) => (
    <Avatar key={user.id} className="border-2 border-background">
      <AvatarImage src={user.image} />
      <AvatarFallback>{user.initials}</AvatarFallback>
    </Avatar>
  ))}
</div>
```

## Skeleton

Loading placeholder that mimics content layout.

```bash
npx shadcn@latest add skeleton
```

```tsx
import { Skeleton } from "@/components/ui/skeleton";

// Basic shapes
<Skeleton className="h-4 w-[250px]" />      {/* Text line */}
<Skeleton className="h-12 w-12 rounded-full" /> {/* Avatar */}
<Skeleton className="h-[125px] w-[250px] rounded-xl" /> {/* Card */}

// Card skeleton
<div className="flex items-center space-x-4">
  <Skeleton className="h-12 w-12 rounded-full" />
  <div className="space-y-2">
    <Skeleton className="h-4 w-[250px]" />
    <Skeleton className="h-4 w-[200px]" />
  </div>
</div>

// Conditional loading
{isLoading ? (
  <div className="space-y-2">
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-3/4" />
  </div>
) : (
  <p>{content}</p>
)}
```

## Progress

Progress bar for loading states or completion indicators.

```bash
npx shadcn@latest add progress
```

```tsx
import { Progress } from "@/components/ui/progress";

// Static
<Progress value={33} />

// Animated
const [progress, setProgress] = useState(0);

useEffect(() => {
  const timer = setTimeout(() => setProgress(66), 500);
  return () => clearTimeout(timer);
}, []);

<Progress value={progress} />

// With label
<div className="space-y-2">
  <div className="flex justify-between text-sm">
    <span>Uploading...</span>
    <span>{progress}%</span>
  </div>
  <Progress value={progress} />
</div>
```

## Calendar

Date selection calendar component.

```bash
npx shadcn@latest add calendar
```

```tsx
import { Calendar } from "@/components/ui/calendar";

// Single date
const [date, setDate] = useState<Date | undefined>(new Date());
<Calendar mode="single" selected={date} onSelect={setDate} className="rounded-md border" />

// Date range
const [range, setRange] = useState<DateRange | undefined>();
<Calendar mode="range" selected={range} onSelect={setRange} numberOfMonths={2} />

// Multiple dates
const [dates, setDates] = useState<Date[] | undefined>();
<Calendar mode="multiple" selected={dates} onSelect={setDates} />

// Disabled dates
<Calendar
  mode="single"
  selected={date}
  onSelect={setDate}
  disabled={(date) => date < new Date() || date > addDays(new Date(), 30)}
/>
```

## Carousel

Swipeable content carousel built on Embla Carousel.

```bash
npx shadcn@latest add carousel
```

```tsx
import {
  Carousel, CarouselContent, CarouselItem,
  CarouselNext, CarouselPrevious,
} from "@/components/ui/carousel";

<Carousel className="w-full max-w-xs">
  <CarouselContent>
    {items.map((item, index) => (
      <CarouselItem key={index}>
        <Card>
          <CardContent className="flex aspect-square items-center justify-center p-6">
            <span className="text-4xl font-semibold">{index + 1}</span>
          </CardContent>
        </Card>
      </CarouselItem>
    ))}
  </CarouselContent>
  <CarouselPrevious />
  <CarouselNext />
</Carousel>

// Multiple items per view
<CarouselItem className="basis-1/3">  {/* 3 items visible */}
<CarouselItem className="md:basis-1/2 lg:basis-1/3"> {/* Responsive */}
```

## Toggle & Toggle Group

Toggle buttons for on/off states and grouped options.

```bash
npx shadcn@latest add toggle
```

```tsx
import { Toggle } from "@/components/ui/toggle";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

// Single toggle
<Toggle aria-label="Toggle bold">
  <Bold className="h-4 w-4" />
</Toggle>

// Toggle variants
<Toggle variant="outline">Outline</Toggle>
<Toggle size="sm">Small</Toggle>
<Toggle size="lg">Large</Toggle>

// Toggle group (single select)
<ToggleGroup type="single" defaultValue="center">
  <ToggleGroupItem value="left" aria-label="Align left">
    <AlignLeft className="h-4 w-4" />
  </ToggleGroupItem>
  <ToggleGroupItem value="center" aria-label="Align center">
    <AlignCenter className="h-4 w-4" />
  </ToggleGroupItem>
  <ToggleGroupItem value="right" aria-label="Align right">
    <AlignRight className="h-4 w-4" />
  </ToggleGroupItem>
</ToggleGroup>

// Toggle group (multi select)
<ToggleGroup type="multiple">
  <ToggleGroupItem value="bold"><Bold className="h-4 w-4" /></ToggleGroupItem>
  <ToggleGroupItem value="italic"><Italic className="h-4 w-4" /></ToggleGroupItem>
  <ToggleGroupItem value="underline"><Underline className="h-4 w-4" /></ToggleGroupItem>
</ToggleGroup>
```
