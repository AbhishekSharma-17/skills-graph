# Dependent & Parallel Queries

> Source: [TanStack Query Docs — Dependent Queries](https://tanstack.com/query/v5/docs/framework/react/guides/dependent-queries) | [Parallel Queries](https://tanstack.com/query/v5/docs/framework/react/guides/parallel-queries)

## Table of Contents

- [Overview](#overview)
- [Parallel Queries](#parallel-queries)
- [useQueries — Dynamic Parallel Queries](#usequeries--dynamic-parallel-queries)
- [Dependent (Serial) Queries](#dependent-serial-queries)
- [Chaining Multiple Dependencies](#chaining-multiple-dependencies)
- [Combining Dependent and Parallel](#combining-dependent-and-parallel)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

- **Parallel queries** — Multiple independent queries that fetch simultaneously
- **Dependent queries** — Queries that depend on the result of another query (serial execution)

---

## Parallel Queries

Multiple `useQuery` hooks in the same component automatically run in parallel:

```tsx
function Dashboard() {
  const usersQuery = useQuery({ queryKey: ['users'], queryFn: fetchUsers })
  const todosQuery = useQuery({ queryKey: ['todos'], queryFn: fetchTodos })
  const statsQuery = useQuery({ queryKey: ['stats'], queryFn: fetchStats })

  // All three fetch simultaneously
  if (usersQuery.isPending || todosQuery.isPending || statsQuery.isPending) {
    return <Loading />
  }

  return (
    <div>
      <UserList users={usersQuery.data} />
      <TodoList todos={todosQuery.data} />
      <StatsPanel stats={statsQuery.data} />
    </div>
  )
}
```

No special configuration needed — React Query automatically deduplicates and parallelizes.

---

## useQueries — Dynamic Parallel Queries

When the number of queries is dynamic (not known at render time), use `useQueries`:

```tsx
import { useQueries } from '@tanstack/react-query'

function UserProfiles({ userIds }: { userIds: number[] }) {
  const userQueries = useQueries({
    queries: userIds.map((id) => ({
      queryKey: ['user', id],
      queryFn: () => fetchUser(id),
      staleTime: 60000,
    })),
  })

  const isLoading = userQueries.some((q) => q.isPending)
  const users = userQueries.map((q) => q.data).filter(Boolean)

  if (isLoading) return <Loading />

  return (
    <div>
      {users.map((user) => (
        <UserCard key={user.id} user={user} />
      ))}
    </div>
  )
}
```

### useQueries with Combine

Transform the combined results:

```tsx
const { data: allUsers, pending } = useQueries({
  queries: userIds.map((id) => ({
    queryKey: ['user', id],
    queryFn: () => fetchUser(id),
  })),
  combine: (results) => ({
    data: results.map((r) => r.data).filter(Boolean),
    pending: results.some((r) => r.isPending),
  }),
})

// allUsers is User[] (filtered, combined)
// pending is boolean
```

### Suspense with useQueries

```tsx
import { useSuspenseQueries } from '@tanstack/react-query'

function UserProfiles({ userIds }: { userIds: number[] }) {
  const userQueries = useSuspenseQueries({
    queries: userIds.map((id) => ({
      queryKey: ['user', id],
      queryFn: () => fetchUser(id),
    })),
  })

  // All data is guaranteed to be defined
  return (
    <div>
      {userQueries.map((q) => (
        <UserCard key={q.data.id} user={q.data} />
      ))}
    </div>
  )
}
```

---

## Dependent (Serial) Queries

Use the `enabled` option to make a query wait for another:

```tsx
function UserTodos({ userId }: { userId: number }) {
  // First query — fetch the user
  const { data: user } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
  })

  // Second query — depends on user data
  const { data: todos, isPending: todosLoading } = useQuery({
    queryKey: ['todos', user?.id],
    queryFn: () => fetchTodosByUser(user!.id),
    enabled: !!user, // Only fetch when user is available
  })

  if (!user) return <Loading />
  if (todosLoading) return <Loading />

  return (
    <div>
      <h1>{user.name}'s Todos</h1>
      <ul>
        {todos?.map((t) => <li key={t.id}>{t.title}</li>)}
      </ul>
    </div>
  )
}
```

### How Dependent Queries Work

1. First `useQuery` fetches immediately
2. Second `useQuery` has `enabled: false` (since `user` is undefined)
3. First query resolves → `user` is now defined → `enabled` becomes `true`
4. Second query starts fetching

### Status of Disabled Queries

When `enabled: false`:
- `status`: `'pending'` (no data)
- `fetchStatus`: `'idle'` (not fetching)
- `isPending`: `true`
- `isLoading`: `false` (not fetching)

---

## Chaining Multiple Dependencies

```tsx
function OrderDetails({ orderId }: { orderId: string }) {
  // 1. Fetch order
  const { data: order } = useQuery({
    queryKey: ['order', orderId],
    queryFn: () => fetchOrder(orderId),
  })

  // 2. Fetch customer (depends on order)
  const { data: customer } = useQuery({
    queryKey: ['customer', order?.customerId],
    queryFn: () => fetchCustomer(order!.customerId),
    enabled: !!order?.customerId,
  })

  // 3. Fetch customer preferences (depends on customer)
  const { data: preferences } = useQuery({
    queryKey: ['preferences', customer?.id],
    queryFn: () => fetchPreferences(customer!.id),
    enabled: !!customer?.id,
  })

  // Renders progressively as each query resolves
  return (
    <div>
      {order && <OrderInfo order={order} />}
      {customer && <CustomerInfo customer={customer} />}
      {preferences && <Preferences prefs={preferences} />}
    </div>
  )
}
```

---

## Combining Dependent and Parallel

Fetch some queries in parallel, others in sequence:

```tsx
function ProjectDashboard({ projectId }: { projectId: string }) {
  // Parallel: project and team members
  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(projectId),
  })

  const { data: members } = useQuery({
    queryKey: ['members', projectId],
    queryFn: () => fetchMembers(projectId),
  })

  // Dependent: tasks require project data for the correct team filter
  const { data: tasks } = useQuery({
    queryKey: ['tasks', projectId, project?.teamId],
    queryFn: () => fetchTasks(project!.teamId),
    enabled: !!project?.teamId,
  })

  // Dependent on tasks: statistics
  const { data: stats } = useQuery({
    queryKey: ['task-stats', projectId],
    queryFn: () => computeStats(tasks!),
    enabled: !!tasks,
  })

  return <div>{/* render all data */}</div>
}
```

---

## Common Patterns

### Fetch-Then-Render with Dependent Data

```tsx
// Custom hook for a complex dependent query pattern
function useProjectWithDetails(projectId: string) {
  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(projectId),
  })

  const detailQueries = useQueries({
    queries: (projectQuery.data?.moduleIds ?? []).map((moduleId) => ({
      queryKey: ['module', moduleId],
      queryFn: () => fetchModule(moduleId),
      enabled: !!projectQuery.data, // Wait for project
    })),
  })

  return {
    project: projectQuery.data,
    modules: detailQueries.map((q) => q.data).filter(Boolean),
    isLoading:
      projectQuery.isPending || detailQueries.some((q) => q.isPending),
  }
}
```

### Avoiding Request Waterfalls

```tsx
// BAD: Sequential fetches (waterfall)
// Component A fetches user → Component B (child) fetches todos

// GOOD: Parallel prefetch at route level
async function loader() {
  await Promise.all([
    queryClient.prefetchQuery({ queryKey: ['user'], queryFn: fetchUser }),
    queryClient.prefetchQuery({ queryKey: ['todos'], queryFn: fetchTodos }),
  ])
}
```

### Dynamic Query Count with Loading State

```tsx
function MultiUserView({ userIds }: { userIds: string[] }) {
  const queries = useQueries({
    queries: userIds.map((id) => ({
      queryKey: ['user', id],
      queryFn: () => fetchUser(id),
    })),
    combine: (results) => ({
      users: results.filter((r) => r.isSuccess).map((r) => r.data!),
      loading: results.filter((r) => r.isPending).length,
      errors: results.filter((r) => r.isError).length,
      total: results.length,
    }),
  })

  return (
    <div>
      <p>Loaded {queries.users.length}/{queries.total} ({queries.loading} loading, {queries.errors} errors)</p>
      {queries.users.map((user) => <UserCard key={user.id} user={user} />)}
    </div>
  )
}
```

---

## Common Pitfalls

1. **enabled with undefined query key values** — `queryKey: ['todos', user?.id]` with `user` undefined stores under `['todos', undefined]`. Always pair with `enabled`.

2. **Stale closures in queryFn** — The queryFn captures variables at definition time. Use the queryKey for dynamic values: `queryFn: ({ queryKey }) => fetch(queryKey[1])`.

3. **useQueries with empty array** — `useQueries({ queries: [] })` is valid and returns empty array.

4. **Dependent query stays pending forever** — If the parent query errors, the dependent query stays `pending` with `fetchStatus: 'idle'`. Handle parent errors explicitly.

5. **Too many parallel queries** — Browsers limit concurrent connections (~6 per domain). Hundreds of parallel queries will be throttled. Batch or paginate.

---

## Related

- **01-queries.md** — useQuery basics
- **09-suspense.md** — Suspense variants
- **07-prefetching.md** — Avoiding waterfalls with prefetching
