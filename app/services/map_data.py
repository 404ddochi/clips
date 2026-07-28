"""Region / map catalogue data (officially disclosed entries only).

Official site check (https://eclipse.onstove.com/ko/home, 2026-07):

- GNB-style routes include /ko/world, /ko/story, /ko/sanctuary (SPA shell).
- There is no enumerable public catalogue of named fields/regions with
  descriptions suitable for CLIPS entries.
- No official downloadable world-map asset URL was identified in static HTML.
- /ko/region returns 404.

REGION_ENTRIES stays empty until official named regions are published — do not
invent areas, pins, or hunting ground lists.
"""

from __future__ import annotations

from app.services.boss_data import get_boss_by_slug
from app.services.content_types import BossItem, ItemEntry, RegionEntry
from app.services.item_data import get_item_by_slug

REGION_ENTRIES: tuple[RegionEntry, ...] = ()


def list_regions() -> tuple[RegionEntry, ...]:
    return REGION_ENTRIES


def get_region_by_slug(slug: str) -> RegionEntry | None:
    for entry in REGION_ENTRIES:
        if entry.slug == slug:
            return entry
    return None


def has_region_catalogue() -> bool:
    return bool(REGION_ENTRIES)


def resolve_related_bosses(slugs: tuple[str, ...]) -> tuple[BossItem, ...]:
    out: list[BossItem] = []
    for slug in slugs:
        boss = get_boss_by_slug(slug)
        if boss is not None:
            out.append(boss)
    return tuple(out)


def resolve_related_items(slugs: tuple[str, ...]) -> tuple[ItemEntry, ...]:
    out: list[ItemEntry] = []
    for slug in slugs:
        item = get_item_by_slug(slug)
        if item is not None:
            out.append(item)
    return tuple(out)
