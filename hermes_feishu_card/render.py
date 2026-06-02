from __future__ import annotations

import re
from typing import Any, Dict

from .session import CardSession
from .text import normalize_stream_text, split_markdown_blocks, _markdown_structure_blocks, TABLE_SEPARATOR_RE
import time as _time

DEFAULT_FOOTER_FIELDS = (
    "duration",
    "model",
    "input_tokens",
    "output_tokens",
    "context",
)
MAIN_CONTENT_CHUNK_CHARS = 2400
DEFAULT_TITLE = "Hermes Agent"


def render_card(
    session: CardSession,
    footer_fields: list[str] | tuple[str, ...] | None = None,
    title: str = DEFAULT_TITLE,
    loading_gif_img_key: str | None = None,
) -> Dict[str, Any]:
    cards = render_cards(
        session,
        footer_fields=footer_fields,
        title=title,
        loading_gif_img_key=loading_gif_img_key,
    )
    return cards[0] if cards else {}


def render_cards(
    session: CardSession,
    footer_fields: list[str] | tuple[str, ...] | None = None,
    title: str = DEFAULT_TITLE,
    loading_gif_img_key: str | None = None,
) -> list[Dict[str, Any]]:
    status = _render_status(session)
    main_text = normalize_stream_text(session.visible_main_text) or ("正在思考..." if session.status == "thinking" else "")
    tool_summary = _render_tool_summary(session)
    attachment_summary = _render_attachment_summary(session)
    footer = _render_footer(session, footer_fields, loading_gif_img_key)
    header_title = title.strip() if isinstance(title, str) and title.strip() else DEFAULT_TITLE
    
    content_parts = _split_content_by_tables(main_text)
    
    if len(content_parts) <= 1:
        elements = _render_main_content_elements(main_text)
        if attachment_summary:
            elements.append(
                {
                    "tag": "markdown",
                    "element_id": "attachment_summary",
                    "content": attachment_summary,
                }
            )
        elements.append({"tag": "hr", "element_id": "main_divider"})
        if isinstance(footer, list):
            elements.extend(footer)
        else:
            elements.append(
                {
                    "tag": "markdown",
                    "element_id": "footer",
                    "content": footer,
                    "text_size": "x-small",
                }
            )
        return [_build_card(elements, status, header_title)]
    
    cards = []
    total_parts = len(content_parts)
    for index, part_text in enumerate(content_parts):
        is_first = index == 0
        is_last = index == total_parts - 1
        part_elements = _render_main_content_elements(part_text)
        
        if is_first and attachment_summary:
            part_elements.append(
                {
                    "tag": "markdown",
                    "element_id": "attachment_summary",
                    "content": attachment_summary,
                }
            )
        
        part_elements.append({"tag": "hr", "element_id": "main_divider"})
        
        if is_last:
            if isinstance(footer, list):
                part_elements.extend(footer)
            else:
                part_elements.append(
                    {
                        "tag": "markdown",
                        "element_id": "footer",
                        "content": footer,
                        "text_size": "x-small",
                    }
                )
        else:
            part_elements.append(
                {
                    "tag": "markdown",
                    "element_id": "footer",
                    "content": f"({index + 1}/{total_parts})",
                    "text_size": "x-small",
                }
            )
        
        part_status = status if is_first else {"subtitle": f"({index + 1}/{total_parts})", "template": status["template"]}
        part_title = header_title if is_first else f"{header_title} (续)"
        cards.append(_build_card(part_elements, part_status, part_title))
    
    return cards


def _build_card(
    elements: list[Dict[str, Any]],
    status: Dict[str, str],
    title: str,
) -> Dict[str, Any]:
    return {
        "schema": "2.0",
        "config": {
            "update_multi": True,
            "summary": {"content": status["subtitle"]},
        },
        "header": {
            "template": status["template"],
            "title": {"tag": "plain_text", "content": title},
            "subtitle": {"tag": "plain_text", "content": status["subtitle"]},
        },
        "body": {
            "elements": elements
        },
    }


def _split_content_by_tables(text: str) -> list[str]:
    from .text import MAX_CARD_TABLES
    
    table_count = _count_markdown_tables(text)
    if table_count <= MAX_CARD_TABLES:
        return [text] if text else []
    
    blocks = _markdown_structure_blocks(text)
    parts: list[str] = []
    current_tables = 0
    current_blocks: list[str] = []
    
    for block in blocks:
        block_tables = _count_markdown_tables(block)
        if current_tables + block_tables > MAX_CARD_TABLES and current_tables > 0:
            parts.append("".join(current_blocks))
            current_blocks = []
            current_tables = 0
        
        current_blocks.append(block)
        current_tables += block_tables
    
    if current_blocks:
        parts.append("".join(current_blocks))
    
    return parts


def _count_markdown_tables(text: str) -> int:
    return len(re.findall(r'^\|[-: ]+\|', text, re.MULTILINE))


def _render_status(session: CardSession) -> Dict[str, str]:
    if session.status == "completed":
        subtitle = _generate_summary_subtitle(session.answer_text)
        return {"subtitle": subtitle, "template": "green"}
    if session.status == "failed":
        return {"subtitle": "处理失败", "template": "red"}
    return {"subtitle": "思考中", "template": "indigo"}


def _generate_summary_subtitle(text: str, max_length: int = 40) -> str:
    if not text or not text.strip():
        return "已完成"
    cleaned = re.sub(r'```[\s\S]*?```', '', text)
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
    cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
    cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
    cleaned = re.sub(r'#+\s*', '', cleaned)
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
    cleaned = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', cleaned)
    cleaned = re.sub(r'[\*\#`\[\]()>|-]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    first_sentence = re.split(r'[。！？\n]', cleaned)[0].strip()
    if len(first_sentence) > max_length:
        return first_sentence[:max_length - 1] + "…"
    return first_sentence if first_sentence else "已完成"


def _render_main_content_elements(main_text: str) -> list[Dict[str, Any]]:
    chunks = split_markdown_blocks(main_text, MAIN_CONTENT_CHUNK_CHARS)
    elements = []
    for index, chunk in enumerate(chunks):
        element_id = "main_content" if index == 0 else f"main_content_{index}"
        elements.append({"tag": "markdown", "element_id": element_id, "content": chunk})
    return elements

def _render_tool_summary(session: CardSession) -> str:
    if not session.tools:
        return "工具调用 0 次"
    lines = [f"工具调用 {session.tool_count} 次"]
    for tool in session.tools.values():
        lines.append(f"- `{tool.name}`: {tool.status}")
    return "\n".join(lines)


def _render_attachment_summary(session: CardSession) -> str:
    items = []
    for item in session.attachments:
        if not isinstance(item, dict):
            continue
        name = str(item.get("summary") or item.get("name") or "").strip()
        if name:
            items.append(name)
    if not items:
        return ""
    return "附件：" + "、".join(items[:8])


def _render_footer(
    session: CardSession,
    footer_fields: list[str] | tuple[str, ...] | None = None,
    loading_gif_img_key: str | None = None,
) -> str | list[dict[str, Any]]:
    if session.status == "failed":
        return "已停止"
    if session.status != "completed":
        if loading_gif_img_key:
            return _render_thinking_footer_gif(loading_gif_img_key)
        return "生成中"
    tokens = session.tokens if isinstance(session.tokens, dict) else {}
    input_tokens = _safe_int(tokens.get("input_tokens"))
    output_tokens = _safe_int(tokens.get("output_tokens"))
    try:
        duration = float(session.duration)
    except (TypeError, ValueError):
        duration = 0.0
    model = session.model if isinstance(session.model, str) and session.model.strip() else "Unknown"
    context = session.context if isinstance(session.context, dict) else {}
    used_context = _safe_int(context.get("used_tokens"))
    max_context = _safe_int(context.get("max_tokens"))
    context_percent = round(used_context / max_context * 100) if max_context > 0 else 0
    values = {
        "duration": _format_duration(duration),
        "model": model,
        "input_tokens": f"↑{_format_count(input_tokens)}",
        "output_tokens": f"↓{_format_count(output_tokens)}",
        "context": (
            f"ctx {_format_count(used_context)}/"
            f"{_format_count(max_context)} {context_percent}%"
        ),
    }
    selected = []
    fields = DEFAULT_FOOTER_FIELDS if footer_fields is None else footer_fields
    for field in fields:
        value = values.get(field)
        if value:
            selected.append(value)
    return " · ".join(selected) if selected else values["duration"]


def _render_thinking_footer_gif(img_key: str) -> list[dict[str, Any]]:
    """Render thinking-state footer as markdown with inline custom icon."""
    return [
        {
            "tag": "markdown",
            "content": "生成中",
            "text_align": "left",
            "text_size": "small",
            "icon": {
                "tag": "custom_icon",
                "img_key": img_key,
            },
        },
    ]


def _safe_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0


def _format_duration(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    minutes, remaining_seconds = divmod(total_seconds, 60)
    hours, remaining_minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{remaining_minutes}m{remaining_seconds}s"
    if minutes:
        return f"{minutes}m{remaining_seconds}s"
    return f"{remaining_seconds}s"


def _format_count(value: int) -> str:
    if value >= 1_000_000:
        return _format_scaled(value, 1_000_000, "m")
    if value >= 1_000:
        return _format_scaled(value, 1_000, "k")
    return str(value)


def _format_scaled(value: int, factor: int, suffix: str) -> str:
    scaled = value / factor
    if scaled >= 100 or scaled.is_integer():
        return f"{int(round(scaled))}{suffix}"
    return f"{scaled:.1f}".rstrip("0").rstrip(".") + suffix
