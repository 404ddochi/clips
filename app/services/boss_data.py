"""Boss catalogue data (officially disclosed entries only).

As of the official Eclipse: The Awakening site navigation check
(https://eclipse.onstove.com/ko/home), there is no Boss section and no
publicly named boss entries. BOSS_ITEMS stays empty until official
disclosure — do not invent spawn times, drops, difficulty, or patterns.
"""

from __future__ import annotations

from app.services.content_types import BossItem

# Populated only with officially named bosses. Empty = waiting UI.
BOSS_ITEMS: tuple[BossItem, ...] = ()


def list_bosses() -> tuple[BossItem, ...]:
    return BOSS_ITEMS


def get_boss_by_slug(slug: str) -> BossItem | None:
    for item in BOSS_ITEMS:
        if item.slug == slug:
            return item
    return None


def has_boss_catalogue() -> bool:
    return bool(BOSS_ITEMS)
