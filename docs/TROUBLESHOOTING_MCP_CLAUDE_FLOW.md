# Troubleshooting: MCP Tool Error (claude-flow in WSL)

## Problem Description

When attempting to spawn a hive-mind swarm using `claude-flow@alpha`, you may encounter the following error:

```
[ERROR] Spawn error: MCP tool not found: hive-mind/spawn
[DEBUG] Completed in 0ms
[Process exited with code 1 (0x00000001)]
```

**Full Error Context:**
```bash
npx claude-flow@alpha hive-mind spawn "Task <task>" \
  --queen-type strategic \
  --max-workers 10 \
  --consensus majority \
  --memory-size 256 \
  --auto-spawn \
  --verbose
```

## Root Cause

This error occurs when:
1. The MCP (Model Context Protocol) server is not properly registered with Claude Code
2. There's a naming discrepancy in the alpha version of `claude-flow`
3. The orchestration tool attempts to access a function that Claude Code doesn't recognize
4. WSL-specific path or permission issues

## Environment Information

**Verified Working Configuration:**
- **Node.js**: v20.19.6
- **npm**: 10.8.2
- **npx**: 10.8.2
- **claude-flow**: v3.0.0-alpha.86
- **Platform**: WSL (Windows Subsystem for Linux)

## Solutions

### Solution 1: Register MCP Server Manually

Claude Code needs to know that `claude-flow` exists and what tools it provides.

```bash
claude mcp add claude-flow "npx claude-flow@alpha mcp start"
```

**What this does:**
- Creates an entry in your `~/.claude.json` configuration
- Registers the `claude-flow` MCP server with Claude Code
- Enables Claude Code to discover available tools

**Verification:**
```bash
cat ~/.claude.json
```

Expected output should include:
```json
{
  "mcpServers": {
    "claude-flow": {
      "command": "npx",
      "args": ["-y", "claude-flow@alpha", "mcp", "start"]
    }
  }
}
```

### Solution 2: Force Reinitialization

Local directories (`.hive-mind`, `.swarm`) may be corrupted or have incorrect permissions in WSL.

```bash
npx claude-flow@alpha init --force
```

**What this does:**
- Clears corrupted local state
- Reinitializes project structure
- Resets permissions

### Solution 3: Use Alternative `swarm` Command

The `hive-mind spawn` command has known issues in alpha builds. The `swarm` command is more stable:

```bash
npx claude-flow@alpha swarm \
  "Process all issues in Root->issues folder sequentially" \
  --agents 10 \
  --claude
```

**Advantages:**
- More stable in alpha versions
- Same functionality as hive-mind
- Better error handling

### Solution 4: Global Installation

Install `claude-flow@alpha` globally to avoid cache issues:

```bash
npm install -g claude-flow@alpha
```

Then use:
```bash
claude-flow swarm "Your task description" --agents 10
```

### Solution 5: Manual Configuration File

If `claude mcp add` fails to write properly, manually edit `~/.claude.json`:

```json
{
  "mcpServers": {
    "claude-flow": {
      "command": "npx",
      "args": ["-y", "claude-flow@alpha", "mcp", "start"]
    }
  }
}
```

## WSL-Specific Considerations

### Path Configuration
Ensure Claude Code searches in the correct location:
```bash
# Check your configuration location
ls -la ~/.claude.json

# Check WSL mount paths
echo $PATH | grep "/mnt/"
```

### Permission Issues
Avoid using `sudo` with Node.js commands in WSL:
```bash
# ✅ Good: Use nvm to manage Node
nvm use 20

# ❌ Bad: Using sudo with npm
sudo npm install -g claude-flow@alpha
```

### Interactive Prompts
Use `npx -y` to avoid interactive prompts that can hang in WSL:
```bash
npx -y claude-flow@alpha mcp start
```

## Diagnostic Commands

Run these commands to diagnose configuration issues:

```bash
# 1. Check Node/npm versions
node --version
npm --version
npx --version

# 2. Check claude-flow installation
npx claude-flow@alpha --version

# 3. Verify MCP registration
cat ~/.claude.json

# 4. Test MCP server startup
npx -y claude-flow@alpha mcp start

# 5. Check for corrupted directories
ls -la .hive-mind .swarm 2>/dev/null || echo "Directories not found (this is OK)"
```

## Troubleshooting Decision Tree

| Symptom | Probable Cause | Solution |
|---------|---------------|----------|
| `MCP tool not found` | Tool not registered | Solution 1: Register MCP server |
| `hive-mind spawn` fails | Alpha version bug | Solution 3: Use `swarm` command |
| Command hangs | Interactive prompt in WSL | Use `npx -y` flag |
| Permission denied | Using `sudo` with npm | Solution 5: Use `nvm`, avoid `sudo` |
| Configuration not found | WSL path conflict | Check `~/.claude.json` manually |

## Alternative Approach: Direct Task Execution

Instead of using hive-mind spawn, you can use Claude Code's built-in Task tool:

```markdown
In Claude Code conversation:
"Process all open issues in the /issues folder sequentially.
For each issue, complete all tasks and subtasks, test thoroughly,
and only close when fully verified."
```

Claude Code will handle agent spawning internally without requiring MCP tools.

## Cleanup Script

If all else fails, use this script to reset your configuration:

```bash
#!/bin/bash
# cleanup_claude_flow.sh

echo "🧹 Cleaning up claude-flow configuration..."

# Backup existing config
[ -f ~/.claude.json ] && cp ~/.claude.json ~/.claude.json.backup

# Remove corrupted directories
rm -rf .hive-mind .swarm .AI_Exchange .ai_exchange

# Clear npm cache
npm cache clean --force

# Reinstall claude-flow
npm uninstall -g claude-flow
npm install -g claude-flow@alpha

# Re-register MCP server
claude mcp add claude-flow "npx -y claude-flow@alpha mcp start"

# Initialize project
npx claude-flow@alpha init --force

echo "✅ Cleanup complete. Try running your command again."
```

## Additional Resources

- **Video Tutorial**: [Claude Flow: Why is NO ONE TALKING ABOUT THIS?](https://www.youtube.com/watch?v=example) by AICodeKing
- **GitHub Issues**: [claude-flow GitHub](https://github.com/ruvnet/claude-flow/issues)
- **Claude Code Documentation**: [Claude Code MCP Setup](https://docs.anthropic.com/claude-code)

## Related Issues

- Issue #63: Initial MCP tool error documentation
- WSL compatibility issues with claude-flow alpha versions
- MCP server registration in multi-environment setups

---

**Last Updated**: 2026-01-13
**Status**: Verified working with claude-flow v3.0.0-alpha.86
**Platform**: WSL (Windows Subsystem for Linux)
