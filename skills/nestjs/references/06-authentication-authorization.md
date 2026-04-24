# NestJS — Authentication & Authorization

> Source: [docs.nestjs.com/security/authentication](https://docs.nestjs.com/security/authentication) | @nestjs/core 11.x

## Table of Contents

- [Overview](#overview)
- [JWT Authentication Setup](#jwt-authentication-setup)
- [Passport Integration](#passport-integration)
- [JWT Strategy](#jwt-strategy)
- [Auth Guard](#auth-guard)
- [Role-Based Access Control](#role-based-access-control)
- [Claims-Based Authorization](#claims-based-authorization)
- [CASL Integration](#casl-integration)
- [Session-Based Authentication](#session-based-authentication)
- [API Key Authentication](#api-key-authentication)
- [Multi-Strategy Auth](#multi-strategy-auth)
- [Common Pitfalls](#common-pitfalls)

## Overview

NestJS authentication typically uses:
- **@nestjs/passport** — wraps Passport.js strategies as NestJS guards
- **@nestjs/jwt** — JWT token creation and verification
- **Guards** — protect routes based on authentication/authorization
- **Custom decorators** — extract user data and set metadata

### Required Packages

```bash
npm install @nestjs/passport @nestjs/jwt passport passport-jwt passport-local
npm install -D @types/passport-jwt @types/passport-local
```

## JWT Authentication Setup

### AuthModule

```typescript
import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { AuthService } from './auth.service';
import { AuthController } from './auth.controller';
import { JwtStrategy } from './strategies/jwt.strategy';
import { LocalStrategy } from './strategies/local.strategy';

@Module({
  imports: [
    PassportModule,
    JwtModule.registerAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        secret: config.get<string>('JWT_SECRET'),
        signOptions: { expiresIn: '15m' },
      }),
      inject: [ConfigService],
    }),
    UsersModule,
  ],
  controllers: [AuthController],
  providers: [AuthService, JwtStrategy, LocalStrategy],
  exports: [AuthService],
})
export class AuthModule {}
```

### AuthService

```typescript
@Injectable()
export class AuthService {
  constructor(
    private usersService: UsersService,
    private jwtService: JwtService,
  ) {}

  async validateUser(email: string, password: string): Promise<User | null> {
    const user = await this.usersService.findByEmail(email);
    if (user && await bcrypt.compare(password, user.passwordHash)) {
      return user;
    }
    return null;
  }

  async login(user: User) {
    const payload = { sub: user.id, email: user.email, roles: user.roles };
    return {
      accessToken: this.jwtService.sign(payload),
      refreshToken: this.jwtService.sign(payload, { expiresIn: '7d' }),
    };
  }

  async refreshToken(token: string) {
    const payload = this.jwtService.verify(token);
    const user = await this.usersService.findById(payload.sub);
    if (!user) throw new UnauthorizedException();
    return this.login(user);
  }
}
```

### AuthController

```typescript
@Controller('auth')
export class AuthController {
  constructor(private authService: AuthService) {}

  @Post('login')
  @UseGuards(LocalAuthGuard)
  @HttpCode(200)
  login(@Request() req) {
    return this.authService.login(req.user);
  }

  @Post('register')
  async register(@Body() dto: RegisterDto) {
    const user = await this.authService.register(dto);
    return this.authService.login(user);
  }

  @Post('refresh')
  refreshToken(@Body('refreshToken') token: string) {
    return this.authService.refreshToken(token);
  }

  @Get('profile')
  @UseGuards(JwtAuthGuard)
  getProfile(@Request() req) {
    return req.user;
  }
}
```

## Passport Integration

### Local Strategy (Username/Password)

```typescript
import { Strategy } from 'passport-local';
import { PassportStrategy } from '@nestjs/passport';

@Injectable()
export class LocalStrategy extends PassportStrategy(Strategy) {
  constructor(private authService: AuthService) {
    super({ usernameField: 'email' });
  }

  async validate(email: string, password: string): Promise<User> {
    const user = await this.authService.validateUser(email, password);
    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }
    return user;
  }
}
```

### Local Auth Guard

```typescript
@Injectable()
export class LocalAuthGuard extends AuthGuard('local') {}
```

## JWT Strategy

```typescript
import { ExtractJwt, Strategy } from 'passport-jwt';
import { PassportStrategy } from '@nestjs/passport';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(config: ConfigService) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: config.get<string>('JWT_SECRET'),
    });
  }

  async validate(payload: JwtPayload) {
    return { id: payload.sub, email: payload.email, roles: payload.roles };
  }
}
```

## Auth Guard

### JWT Guard

```typescript
@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  canActivate(context: ExecutionContext) {
    return super.canActivate(context);
  }

  handleRequest(err: any, user: any) {
    if (err || !user) {
      throw err || new UnauthorizedException();
    }
    return user;
  }
}
```

### Optional Auth Guard

```typescript
@Injectable()
export class OptionalJwtAuthGuard extends AuthGuard('jwt') {
  handleRequest(err: any, user: any) {
    return user || null;
  }
}
```

### Current User Decorator

```typescript
import { createParamDecorator, ExecutionContext } from '@nestjs/common';

export const CurrentUser = createParamDecorator(
  (data: string | undefined, ctx: ExecutionContext) => {
    const request = ctx.switchToHttp().getRequest();
    const user = request.user;
    return data ? user?.[data] : user;
  },
);

// Usage
@Get('profile')
@UseGuards(JwtAuthGuard)
getProfile(@CurrentUser() user: User) {
  return user;
}

@Get('email')
@UseGuards(JwtAuthGuard)
getEmail(@CurrentUser('email') email: string) {
  return { email };
}
```

## Role-Based Access Control

### Roles Decorator & Guard

```typescript
// roles.decorator.ts
export enum Role {
  User = 'user',
  Admin = 'admin',
  SuperAdmin = 'superadmin',
}

export const ROLES_KEY = 'roles';
export const Roles = (...roles: Role[]) => SetMetadata(ROLES_KEY, roles);

// roles.guard.ts
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<Role[]>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (!requiredRoles) return true;

    const { user } = context.switchToHttp().getRequest();
    return requiredRoles.some(role => user.roles?.includes(role));
  }
}

// Usage
@Controller('admin')
@UseGuards(JwtAuthGuard, RolesGuard)
export class AdminController {
  @Get('users')
  @Roles(Role.Admin)
  getUsers() {}

  @Delete('users/:id')
  @Roles(Role.SuperAdmin)
  deleteUser(@Param('id') id: string) {}
}
```

### Global Guard Registration

```typescript
@Module({
  providers: [
    { provide: APP_GUARD, useClass: JwtAuthGuard },
    { provide: APP_GUARD, useClass: RolesGuard },
  ],
})
export class AppModule {}
```

### Public Routes Decorator

```typescript
export const IS_PUBLIC_KEY = 'isPublic';
export const Public = () => SetMetadata(IS_PUBLIC_KEY, true);

@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  constructor(private reflector: Reflector) {
    super();
  }

  canActivate(context: ExecutionContext) {
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (isPublic) return true;
    return super.canActivate(context);
  }
}

// Usage
@Public()
@Get('health')
healthCheck() { return { status: 'ok' }; }
```

## Claims-Based Authorization

```typescript
export const PERMISSIONS_KEY = 'permissions';
export const RequirePermissions = (...permissions: string[]) =>
  SetMetadata(PERMISSIONS_KEY, permissions);

@Injectable()
export class PermissionsGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const required = this.reflector.getAllAndOverride<string[]>(PERMISSIONS_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (!required) return true;

    const { user } = context.switchToHttp().getRequest();
    return required.every(perm => user.permissions?.includes(perm));
  }
}

@Put(':id')
@RequirePermissions('users:update')
update(@Param('id') id: string, @Body() dto: UpdateUserDto) {}
```

## CASL Integration

CASL (Isomorphic Authorization) provides attribute-based access control:

```bash
npm install @casl/ability
```

```typescript
import { Ability, AbilityBuilder, AbilityClass } from '@casl/ability';

type Actions = 'manage' | 'create' | 'read' | 'update' | 'delete';
type Subjects = 'User' | 'Article' | 'Comment' | 'all';
export type AppAbility = Ability<[Actions, Subjects]>;

@Injectable()
export class CaslAbilityFactory {
  createForUser(user: User) {
    const { can, cannot, build } = new AbilityBuilder<AppAbility>(
      Ability as AbilityClass<AppAbility>,
    );

    if (user.roles.includes(Role.Admin)) {
      can('manage', 'all');
    } else {
      can('read', 'all');
      can('create', 'Article');
      can('update', 'Article', { authorId: user.id });
      can('delete', 'Article', { authorId: user.id });
      cannot('delete', 'User');
    }

    return build();
  }
}
```

## Session-Based Authentication

```bash
npm install express-session @types/express-session
```

```typescript
// main.ts
import * as session from 'express-session';

app.use(
  session({
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: { maxAge: 3600000 },
  }),
);
```

```typescript
@Injectable()
export class AuthenticatedGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    return request.isAuthenticated();
  }
}
```

## API Key Authentication

```typescript
@Injectable()
export class ApiKeyGuard implements CanActivate {
  constructor(private config: ConfigService) {}

  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const apiKey = request.headers['x-api-key'];
    const validKeys = this.config.get<string[]>('API_KEYS');
    return validKeys?.includes(apiKey) ?? false;
  }
}
```

## Multi-Strategy Auth

Support both JWT and API key authentication:

```typescript
@Injectable()
export class CombinedAuthGuard implements CanActivate {
  constructor(
    private jwtGuard: JwtAuthGuard,
    private apiKeyGuard: ApiKeyGuard,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();

    if (request.headers['x-api-key']) {
      return this.apiKeyGuard.canActivate(context);
    }

    return this.jwtGuard.canActivate(context) as Promise<boolean>;
  }
}
```

## Common Pitfalls

1. **JWT secret in code** — always use environment variables via `ConfigService`
2. **Not hashing passwords** — use bcrypt with salt rounds ≥ 10
3. **Guard order matters** — `@UseGuards(JwtAuthGuard, RolesGuard)` runs left to right; auth before authorization
4. **Missing Passport strategy name** — `PassportStrategy(Strategy, 'custom-name')` to avoid conflicts with multiple strategies
5. **Refresh token storage** — store refresh tokens hashed in the database, not in localStorage
6. **Token expiry** — access tokens should be short-lived (15m); use refresh tokens for renewal
