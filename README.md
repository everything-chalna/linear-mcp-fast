# linear-mcp-fast

Fast, read-only MCP server for Linear that reads from Linear.app's local cache on macOS.

**Why?**
- **Instant**: No API calls, reads directly from local IndexedDB cache
- **Offline**: Works without internet
- **Lower context**: Smaller responses for AI assistants

**Use with**: Official Linear MCP for write operations (comments, updates).

## Installation

```bash
pip install linear-mcp-fast
# or
uv pip install linear-mcp-fast
```

## Setup

### Claude Code

```bash
# 1. Add linear-mcp-fast (reads from local cache)
claude mcp add linear-fast -- uvx linear-mcp-fast

# 2. Add official Linear MCP (for writes)
claude mcp add --transport http linear https://mcp.linear.app/mcp
```

Now you have:
- `linear-fast` → Fast reads from local cache
- `linear` → Writes (comments, updates)

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "linear-fast": {
      "command": "uvx",
      "args": ["linear-mcp-fast"]
    },
    "linear": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.linear.app/mcp"]
    }
  }
}
```

### Cursor / VS Code

```json
{
  "mcpServers": {
    "linear-fast": {
      "command": "uvx",
      "args": ["linear-mcp-fast"]
    },
    "linear": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.linear.app/mcp"]
    }
  }
}
```

---

## Prerequisites

- **macOS** (Linear.app stores cache in `~/Library/Application Support/Linear/`)
- **Linear.app** installed and opened at least once

---

## Available Tools

### Reading (linear-fast)

| Tool | Description |
|------|-------------|
| `list_issues` | List issues with filters (assignee, team, state, priority) |
| `get_issue` | Get issue details with comments |
| `search_issues` | Search issues by title |
| `get_my_issues` | Get issues assigned to a user |
| `list_teams` | List all teams |
| `list_projects` | List all projects |
| `get_summary` | Get cache summary |

### Writing (official Linear MCP)

Use the official Linear MCP (`linear`) for:
- Creating/updating issues
- Adding comments
- Changing status

---

## Troubleshooting

### "Linear database not found"

Linear.app needs to be installed and opened at least once:
```bash
ls ~/Library/Application\ Support/Linear/IndexedDB/
```

### Data seems stale

Local cache is updated when Linear.app syncs. Open Linear.app to refresh.

---

## How It Works

```
Linear.app (Electron)
    ↓ syncs to
IndexedDB (LevelDB format)
~/Library/Application Support/Linear/IndexedDB/...
    ↓ read by
linear-mcp-fast
    ↓ provides
Fast read-only access to issues, users, teams, comments
```

---

## License

MIT
