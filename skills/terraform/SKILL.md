---
name: terraform
description: "HashiCorp Terraform — Infrastructure as Code (IaC) tool for provisioning and managing cloud/on-prem infrastructure declaratively using HCL. MANDATORY TRIGGERS: terraform, HCL, HashiCorp Configuration Language, infrastructure as code, IaC, terraform plan, terraform apply, terraform state, terraform modules, terraform providers, AWS provider, Azure provider, Google Cloud provider, terraform backend, terraform workspaces, terraform registry, tfstate, tfvars. Also trigger when the user asks about provisioning cloud resources declaratively, writing .tf files, managing state, authoring reusable modules, or planning/applying infrastructure changes. When in doubt about whether to use this skill for IaC tasks on AWS/Azure/GCP/Kubernetes with Terraform, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["terraform", "iac", "devops", "hashicorp", "cloud"]
---

# Terraform

> **Skill Version:** 1.0.0 | **Tracks:** Terraform v1.14.8 | **Source:** https://developer.hashicorp.com/terraform/docs

Terraform is HashiCorp's Infrastructure as Code tool that provisions and manages resources across 4,000+ providers using a declarative configuration language (HCL). This skill covers the full Terraform workflow — from writing configurations to managing state, composing modules, and integrating with CI/CD.

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview** | `references/00-overview.md` | "what is terraform", "install terraform", "getting started", "tf basics" |
| **Configuration Language** | `references/01-configuration-language.md` | "HCL syntax", "blocks", "expressions", "types", "terraform language" |
| **Providers** | `references/02-providers.md` | "provider block", "required_providers", "provider aliases", "provider version" |
| **Resources** | `references/03-resources.md` | "resource block", "arguments", "creating resources", "importing" |
| **Variables & Outputs** | `references/04-variables-and-outputs.md` | "input variables", "tfvars", "output values", "locals", "validation" |
| **State** | `references/05-state.md` | "terraform state", "tfstate", "remote backend", "state locking", "workspaces" |
| **Modules** | `references/06-modules.md` | "modules", "module composition", "reusable modules", "module registry" |
| **Data Sources** | `references/07-data-sources.md` | "data block", "data source", "fetching existing resources", "ephemeral data" |
| **Meta-Arguments & Lifecycle** | `references/08-lifecycle-and-meta-arguments.md` | "count", "for_each", "depends_on", "lifecycle", "dynamic blocks" |
| **Functions & Expressions** | `references/09-functions-and-expressions.md` | "built-in functions", "conditionals", "for expressions", "string manipulation" |
| **Testing & Validation** | `references/10-testing-and-validation.md` | "terraform test", "preconditions", "postconditions", "validate" |
| **CI/CD Patterns** | `references/11-cicd-patterns.md` | "gitops", "atlantis", "github actions terraform", "automated plans" |
| **Best Practices** | `references/12-best-practices.md` | "secrets management", "common pitfalls", "security", "tf conventions" |

## Installation

```bash
# macOS
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Linux (apt)
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Copy skill to Claude Code
cp -r . ~/.claude/skills/terraform/
```

## Quick Reference

- **Docs:** https://developer.hashicorp.com/terraform/docs
- **Registry:** https://registry.terraform.io
- **Language Reference:** https://developer.hashicorp.com/terraform/language
- **Provider Catalog:** https://registry.terraform.io/browse/providers
