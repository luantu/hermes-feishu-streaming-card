"""Model name normalization for Hermes Feishu card footer.

Converts raw uniapi model IDs like 'origin-deepseek-v4-pro-maxthink'
into readable display names like 'DeepSeek V4 Pro'.
"""

import re
from typing import Dict, List, Pattern


_MODEL_FAMILIES = {
    "deepseek", "claude", "gpt", "kimi", "glm", "qwen", "qwq",
    "gemini", "hunyuan", "moonshot", "minimax", "doubao", "ernie",
    "yi", "mistral", "llama", "phi", "command",
}

_VARIANTS = {
    "pro", "flash", "lite", "turbo", "plus", "mini", "ultra",
    "max", "preview", "thinking", "fable", "sonnet", "haiku", "opus",
}

_KNOWN_SERIES = {
    "r1", "o1", "o3", "o4",
    "c4", "c5",
}

_DISPLAY_NAMES: Dict[str, str] = {
    "deepseek": "DeepSeek", "claude": "Claude", "gpt": "GPT",
    "kimi": "Kimi", "glm": "GLM", "qwen": "Qwen", "qwq": "QWQ",
    "gemini": "Gemini", "hunyuan": "Hunyuan", "moonshot": "Moonshot",
    "minimax": "MiniMax", "doubao": "Doubao", "ernie": "Ernie",
    "yi": "Yi", "mistral": "Mistral", "llama": "Llama", "phi": "Phi",
    "command": "Command",
    "v2": "V2", "v3": "V3", "v4": "V4", "v5": "V5",
    "pro": "Pro", "flash": "Flash", "lite": "Lite", "turbo": "Turbo",
    "plus": "Plus", "mini": "Mini", "ultra": "Ultra", "max": "Max",
    "preview": "Preview", "thinking": "Thinking",
    "fable": "Fable", "sonnet": "Sonnet", "haiku": "Haiku", "opus": "Opus",
    "r1": "R1", "o1": "O1", "o3": "O3", "o4": "O4",
    "c4": "C4", "c5": "C5",
    "api": "API", "chat": "Chat", "coder": "Coder", "reasoner": "Reasoner",
}

_DISPLAY_NAMES_LOWER = {k.lower(): v for k, v in _DISPLAY_NAMES.items()}

_DATE_SUFFIX: Pattern = re.compile(r"-(?:\d{6}|\d{8})$")
_MAXTHINK: Pattern = re.compile(r"-maxthink$", re.IGNORECASE)
_API_PATH: Pattern = re.compile(r"/(chat|coder|reasoner|completions)$")
_SUB_VERSION: Pattern = re.compile(r"(v\d+)-(\d+)", re.IGNORECASE)
_DECIMAL_VERSION: Pattern = re.compile(r"(\d)-(\d)")

_EXACT_MAP: Dict[str, str] = {
    "deepseek/chat": "DeepSeek Chat",
    "deepseek/coder": "DeepSeek Coder",
    "deepseek/reasoner": "DeepSeek R1",
    "hunyuan-t1-latest": "Hunyuan T1",
    "ali-glm-5.2": "GLM 5.2",
}


def _strip_provider_prefix(name: str) -> str:
    """Strip leading provider prefix if it's not a known model family."""
    if "-" not in name:
        return name
    first, rest = name.split("-", 1)
    if first.lower() not in _MODEL_FAMILIES:
        return rest
    return name


def normalize_model_name(model: str) -> str:
    """Convert a raw model ID into a readable display name.

    E.g. 'origin-deepseek-v4-pro' → 'DeepSeek V4 Pro'
         'claude-haiku-4-5-20251001' → 'Claude Haiku 4.5'
         'deepseek-v3-1-250821' → 'DeepSeek V3.1'
    """
    name = str(model or "").strip()
    if not name:
        return ""
    if re.search(r"[<>\"'&]", name):
        return name

    lower = name.lower()
    if lower in _EXACT_MAP:
        return _EXACT_MAP[lower]

    original_tokens = set(re.split(r"[-\s/]+", name))

    name = _strip_provider_prefix(name)
    name = _MAXTHINK.sub("", name)
    name = _API_PATH.sub("", name)
    name = _DATE_SUFFIX.sub("", name)
    name = _SUB_VERSION.sub(r"\1.\2", name)
    name = _DECIMAL_VERSION.sub(r"\1.\2", name)
    name = re.sub(r"[-/]+", " ", name).strip()

    parts = name.split()
    result = []
    for part in parts:
        part = part.strip().strip("-")
        if not part:
            continue
        lower_part = part.lower()
        if lower_part in _DISPLAY_NAMES_LOWER:
            result.append(_DISPLAY_NAMES_LOWER[lower_part])
        elif part.isdigit():
            result.append(part)
        else:
            matches = [t for t in original_tokens if t.lower() == lower_part]
            if matches and any(c.isupper() for c in matches[0]):
                result.append(matches[0])
            elif "." in part and part[0].isalpha():
                result.append(part[0].upper() + part[1:])
            else:
                result.append(part.capitalize())
    return " ".join(result) if result else name
