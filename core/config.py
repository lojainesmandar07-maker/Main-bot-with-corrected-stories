import os
import json
from dotenv import load_dotenv

load_dotenv()

# Resolve the Discord token from common environment variable names.
# Primary key for this project is DISCORD_TOKEN, but BOT_TOKEN/TOKEN are
# supported to reduce deployment misconfiguration issues.
def _resolve_discord_token() -> str:
    # Ordered by preference.
    candidate_keys = (
        "DISCORD_TOKEN",
        "BOT_TOKEN",
        "TOKEN",
        "DISCORD_BOT_TOKEN",
        "TOKEN_BOT",
        "token",
        "bot_token",
    )
    for env_key in candidate_keys:
        value = os.getenv(env_key, "").strip()
        if value:
            return value
    return ""


DISCORD_TOKEN = _resolve_discord_token()
GUILD_ID = os.getenv("GUILD_ID") # Optional, for testing sync commands faster

# --- New config helpers ---
CONFIG_PATH = "data/config.json"

_DEFAULT_CONFIG = {
    "world_channels": {},
    "test_channel": None,
    "archetype_roles": {},
    "npc_channels": {}
}
_config_cache: dict | None = None

def load_config() -> dict:
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if not os.path.exists(CONFIG_PATH):
        _config_cache = _DEFAULT_CONFIG.copy()
        save_config(_config_cache)
        return _config_cache
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = f.read().strip()

        # Empty file => safe defaults
        if not raw:
            _config_cache = _DEFAULT_CONFIG.copy()
            save_config(_config_cache)
            return _config_cache

        data = json.loads(raw)
        if not isinstance(data, dict):
            _config_cache = _DEFAULT_CONFIG.copy()
            save_config(_config_cache)
            return _config_cache

        # Merge with defaults and sanitize known dict fields
        for key, val in _DEFAULT_CONFIG.items():
            data.setdefault(key, val)
        for dict_key in ("world_channels", "archetype_roles", "npc_channels"):
            if not isinstance(data.get(dict_key), dict):
                data[dict_key] = {}

        _config_cache = data
        return _config_cache
    except Exception:
        _config_cache = _DEFAULT_CONFIG.copy()
        return _config_cache

def save_config(config: dict) -> None:
    global _config_cache
    _config_cache = config
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_config(key: str, default=None):
    return load_config().get(key, default)
