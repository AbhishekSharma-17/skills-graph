# Milvus — Security & RBAC

> Source: [milvus.io/docs/users_and_roles.md](https://milvus.io/docs/users_and_roles.md) | Version: 3.0-beta

## Table of Contents

- [Authentication](#authentication)
- [User Management](#user-management)
- [Role Management](#role-management)
- [Privilege Management](#privilege-management)
- [Privilege Groups](#privilege-groups)
- [TLS Encryption](#tls-encryption)
- [Security Best Practices](#security-best-practices)
- [Common Pitfalls](#common-pitfalls)

## Overview

Milvus provides enterprise security features including authentication, role-based access control (RBAC), TLS encryption, and audit logging. These features protect data in multi-tenant and production environments.

## Authentication

### Default Credentials

Milvus ships with a default root user:
- **Username:** `root`
- **Password:** `Milvus`

```python
from pymilvus import MilvusClient

client = MilvusClient(
    uri="http://localhost:19530",
    token="root:Milvus",
)
```

**Always change the default password in production.**

### Enable Authentication

In `milvus.yaml` or Docker environment:

```yaml
common:
  security:
    authorizationEnabled: true
```

Or via Docker Compose environment variable:

```yaml
environment:
  - COMMON_SECURITY_AUTHORIZATIONENABLED=true
```

## User Management

### Create a User

```python
client.create_user(
    user_name="app_user",
    password="S3cur3P@ssw0rd!",
)
```

**Username rules:** Start with a letter; only letters, numbers, underscores.

**Password rules:** 8–64 characters; must include 3 of: uppercase, lowercase, numbers, special characters.

### List Users

```python
users = client.list_users()
# ['root', 'app_user']
```

### Update Password

```python
client.update_password(
    user_name="app_user",
    old_password="S3cur3P@ssw0rd!",
    new_password="N3wS3cur3P@ss!",
)
```

### Drop a User

```python
client.drop_user(user_name="app_user")
```

### Describe a User

```python
info = client.describe_user(user_name="app_user")
# Returns user details and assigned roles
```

## Role Management

### Built-In Roles

| Role | Permissions |
|------|------------|
| `admin` | Full access to all resources |
| `public` | Read access to collections (CollectionReadOnly) |

### Create a Custom Role

```python
client.create_role(role_name="data_scientist")
```

### List Roles

```python
roles = client.list_roles()
# ['admin', 'public', 'data_scientist']
```

### Grant a Role to a User

```python
client.grant_role(
    user_name="app_user",
    role_name="data_scientist",
)
```

### Revoke a Role from a User

```python
client.revoke_role(
    user_name="app_user",
    role_name="data_scientist",
)
```

### Drop a Role

```python
client.drop_role(role_name="data_scientist")
```

## Privilege Management

### Grant Privileges to a Role

```python
# Grant search permission on a specific collection
client.grant_privilege(
    role_name="data_scientist",
    object_type="Collection",
    object_name="articles",
    privilege="Search",
)

# Grant insert permission
client.grant_privilege(
    role_name="data_scientist",
    object_type="Collection",
    object_name="articles",
    privilege="Insert",
)

# Grant all collection privileges
client.grant_privilege(
    role_name="data_scientist",
    object_type="Collection",
    object_name="*",          # all collections
    privilege="CollectionReadOnly",
)
```

### Available Privileges

| Object Type | Privilege | Description |
|-------------|-----------|-------------|
| Collection | `Insert` | Insert entities |
| Collection | `Delete` | Delete entities |
| Collection | `Search` | Vector search |
| Collection | `Query` | Scalar query |
| Collection | `Load` | Load collection |
| Collection | `Release` | Release collection |
| Collection | `CreateIndex` | Create indexes |
| Collection | `DropIndex` | Drop indexes |
| Collection | `GetStatistics` | Collection stats |
| Collection | `Compaction` | Trigger compaction |
| Collection | `CollectionReadOnly` | All read operations |
| Collection | `CollectionReadWrite` | All read/write operations |
| Collection | `CollectionAdmin` | Full collection control |
| Global | `CreateCollection` | Create new collections |
| Global | `DropCollection` | Drop collections |
| Global | `CreateDatabase` | Create databases |
| Global | `DropDatabase` | Drop databases |
| Global | `ManageUser` | Create/drop users |
| Global | `ManageRole` | Create/drop roles |
| Global | `ManagePrivilege` | Grant/revoke privileges |

### Revoke Privileges

```python
client.revoke_privilege(
    role_name="data_scientist",
    object_type="Collection",
    object_name="articles",
    privilege="Insert",
)
```

### Describe Role Privileges

```python
privileges = client.describe_role(role_name="data_scientist")
```

## Privilege Groups

Group multiple privileges for easier management:

```python
# Create a privilege group
client.create_privilege_group(group_name="reader_group")

# Add privileges to the group
client.add_privileges_to_group(
    group_name="reader_group",
    privileges=["Search", "Query", "GetStatistics"],
)

# Grant the group to a role
client.grant_privilege(
    role_name="data_scientist",
    object_type="Collection",
    object_name="*",
    privilege="reader_group",
)
```

## TLS Encryption

### Generate Certificates

```bash
# Generate CA key and certificate
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 365 -key ca.key -out ca.pem

# Generate server key and certificate
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr
openssl x509 -req -days 365 -in server.csr -CA ca.pem -CAkey ca.key -out server.pem
```

### Enable TLS in Milvus

```yaml
# milvus.yaml
tls:
  serverPemPath: /milvus/tls/server.pem
  serverKeyPath: /milvus/tls/server.key
  caPemPath: /milvus/tls/ca.pem

common:
  security:
    tlsMode: 2  # 0=off, 1=one-way, 2=mutual
```

### Connect with TLS

```python
from pymilvus import MilvusClient

client = MilvusClient(
    uri="https://localhost:19530",
    token="root:Milvus",
    server_pem_path="path/to/server.pem",
    server_name="localhost",
)
```

## Security Best Practices

1. **Change default credentials** — never use `root:Milvus` in production
2. **Enable authentication** — set `authorizationEnabled: true`
3. **Use TLS** — encrypt all client-server communication
4. **Principle of least privilege** — grant only necessary permissions per role
5. **Separate admin and application users** — don't use root for application queries
6. **Audit role assignments** — regularly review who has what access
7. **Use privilege groups** — simplify management of common permission sets

## RBAC Setup Example

```python
# As root, set up application users
admin_client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")

# Create roles
admin_client.create_role(role_name="app_reader")
admin_client.create_role(role_name="app_writer")

# Grant privileges
admin_client.grant_privilege("app_reader", "Collection", "*", "Search")
admin_client.grant_privilege("app_reader", "Collection", "*", "Query")
admin_client.grant_privilege("app_writer", "Collection", "*", "CollectionReadWrite")

# Create users
admin_client.create_user("search_service", "S3archP@ss123!")
admin_client.create_user("ingestion_service", "Ing3stP@ss456!")

# Assign roles
admin_client.grant_role("search_service", "app_reader")
admin_client.grant_role("ingestion_service", "app_writer")

# Application connects with limited user
app_client = MilvusClient(uri="http://localhost:19530", token="search_service:S3archP@ss123!")
```

## Common Pitfalls

- **Forgetting to enable auth** — RBAC rules are ignored if `authorizationEnabled` is false
- **Using root in application code** — creates security risk; create dedicated service users
- **Wildcard privileges on production** — `object_name="*"` grants access to all collections
- **Not using TLS** — credentials sent in plaintext without encryption
- **Password complexity** — weak passwords are rejected; must meet 3-of-4 character type rule
