"""Guide catalogue (CLIPS editorial content only).

GUIDE_ENTRIES stays empty until real guides are authored.
Do not invent beginner tips, tier lists, builds, or hunting-spot posts
for the user-facing catalogue.
"""

from __future__ import annotations

import re
from urllib.parse import urlencode

from app.services.content_types import GuideEntry

# Populated only with authored published/draft guides. Empty = editorial desk UI.
GUIDE_ENTRIES: tuple[GuideEntry, ...] = ()

_SLUGIFY_RE = re.compile(r"[^a-z0-9가-힣]+", re.IGNORECASE)


def list_guides() -> tuple[GuideEntry, ...]:
    return GUIDE_ENTRIES


def list_published_guides() -> tuple[GuideEntry, ...]:
    return tuple(g for g in GUIDE_ENTRIES if g.status == "published")


def has_guide_catalogue() -> bool:
    return bool(list_published_guides())


def get_guide_by_slug(slug: str) -> GuideEntry | None:
    """Return a published guide only — draft/archived are not public."""
    for guide in GUIDE_ENTRIES:
        if guide.slug == slug and guide.status == "published":
            return guide
    return None


def sort_guides(guides: tuple[GuideEntry, ...]) -> tuple[GuideEntry, ...]:
    return tuple(
        sorted(
            guides,
            key=lambda g: (g.updated_at, g.published_at),
            reverse=True,
        )
    )


def published_category_keys() -> tuple[tuple[str, str], ...]:
    """Distinct categories from published guides, sorted by label."""
    seen: dict[str, str] = {}
    for guide in list_published_guides():
        if guide.category and guide.category not in seen:
            seen[guide.category] = guide.category_label or guide.category
    return tuple(sorted(seen.items(), key=lambda item: item[1]))


def has_guide_category_filters() -> bool:
    return len(published_category_keys()) >= 1


def parse_guide_category(raw: str | None) -> str:
    if raw is None or raw == "" or raw == "all":
        return "all"
    keys = {key for key, _ in published_category_keys()}
    return raw if raw in keys else "all"


def _guide_search_blob(guide: GuideEntry) -> str:
    parts: list[str] = [
        guide.title,
        guide.summary,
        guide.category,
        guide.category_label,
        guide.author_name,
        *guide.tags,
    ]
    for section in guide.sections:
        parts.append(section.heading)
        parts.append(section.body)
        parts.extend(section.bullets)
        parts.append(section.note)
        parts.append(section.warning)
        parts.append(section.tip)
    return " ".join(parts).casefold()


def filter_guides(
    *,
    category: str = "all",
    query: str = "",
) -> tuple[GuideEntry, ...]:
    guides = list_published_guides()
    if category != "all":
        guides = tuple(g for g in guides if g.category == category)
    q = query.strip().casefold()
    if q:
        guides = tuple(g for g in guides if q in _guide_search_blob(g))
    return sort_guides(guides)


def featured_guides() -> tuple[GuideEntry, ...]:
    return sort_guides(tuple(g for g in list_published_guides() if g.is_featured))


def build_guide_list_query(*, category: str = "all", query: str = "") -> str:
    params: dict[str, str] = {}
    if category != "all":
        params["category"] = category
    if query.strip():
        params["q"] = query.strip()
    if not params:
        return "/guides"
    return f"/guides?{urlencode(params)}"


def guide_category_tabs(*, query: str = "") -> list[dict[str, str]]:
    if not has_guide_category_filters():
        return []
    tabs: list[dict[str, str]] = [
        {
            "key": "all",
            "label": "전체",
            "href": build_guide_list_query(category="all", query=query),
        }
    ]
    for key, label in published_category_keys():
        tabs.append(
            {
                "key": key,
                "label": label,
                "href": build_guide_list_query(category=key, query=query),
            }
        )
    return tabs


def section_anchor_id(heading: str, index: int) -> str:
    cleaned = _SLUGIFY_RE.sub("-", heading.strip()).strip("-").casefold()
    if not cleaned:
        cleaned = "section"
    return f"guide-section-{index}-{cleaned}"


def related_guides(current: GuideEntry, *, limit: int = 3) -> tuple[GuideEntry, ...]:
    others = [g for g in list_published_guides() if g.slug != current.slug]
    if not others:
        return ()

    current_tags = set(current.tags)

    def score(guide: GuideEntry) -> tuple[int, int, object]:
        same_category = 1 if guide.category == current.category else 0
        tag_overlap = len(current_tags.intersection(guide.tags))
        return (same_category, tag_overlap, guide.updated_at)

    ranked = sorted(others, key=score, reverse=True)
    return tuple(ranked[:limit])
