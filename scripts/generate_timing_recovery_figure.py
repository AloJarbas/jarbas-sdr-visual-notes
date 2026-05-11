#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / 'assets/2026-05-11-symbol-timing-and-eye-opening.svg'
BETA = 0.35
SPAN = 8.0
DT = 0.01


def sinc(x: float) -> float:
    if abs(x) < 1e-12:
        return 1.0
    return math.sin(math.pi * x) / (math.pi * x)


def raised_cosine(t: float, beta: float = BETA) -> float:
    if abs(t) < 1e-12:
        return 1.0
    if beta > 0 and abs(abs(t) - 1.0 / (2.0 * beta)) < 1e-9:
        return (math.pi / 4.0) * sinc(1.0 / (2.0 * beta))
    denom = 1.0 - (2.0 * beta * t) ** 2
    return sinc(t) * math.cos(math.pi * beta * t) / denom


def waveform(symbols: list[float], start: int, end: int, dt: float = DT) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    t = float(start)
    while t <= end + 1e-9:
        y = 0.0
        for idx, sym in enumerate(symbols):
            y += sym * raised_cosine(t - idx)
        xs.append(t)
        ys.append(y)
        t += dt
    return xs, ys


def map_x(x: float, left: float, right: float, x_min: float, x_max: float) -> float:
    return left + (x - x_min) / (x_max - x_min) * (right - left)


def map_y(y: float, top: float, bottom: float, y_min: float, y_max: float) -> float:
    return bottom - (y - y_min) / (y_max - y_min) * (bottom - top)


def polyline(xs: list[float], ys: list[float], *, left: float, right: float, top: float, bottom: float, x_min: float, x_max: float, y_min: float, y_max: float, stroke: str, opacity: float = 1.0, width: float = 3.0) -> str:
    points = ' '.join(
        f'{map_x(x, left, right, x_min, x_max):.1f},{map_y(y, top, bottom, y_min, y_max):.1f}'
        for x, y in zip(xs, ys)
    )
    return f'<polyline points="{points}" fill="none" stroke="{stroke}" stroke-opacity="{opacity}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'


def vertical_line(x: float, y1: float, y2: float, stroke: str, dash: str = '8 8', width: float = 2.0, opacity: float = 0.8) -> str:
    return f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" stroke-dasharray="{dash}" opacity="{opacity}"/>'


def text(x: float, y: float, value: str, klass: str, anchor: str = 'start') -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{klass}" text-anchor="{anchor}">{value}</text>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"/>'


def main() -> None:
    width, height = 1300, 820
    top_left, top_right, top_top, top_bottom = 80.0, 1220.0, 170.0, 390.0
    bot_left, bot_right, bot_top, bot_bottom = 80.0, 1220.0, 500.0, 740.0
    x_min, x_max = -0.6, 4.6
    y_min, y_max = -1.5, 1.5

    main_symbols = [1.0, -1.0, 1.0, 1.0, -1.0]
    xs, ys = waveform(main_symbols, -0.5, 4.5)

    eye_sequences = [
        [-1.0, -1.0, 1.0, 1.0],
        [-1.0, 1.0, 1.0, -1.0],
        [1.0, -1.0, -1.0, 1.0],
        [1.0, 1.0, -1.0, -1.0],
    ]
    eye_paths: list[tuple[list[float], list[float]]] = []
    for seq in eye_sequences:
        exs, eys = waveform(seq, 0, 2)
        eye_paths.append((exs, eys))

    sample_offsets = {
        'early': (1.82, '#f97316'),
        'on-time': (2.00, '#f8fafc'),
        'late': (2.18, '#22c55e'),
    }

    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#081018"/>',
        '    <stop offset="100%" stop-color="#101d2a"/>',
        '  </linearGradient>',
        '  <style>',
        '    .title { font: 700 34px Helvetica, Arial, sans-serif; fill: #e6edf3; }',
        '    .subtitle { font: 500 18px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .label { font: 600 18px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .small { font: 500 15px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .panel { fill: #122131; stroke: #5e7fa3; stroke-width: 2; rx: 18; }',
        '    .axis { stroke: #39516a; stroke-width: 2; }',
        '    .grid { stroke: #223445; stroke-width: 1; opacity: 0.8; }',
        '  </style>',
        '</defs>',
        f'<rect width="{width}" height="{height}" fill="url(#bg)"/>',
        text(60, 58, 'Symbol timing and eye opening', 'title'),
        text(60, 88, 'Matched filtering is not enough by itself. You still need to sample near the center of the eye, where the current symbol is strongest and neighbors cancel.', 'subtitle'),
        f'<rect x="50" y="130" width="1200" height="300" class="panel"/>',
        f'<rect x="50" y="460" width="1200" height="320" class="panel"/>',
        text(80, 158, '1. Same matched-filter output, three different sampling phases', 'label'),
        text(80, 488, '2. Eye-diagram view: the best sample sits at the widest opening', 'label'),
    ]

    for tick in range(0, 5):
        x = map_x(tick, top_left, top_right, x_min, x_max)
        svg.append(f'<line x1="{x:.1f}" y1="{top_top}" x2="{x:.1f}" y2="{top_bottom}" class="grid"/>')
        svg.append(text(x, top_bottom + 24, f'{tick}T', 'small', 'middle'))

    eye_left, eye_right = -1.0, 1.0
    eye_ticks = [(-1.0, '-T'), (0.0, '0'), (1.0, '+T')]
    for tick, label in eye_ticks:
        x = map_x(tick, bot_left, bot_right, eye_left, eye_right)
        svg.append(f'<line x1="{x:.1f}" y1="{bot_top}" x2="{x:.1f}" y2="{bot_bottom}" class="grid"/>')
        svg.append(text(x, bot_bottom + 24, label, 'small', 'middle'))

    zero_top = map_y(0.0, top_top, top_bottom, y_min, y_max)
    zero_bot = map_y(0.0, bot_top, bot_bottom, y_min, y_max)
    svg.append(f'<line x1="{top_left}" y1="{zero_top:.1f}" x2="{top_right}" y2="{zero_top:.1f}" class="axis"/>')
    svg.append(f'<line x1="{bot_left}" y1="{zero_bot:.1f}" x2="{bot_right}" y2="{zero_bot:.1f}" class="axis"/>')
    svg.append(f'<line x1="{top_left}" y1="{top_bottom}" x2="{top_right}" y2="{top_bottom}" class="axis"/>')
    svg.append(f'<line x1="{bot_left}" y1="{bot_bottom}" x2="{bot_right}" y2="{bot_bottom}" class="axis"/>')
    svg.append(f'<line x1="{top_left}" y1="{top_top}" x2="{top_left}" y2="{top_bottom}" class="axis"/>')
    svg.append(f'<line x1="{bot_left}" y1="{bot_top}" x2="{bot_left}" y2="{bot_bottom}" class="axis"/>')

    svg.append(polyline(xs, ys, left=top_left, right=top_right, top=top_top, bottom=top_bottom, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, stroke='#60a5fa', width=3.5))

    legend_x = 910.0
    legend_y = 185.0
    for idx, (label, (offset, color)) in enumerate(sample_offsets.items()):
        x = map_x(offset, top_left, top_right, x_min, x_max)
        svg.append(vertical_line(x, top_top, top_bottom, color))
        sample_index = min(range(len(xs)), key=lambda i: abs(xs[i] - offset))
        y = map_y(ys[sample_index], top_top, top_bottom, y_min, y_max)
        svg.append(circle(x, y, 6.0, color))
        svg.append(circle(legend_x, legend_y + idx * 28.0 - 6.0, 6.0, color))
        svg.append(text(legend_x + 16.0, legend_y + idx * 28.0, label, 'small'))

    svg.append(text(80, 414, 'Too early or too late still lands on the right waveform, just not at the best decision instant.', 'small'))

    for exs, eys in eye_paths:
        shifted_xs = [x - 1.0 for x in exs]
        svg.append(polyline(shifted_xs, eys, left=bot_left, right=bot_right, top=bot_top, bottom=bot_bottom, x_min=eye_left, x_max=eye_right, y_min=y_min, y_max=y_max, stroke='#c084fc', opacity=0.48, width=2.8))

    eye_sample_positions = {
        'too early': (-0.12, '#f97316'),
        'best instant': (0.00, '#f8fafc'),
        'too late': (0.12, '#22c55e'),
    }
    note_x = 910.0
    note_y = 545.0
    for idx, (label, (offset, color)) in enumerate(eye_sample_positions.items()):
        x = map_x(offset, bot_left, bot_right, eye_left, eye_right)
        svg.append(vertical_line(x, bot_top, bot_bottom, color))
        svg.append(circle(note_x, note_y + idx * 28.0 - 6.0, 6.0, color))
        svg.append(text(note_x + 16.0, note_y + idx * 28.0, label, 'small'))

    svg.append(text(80, 770, 'The eye opening is widest at the centered instant. That is why timing recovery tries to keep the sampler there instead of drifting across the slopes.', 'small'))
    svg.append('</svg>')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(svg) + '\n')
    print(f'WROTE {OUT}')


if __name__ == '__main__':
    main()
