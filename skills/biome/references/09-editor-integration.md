# Biome — Editor Integration

> Source: [biomejs.dev/editors](https://biomejs.dev/editors/) | Version: 2.5.x

## Table of Contents
- [Overview](#overview)
- [VS Code](#vs-code)
- [IntelliJ / JetBrains IDEs](#intellij--jetbrains-ides)
- [Zed](#zed)
- [Neovim](#neovim)
- [Helix](#helix)
- [Sublime Text](#sublime-text)
- [Daemon Mode](#daemon-mode)
- [Recommended Settings](#recommended-settings)
- [Troubleshooting](#troubleshooting)

---

## Overview

Biome integrates with editors via the Language Server Protocol (LSP). It provides:

- **Real-time diagnostics** — lint errors/warnings as you type
- **Format on save** — automatic formatting when saving files
- **Quick fixes** — code actions for lint violations
- **Import organization** — sort imports on save or via command
- **Hover information** — explanations for lint rule violations

All editors connect to the same Biome binary. Install Biome as a project dependency, then configure your editor.

## VS Code

### Installation

Install the official [Biome VS Code extension](https://marketplace.visualstudio.com/items?itemName=biomejs.biome) from the marketplace. Also works in VSCodium, Cursor, and other VS Code forks (via Open VSX).

### Recommended Settings

```json
// .vscode/settings.json
{
  // Use Biome as the default formatter
  "editor.defaultFormatter": "biomejs.biome",

  // Format on save
  "editor.formatOnSave": true,

  // Organize imports on save
  "editor.codeActionsOnSave": {
    "source.organizeImports.biome": "explicit",
    "source.fixAll.biome": "explicit"
  },

  // Language-specific formatter overrides
  "[javascript]": { "editor.defaultFormatter": "biomejs.biome" },
  "[typescript]": { "editor.defaultFormatter": "biomejs.biome" },
  "[typescriptreact]": { "editor.defaultFormatter": "biomejs.biome" },
  "[javascriptreact]": { "editor.defaultFormatter": "biomejs.biome" },
  "[json]": { "editor.defaultFormatter": "biomejs.biome" },
  "[jsonc]": { "editor.defaultFormatter": "biomejs.biome" },
  "[css]": { "editor.defaultFormatter": "biomejs.biome" },
  "[graphql]": { "editor.defaultFormatter": "biomejs.biome" }
}
```

### Available Code Actions

| Action | Description |
|--------|-------------|
| `source.fixAll.biome` | Apply all safe fixes |
| `source.organizeImports.biome` | Sort and group imports |
| `source.suppressRule.inline.biome` | Add `biome-ignore` comment |
| Quick Fix (lightbulb) | Rule-specific fix suggestions |

### Extension Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `biome.enabled` | `true` | Enable/disable the extension |
| `biome.lspBin` | — | Custom path to Biome binary |
| `biome.requireConfiguration` | `false` | Only activate if biome.json exists |

### Disabling Prettier and ESLint

When migrating, disable the old extensions for Biome-supported files:

```json
{
  "prettier.enable": false,
  "eslint.enable": false
}
```

Or selectively disable per language:

```json
{
  "[typescript]": {
    "editor.defaultFormatter": "biomejs.biome"
  }
}
```

## IntelliJ / JetBrains IDEs

Works with IntelliJ IDEA, WebStorm, PhpStorm, PyCharm, and other JetBrains IDEs.

### Installation

1. Open **Settings/Preferences** → **Plugins** → **Marketplace**
2. Search "Biome" → click **Install**
3. Restart the IDE

### Configuration

1. **Settings** → **Languages & Frameworks** → **Biome**
2. The plugin auto-detects `node_modules/.bin/biome`
3. Enable **LSP-based Code Formatting** for formatting support

### Format on Save

Use the standard IntelliJ "Reformat Code" action (Ctrl+Alt+L / Cmd+Alt+L). To auto-format on save:

1. **Settings** → **Tools** → **Actions on Save**
2. Enable **Reformat code** → select **Biome** as the formatter

### Organize Imports

Use **Code** → **Optimize Imports** (Ctrl+Alt+O / Cmd+Alt+O), which triggers Biome's import sorting via LSP.

## Zed

Zed has built-in Biome support.

### Configuration

```json
// settings.json
{
  "formatter": {
    "external": {
      "command": "biome",
      "arguments": ["format", "--stdin-file-path", "{buffer_path}"]
    }
  },
  "lsp": {
    "biome": {
      "binary": { "path": "node_modules/.bin/biome" }
    }
  }
}
```

## Neovim

Use Biome with `nvim-lspconfig` or `none-ls` (null-ls successor).

### Using nvim-lspconfig

```lua
-- init.lua or lua/plugins/lsp.lua
require("lspconfig").biome.setup({
  cmd = { "npx", "@biomejs/biome", "lsp-proxy" },
  root_dir = require("lspconfig.util").root_pattern("biome.json", "biome.jsonc"),
})
```

### Using conform.nvim (formatting)

```lua
require("conform").setup({
  formatters_by_ft = {
    javascript = { "biome" },
    typescript = { "biome" },
    typescriptreact = { "biome" },
    javascriptreact = { "biome" },
    json = { "biome" },
    css = { "biome" },
  },
  format_on_save = {
    timeout_ms = 500,
    lsp_fallback = true,
  },
})
```

### Using nvim-lint (linting)

```lua
require("lint").linters_by_ft = {
  javascript = { "biomejs" },
  typescript = { "biomejs" },
}
```

## Helix

```toml
# ~/.config/helix/languages.toml
[[language]]
name = "typescript"
language-servers = ["biome"]
auto-format = true
formatter = { command = "biome", args = ["format", "--stdin-file-path", "file.ts"] }

[language-server.biome]
command = "biome"
args = ["lsp-proxy"]
```

## Sublime Text

Install the [LSP-biome](https://packagecontrol.io/packages/LSP-biome) package through Package Control.

## Daemon Mode

For faster editor responsiveness, Biome can run as a persistent daemon:

```bash
# Start the daemon
npx @biomejs/biome start

# Stop the daemon
npx @biomejs/biome stop
```

The daemon keeps the project parsed in memory, making subsequent operations near-instant. The VS Code and IntelliJ extensions manage the daemon automatically.

### When to Use Daemon Mode

- **Large projects** — avoids re-parsing on every keystroke
- **Slow file systems** — keeps file contents cached
- **Multiple editor windows** — shares a single Biome instance

## Recommended Settings

### Team-Shared VS Code Settings

Commit a `.vscode/settings.json` and `.vscode/extensions.json`:

```json
// .vscode/extensions.json
{
  "recommendations": ["biomejs.biome"]
}
```

```json
// .vscode/settings.json
{
  "editor.defaultFormatter": "biomejs.biome",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports.biome": "explicit"
  }
}
```

## Troubleshooting

### Extension not finding Biome binary

Ensure Biome is installed as a project dependency:
```bash
npm ls @biomejs/biome
```

Or set a custom path in VS Code settings:
```json
{ "biome.lspBin": "./node_modules/.bin/biome" }
```

### Formatter conflicts with Prettier

Disable Prettier for Biome-supported files or uninstall the Prettier extension entirely.

### LSP not responding

Restart the Biome daemon:
```bash
npx @biomejs/biome stop && npx @biomejs/biome start
```

Or in VS Code: Command Palette → "Biome: Restart LSP Server"

### Diagnostics not updating

Check that `biome.json` exists in the project root. Run `npx @biomejs/biome rage` and include the output in bug reports.
