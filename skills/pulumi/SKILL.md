---
name: pulumi
description: "Pulumi — Infrastructure as Code using real programming languages (Python, TypeScript, Go, C#, Java, YAML). MANDATORY TRIGGERS: pulumi, pulumi up, pulumi preview, pulumi stack, pulumi config, Pulumi.yaml, infrastructure as code Python, IaC TypeScript, pulumi import, CrossGuard, Pulumi ESC, Pulumi Automation API, pulumi destroy, pulumi refresh, ComponentResource. Also trigger when the user asks about provisioning cloud infrastructure with Python or TypeScript code, managing IaC state with Pulumi, building reusable infrastructure components, policy as code for cloud resources, or migrating from Terraform to Pulumi. When in doubt about whether to use this skill for IaC tasks using general-purpose languages, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["pulumi", "iac", "devops", "cloud", "infrastructure", "python", "typescript"]
---

# Pulumi

> **Skill Version:** 1.0.0 | **Tracks:** Pulumi v3.242.0 | **Source:** https://www.pulumi.com/docs/

Pulumi is an infrastructure as code platform that lets you define, deploy, and manage cloud infrastructure using real programming languages — Python, TypeScript, Go, C#, Java, and YAML. Unlike HCL-based tools, Pulumi gives you loops, conditionals, classes, package managers, and testing frameworks out of the box.

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview** | `references/00-overview.md` | "what is pulumi", "install pulumi", "getting started", "pulumi vs terraform" |
| **Projects & Stacks** | `references/01-projects-stacks.md` | "Pulumi.yaml", "pulumi stack", "stack init", "environments", "organizations" |
| **Resources** | `references/02-resources.md` | "resource types", "custom resource", "URN", "resource lifecycle", "CRUD" |
| **Resource Options** | `references/03-resource-options.md` | "depends_on", "protect", "aliases", "ignore_changes", "transforms", "parent" |
| **Inputs & Outputs** | `references/04-inputs-outputs.md` | "Output", "apply", "all", "concat", "stack outputs", "stack references" |
| **Configuration & Secrets** | `references/05-configuration-secrets.md` | "pulumi config", "secrets", "encryption", "Pulumi ESC", "environment variables" |
| **State & Backends** | `references/06-state-backends.md` | "state", "backend", "Pulumi Cloud", "self-managed", "state import", "locking" |
| **Providers** | `references/07-providers.md` | "provider", "AWS", "Azure", "GCP", "explicit provider", "dynamic provider" |
| **Component Resources** | `references/08-component-resources.md` | "ComponentResource", "reusable component", "abstraction", "multi-language" |
| **Testing** | `references/09-testing.md` | "unit test", "mock", "property testing", "integration test", "pulumi test" |
| **Policy & CrossGuard** | `references/10-policy-crossguard.md` | "policy as code", "CrossGuard", "policy pack", "compliance", "enforcement" |
| **Automation API** | `references/11-automation-api.md` | "Automation API", "programmatic", "inline program", "embedded pulumi" |
| **CI/CD & Migration** | `references/12-ci-cd-migration.md` | "GitHub Actions", "CI/CD", "Pulumi Deployments", "terraform migration", "import" |

## Installation

```bash
# macOS
brew install pulumi/tap/pulumi

# Linux (curl)
curl -fsSL https://get.pulumi.com | sh

# Windows (choco)
choco install pulumi

# Python SDK
pip install pulumi pulumi-aws pulumi-azure-native pulumi-gcp

# Copy skill to Claude Code
cp -r . ~/.claude/skills/pulumi/
```

## Quick Reference

- **Docs:** https://www.pulumi.com/docs/
- **Registry:** https://www.pulumi.com/registry/
- **Examples:** https://github.com/pulumi/examples
- **GitHub:** https://github.com/pulumi/pulumi
