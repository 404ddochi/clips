"""Publicly disclosed class information (not fabricated game data).

Sources: Smilegate / Npixel showcase coverage (press). Fields without
public detail use CLASS_PENDING_LABEL via pending flags — do not invent
skills, builds, tiers, or unreleased content.
"""

from __future__ import annotations

from urllib.parse import urlencode

from app.services.content_types import (
    CLASS_PENDING_LABEL,
    CLASS_STYLE_FILTERS,
    CLASS_STYLE_LABELS,
    ClassFilterKey,
    ClassItem,
    ClassStyle,
)

# Only publicly named classes and weapon/role summaries from press coverage.
CLASS_ITEMS: tuple[ClassItem, ...] = (
    ClassItem(
        slug="fighter",
        name="파이터",
        name_en="Fighter",
        symbol="class-fighter",
        accent="melee",
        styles=("melee",),
        weapons=("한손검", "대검"),
        combat_styles=("방어·보호", "공격 집중"),
        summary=(
            "한손검과 대검 중 무기를 선택해 방어·보호 또는 공격 집중으로 "
            "역할을 나눌 수 있는 클래스로 공개되었습니다."
        ),
        source_note="공식 쇼케이스·보도 공개 정보 기준 (비공식 정리)",
    ),
    ClassItem(
        slug="ranger",
        name="레인저",
        name_en="Ranger",
        symbol="class-ranger",
        accent="ranged",
        styles=("ranged",),
        weapons=("활", "석궁"),
        combat_styles=("원거리 압박", "덫·동선 통제"),
        summary=(
            "활과 석궁을 사용하며, 원거리 압박 또는 덫을 활용한 동선 통제로 "
            "전투 방식을 나눌 수 있다고 공개되었습니다."
        ),
        source_note="공식 쇼케이스·보도 공개 정보 기준 (비공식 정리)",
    ),
    ClassItem(
        slug="sorceress",
        name="소서리스",
        name_en="Sorceress",
        symbol="class-sorceress",
        accent="magic",
        styles=("magic", "support"),
        weapons=("지팡이", "오브"),
        combat_styles=("화력 중심", "회복·약화 지원"),
        summary=(
            "지팡이와 오브로 화력 중심 전투와 회복·약화 지원 중 "
            "방향을 고를 수 있는 클래스로 공개되었습니다."
        ),
        source_note="공식 쇼케이스·보도 공개 정보 기준 (비공식 정리)",
    ),
    ClassItem(
        slug="assassin",
        name="어쌔신",
        name_en="Assassin",
        symbol="class-assassin",
        accent="melee",
        styles=("melee",),
        weapons=("카타나", "쌍단검"),
        combat_styles=(),
        summary=(
            "카타나와 쌍단검을 활용하는 클래스로 공개되었습니다. "
            "세부 전투 스타일 설명은 추가 공식 공개를 기다립니다."
        ),
        combat_styles_pending=True,
        source_note="공식 쇼케이스·보도 공개 정보 기준 (비공식 정리)",
    ),
)


def list_classes() -> tuple[ClassItem, ...]:
    return CLASS_ITEMS


def get_class_by_slug(slug: str) -> ClassItem | None:
    for item in CLASS_ITEMS:
        if item.slug == slug:
            return item
    return None


def parse_class_filter(raw: str | None) -> ClassFilterKey:
    if raw is None or raw == "" or raw == "all":
        return "all"
    mapping: dict[str, ClassFilterKey] = {
        key: key for key, _ in CLASS_STYLE_FILTERS if key != "all"
    }
    return mapping.get(raw, "all")


def filter_classes(*, style: ClassFilterKey = "all") -> tuple[ClassItem, ...]:
    items = list_classes()
    if style == "all":
        return items
    return tuple(item for item in items if style in item.styles)


def build_class_list_query(*, style: ClassFilterKey) -> str:
    if style == "all":
        return "/classes"
    return f"/classes?{urlencode({'style': style})}"


def class_filter_tabs() -> list[dict[str, str]]:
    return [
        {
            "key": key,
            "label": label,
            "href": build_class_list_query(style=key),
        }
        for key, label in CLASS_STYLE_FILTERS
    ]


def class_style_labels(styles: tuple[ClassStyle, ...]) -> tuple[str, ...]:
    return tuple(CLASS_STYLE_LABELS[s] for s in styles)


def display_or_pending(values: tuple[str, ...], *, pending: bool) -> tuple[str, ...]:
    if pending or not values:
        return (CLASS_PENDING_LABEL,)
    return values
