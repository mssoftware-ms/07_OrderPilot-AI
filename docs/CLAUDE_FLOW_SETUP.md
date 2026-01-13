# Claude Flow Setup Guide

## Overview

This project uses **claude-flow** for multi-agent orchestration. There are two different packages available:

1. **`@claude-flow/cli@latest`** - Official stable release (recommended)
2. **`claude-flow@alpha`** - Alpha/development version

## Important: Package Naming

⚠️ **Common Confusion:**
- `@claude-flow/cli` - **Official package** (scoped npm package)
- `claude-flow` - **Legacy/alpha package** (may have compatibility issues)

The `.mcp.json.disabled` file in this project uses the **official** `@claude-flow/cli@latest` package, which is the recommended version.

## Installation

### Option 1: Use Official Package (Recommended)

```bash
# Add MCP server to Claude Code
claude mcp add claude-flow "npx @claude-flow/cli@latest mcp start"

# Or install globally
npm install -g @claude-flow/cli@latest

# Verify installation
npx @claude-flow/cli@latest --version
```

### Option 2: Use Alpha Version (If Required)

```bash
# Add MCP server to Claude Code
claude mcp add claude-flow "npx -y claude-flow@alpha mcp start"

# Or install globally
npm install -g claude-flow@alpha

# Verify installation
npx claude-flow@alpha --version
```

## MCP Configuration

The project includes a `.mcp.json.disabled` file with pre-configured settings:

```json
{
  "mcpServers": {
    "claude-flow": {
      "command": "npx",
      "args": ["@claude-flow/cli@latest", "mcp", "start"],
      "env": {
        "CLAUDE_FLOW_MODE": "v3",
        "CLAUDE_FLOW_HOOKS_ENABLED": "true",
        "CLAUDE_FLOW_TOPOLOGY": "hierarchical-mesh",
        "CLAUDE_FLOW_MAX_AGENTS": "15",
        "CLAUDE_FLOW_MEMORY_BACKEND": "hybrid"
      },
      "autoStart": false
    }
  }
}
```

### Configuration Options Explained

| Variable | Value | Description |
|----------|-------|-------------|
| `CLAUDE_FLOW_MODE` | `v3` | Use V3 architecture with enhanced features |
| `CLAUDE_FLOW_HOOKS_ENABLED` | `true` | Enable hooks for learning and automation |
| `CLAUDE_FLOW_TOPOLOGY` | `hierarchical-mesh` | Hybrid topology (anti-drift) |
| `CLAUDE_FLOW_MAX_AGENTS` | `15` | Maximum concurrent agents |
| `CLAUDE_FLOW_MEMORY_BACKEND` | `hybrid` | Use hybrid memory (HNSW + SQLite) |
| `autoStart` | `false` | Don't auto-start server (manual control) |

## Project Structure

```
OrderPilot-AI/
├── .mcp.json.disabled         # MCP server configuration (inactive)
├── .claude/                   # Claude Code configuration
│   ├── config.json           # Project settings
│   ├── settings.json         # User preferences
│   └── agents/               # Agent definitions
├── .claude-flow/             # Claude Flow state
│   └── metrics/              # Performance metrics
└── docs/
    ├── CLAUDE_FLOW_SETUP.md  # This file
    └── TROUBLESHOOTING_MCP_CLAUDE_FLOW.md  # Error solutions
```

## Enable/Disable MCP Server

The MCP configuration is **disabled** by default to prevent conflicts. To enable:

```bash
# Enable (rename to .mcp.json)
mv .mcp.json.disabled .mcp.json

# Disable (rename back)
mv .mcp.json .mcp.json.disabled
```

## Usage Examples

### 1. Initialize Claude Flow

```bash
npx @claude-flow/cli@latest init
```

### 2. Spawn Agents with Swarm

```bash
npx @claude-flow/cli@latest swarm \
  "Process all open issues in /issues folder" \
  --agents 10 \
  --claude
```

### 3. Use Hive-Mind (Alternative)

```bash
npx @claude-flow/cli@latest hive-mind spawn \
  "Task description" \
  --queen-type strategic \
  --max-workers 10 \
  --consensus majority
```

### 4. Check Swarm Status

```bash
npx @claude-flow/cli@latest swarm status
```

### 5. Memory Operations

```bash
# Store pattern
npx @claude-flow/cli@latest memory store \
  --key "auth-pattern" \
  --value "JWT with refresh tokens" \
  --namespace patterns

# Search memory
npx @claude-flow/cli@latest memory search \
  --query "authentication" \
  --namespace patterns
```

## Integration with Claude Code

Claude Code can use claude-flow in two ways:

### Method 1: MCP Tools (Requires MCP Server)

With `.mcp.json` enabled, Claude Code can call MCP tools:
- `agent_spawn`
- `swarm_init`
- `memory_store`
- `task_create`
- etc.

### Method 2: Task Tool (Built-in)

Without MCP, use Claude Code's built-in Task tool:

```
"Spawn 5 agents to process issues:
- researcher: Analyze requirements
- coder: Implement solutions
- tester: Write tests
- reviewer: Code review"
```

Claude Code handles spawning internally.

## Troubleshooting

If you encounter errors, see:
- **[TROUBLESHOOTING_MCP_CLAUDE_FLOW.md](./TROUBLESHOOTING_MCP_CLAUDE_FLOW.md)** - Comprehensive error solutions

### Quick Fixes

| Error | Quick Fix |
|-------|-----------|
| `MCP tool not found` | `claude mcp add claude-flow "npx @claude-flow/cli@latest mcp start"` |
| `hive-mind spawn` fails | Use `swarm` command instead |
| WSL permission errors | Use `nvm`, avoid `sudo` |
| Configuration not found | Check `~/.claude.json` exists |

## Best Practices

1. **Use Official Package**: Prefer `@claude-flow/cli@latest` over `claude-flow@alpha`
2. **Test Before Production**: Initialize with `--force` flag to reset state
3. **Monitor Memory**: Check `.claude-flow/metrics/` for performance data
4. **Hierarchical Topology**: Use `hierarchical-mesh` to prevent agent drift
5. **Limit Agents**: Keep `max-agents` ≤ 15 for stability

## Version Compatibility

| Package | Version | Claude Code | Node.js | Status |
|---------|---------|-------------|---------|--------|
| `@claude-flow/cli` | v3.0.0+ | ≥ 0.3.0 | ≥ 20.0 | ✅ Stable |
| `claude-flow@alpha` | v3.0.0-alpha.86 | ≥ 0.3.0 | ≥ 20.0 | ⚠️ Alpha |

## Environment Variables

Optional environment variables for fine-tuning:

```bash
export CLAUDE_FLOW_LOG_LEVEL=debug      # Verbose logging
export CLAUDE_FLOW_MCP_PORT=3000        # MCP server port
export CLAUDE_FLOW_MCP_TRANSPORT=stdio  # Transport method
export ANTHROPIC_API_KEY=sk-ant-...     # API key (if needed)
```

## Additional Resources

- **Claude Flow GitHub**: [https://github.com/ruvnet/claude-flow](https://github.com/ruvnet/claude-flow)
- **MCP Documentation**: [https://modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Claude Code**: [https://claude.com/code](https://claude.com/code)

---

**Last Updated**: 2026-01-13
**Maintainer**: OrderPilot-AI Team
