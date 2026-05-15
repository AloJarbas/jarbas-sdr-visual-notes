#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text, text_block, wrap_text

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-15-qpsk-phase-ambiguity-resolution.svg'
PNG_OUT = REPO / 'assets/2026-05-15-qpsk-phase-ambiguity-resolution.png'

WIDTH = 1580
HEIGHT = 760
PANEL_W = 440.0
PANEL_H = 510.0
PANEL_TOP = 170.0
PANEL_LEFTS = [40.0, 520.0, 1000.0]

QPSK_LABELS = ['00', '01', '11', '10']
QPSK_ANGLES = [math.pi / 4.0 + k * math.pi / 2.0 for k in range(4)]
STEP_COLORS = ['#60a5fa', '#22c55e', '#f59e0b', '#f97316']


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round"{dash_attr}/>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0, stroke: str | None = None, stroke_width: float = 0.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def panel(svg: list[str], left: float, title: str, subtitle: str) -> None:
    svg.append(f'<rect x="{left:.1f}" y="{PANEL_TOP:.1f}" width="{PANEL_W:.1f}" height="{PANEL_H:.1f}" class="panel"/>')
    title_lines = wrap_text(title, max_width=PANEL_W - 44.0, font_size=18)
    svg.append(text_block(left + 22.0, PANEL_TOP + 34.0, title_lines, 'label', 22.0))
    subtitle_y = PANEL_TOP + 34.0 + 22.0 * max(len(title_lines), 1) + 8.0
    add_wrapped_text(svg, left + 22.0, subtitle_y, subtitle, 'small', max_width=PANEL_W - 44.0, font_size=15, line_height=20)


def arrow(svg: list[str], x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 3.0, opacity: float = 0.9) -> None:
    svg.append(line(x1, y1, x2, y2, stroke, width, opacity))
    angle = math.atan2(y2 - y1, x2 - x1)
    back = 12.0
    spread = 0.44
    p1 = (x2 - back * math.cos(angle - spread), y2 - back * math.sin(angle - spread))
    p2 = (x2 - back * math.cos(angle + spread), y2 - back * math.sin(angle + spread))
    svg.append(line(x2, y2, p1[0], p1[1], stroke, width, opacity))
    svg.append(line(x2, y2, p2[0], p2[1], stroke, width, opacity))


def draw_constellation(svg: list[str], cx: float, cy: float, radius: float, labels: list[str], badge: str) -> None:
    svg.append(circle(cx, cy, radius, 'none', 1.0, '#284055', 2.0))
    svg.append(line(cx - radius - 16.0, cy, cx + radius + 16.0, cy, '#35506a', 2.0))
    svg.append(line(cx, cy - radius - 16.0, cx, cy + radius + 16.0, '#35506a', 2.0))
    for angle, label in zip(QPSK_ANGLES, labels):
        px = cx + radius * math.cos(angle)
        py = cy - radius * math.sin(angle)
        svg.append(circle(px, py, 7.0, '#f8fafc', 0.95))
        tx = cx + (radius + 28.0) * math.cos(angle)
        ty = cy - (radius + 28.0) * math.sin(angle)
        svg.append(text(tx, ty + 5.0, label, 'micro', 'middle'))
    svg.append(text(cx, cy - radius - 18.0, badge, 'tiny', 'middle'))


def panel_one(svg: list[str], left: float) -> None:
    positions = [
        (left + 122.0, PANEL_TOP + 192.0, 54.0, '0°'),
        (left + 322.0, PANEL_TOP + 192.0, 54.0, '+90°'),
        (left + 122.0, PANEL_TOP + 374.0, 54.0, '+180°'),
        (left + 322.0, PANEL_TOP + 374.0, 54.0, '+270°'),
    ]
    for idx, (cx, cy, radius, badge) in enumerate(positions):
        rotation = idx % 4
        labels = QPSK_LABELS[-rotation:] + QPSK_LABELS[:-rotation] if rotation else list(QPSK_LABELS)
        draw_constellation(svg, cx, cy, radius, labels, badge)
    add_wrapped_text(
        svg,
        left + 22.0,
        PANEL_TOP + 470.0,
        'Once the loop stops the fast spin, the cloud is stable. But QPSK still has four equally valid labelings, separated by 90°.',
        'tiny',
        max_width=PANEL_W - 44.0,
        font_size=14,
        line_height=20,
    )


def candidate_row(svg: list[str], left: float, y: float, label: str, sequence: str, highlight: bool = False) -> None:
    fill = '#16324a' if not highlight else '#14532d'
    stroke = '#35506a' if not highlight else '#22c55e'
    svg.append(f'<rect x="{left:.1f}" y="{y - 20.0:.1f}" width="396.0" height="40.0" rx="12.0" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    svg.append(text(left + 16.0, y + 6.0, label, 'tiny'))
    svg.append(text(left + 212.0, y + 6.0, sequence, 'mono', 'middle'))
    if highlight:
        svg.append(text(left + 368.0, y + 6.0, 'match', 'tiny', 'end'))


def panel_two(svg: list[str], left: float) -> None:
    svg.append(text(left + 22.0, PANEL_TOP + 140.0, 'expected unique word:', 'tiny'))
    svg.append(text(left + 246.0, PANEL_TOP + 140.0, '00  01  11  10', 'mono', 'middle'))
    svg.append(line(left + 22.0, PANEL_TOP + 152.0, left + PANEL_W - 22.0, PANEL_TOP + 152.0, '#35506a', 2.0))
    rows = [
        ('try 0°', '11  10  00  01', False),
        ('try -90°', '10  00  01  11', False),
        ('try -180°', '00  01  11  10', True),
        ('try -270°', '01  11  10  00', False),
    ]
    for idx, row in enumerate(rows):
        candidate_row(svg, left + 22.0, PANEL_TOP + 212.0 + idx * 56.0, *row)
    arrow(svg, left + 310.0, PANEL_TOP + 382.0, left + 310.0, PANEL_TOP + 430.0, '#22c55e', 3.0)
    add_wrapped_text(
        svg,
        left + 22.0,
        PANEL_TOP + 468.0,
        'Known symbols or a unique word let the receiver test the four rotations and keep the one that matches the expected pattern.',
        'tiny',
        max_width=PANEL_W - 44.0,
        font_size=14,
        line_height=20,
    )


def phase_point(cx: float, cy: float, radius: float, degrees: float) -> tuple[float, float]:
    angle = math.radians(degrees)
    return cx + radius * math.cos(angle), cy - radius * math.sin(angle)


def draw_phase_track(svg: list[str], cx: float, cy: float, radius: float, phases: list[float], title: str) -> None:
    svg.append(text(cx, cy - radius - 30.0, title, 'tiny', 'middle'))
    svg.append(circle(cx, cy, radius, 'none', 1.0, '#284055', 2.0))
    for axis in (0.0, 90.0, 180.0, 270.0):
        x, y = phase_point(cx, cy, radius, axis)
        svg.append(line(cx, cy, x, y, '#223445', 1.4, 0.55, '5 7'))
    points = [phase_point(cx, cy, radius, value) for value in phases]
    for idx, (x, y) in enumerate(points):
        svg.append(circle(x, y, 7.0, STEP_COLORS[idx], 0.95))
        svg.append(text(x, y - 12.0, f's{idx}', 'micro', 'middle'))
    for idx in range(len(points) - 1):
        arrow(svg, points[idx][0], points[idx][1], points[idx + 1][0], points[idx + 1][1], STEP_COLORS[idx + 1], 2.8, 0.88)


def panel_three(svg: list[str], left: float) -> None:
    tx = [45.0, 135.0, 225.0, 135.0]
    rx = [value + 90.0 for value in tx]
    draw_phase_track(svg, left + 220.0, PANEL_TOP + 220.0, 78.0, tx, 'Tx absolute phase')
    draw_phase_track(svg, left + 220.0, PANEL_TOP + 390.0, 78.0, rx, 'Rx after a constant +90° lock offset')
    svg.append(text(left + 220.0, PANEL_TOP + 492.0, 'phase steps on both rows: +90°, +90°, -90°', 'mono', 'middle'))
    add_wrapped_text(
        svg,
        left + 22.0,
        PANEL_TOP + 528.0,
        'Differential encoding keeps information in symbol-to-symbol phase changes, so a constant quadrant offset cancels during differential decoding. This is still coherent carrier recovery, not noncoherent differential detection.',
        'tiny',
        max_width=PANEL_W - 44.0,
        font_size=14,
        line_height=20,
    )


def main() -> None:
    svg: list[str] = [
        svg_root(WIDTH, HEIGHT),
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#071018"/>',
        '    <stop offset="100%" stop-color="#0f1d2b"/>',
        '  </linearGradient>',
        '  <style>',
        '    .title { font: 700 32px Helvetica, Arial, sans-serif; fill: #e6edf3; }',
        '    .subtitle { font: 500 18px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .label { font: 700 18px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .small { font: 500 15px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .tiny { font: 500 14px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .micro { font: 600 12px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .mono { font: 600 18px Menlo, Consolas, monospace; fill: #e6edf3; }',
        '    .badge { font: 700 12px Helvetica, Arial, sans-serif; fill: #eff6ff; }',
        '    .axislabel { font: 600 13px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .panel { fill: #122131; stroke: #5e7fa3; stroke-width: 2; rx: 18; }',
        '  </style>',
        '</defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>',
        text(50.0, 52.0, 'QPSK phase ambiguity resolution', 'title'),
    ]
    svg.append(
        text_block(
            50.0,
            82.0,
            [
                'Carrier lock can stop rotation without fixing the QPSK labels.',
                'Known symbols or differential encoding finish the job.',
            ],
            'subtitle',
            24.0,
        )
    )

    panel(svg, PANEL_LEFTS[0], '1. Carrier lock can still leave four labelings', 'A decision-directed QPSK loop removes rotation, but the final lock is only known modulo 90°.')
    panel(svg, PANEL_LEFTS[1], '2. Known symbols choose the right rotation', 'Test the four candidate rotations against a known pattern and keep the one that matches.')
    panel(svg, PANEL_LEFTS[2], '3. Differential encoding makes constant rotation harmless', 'Absolute phase may shift, but symbol-to-symbol phase changes survive a fixed quadrant offset.')

    panel_one(svg, PANEL_LEFTS[0])
    panel_two(svg, PANEL_LEFTS[1])
    panel_three(svg, PANEL_LEFTS[2])

    add_wrapped_text(
        svg,
        50.0,
        722.0,
        'Known symbols fix the labeling after lock. Differential encoding avoids caring about the absolute quadrant.',
        'small',
        max_width=1320.0,
        font_size=15,
        line_height=21.0,
    )
    svg.append('</svg>')

    SVG_OUT.parent.mkdir(parents=True, exist_ok=True)
    SVG_OUT.write_text('\n'.join(svg) + '\n')
    export_png_from_svg(SVG_OUT, PNG_OUT, size=1600, dpi=300)
    print(f'WROTE {SVG_OUT}')
    print(f'WROTE {PNG_OUT}')


if __name__ == '__main__':
    main()
