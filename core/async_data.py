import asyncio
import json
from pathlib import Path
from typing import Any

_json_cache: dict[str, tuple[float, Any]] = {}


def invalidate_json_cache(path: str | Path | None = None) -> None:
    if path is None:
        _json_cache.clear()
        return
    _json_cache.pop(str(Path(path)), None)


def _read_json_sync(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


async def load_json_cached(path: str | Path) -> Any:
    resolved = Path(path)
    key = str(resolved)
    stat = await asyncio.to_thread(resolved.stat)
    mtime = stat.st_mtime

    cached = _json_cache.get(key)
    if cached and cached[0] == mtime:
        return cached[1]

    data = await asyncio.to_thread(_read_json_sync, resolved)
    _json_cache[key] = (mtime, data)
    return data


def _write_json_sync(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def save_json(path: str | Path, data: Any) -> None:
    resolved = Path(path)
    await asyncio.to_thread(_write_json_sync, resolved, data)
    invalidate_json_cache(resolved)
