# Deployment Checklist

## Discord Developer Portal (Required)

Before deploying, open **Discord Developer Portal → Applications → _Your App_ → Bot** and verify:

1. **Privileged Gateway Intents**
   - ✅ **SERVER MEMBERS INTENT**: **Enabled** (required for welcome flow and role-based profile logic).
   - ❌ **MESSAGE CONTENT INTENT**: Disabled (not required).
   - ❌ **PRESENCE INTENT**: Disabled (not required).

2. **Bot Token**
   - Regenerate only if compromised.
   - Keep token secret and store it in environment variables (never in source control).

## Runtime Environment

Provide one valid token variable:

- `DISCORD_TOKEN` (preferred), or fallback aliases used by this codebase:
  - `BOT_TOKEN`
  - `DISCORD_BOT_TOKEN`
  - `TOKEN`
  - `TOKEN_BOT`

## Startup Validation Behavior

At startup, the bot validates privileged intent grants against runtime intent configuration.

- If required privileged intents are missing in the portal, startup fails immediately with a clear error.
- On ready, the bot logs configured intents and diagnostics to simplify production troubleshooting.
