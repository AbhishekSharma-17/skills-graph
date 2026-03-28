# Codecs — Bidirectional Transforms

> Source: [zod.dev/codecs](https://zod.dev/codecs)

## Table of Contents

- [Overview](#overview)
- [Creating Codecs](#creating-codecs)
- [Decode and Encode](#decode-and-encode)
- [Type Safety](#type-safety)
- [Composability](#composability)
- [Encoding Behavior](#encoding-behavior)
- [Common Codec Patterns](#common-codec-patterns)

---

## Overview

Codecs define **bidirectional transforms** between two schemas. Unlike `.transform()` (which is unidirectional), codecs can convert data both ways:

- **Forward** (decode): Input → Output (like `.parse()`)
- **Backward** (encode): Output → Input (serialization)

This is useful for converting between serialized formats (strings, JSON) and rich runtime types (Date, Map, custom classes).

## Creating Codecs

```typescript
import { z } from "zod";

const StringToDate = z.codec(
  z.iso.datetime(),  // input schema
  z.date(),          // output schema
  {
    decode: (isoString) => new Date(isoString),
    encode: (date) => date.toISOString(),
  }
);
```

### Codec Arguments

1. **Input schema** — validates the raw/serialized form
2. **Output schema** — validates the rich/decoded form
3. **Options object**:
   - `decode: (input) => output` — forward transform
   - `encode: (output) => input` — backward transform

## Decode and Encode

### Decoding (Forward)

```typescript
const date = StringToDate.decode("2024-01-15T10:30:00Z");
// Date object: Mon Jan 15 2024 ...

// Safe variant
const result = StringToDate.safeDecode("2024-01-15T10:30:00Z");
if (result.success) {
  console.log(result.data); // Date
}

// Async variant
await StringToDate.decodeAsync("2024-01-15T10:30:00Z");
```

### Encoding (Backward)

```typescript
const isoString = StringToDate.encode(new Date("2024-01-15T10:30:00Z"));
// "2024-01-15T10:30:00.000Z"
```

### `.parse()` Still Works

`.parse()` behaves like `.decode()` but accepts `unknown`:

```typescript
StringToDate.parse("2024-01-15T10:30:00Z"); // Date object
```

## Type Safety

Key difference from `.parse()`: `.decode()` and `.encode()` have **strongly-typed inputs**:

```typescript
// .parse() accepts unknown
StringToDate.parse(42); // runtime error

// .decode() requires correct input type
StringToDate.decode("2024-01-15T10:30:00Z"); // OK
// StringToDate.decode(42); // TypeScript compilation error

// .encode() requires correct output type
StringToDate.encode(new Date()); // OK
// StringToDate.encode("not a date"); // TypeScript compilation error
```

## Composability

Codecs compose with all Zod features — they nest inside objects, arrays, and other schemas:

```typescript
const Event = z.object({
  name: z.string(),
  startDate: StringToDate,
  endDate: StringToDate,
  tags: z.array(z.string()),
});

// Decode JSON → rich types
const event = Event.decode({
  name: "Conference",
  startDate: "2024-06-15T09:00:00Z",
  endDate: "2024-06-17T17:00:00Z",
  tags: ["tech", "ai"],
});
// event.startDate is a Date object

// Encode rich types → JSON
const json = Event.encode(event);
// json.startDate is "2024-06-15T09:00:00.000Z"
```

## Encoding Behavior

### Two-Pass Encoding

Zod performs two passes during `z.encode()`:
1. **Type validation** — validates against the output schema
2. **Transform execution** — runs the encode function and refinements

### Refinements

All refinements execute in both directions:

```typescript
const PositiveDate = StringToDate.refine(
  (date) => date.getTime() > 0,
  { error: "Date must be after epoch" }
);

// Refinement runs during decode AND encode
```

### Defaults

Defaults only apply during forward operations (decode), not encode.

### Transforms

Unidirectional `.transform()` throws a runtime error if encountered during encoding. Use codecs instead when you need bidirectional behavior.

### Mutating Operations

String operations like `.trim()` work bidirectionally.

## Common Codec Patterns

### Number ↔ String

```typescript
const NumericString = z.codec(
  z.string(),
  z.number(),
  {
    decode: (str) => Number(str),
    encode: (num) => String(num),
  }
);
```

### Epoch ↔ Date

```typescript
const EpochDate = z.codec(
  z.number().int().positive(),
  z.date(),
  {
    decode: (epoch) => new Date(epoch * 1000),
    encode: (date) => Math.floor(date.getTime() / 1000),
  }
);
```

### JSON String ↔ Object

```typescript
const JsonConfig = z.codec(
  z.string(),
  z.object({
    host: z.string(),
    port: z.number(),
  }),
  {
    decode: (str) => JSON.parse(str),
    encode: (obj) => JSON.stringify(obj),
  }
);
```

### Base64 ↔ String

```typescript
const Base64Text = z.codec(
  z.base64(),
  z.string(),
  {
    decode: (b64) => atob(b64),
    encode: (text) => btoa(text),
  }
);
```

### Comma-Separated ↔ Array

```typescript
const CsvList = z.codec(
  z.string(),
  z.array(z.string()),
  {
    decode: (csv) => csv.split(",").map((s) => s.trim()),
    encode: (arr) => arr.join(", "),
  }
);

CsvList.decode("a, b, c");    // ["a", "b", "c"]
CsvList.encode(["a", "b"]);   // "a, b"
```

### URI Component ↔ String

```typescript
const UriEncoded = z.codec(
  z.string(),
  z.string(),
  {
    decode: (encoded) => decodeURIComponent(encoded),
    encode: (decoded) => encodeURIComponent(decoded),
  }
);
```

### When to Use Codecs vs Transforms

| Feature | `.transform()` | Codec |
|---|---|---|
| Direction | One-way (forward) | Two-way (decode + encode) |
| `.encode()` | Throws error | Works correctly |
| Type safety | `.parse()` accepts `unknown` | `.decode()` is typed |
| Use case | Data processing | Serialization/deserialization |
