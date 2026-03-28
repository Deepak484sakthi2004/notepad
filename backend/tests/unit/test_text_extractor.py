"""
Unit tests for app/utils/text_extractor.py

Tests cover:
- extract_text_from_blocks with TipTap JSON structures
- Empty / None / falsy input
- Nested content (paragraphs inside lists)
- Individual node types: paragraph, heading, codeBlock, bulletList, orderedList
- truncate_text behaviour
"""
import pytest
from app.utils.text_extractor import extract_text_from_blocks, truncate_text


# ---------------------------------------------------------------------------
# Helpers – TipTap node constructors
# ---------------------------------------------------------------------------

def text_node(text: str) -> dict:
    return {"type": "text", "text": text}


def paragraph(*texts: str) -> dict:
    return {"type": "paragraph", "content": [text_node(t) for t in texts]}


def heading(level: int, *texts: str) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [text_node(t) for t in texts],
    }


def code_block(*texts: str) -> dict:
    return {"type": "codeBlock", "content": [text_node(t) for t in texts]}


def bullet_list(*items: str) -> dict:
    return {
        "type": "bulletList",
        "content": [
            {"type": "listItem", "content": [paragraph(item)]}
            for item in items
        ],
    }


def ordered_list(*items: str) -> dict:
    return {
        "type": "orderedList",
        "content": [
            {"type": "listItem", "content": [paragraph(item)]}
            for item in items
        ],
    }


def doc(*nodes) -> dict:
    return {"type": "doc", "content": list(nodes)}


# ---------------------------------------------------------------------------
# Falsy / empty inputs
# ---------------------------------------------------------------------------

class TestExtractTextFromBlocksEdgeCases:
    def test_none_input_returns_empty_string(self):
        assert extract_text_from_blocks(None) == ""

    def test_empty_dict_returns_empty_string(self):
        assert extract_text_from_blocks({}) == ""

    def test_empty_list_returns_empty_string(self):
        assert extract_text_from_blocks([]) == ""

    def test_false_returns_empty_string(self):
        assert extract_text_from_blocks(False) == ""

    def test_zero_returns_empty_string(self):
        # 0 is falsy; the guard `if not blocks` should catch it
        assert extract_text_from_blocks(0) == ""

    def test_string_input_returns_string_as_is(self):
        assert extract_text_from_blocks("plain text") == "plain text"

    def test_dict_with_no_text_no_content_returns_empty(self):
        assert extract_text_from_blocks({"type": "doc"}) == ""


# ---------------------------------------------------------------------------
# Paragraph nodes
# ---------------------------------------------------------------------------

class TestExtractTextParagraph:
    def test_single_paragraph_extracts_text(self):
        node = paragraph("Hello, world!")
        result = extract_text_from_blocks(node)
        assert "Hello, world!" in result

    def test_paragraph_adds_newline_after_content(self):
        node = paragraph("Line one")
        result = extract_text_from_blocks(node)
        # After stripping the result must contain the text;
        # the raw (un-stripped) join would contain a trailing \n,
        # but extract_text_from_blocks strips the final result.
        assert result == "Line one"

    def test_multiple_paragraphs_in_doc(self):
        node = doc(paragraph("First"), paragraph("Second"))
        result = extract_text_from_blocks(node)
        assert "First" in result
        assert "Second" in result

    def test_empty_paragraph_produces_no_text(self):
        node = {"type": "paragraph", "content": []}
        result = extract_text_from_blocks(node)
        # No text nodes, only the trailing newline which is stripped
        assert result == ""


# ---------------------------------------------------------------------------
# Heading nodes
# ---------------------------------------------------------------------------

class TestExtractTextHeading:
    def test_heading_extracts_text(self):
        node = heading(1, "Introduction")
        result = extract_text_from_blocks(node)
        assert "Introduction" in result

    def test_heading_level_does_not_appear_in_plain_text(self):
        node = heading(2, "Chapter Two")
        result = extract_text_from_blocks(node)
        assert result == "Chapter Two"

    def test_mixed_heading_and_paragraph(self):
        node = doc(heading(1, "Title"), paragraph("Body text here."))
        result = extract_text_from_blocks(node)
        assert "Title" in result
        assert "Body text here." in result


# ---------------------------------------------------------------------------
# codeBlock nodes
# ---------------------------------------------------------------------------

class TestExtractTextCodeBlock:
    def test_code_block_extracts_code_text(self):
        node = code_block("print('hello')")
        result = extract_text_from_blocks(node)
        assert "print('hello')" in result

    def test_code_block_multiline(self):
        node = code_block("def foo():\n    return 42")
        result = extract_text_from_blocks(node)
        assert "def foo():" in result
        assert "return 42" in result


# ---------------------------------------------------------------------------
# bulletList nodes
# ---------------------------------------------------------------------------

class TestExtractTextBulletList:
    def test_bullet_list_extracts_all_items(self):
        node = bullet_list("Apple", "Banana", "Cherry")
        result = extract_text_from_blocks(node)
        assert "Apple" in result
        assert "Banana" in result
        assert "Cherry" in result

    def test_bullet_list_single_item(self):
        node = bullet_list("Only item")
        result = extract_text_from_blocks(node)
        assert "Only item" in result


# ---------------------------------------------------------------------------
# orderedList nodes
# ---------------------------------------------------------------------------

class TestExtractTextOrderedList:
    def test_ordered_list_extracts_all_items(self):
        node = ordered_list("Step one", "Step two", "Step three")
        result = extract_text_from_blocks(node)
        assert "Step one" in result
        assert "Step two" in result
        assert "Step three" in result


# ---------------------------------------------------------------------------
# Nested content
# ---------------------------------------------------------------------------

class TestExtractTextNested:
    def test_nested_list_inside_paragraph_doc(self):
        """A doc containing both a paragraph and a nested bullet list."""
        node = doc(
            paragraph("Intro paragraph"),
            bullet_list("Item A", "Item B"),
            paragraph("Closing paragraph"),
        )
        result = extract_text_from_blocks(node)
        assert "Intro paragraph" in result
        assert "Item A" in result
        assert "Item B" in result
        assert "Closing paragraph" in result

    def test_deeply_nested_text_is_extracted(self):
        """Text buried three levels deep is still extracted."""
        deep = {
            "type": "blockquote",
            "content": [
                {
                    "type": "paragraph",
                    "content": [text_node("deep quote")],
                }
            ],
        }
        result = extract_text_from_blocks(deep)
        assert "deep quote" in result

    def test_list_input_of_nodes(self):
        """A raw list of TipTap nodes (not wrapped in a doc)."""
        nodes = [paragraph("Para one"), paragraph("Para two")]
        result = extract_text_from_blocks(nodes)
        assert "Para one" in result
        assert "Para two" in result


# ---------------------------------------------------------------------------
# truncate_text
# ---------------------------------------------------------------------------

class TestTruncateText:
    def test_short_text_not_truncated(self):
        text = "Hello world"
        assert truncate_text(text, max_chars=100) == text

    def test_text_exactly_at_limit_not_truncated(self):
        text = "a" * 8000
        result = truncate_text(text)
        assert result == text

    def test_text_exceeding_limit_is_truncated(self):
        text = "a" * 9000
        result = truncate_text(text)
        assert len(result) < len(text)

    def test_truncated_text_contains_notice(self):
        text = "x" * 9000
        result = truncate_text(text)
        assert "[Note truncated for AI processing]" in result

    def test_truncated_text_starts_with_original_content(self):
        text = "start" + "z" * 8100
        result = truncate_text(text, max_chars=8000)
        assert result.startswith("start")

    def test_custom_max_chars_respected(self):
        text = "b" * 500
        result = truncate_text(text, max_chars=100)
        # First 100 chars of original + the notice
        assert result.startswith("b" * 100)
        assert "[Note truncated for AI processing]" in result

    def test_empty_string_not_truncated(self):
        assert truncate_text("") == ""
