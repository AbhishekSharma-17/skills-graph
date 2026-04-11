---
name: payload-cms
description: "Payload CMS — open-source headless CMS and app framework built on Next.js with TypeScript. MANDATORY TRIGGERS: payload, payload-cms, payloadcms, payload cms, headless cms nextjs. Also trigger when building content management systems with Next.js, configuring CMS collections/fields/hooks, or implementing admin panels with TypeScript. When in doubt about whether to use this skill for CMS or content modeling tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["cms", "headless-cms", "nextjs", "typescript", "react", "content-management", "admin-panel", "api"]
---

# Payload CMS

> Version tracked: 3.82.x | Source: https://payloadcms.com/docs

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview](references/00-overview.md) | Starting with Payload, installation, core concepts, project structure |
| [01-collections](references/01-collections.md) | Defining collections, document schemas, CRUD config |
| [02-fields](references/02-fields.md) | Field types, validation, conditional logic, field-level config |
| [03-globals](references/03-globals.md) | Singleton data like site settings, nav, footers |
| [04-access-control](references/04-access-control.md) | Function-based access control, RBAC patterns, field-level |
| [05-hooks](references/05-hooks.md) | Lifecycle hooks for collections, globals, and fields |
| [06-authentication](references/06-authentication.md) | Auth strategies, JWT, API keys, email/password, custom |
| [07-apis](references/07-apis.md) | Local API, REST API, GraphQL — querying and mutations |
| [08-admin-panel](references/08-admin-panel.md) | Admin customization, custom components, live preview |
| [09-database-adapters](references/09-database-adapters.md) | Postgres, MongoDB, SQLite — adapter config and migrations |
| [10-rich-text-lexical](references/10-rich-text-lexical.md) | Lexical editor, features, custom nodes, serialization |
| [11-plugins](references/11-plugins.md) | Official plugins — SEO, forms, search, cloud storage, nested docs |
| [12-versions-drafts](references/12-versions-drafts.md) | Version history, drafts, autosave, publishing workflows |

## Installation

```bash
npx create-payload-app@latest my-project
# or add to existing Next.js app
npm install payload @payloadcms/next @payloadcms/richtext-lexical
```

## Quick Reference

- Docs: https://payloadcms.com/docs
- GitHub: https://github.com/payloadcms/payload
- npm: https://www.npmjs.com/package/payload
- Templates: https://payloadcms.com/get-started
