#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_FILES = [
    'assets/2026-05-10-pulse-shaping-matched-filter.svg',
    'assets/2026-05-11-srrc-rolloff-and-matched-filter.svg',
    'assets/2026-05-11-symbol-timing-and-eye-opening.svg',
    'assets/2026-05-11-gardner-vs-mueller-muller.svg',
    'assets/2026-05-14-carrier-recovery-after-timing.svg',
    'assets/2026-05-16-carrier-lock-detection-and-handoff.svg',
    'assets/2026-05-17-carrier-offset-pull-in-alias.svg',
    'assets/2026-05-20-band-edge-discriminant-slope-check.svg',
    'assets/2026-05-22-band-edge-filter-design-comparison.svg',
    'assets/2026-05-22-band-edge-guardband-cost-comparison.svg',
    'assets/2026-05-15-qpsk-phase-ambiguity-resolution.svg',
]
SVG_NS = {'svg': 'http://www.w3.org/2000/svg'}
FONT_RE = re.compile(r'\.(\w+)\s*\{[^}]*font:\s*\d+\s+(\d+)px')
CHAR_WIDTH = 0.56
EDGE_MARGIN = 14.0


def iter_targets(argv: list[str]) -> list[Path]:
    if len(argv) > 1:
        return [Path(value) for value in argv[1:]]
    return [Path(value) for value in DEFAULT_FILES]


def class_font_sizes(root: ET.Element) -> dict[str, int]:
    style_text = ''.join((node.text or '') for node in root.findall('.//svg:style', SVG_NS))
    return {klass: int(size) for klass, size in FONT_RE.findall(style_text)}


def line_bounds(x: float, anchor: str, text_value: str, font_size: int) -> tuple[float, float]:
    est_width = len(text_value) * font_size * CHAR_WIDTH
    if anchor == 'middle':
        left = x - est_width / 2.0
    elif anchor == 'end':
        left = x - est_width
    else:
        left = x
    return left, left + est_width


def check_svg(path: Path) -> list[str]:
    root = ET.parse(path).getroot()
    width = float(root.attrib.get('width', root.attrib['viewBox'].split()[2]))
    font_sizes = class_font_sizes(root)
    issues: list[str] = []

    for node in root.findall('.//svg:text', SVG_NS):
        klass = node.attrib.get('class', '')
        font_size = font_sizes.get(klass, 16)
        anchor = node.attrib.get('text-anchor', 'start')
        base_x = float(node.attrib.get('x', '0'))
        tspans = node.findall('svg:tspan', SVG_NS)
        lines = tspans if tspans else [node]
        for line in lines:
            text_value = ''.join(line.itertext()).strip()
            if not text_value:
                continue
            x = float(line.attrib.get('x', base_x))
            left, right = line_bounds(x, anchor, text_value, font_size)
            if left < EDGE_MARGIN or right > width - EDGE_MARGIN:
                issues.append(
                    f'{path}: text may exceed bounds ({klass!r}) -> {text_value!r} [{left:.1f}, {right:.1f}] within width {width:.1f}'
                )
    return issues


def main(argv: list[str]) -> int:
    targets = iter_targets(argv)
    all_issues: list[str] = []
    for target in targets:
        all_issues.extend(check_svg(target))
    if all_issues:
        print('\n'.join(all_issues))
        return 1
    print('SVG layout check passed for', len(targets), 'file(s).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
