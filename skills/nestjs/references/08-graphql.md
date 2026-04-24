# NestJS — GraphQL

> Source: [docs.nestjs.com/graphql/quick-start](https://docs.nestjs.com/graphql/quick-start) | @nestjs/graphql 13.x

## Table of Contents

- [Overview](#overview)
- [Code-First Approach](#code-first-approach)
- [Schema-First Approach](#schema-first-approach)
- [Resolvers](#resolvers)
- [Mutations](#mutations)
- [Subscriptions](#subscriptions)
- [Data Loaders](#data-loaders)
- [Guards & Interceptors in GraphQL](#guards--interceptors-in-graphql)
- [Federation](#federation)
- [Complexity & Depth Limiting](#complexity--depth-limiting)
- [Common Pitfalls](#common-pitfalls)

## Overview

NestJS provides two approaches to building GraphQL APIs. Both use Apollo Server v4 under the hood (NestJS 11+).

```bash
npm install @nestjs/graphql @nestjs/apollo @apollo/server graphql
```

### Module Setup

```typescript
import { ApolloDriver, ApolloDriverConfig } from '@nestjs/apollo';
import { GraphQLModule } from '@nestjs/graphql';

@Module({
  imports: [
    GraphQLModule.forRoot<ApolloDriverConfig>({
      driver: ApolloDriver,
      autoSchemaFile: join(process.cwd(), 'src/schema.gql'),
      sortSchema: true,
      playground: true,
    }),
  ],
})
export class AppModule {}
```

## Code-First Approach

Define your GraphQL schema using TypeScript decorators. The schema is auto-generated.

### Object Types

```typescript
import { ObjectType, Field, Int, ID } from '@nestjs/graphql';

@ObjectType()
export class User {
  @Field(() => ID)
  id: number;

  @Field()
  name: string;

  @Field()
  email: string;

  @Field(() => [Post], { nullable: true })
  posts?: Post[];

  @Field()
  createdAt: Date;
}

@ObjectType()
export class Post {
  @Field(() => ID)
  id: number;

  @Field()
  title: string;

  @Field({ nullable: true })
  content?: string;

  @Field(() => User)
  author: User;
}
```

### Input Types

```typescript
import { InputType, Field, PartialType } from '@nestjs/graphql';

@InputType()
export class CreateUserInput {
  @Field()
  @IsString()
  name: string;

  @Field()
  @IsEmail()
  email: string;
}

@InputType()
export class UpdateUserInput extends PartialType(CreateUserInput) {
  @Field(() => Int)
  id: number;
}
```

### Enums

```typescript
import { registerEnumType } from '@nestjs/graphql';

export enum UserRole {
  ADMIN = 'ADMIN',
  USER = 'USER',
  MODERATOR = 'MODERATOR',
}

registerEnumType(UserRole, { name: 'UserRole' });
```

## Schema-First Approach

Write `.graphql` files manually, generate TypeScript types from them.

```graphql
# schema.graphql
type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]
}

type Query {
  users: [User!]!
  user(id: ID!): User
}

input CreateUserInput {
  name: String!
  email: String!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
}
```

```typescript
// Module setup for schema-first
GraphQLModule.forRoot<ApolloDriverConfig>({
  driver: ApolloDriver,
  typePaths: ['./**/*.graphql'],
  definitions: {
    path: join(process.cwd(), 'src/graphql.ts'),
    outputAs: 'class',
  },
}),
```

## Resolvers

Resolvers handle GraphQL queries and mutations, equivalent to controllers in REST.

```typescript
import { Resolver, Query, Args, Int, ResolveField, Parent } from '@nestjs/graphql';

@Resolver(() => User)
export class UsersResolver {
  constructor(
    private usersService: UsersService,
    private postsService: PostsService,
  ) {}

  @Query(() => [User], { name: 'users' })
  findAll(
    @Args('page', { type: () => Int, defaultValue: 1 }) page: number,
    @Args('limit', { type: () => Int, defaultValue: 10 }) limit: number,
  ) {
    return this.usersService.findAll(page, limit);
  }

  @Query(() => User, { name: 'user', nullable: true })
  findOne(@Args('id', { type: () => Int }) id: number) {
    return this.usersService.findOne(id);
  }

  @ResolveField(() => [Post])
  posts(@Parent() user: User) {
    return this.postsService.findByAuthorId(user.id);
  }
}
```

### Paginated Results

```typescript
@ObjectType()
export class PaginatedUsers {
  @Field(() => [User])
  items: User[];

  @Field(() => Int)
  total: number;

  @Field()
  hasMore: boolean;
}

@Query(() => PaginatedUsers)
async paginatedUsers(
  @Args('page', { type: () => Int, defaultValue: 1 }) page: number,
  @Args('limit', { type: () => Int, defaultValue: 10 }) limit: number,
): Promise<PaginatedUsers> {
  const [items, total] = await this.usersService.findAll(page, limit);
  return { items, total, hasMore: page * limit < total };
}
```

## Mutations

```typescript
@Resolver(() => User)
export class UsersResolver {
  @Mutation(() => User)
  createUser(@Args('input') input: CreateUserInput) {
    return this.usersService.create(input);
  }

  @Mutation(() => User)
  updateUser(@Args('input') input: UpdateUserInput) {
    return this.usersService.update(input.id, input);
  }

  @Mutation(() => Boolean)
  removeUser(@Args('id', { type: () => Int }) id: number) {
    return this.usersService.remove(id);
  }
}
```

## Subscriptions

Real-time updates via WebSocket (using `graphql-ws`):

```bash
npm install graphql-ws
```

```typescript
// Module config
GraphQLModule.forRoot<ApolloDriverConfig>({
  driver: ApolloDriver,
  autoSchemaFile: true,
  subscriptions: {
    'graphql-ws': true,
  },
}),
```

```typescript
import { Subscription } from '@nestjs/graphql';
import { PubSub } from 'graphql-subscriptions';

const pubSub = new PubSub();

@Resolver(() => Post)
export class PostsResolver {
  @Mutation(() => Post)
  async createPost(@Args('input') input: CreatePostInput) {
    const post = await this.postsService.create(input);
    pubSub.publish('postCreated', { postCreated: post });
    return post;
  }

  @Subscription(() => Post, {
    filter: (payload, variables) =>
      payload.postCreated.authorId === variables.authorId,
  })
  postCreated(@Args('authorId', { type: () => Int }) authorId: number) {
    return pubSub.asyncIterableIterator('postCreated');
  }
}
```

## Data Loaders

Solve the N+1 problem by batching and caching database queries:

```typescript
import * as DataLoader from 'dataloader';

@Injectable({ scope: Scope.REQUEST })
export class UsersLoader {
  constructor(private usersService: UsersService) {}

  readonly batchUsers = new DataLoader<number, User>(async (ids: number[]) => {
    const users = await this.usersService.findByIds([...ids]);
    const usersMap = new Map(users.map(u => [u.id, u]));
    return ids.map(id => usersMap.get(id) || new Error(`User ${id} not found`));
  });
}

@Resolver(() => Post)
export class PostsResolver {
  constructor(private usersLoader: UsersLoader) {}

  @ResolveField(() => User)
  author(@Parent() post: Post) {
    return this.usersLoader.batchUsers.load(post.authorId);
  }
}
```

## Guards & Interceptors in GraphQL

```typescript
import { GqlExecutionContext } from '@nestjs/graphql';

@Injectable()
export class GqlAuthGuard extends AuthGuard('jwt') {
  getRequest(context: ExecutionContext) {
    const ctx = GqlExecutionContext.create(context);
    return ctx.getContext().req;
  }
}

@Resolver()
@UseGuards(GqlAuthGuard)
export class ProtectedResolver {
  @Query(() => User)
  me(@CurrentUser() user: User) {
    return user;
  }
}
```

## Federation

Build a distributed GraphQL architecture with Apollo Federation:

```bash
npm install @apollo/subgraph
```

```typescript
// Users subgraph
GraphQLModule.forRoot<ApolloDriverConfig>({
  driver: ApolloDriver,
  autoSchemaFile: { federation: 2 },
}),

@ObjectType()
@Directive('@key(fields: "id")')
export class User {
  @Field(() => ID)
  id: number;

  @Field()
  name: string;
}

@Resolver(() => User)
export class UsersResolver {
  @ResolveReference()
  resolveReference(reference: { __typename: string; id: number }) {
    return this.usersService.findOne(reference.id);
  }
}
```

## Complexity & Depth Limiting

Protect against abusive queries:

```typescript
import { complexityEstimatorPlugin } from 'graphql-query-complexity';

GraphQLModule.forRoot<ApolloDriverConfig>({
  driver: ApolloDriver,
  autoSchemaFile: true,
  plugins: [
    complexityEstimatorPlugin({
      maximumComplexity: 100,
      estimators: [
        fieldExtensionsEstimator(),
        simpleEstimator({ defaultComplexity: 1 }),
      ],
    }),
  ],
}),
```

```bash
npm install graphql-depth-limit
```

```typescript
import depthLimit from 'graphql-depth-limit';

GraphQLModule.forRoot<ApolloDriverConfig>({
  driver: ApolloDriver,
  autoSchemaFile: true,
  validationRules: [depthLimit(5)],
}),
```

## Common Pitfalls

1. **N+1 queries** — always use DataLoader for `@ResolveField()` that queries the database
2. **Missing `@Field()` decorator** — fields without `@Field()` won't appear in the schema
3. **Nullable handling** — GraphQL defaults to non-null; use `{ nullable: true }` explicitly
4. **`PubSub` in production** — `graphql-subscriptions` PubSub is in-memory; use Redis PubSub for multi-instance
5. **Guard context** — GraphQL guards must override `getRequest()` to extract from GqlExecutionContext
6. **Schema auto-generation path** — `autoSchemaFile: true` keeps schema in memory; use a path to persist
