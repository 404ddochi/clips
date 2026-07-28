"""Item catalogue data (officially disclosed entries only).

Official site navigation (https://eclipse.onstove.com/ko/home) has no item
menu or named item catalogue as of this check. ITEM_ENTRIES stays empty
until official disclosure — do not invent grades, stats, or drop sources.
"""

from __future__ import annotations

from urllib.parse import urlencode

from app.services.content_types import ItemEntry

ITEM_ENTRIES: tuple[ItemEntry, ...] = ()

# Populated only when official category labels exist. Empty = no SSR filter UI.
ITEM_CATEGORY_FILTERS: tuple[tuple[str, str], ...] = ()


def list_items() -> tuple[ItemEntry, ...]:
    return ITEM_ENTRIES


def get_item_by_slug(slug: str) -> ItemEntry | None:
    for item in ITEM_ENTRIES:
        if item.slug == slug:
            return item
    return None


def has_item_catalogue() -> bool:
    return bool(ITEM_ENTRIES)


def has_item_category_filters() -> bool:
    return len(ITEM_CATEGORY_FILTERS) > 1


def parse_item_category(raw: str | None) -> str:
    if raw is None or raw == "" or raw == "all":
        return "all"
    keys = {key for key, _ in ITEM_CATEGORY_FILTERS if key != "all"}
    return raw if raw in keys else "all"


def filter_items(
    *,
    category: str = "all",
    query: str = "",
) -> tuple[ItemEntry, ...]:
    items = list_items()
    if category != "all":
        items = tuple(i for i in items if i.category == category)
    q = query.strip().casefold()
    if not q:
        return items
    out: list[ItemEntry] = []
    for item in items:
        haystack = " ".join(
            (
                item.name,
                item.name_en,
                item.category,
                item.slot_or_purpose,
                item.summary,
            )
        ).casefold()
        if q in haystack:
            out.append(item)
    return tuple(out)


def build_item_list_query(*, category: str = "all", query: str = "") -> str:
    params: dict[str, str] = {}
    if category != "all":
        params["category"] = category
    if query.strip():
        params["q"] = query.strip()
    if not params:
        return "/items"
    return f"/items?{urlencode(params)}"


def item_category_tabs(*, query: str = "") -> list[dict[str, str]]:
    if not has_item_category_filters():
        return []
    return [
        {
            "key": key,
            "label": label,
            "href": build_item_list_query(category=key, query=query),
        }
        for key, label in ITEM_CATEGORY_FILTERS
    ]
