import uuid
import os
from datetime import datetime, timezone
from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.page import Page
from app.models.workspace import Workspace
from app.utils.text_extractor import extract_text_from_blocks

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_pages_tree(workspace_id: str, user_id: str) -> list:
    """Return all non-deleted pages as a flat list (tree built on frontend)."""
    pages = (
        Page.query.filter_by(workspace_id=workspace_id, is_deleted=False)
        .order_by(Page.sort_order, Page.created_at)
        .all()
    )
    return [p.to_tree_dict() for p in pages]


def create_page(
    workspace_id: str,
    user_id: str,
    title: str = "Untitled",
    parent_page_id: str = None,
    icon: str = "📄",
) -> Page:
    # Calculate next sort_order
    last = (
        Page.query.filter_by(
            workspace_id=workspace_id,
            parent_page_id=parent_page_id,
            is_deleted=False,
        )
        .order_by(Page.sort_order.desc())
        .first()
    )
    sort_order = (last.sort_order + 1.0) if last else 0.0

    page = Page(
        workspace_id=workspace_id,
        created_by=user_id,
        title=title,
        parent_page_id=parent_page_id,
        icon=icon,
        blocks={},
        plain_text="",
        sort_order=sort_order,
    )
    db.session.add(page)
    db.session.commit()
    return page


def update_page_content(page: Page, blocks: dict, plain_text: str = None) -> Page:
    page.blocks = blocks
    if plain_text is not None:
        page.plain_text = plain_text
    else:
        page.plain_text = extract_text_from_blocks(blocks)
    page.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return page


def duplicate_page(page: Page, user_id: str) -> Page:
    new_page = Page(
        workspace_id=page.workspace_id,
        parent_page_id=page.parent_page_id,
        title=f"{page.title} (Copy)",
        icon=page.icon,
        blocks=page.blocks,
        plain_text=page.plain_text,
        sort_order=page.sort_order + 0.5,
        created_by=user_id,
    )
    db.session.add(new_page)
    db.session.commit()
    return new_page


def move_page(page: Page, new_parent_id: str = None, new_workspace_id: str = None) -> Page:
    if new_parent_id is not None:
        # Prevent circular reference
        if new_parent_id == page.id:
            raise ValueError("A page cannot be its own parent")
        page.parent_page_id = new_parent_id
    if new_workspace_id is not None:
        page.workspace_id = new_workspace_id
    db.session.commit()
    return page


def export_page_markdown(page: Page) -> str:
    lines = [f"# {page.title}\n"]
    lines.append(page.plain_text or "")
    return "\n".join(lines)


def export_page_txt(page: Page) -> str:
    return f"{page.title}\n{'=' * len(page.title)}\n\n{page.plain_text or ''}"


def export_page_pdf(page: Page) -> bytes:
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, page.title[:80], ln=True)
        pdf.ln(4)
        pdf.set_font("Helvetica", size=11)
        text = page.plain_text or ""
        for line in text.split("\n"):
            pdf.multi_cell(0, 6, line[:200])
        return pdf.output()
    except ImportError:
        return b"PDF export requires fpdf2"


def handle_image_upload(page: Page, file) -> str:
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "./uploads")
    os.makedirs(upload_folder, exist_ok=True)

    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    return f"/uploads/{filename}"
