# Primitive Types

> Source: [zod.dev/api](https://zod.dev/api)

## Table of Contents

- [Primitives](#primitives)
- [Numbers](#numbers)
- [Integers](#integers)
- [Strings](#strings)
- [Booleans](#booleans)
- [Literals](#literals)
- [Enums](#enums)
- [Native Enums](#native-enums)
- [Coercion](#coercion)
- [Special Types](#special-types)

---

## Primitives

Zod provides validators for all JavaScript primitive types:

```typescript
import { z } from "zod";

z.string();     // string
z.number();     // number (finite only, rejects NaN/Infinity)
z.bigint();     // bigint
z.boolean();    // boolean
z.symbol();     // symbol
z.undefined();  // undefined
z.null();       // null
```

## Numbers

`z.number()` validates finite numbers. It rejects `NaN` and `Infinity` by default.

### Constraints

```typescript
z.number().gt(5);        // > 5
z.number().gte(5);       // >= 5 (alias: .min(5))
z.number().lt(10);       // < 10
z.number().lte(10);      // <= 10 (alias: .max(10))
z.number().positive();   // > 0
z.number().negative();   // < 0
z.number().nonnegative(); // >= 0
z.number().nonpositive(); // <= 0
z.number().multipleOf(5); // divisible by 5
z.number().finite();     // rejects Infinity (default behavior)
```

### Custom Error Messages

```typescript
z.number().gt(5, { error: "Must be greater than 5" });
z.number().lte(10, { error: "Maximum is 10" });
```

## Integers

```typescript
z.int();       // safe integer (Number.MIN_SAFE_INTEGER to MAX_SAFE_INTEGER)
z.int32();     // 32-bit integer (-2^31 to 2^31-1)
```

Integer constraints:

```typescript
z.int().gt(0);
z.int().lte(100);
z.int().positive();
```

## Strings

`z.string()` validates string values.

### Validation Methods

```typescript
z.string().min(1);              // minimum length
z.string().max(255);            // maximum length
z.string().length(10);          // exact length
z.string().regex(/^[a-z]+$/);   // regex pattern
z.string().startsWith("https");
z.string().endsWith(".com");
z.string().includes("@");
z.string().uppercase();         // must be uppercase
z.string().lowercase();         // must be lowercase
```

### Transform Methods

These modify the string during parsing:

```typescript
z.string().trim();              // strip whitespace
z.string().toLowerCase();       // convert to lowercase
z.string().toUpperCase();       // convert to uppercase
z.string().normalize();         // Unicode normalization
```

### Combining Validation and Transform

```typescript
const CleanEmail = z.string()
  .trim()
  .toLowerCase()
  .min(5)
  .includes("@");
```

## Literals

`z.literal()` matches exact values:

```typescript
const tuna = z.literal("tuna");
const fortyTwo = z.literal(42);
const isTrue = z.literal(true);
const nul = z.literal(null);
const undef = z.literal(undefined);
const bigNum = z.literal(42n);
```

### Multiple Literals

Pass an array for union of literals:

```typescript
const Color = z.literal(["red", "green", "blue"]);
type Color = z.infer<typeof Color>; // "red" | "green" | "blue"

// Access allowed values
Color.values; // Set(["red", "green", "blue"])
```

## Enums

`z.enum()` creates a string enum schema:

```typescript
const FishEnum = z.enum(["Salmon", "Tuna", "Trout"]);
type FishEnum = z.infer<typeof FishEnum>; // "Salmon" | "Tuna" | "Trout"
```

### Enum Utilities

```typescript
// Access as object
FishEnum.enum.Salmon; // "Salmon"
FishEnum.enum.Tuna;   // "Tuna"

// Access values
FishEnum.options; // ["Salmon", "Tuna", "Trout"]

// Create subsets
const SushiFish = FishEnum.extract(["Salmon", "Tuna"]);
const NotSushi = FishEnum.exclude(["Trout"]);
```

### Autocompletion Trick

For string enums that should also accept any string:

```typescript
const Framework = z.enum(["React", "Vue", "Svelte"]);
// Only allows the three values above

// To allow any string but suggest these values:
type Framework = z.infer<typeof Framework> | (string & {});
```

## Native Enums

In Zod v4, `z.nativeEnum()` is deprecated. Use the overloaded `z.enum()`:

```typescript
// TypeScript enum
enum Fruits {
  Apple = "apple",
  Banana = "banana",
}
const FruitSchema = z.enum(Fruits);

// const object
const Fruits = {
  Apple: "apple",
  Banana: "banana",
} as const;
const FruitSchema = z.enum(Fruits);
```

## Coercion

`z.coerce.*` variants convert input before validating:

```typescript
z.coerce.string();   // String(input)
z.coerce.number();   // Number(input)
z.coerce.boolean();  // Boolean(input)
z.coerce.bigint();   // BigInt(input)
z.coerce.date();     // new Date(input)
```

### Examples

```typescript
z.coerce.number().parse("42");     // 42
z.coerce.number().parse("");       // 0
z.coerce.boolean().parse("true");  // true
z.coerce.boolean().parse("");      // false (Boolean("") === false)
z.coerce.date().parse("2024-01-01"); // Date object
```

### Stringbool (Better Boolean Coercion)

`z.stringbool()` handles common boolean string representations:

```typescript
z.stringbool().parse("true");     // true
z.stringbool().parse("1");        // true
z.stringbool().parse("yes");      // true
z.stringbool().parse("on");       // true
z.stringbool().parse("false");    // false
z.stringbool().parse("0");        // false
z.stringbool().parse("no");       // false
```

Custom truthy/falsy values:

```typescript
z.stringbool({
  truthy: ["yes", "y", "1"],
  falsy: ["no", "n", "0"],
  case: "sensitive",
});
```

## Special Types

```typescript
z.any();          // any — passes everything, type: any
z.unknown();      // unknown — passes everything, type: unknown
z.never();        // never — rejects everything
z.void();         // void — accepts undefined
z.date();         // Date instances
z.nan();          // NaN value

// File validation (browser/Node.js)
z.file();
z.file().min(1024);              // min 1KB
z.file().max(5 * 1024 * 1024);   // max 5MB
z.file().mime("image/png");      // MIME type

// JSON-safe values
z.json();         // any JSON-serializable value

// Class instances
z.instanceof(Map);
z.instanceof(URLSearchParams);

// Custom types
z.custom<MyType>((val) => val instanceof MyType);
```

## Common Patterns

### Nullable and Optional

```typescript
z.string().optional();   // string | undefined
z.string().nullable();   // string | null
z.string().nullish();    // string | null | undefined
```

### Defaults

```typescript
z.string().default("hello");   // uses "hello" if undefined
z.number().default(0);

// With transform — .default() accepts output type in v4
z.string().transform(s => s.length).default(0);

// .prefault() accepts input type (v3 behavior)
z.string().transform(s => s.length).prefault("hello");
```

### Catch (Fallback on Error)

```typescript
z.string().catch("fallback"); // returns "fallback" on validation error
z.number().catch(0);
```
