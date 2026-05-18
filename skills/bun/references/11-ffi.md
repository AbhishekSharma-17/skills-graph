# Bun -- Foreign Function Interface (FFI)

> Source: [bun.sh/docs/api/ffi](https://bun.sh/docs/api/ffi)

## Table of Contents

- [Overview](#overview)
- [Loading Shared Libraries with dlopen](#loading-shared-libraries-with-dlopen)
- [Defining Function Signatures](#defining-function-signatures)
- [Calling Native Functions](#calling-native-functions)
- [Type Mapping Table](#type-mapping-table)
- [Pointer Handling](#pointer-handling)
- [Strings -- cstring](#strings----cstring)
- [Callbacks -- CFunction](#callbacks----cfunction)
- [Practical Example -- Calling a C Library](#practical-example----calling-a-c-library)
- [Practical Example -- Calling a Rust Library](#practical-example----calling-a-rust-library)
- [Performance Characteristics](#performance-characteristics)
- [When to Use FFI vs Node-API](#when-to-use-ffi-vs-node-api)
- [Limitations and Caveats](#limitations-and-caveats)
- [Common Pitfalls](#common-pitfalls)

## Overview

The `bun:ffi` module allows JavaScript code to call functions in native shared libraries (`.so` on Linux, `.dylib` on macOS, `.dll` on Windows) that expose a C ABI. This makes it possible to use high-performance native code -- written in C, C++, Rust, Zig, or any language that compiles to a shared library -- directly from Bun without writing a native addon.

```typescript
import { dlopen, FFIType, ptr } from "bun:ffi";
```

The FFI bridge is built into Bun and requires no additional dependencies.

## Loading Shared Libraries with dlopen

`dlopen()` loads a shared library and binds its exported functions to JavaScript:

```typescript
import { dlopen, FFIType } from "bun:ffi";

// Load a shared library and declare the functions you want to call
const lib = dlopen("libm.so.6", {
  // Function name → signature
  ceil: {
    args: [FFIType.f64],    // Takes a double
    returns: FFIType.f64,   // Returns a double
  },
  floor: {
    args: [FFIType.f64],
    returns: FFIType.f64,
  },
  pow: {
    args: [FFIType.f64, FFIType.f64],
    returns: FFIType.f64,
  },
});

// Call the native functions
console.log(lib.symbols.ceil(4.2));     // 5
console.log(lib.symbols.floor(4.8));    // 4
console.log(lib.symbols.pow(2, 10));    // 1024

// Close the library when done (frees the handle)
lib.close();
```

The path can be absolute, relative, or just the library name (system search paths apply):

```typescript
// macOS
const lib = dlopen("libcrypto.dylib", { /* ... */ });

// Linux
const lib = dlopen("libssl.so.3", { /* ... */ });

// Absolute path
const lib = dlopen("/usr/local/lib/libcustom.so", { /* ... */ });

// Relative path (from cwd)
const lib = dlopen("./target/release/libmyrust.dylib", { /* ... */ });
```

## Defining Function Signatures

Each function binding requires an `args` array and a `returns` type using `FFIType`:

```typescript
import { dlopen, FFIType } from "bun:ffi";

const lib = dlopen("libexample.so", {
  // No arguments, returns void
  initialize: {
    args: [],
    returns: FFIType.void,
  },

  // Single integer argument, returns integer
  square: {
    args: [FFIType.i32],
    returns: FFIType.i32,
  },

  // Multiple arguments of different types
  create_buffer: {
    args: [FFIType.ptr, FFIType.u64],  // pointer, size
    returns: FFIType.ptr,               // returns a pointer
  },

  // String argument (pointer to null-terminated bytes)
  print_message: {
    args: [FFIType.cstring],
    returns: FFIType.void,
  },

  // Function that takes a callback
  set_handler: {
    args: [FFIType.function],
    returns: FFIType.void,
  },
});
```

## Calling Native Functions

Once loaded, call functions via the `symbols` property. JavaScript values are automatically converted to the declared native types:

```typescript
import { dlopen, FFIType } from "bun:ffi";

const lib = dlopen("libmath_utils.so", {
  add: { args: [FFIType.i32, FFIType.i32], returns: FFIType.i32 },
  multiply: { args: [FFIType.f64, FFIType.f64], returns: FFIType.f64 },
  is_prime: { args: [FFIType.u64], returns: FFIType.bool },
  factorial: { args: [FFIType.u32], returns: FFIType.u64 },
});

const { add, multiply, is_prime, factorial } = lib.symbols;

console.log(add(10, 20));           // 30
console.log(multiply(3.14, 2.0));   // 6.28
console.log(is_prime(17n));         // true  (u64 uses BigInt)
console.log(factorial(10));         // 3628800n (u64 returns BigInt)
```

## Type Mapping Table

| FFIType | C Type | JavaScript Type | Size |
|---------|--------|-----------------|------|
| `FFIType.bool` | `bool` | `boolean` | 1 byte |
| `FFIType.i8` | `int8_t` / `char` | `number` | 1 byte |
| `FFIType.u8` | `uint8_t` / `unsigned char` | `number` | 1 byte |
| `FFIType.i16` | `int16_t` / `short` | `number` | 2 bytes |
| `FFIType.u16` | `uint16_t` / `unsigned short` | `number` | 2 bytes |
| `FFIType.i32` | `int32_t` / `int` | `number` | 4 bytes |
| `FFIType.u32` | `uint32_t` / `unsigned int` | `number` | 4 bytes |
| `FFIType.i64` | `int64_t` / `long long` | `BigInt` | 8 bytes |
| `FFIType.u64` | `uint64_t` / `unsigned long long` | `BigInt` | 8 bytes |
| `FFIType.f32` | `float` | `number` | 4 bytes |
| `FFIType.f64` | `double` | `number` | 8 bytes |
| `FFIType.ptr` | `void*` / any pointer | `number` (address) | 8 bytes (64-bit) |
| `FFIType.cstring` | `const char*` | `string` (read) / `Buffer` (write) | pointer |
| `FFIType.void` | `void` | `undefined` | 0 |
| `FFIType.function` | function pointer | `CFunction` | pointer |

64-bit integers (`i64`, `u64`) use JavaScript `BigInt` because they exceed the safe integer range of `number`.

## Pointer Handling

Use `ptr()` to get a pointer to a `TypedArray` or `Buffer`, and `toArrayBuffer()` / `toBuffer()` to read memory from a pointer:

```typescript
import { dlopen, FFIType, ptr, toArrayBuffer, toBuffer } from "bun:ffi";

// Get a pointer to a TypedArray
const data = new Float32Array([1.0, 2.0, 3.0, 4.0]);
const dataPtr = ptr(data); // Returns the memory address as a number

// Pass the pointer to a native function
const lib = dlopen("libprocessor.so", {
  process_floats: {
    args: [FFIType.ptr, FFIType.u32],  // float*, count
    returns: FFIType.ptr,               // returns processed data
  },
  get_buffer_size: {
    args: [FFIType.ptr],
    returns: FFIType.u32,
  },
});

const resultPtr = lib.symbols.process_floats(dataPtr, data.length);

// Read memory from a pointer into an ArrayBuffer
const size = lib.symbols.get_buffer_size(resultPtr);
const resultBuffer = toArrayBuffer(resultPtr, 0, size);
const resultArray = new Float32Array(resultBuffer);

// toBuffer() returns a Node.js Buffer instead
const nodeBuffer = toBuffer(resultPtr, 0, size);

// Working with structs (read fields at byte offsets)
const structPtr = lib.symbols.create_struct();
const view = new DataView(toArrayBuffer(structPtr, 0, 16));
const x = view.getInt32(0, true);  // offset 0, little-endian
const y = view.getInt32(4, true);  // offset 4
const z = view.getFloat64(8, true); // offset 8
```

Use `ptr()` only with `TypedArray` and `Buffer`. The pointer is valid as long as the JavaScript object is alive and not garbage collected. To prevent collection, keep a reference.

## Strings -- cstring

Read C strings (null-terminated `const char*`) from pointers:

```typescript
import { dlopen, FFIType, CString } from "bun:ffi";

const lib = dlopen("libgreet.so", {
  greet: {
    args: [FFIType.cstring],  // Takes a const char*
    returns: FFIType.cstring, // Returns a const char*
  },
  get_version: {
    args: [],
    returns: FFIType.cstring,
  },
});

// Pass a string — Bun encodes it to UTF-8 and null-terminates automatically
const greeting = lib.symbols.greet("World");
console.log(greeting); // "Hello, World!"

// Returned cstrings are JavaScript strings
const version = lib.symbols.get_version();
console.log(typeof version); // "string"

// Manual CString from a pointer
const somePtr = lib.symbols.get_string_ptr();
const str = new CString(somePtr);
console.log(str.toString()); // Reads until null terminator

// CString with explicit length (no null terminator needed)
const fixedStr = new CString(somePtr, 0, 10); // Read 10 bytes from offset 0
```

## Callbacks -- CFunction

Pass JavaScript functions to native code as callbacks using `CFunction`:

```typescript
import { dlopen, FFIType, CFunction } from "bun:ffi";

// Create a native-callable function from a JavaScript function
const compareCallback = new CFunction({
  args: [FFIType.i32, FFIType.i32],
  returns: FFIType.i32,
}, (a: number, b: number): number => {
  return a - b; // Standard comparator
});

const lib = dlopen("libsort.so", {
  sort_array: {
    args: [FFIType.ptr, FFIType.u32, FFIType.function],
    returns: FFIType.void,
  },
});

const numbers = new Int32Array([5, 3, 1, 4, 2]);
lib.symbols.sort_array(ptr(numbers), numbers.length, compareCallback);
console.log(numbers); // Int32Array [1, 2, 3, 4, 5]

// Event callback pattern
const onEvent = new CFunction({
  args: [FFIType.i32, FFIType.cstring],
  returns: FFIType.void,
}, (eventType: number, message: string) => {
  console.log(`Event ${eventType}: ${message}`);
});

lib.symbols.register_callback(onEvent);

// IMPORTANT: prevent garbage collection by keeping a reference
// If `onEvent` is collected, calling the callback from C will crash
```

## Practical Example -- Calling a C Library

A complete example calling a custom C library:

```c
// math_utils.c — compile with: gcc -shared -o libmath_utils.so math_utils.c
#include <math.h>
#include <stdlib.h>

int add(int a, int b) { return a + b; }
double hypotenuse(double a, double b) { return sqrt(a * a + b * b); }

typedef struct { double x; double y; } Point;

Point* create_point(double x, double y) {
    Point* p = malloc(sizeof(Point));
    p->x = x;
    p->y = y;
    return p;
}

void free_point(Point* p) { free(p); }
```

```typescript
// main.ts
import { dlopen, FFIType, toArrayBuffer } from "bun:ffi";

const lib = dlopen("./libmath_utils.so", {
  add: { args: [FFIType.i32, FFIType.i32], returns: FFIType.i32 },
  hypotenuse: { args: [FFIType.f64, FFIType.f64], returns: FFIType.f64 },
  create_point: { args: [FFIType.f64, FFIType.f64], returns: FFIType.ptr },
  free_point: { args: [FFIType.ptr], returns: FFIType.void },
});

const { add, hypotenuse, create_point, free_point } = lib.symbols;

console.log(add(10, 20));           // 30
console.log(hypotenuse(3.0, 4.0)); // 5.0

// Work with a struct pointer
const pointPtr = create_point(3.14, 2.71);
const pointData = new DataView(toArrayBuffer(pointPtr, 0, 16));
console.log("x:", pointData.getFloat64(0, true)); // 3.14
console.log("y:", pointData.getFloat64(8, true)); // 2.71

// Free the allocated memory
free_point(pointPtr);

lib.close();
```

## Practical Example -- Calling a Rust Library

Rust can expose a C ABI using `extern "C"` and `#[no_mangle]`:

```rust
// src/lib.rs — compile with: cargo build --release
// Cargo.toml must include: [lib] crate-type = ["cdylib"]

#[no_mangle]
pub extern "C" fn fibonacci(n: u32) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => {
            let (mut a, mut b) = (0u64, 1u64);
            for _ in 2..=n {
                let temp = b;
                b = a + b;
                a = temp;
            }
            b
        }
    }
}

#[no_mangle]
pub extern "C" fn is_palindrome(s: *const std::os::raw::c_char) -> bool {
    let c_str = unsafe { std::ffi::CStr::from_ptr(s) };
    let s = c_str.to_str().unwrap_or("");
    let bytes = s.as_bytes();
    bytes.iter().eq(bytes.iter().rev())
}
```

```typescript
// main.ts
import { dlopen, FFIType } from "bun:ffi";

const lib = dlopen("./target/release/libmylib.dylib", {
  fibonacci: {
    args: [FFIType.u32],
    returns: FFIType.u64,
  },
  is_palindrome: {
    args: [FFIType.cstring],
    returns: FFIType.bool,
  },
});

console.log(lib.symbols.fibonacci(50));         // 12586269025n (BigInt)
console.log(lib.symbols.is_palindrome("racecar")); // true
console.log(lib.symbols.is_palindrome("hello"));   // false

lib.close();
```

## Performance Characteristics

Bun's FFI is designed for minimal overhead:

- **Call overhead**: approximately 2-6x faster than Node-API (napi) for simple function calls
- **No serialization**: primitive types are passed directly without boxing
- **Pointer access**: direct memory read/write without copying
- **JIT integration**: Bun can inline simple FFI calls at the JIT level

```typescript
// Benchmark pattern: measure FFI call overhead
import { dlopen, FFIType } from "bun:ffi";

const lib = dlopen("libm.so.6", {
  sqrt: { args: [FFIType.f64], returns: FFIType.f64 },
});

const iterations = 10_000_000;
const start = performance.now();

for (let i = 0; i < iterations; i++) {
  lib.symbols.sqrt(i);
}

const elapsed = performance.now() - start;
console.log(`${iterations} calls in ${elapsed.toFixed(1)}ms`);
console.log(`${(iterations / elapsed * 1000).toFixed(0)} calls/sec`);
// Typical result: 50-200M calls/sec depending on function complexity
```

## When to Use FFI vs Node-API

| Factor | bun:ffi | Node-API (napi) |
|--------|---------|-----------------|
| **Setup complexity** | Low (just `dlopen`) | High (C++ addon, build system) |
| **Call overhead** | Lower (2-6x faster) | Higher |
| **Complex types** | Manual pointer math | Native object wrapping |
| **Error handling** | Minimal (crashes on bad args) | Robust (exception propagation) |
| **Thread safety** | Not guaranteed | Thread-safe functions available |
| **Ecosystem** | Bun-specific | Works in Node.js and Bun |
| **Callbacks** | CFunction (basic) | Full async callback support |
| **Best for** | Simple C ABI calls | Complex native addons |

**Use bun:ffi when:**
- Calling a few functions from an existing shared library
- Performance of the bridge itself matters
- The library has a simple C API (no complex object lifecycle)

**Use Node-API when:**
- Building a reusable native addon for the npm ecosystem
- Need complex error handling and object wrapping
- Need thread-safe async operations from native code
- Need to support both Node.js and Bun

## Limitations and Caveats

- **No automatic memory management** -- Memory allocated by native code must be freed by calling the corresponding native free function; JavaScript's garbage collector will not free native allocations
- **No struct definitions** -- You must manually calculate byte offsets and use `DataView` to read struct fields; there is no high-level struct mapping
- **Crash risk** -- Passing an invalid pointer or wrong type can crash the entire Bun process with a segfault; there is no safety net
- **Callback lifetime** -- A `CFunction` must remain referenced in JavaScript for as long as native code may call it; premature garbage collection causes a crash
- **No C++ name mangling** -- Only C ABI functions (`extern "C"`) can be called; C++ methods need a C wrapper
- **Platform-specific libraries** -- Library file extensions and paths differ across operating systems; conditional loading is needed for cross-platform code

## Common Pitfalls

1. **Mismatched type sizes** -- Declaring `FFIType.i32` for a C `long` (which is 8 bytes on 64-bit Linux) silently reads wrong data; always match the exact native type size
2. **Forgetting to keep callback references** -- If a `CFunction` is garbage collected while native code still holds its pointer, calling it crashes the process
3. **Not freeing native memory** -- Memory allocated by `malloc()` in native code is invisible to JavaScript's GC; always call the corresponding `free()` function
4. **Reading past allocated memory** -- `toArrayBuffer(ptr, 0, size)` with an incorrect `size` reads garbage or crashes; always track buffer sizes accurately
5. **Using FFI for complex object APIs** -- FFI works best with flat C functions; if the library returns opaque objects with methods, consider a Node-API wrapper instead
6. **Ignoring endianness** -- `DataView` requires specifying endianness (`true` for little-endian on x86/ARM); omitting it defaults to big-endian, producing wrong values on most systems
7. **Library path hardcoding** -- Use platform detection to select `.so`, `.dylib`, or `.dll`; a hardcoded extension will fail on other operating systems
