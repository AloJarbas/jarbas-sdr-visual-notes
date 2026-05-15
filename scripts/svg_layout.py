from __future__ import annotations

from html import escape
from textwrap import wrap
from typing import Iterable, Sequence


def svg_root(width: int | float, height: int | float) -> str:
    width_int = int(width)
    height_int = int(height)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width_int}" height="{height_int}" '
        f'viewBox="0 0 {width_int} {height_int}">'
    )


def wrap_text(value: str, max_width: float, font_size: float, char_width: float = 0.56) -> list[str]:
    cleaned = ' '.join(value.split())
    if not cleaned:
        return ['']
    max_chars = max(10, int(max_width / max(font_size * char_width, 1.0)))
    return wrap(cleaned, width=max_chars, break_long_words=False, break_on_hyphens=False) or [cleaned]


def text(x: float, y: float, value: str, klass: str, anchor: str = 'start') -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{klass}" text-anchor="{anchor}">{escape(value)}</text>'


def text_block(
    x: float,
    y: float,
    lines: Sequence[str] | str,
    klass: str,
    line_height: float,
    anchor: str = 'start',
) -> str:
    if isinstance(lines, str):
        prepared = [lines]
    else:
        prepared = list(lines) or ['']
    spans: list[str] = []
    for idx, line_value in enumerate(prepared):
        dy = '0' if idx == 0 else f'{line_height:.1f}'
        spans.append(f'<tspan x="{x:.1f}" dy="{dy}">{escape(line_value)}</tspan>')
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{klass}" text-anchor="{anchor}">' + ''.join(spans) + '</text>'


def add_wrapped_text(
    svg: list[str],
    x: float,
    y: float,
    value: str,
    klass: str,
    *,
    max_width: float,
    font_size: float,
    line_height: float,
    anchor: str = 'start',
) -> list[str]:
    lines = wrap_text(value, max_width=max_width, font_size=font_size)
    svg.append(text_block(x, y, lines, klass, line_height, anchor))
    return lines
