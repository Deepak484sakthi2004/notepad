from flask import request


def paginate_query(query, default_per_page: int = 20, max_per_page: int = 100):
    """Apply pagination to a SQLAlchemy query and return data + meta."""
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(
            max_per_page,
            max(1, int(request.args.get("per_page", default_per_page))),
        )
    except (ValueError, TypeError):
        page = 1
        per_page = default_per_page

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return paginated.items, {
        "page": paginated.page,
        "per_page": paginated.per_page,
        "total": paginated.total,
        "pages": paginated.pages,
        "has_next": paginated.has_next,
        "has_prev": paginated.has_prev,
    }
