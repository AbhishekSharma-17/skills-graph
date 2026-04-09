# TypeScript & queryOptions

> Source: [TanStack Query Docs — TypeScript](https://tanstack.com/query/v5/docs/framework/react/typescript)

## Table of Contents

- [Overview](#overview)
- [Type Inference](#type-inference)
- [queryOptions Helper](#queryoptions-helper)
- [Typing useQuery](#typing-usequery)
- [Typing useMutation](#typing-usemutation)
- [Typing useInfiniteQuery](#typing-useinfinitequery)
- [Type Narrowing with Status Checks](#type-narrowing-with-status-checks)
- [Custom Hooks Pattern](#custom-hooks-pattern)
- [Default Error Type](#default-error-type)
- [Typing Query Keys](#typing-query-keys)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

TanStack Query v5 has excellent TypeScript support. Most types are inferred automatically from `queryFn` return types. The `queryOptions` helper provides type-safe reusable query configurations.

---

## Type Inference

TanStack Query infers types from your `queryFn`:

```tsx
// data is inferred as Todo[]
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: async (): Promise<Todo[]> => {
    const res = await fetch('/api/todos')
    return res.json()
  },
})
// data: Todo[] | undefined
```

### Explicit Type Parameters

You can also provide type parameters:

```tsx
const { data } = useQuery<Todo[], Error>({
  queryKey: ['todos'],
  queryFn: fetchTodos,
})
// data: Todo[] | undefined
// error: Error | null
```

Full generics: `useQuery<TData, TError, TSelect, TQueryKey>`

---

## queryOptions Helper

The `queryOptions` helper creates type-safe, reusable query configurations:

```tsx
import { queryOptions } from '@tanstack/react-query'

// Define query options once
const todosQueryOptions = queryOptions({
  queryKey: ['todos'],
  queryFn: async (): Promise<Todo[]> => {
    const res = await fetch('/api/todos')
    if (!res.ok) throw new Error('Failed')
    return res.json()
  },
  staleTime: 60000,
})

// Reuse everywhere — type-safe
function TodoList() {
  const { data } = useQuery(todosQueryOptions)
  // data: Todo[] | undefined
}

// Prefetching
queryClient.prefetchQuery(todosQueryOptions)

// Invalidation
queryClient.invalidateQueries({ queryKey: todosQueryOptions.queryKey })

// Reading cache
const cached = queryClient.getQueryData(todosQueryOptions.queryKey)
// cached: Todo[] | undefined
```

### Factory Pattern with queryOptions

```tsx
const todoQueries = {
  all: () => queryOptions({
    queryKey: ['todos'] as const,
    queryFn: fetchAllTodos,
  }),
  list: (filters: TodoFilters) => queryOptions({
    queryKey: ['todos', 'list', filters] as const,
    queryFn: () => fetchTodos(filters),
  }),
  detail: (id: number) => queryOptions({
    queryKey: ['todos', 'detail', id] as const,
    queryFn: () => fetchTodo(id),
    staleTime: 60000,
  }),
}

// Usage
useQuery(todoQueries.all())
useQuery(todoQueries.list({ status: 'active' }))
useQuery(todoQueries.detail(1))

// Invalidation
queryClient.invalidateQueries({ queryKey: ['todos'] }) // All todo queries
```

---

## Typing useQuery

### With queryFn Return Type (Recommended)

```tsx
const { data } = useQuery({
  queryKey: ['user', userId],
  queryFn: async (): Promise<User> => {
    const res = await fetch(`/api/users/${userId}`)
    return res.json()
  },
})
// data: User | undefined
```

### With select

```tsx
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: (): Promise<Todo[]> => fetchTodos(),
  select: (todos) => todos.filter((t) => t.completed),
})
// data: Todo[] | undefined (selected type)
```

---

## Typing useMutation

```tsx
interface CreateTodoInput {
  title: string
}

interface Todo {
  id: number
  title: string
  completed: boolean
}

const mutation = useMutation({
  mutationFn: async (input: CreateTodoInput): Promise<Todo> => {
    const res = await fetch('/api/todos', {
      method: 'POST',
      body: JSON.stringify(input),
    })
    return res.json()
  },
  onSuccess: (data) => {
    // data: Todo
  },
  onError: (error) => {
    // error: Error (default)
  },
})

// mutation.mutate expects CreateTodoInput
mutation.mutate({ title: 'New Todo' })

// mutation.data is Todo | undefined
// mutation.variables is CreateTodoInput | undefined
```

### Typing onMutate Return Value

```tsx
const mutation = useMutation({
  mutationFn: updateTodo,
  onMutate: async (newTodo: Todo, context) => {
    const previousTodos = context.client.getQueryData<Todo[]>(['todos'])
    return { previousTodos } // Return type is inferred
  },
  onError: (err, newTodo, onMutateResult, context) => {
    // onMutateResult: { previousTodos: Todo[] | undefined } | undefined
    if (onMutateResult?.previousTodos) {
      context.client.setQueryData(['todos'], onMutateResult.previousTodos)
    }
  },
})
```

---

## Typing useInfiniteQuery

```tsx
interface TodoPage {
  items: Todo[]
  nextCursor: number | null
}

const { data } = useInfiniteQuery({
  queryKey: ['todos'],
  queryFn: async ({ pageParam }): Promise<TodoPage> => {
    const res = await fetch(`/api/todos?cursor=${pageParam}`)
    return res.json()
  },
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
})

// data: InfiniteData<TodoPage, number> | undefined
// data.pages: TodoPage[]
// data.pageParams: number[]
```

---

## Type Narrowing with Status Checks

```tsx
const { data, isPending, isError, error } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
})

if (isPending) {
  // data is undefined here
  return <Loading />
}

if (isError) {
  // error is Error here
  return <Error message={error.message} />
}

// data is Todo[] here (narrowed by status checks)
return <TodoList todos={data} />
```

---

## Custom Hooks Pattern

```tsx
// hooks/useTodos.ts
import { queryOptions, useQuery } from '@tanstack/react-query'

interface TodoFilters {
  status?: 'active' | 'completed'
  page?: number
}

export const todosOptions = (filters: TodoFilters = {}) =>
  queryOptions({
    queryKey: ['todos', filters] as const,
    queryFn: async (): Promise<{ items: Todo[]; total: number }> => {
      const params = new URLSearchParams()
      if (filters.status) params.set('status', filters.status)
      if (filters.page) params.set('page', String(filters.page))
      const res = await fetch(`/api/todos?${params}`)
      if (!res.ok) throw new Error('Failed to fetch')
      return res.json()
    },
    staleTime: 30000,
  })

export function useTodos(filters: TodoFilters = {}) {
  return useQuery(todosOptions(filters))
}

export function useTodo(id: number) {
  return useQuery({
    queryKey: ['todo', id],
    queryFn: async (): Promise<Todo> => {
      const res = await fetch(`/api/todos/${id}`)
      if (!res.ok) throw new Error('Not found')
      return res.json()
    },
    enabled: id > 0,
  })
}
```

---

## Default Error Type

Register a global error type:

```tsx
// types/react-query.d.ts
import '@tanstack/react-query'

declare module '@tanstack/react-query' {
  interface Register {
    defaultError: ApiError
  }
}

interface ApiError {
  message: string
  status: number
  code: string
}
```

Now all queries use `ApiError` as the default error type.

---

## Typing Query Keys

### Using as const

```tsx
const queryKey = ['todos', { status: 'active' }] as const
// Type: readonly ['todos', { readonly status: 'active' }]
```

### Query Key Factory

```tsx
const queryKeys = {
  todos: {
    all: ['todos'] as const,
    lists: () => [...queryKeys.todos.all, 'list'] as const,
    list: (filters: TodoFilters) =>
      [...queryKeys.todos.lists(), filters] as const,
    details: () => [...queryKeys.todos.all, 'detail'] as const,
    detail: (id: number) => [...queryKeys.todos.details(), id] as const,
  },
}

// Usage
queryKeys.todos.all        // ['todos']
queryKeys.todos.list({})   // ['todos', 'list', {}]
queryKeys.todos.detail(1)  // ['todos', 'detail', 1]
```

---

## Common Patterns

### Shared Query + Mutation Options

```tsx
// api/todos.ts
export const todoApi = {
  queries: {
    all: () => queryOptions({
      queryKey: ['todos'] as const,
      queryFn: fetchTodos,
    }),
    byId: (id: number) => queryOptions({
      queryKey: ['todo', id] as const,
      queryFn: () => fetchTodo(id),
    }),
  },
  mutations: {
    create: () => ({
      mutationFn: (input: CreateTodoInput) => createTodo(input),
      mutationKey: ['createTodo'] as const,
    }),
    update: () => ({
      mutationFn: (input: UpdateTodoInput) => updateTodo(input),
      mutationKey: ['updateTodo'] as const,
    }),
  },
}

// Usage in components
useQuery(todoApi.queries.all())
useMutation(todoApi.mutations.create())
```

---

## Common Pitfalls

1. **Don't use generics when queryFn provides types** — Let TypeScript infer from `queryFn` return type.

2. **getQueryData needs explicit type** — `queryClient.getQueryData<Todo[]>(['todos'])` since it can't infer from the key alone. Use `queryOptions` to solve this.

3. **select changes the data type** — `select: (d) => d.length` changes data from `Todo[]` to `number`.

4. **Error type defaults to Error** — Register a custom error type or provide it explicitly.

5. **as const on query keys** — Without `as const`, `['todos', id]` is `(string | number)[]`, not `['todos', number]`.

---

## Related

- **01-queries.md** — useQuery options
- **02-mutations.md** — useMutation options
- **00-overview.md** — Setup and installation
