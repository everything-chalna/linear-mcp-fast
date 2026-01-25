# linear-mcp-fast

Fast, read-only MCP server for Linear that reads from Linear.app's local cache on macOS.

## Why I Built This

While using the official Linear MCP with Claude Code, I noticed that **read operations consumed too much context**. Every issue query returned verbose responses with metadata I didn't need, eating into the AI's context window.

The problem:
- Official Linear MCP makes API calls for every read
- Responses include excessive metadata (full user objects, workflow states, etc.)
- Context window fills up quickly when exploring issues
- Slower response times due to network latency

My solution: **Read directly from Linear.app's local cache.**

Linear.app (Electron) syncs all your data to a local IndexedDB. This MCP server reads from that cache, giving you:

- **Zero API calls** - Instant reads from disk
- **Smaller responses** - Only the fields you need
- **Offline access** - Works without internet
- **Faster iteration** - No rate limits, no latency

**Use with**: Official Linear MCP for write operations (comments, status updates, issue creation).

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
| `list_my_issues` | List issues assigned to a user |
| `list_teams` | List all teams |
| `get_team` | Get team details |
| `list_projects` | List all projects |
| `get_project` | Get project details |
| `list_users` | List all users |
| `get_user` | Get user details |
| `list_issue_statuses` | List workflow states for a team |

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
