---
name: playwright
description: "End-to-end testing and browser automation framework by Microsoft — locators, assertions, fixtures, network mocking, visual testing, tracing, codegen, API testing, and CI/CD integration. MANDATORY TRIGGERS: playwright, Playwright, @playwright/test, page.goto, page.click, page.locator, getByRole, getByText, getByTestId, expect(page), toHaveScreenshot, playwright.config, npx playwright. Also trigger when user wants to write E2E tests, automate browser interactions, test across Chromium/Firefox/WebKit, mock network requests in tests, do visual regression testing, generate tests with codegen, or set up CI test pipelines. When in doubt about whether to use this skill for browser testing or E2E automation tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["playwright", "e2e-testing", "browser-automation", "testing", "locators", "assertions", "fixtures", "network-mocking", "visual-testing", "ci-cd"]
---

# Playwright — Skill Router

> Fast and reliable end-to-end testing for modern web apps.

**Source:** [playwright.dev](https://playwright.dev) | **Package:** `@playwright/test` v1.59 | **License:** Apache-2.0

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, project structure, configuration |
| **Locators** | `references/01-locators.md` | Finding elements, getByRole, getByText, getByTestId, chaining, filtering |
| **Actions & Interactions** | `references/02-actions.md` | Clicking, typing, selecting, uploading, drag-and-drop, auto-waiting |
| **Assertions** | `references/03-assertions.md` | expect, web-first assertions, toBeVisible, toHaveText, polling, soft assertions |
| **Page Object Model** | `references/04-page-object-model.md` | POM pattern, reusable page classes, organizing large test suites |
| **Fixtures & Hooks** | `references/05-fixtures.md` | Test fixtures, worker fixtures, hooks, parameterized tests, extending |
| **Network & Mocking** | `references/06-network-mocking.md` | Intercepting requests, mocking APIs, modifying responses, HAR replay |
| **API Testing** | `references/07-api-testing.md` | APIRequestContext, standalone API tests, hybrid browser+API tests |
| **Authentication** | `references/08-authentication.md` | Storage state, global setup, reusing auth, multi-user scenarios |
| **Visual Testing** | `references/09-visual-testing.md` | Screenshot comparison, toHaveScreenshot, baselines, masking, CI strategies |
| **Tracing & Debugging** | `references/10-tracing-debugging.md` | Trace viewer, debug mode, UI mode, codegen, inspector, console logs |
| **Configuration & CLI** | `references/11-configuration-cli.md` | playwright.config.ts, projects, reporters, retries, sharding, CLI commands |
| **CI/CD Integration** | `references/12-ci-cd.md` | GitHub Actions, Docker, parallel CI, artifacts, blob reports, best practices |

## Installation

```bash
# Create a new project
npm init playwright@latest

# Or add to existing project
npm install -D @playwright/test
npx playwright install

# Run tests
npx playwright test

# Run with UI mode
npx playwright test --ui

# Generate tests
npx playwright codegen
```

## Quick Reference

- **Docs:** https://playwright.dev/docs/intro
- **GitHub:** https://github.com/microsoft/playwright
- **npm:** https://www.npmjs.com/package/@playwright/test
- **API:** https://playwright.dev/docs/api/class-playwright
- **Release Notes:** https://playwright.dev/docs/release-notes
