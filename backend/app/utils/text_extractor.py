"""Utility to extract plain text from TipTap JSON blocks."""
from typing import Any


def extract_text_from_blocks(blocks: Any) -> str:
    """Recursively extract plain text from TipTap JSON document."""
    if not blocks:
        return ""

    if isinstance(blocks, str):
        return blocks

    parts: list[str] = []

    if isinstance(blocks, dict):
        node_type = blocks.get("type", "")
        text = blocks.get("text", "")
        if text:
            parts.append(text)

        content = blocks.get("content", [])
        if content:
            for child in content:
                child_text = extract_text_from_blocks(child)
                if child_text:
                    parts.append(child_text)

        # Add newline after block-level nodes
        block_types = {
            "paragraph",
            "heading",
            "bulletList",
            "orderedList",
            "listItem",
            "taskList",
            "taskItem",
            "blockquote",
            "codeBlock",
            "horizontalRule",
            "table",
            "tableRow",
            "tableCell",
            "tableHeader",
        }
        if node_type in block_types:
            parts.append("\n")

    elif isinstance(blocks, list):
        for item in blocks:
            item_text = extract_text_from_blocks(item)
            if item_text:
                parts.append(item_text)

    return "".join(parts).strip()


def truncate_text(text: str, max_chars: int = 8000) -> str:
    """Truncate text to fit within token limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[Note truncated for AI processing]"
