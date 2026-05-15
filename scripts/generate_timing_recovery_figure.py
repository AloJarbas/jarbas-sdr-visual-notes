#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

from svg_layout import add_wrapped_text, svg_root, text, text_block

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


def waveform(symbols: list[float], start: int | float, end: int | float, dt: float = DT) -> tuple[list[float], list[float]]:
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


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"/>'


def polyline(points: list[tuple[float, float]], stroke: str, opacity: float = 1.0, width: float = 3.0, clip_id: str | None = None) -> str:
    clip_attr = f' clip-path="url(#{clip_id})"' if clip_id else ''
    coords = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return (
        f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-opacity="{opacity}" '
        f'stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"{clip_attr}/>'
    )


def vertical_line(x: float, y1: float, y2: float, stroke: str, dash: str = '8 8', width: float = 2.0, opacity: float = 0.8) -> str:
    return f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" stroke-dasharray="{dash}" opacity="{opacity}"/>'


def main() -> None:
    width, height = 1320, 930
    top_panel = (50.0, 160.0, 1220.0, 300.0)
    bottom_panel = (50.0, 500.0, 1220.0, 320.0)

    top_left, top_right, top_top, top_bottom = 90.0, 860.0, 235.0, 400.0
    bot_left, bot_right, bot_top, bot_bottom = 90.0, 860.0, 575.0, 770.0
    notes_left = 910.0
    x_min, x_max = -0.6, 4.6
    eye_left, eye_right = -1.0, 1.0
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
    eye_sample_positions = {
        'too early': (-0.12, '#f97316'),
        'best instant': (0.00, '#f8fafc'),
        'too late': (0.12, '#22c55e'),
    }

    svg: list[str] = [
        svg_root(width, height),
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#081018"/>',
        '    <stop offset="100%" stop-color="#101d2a"/>',
        '  </linearGradient>',
        '  <clipPath id="clip-top"><rect x="90" y="235" width="770" height="165" rx="12"/></clipPath>',
        '  <clipPath id="clip-bottom"><rect x="90" y="575" width="770" height="195" rx="12"/></clipPath>',
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
    ]
    add_wrapped_text(
        svg,
        60,
        92,
        'Matched filtering is not enough by itself. You still need to sample near the center of the eye, where the current symbol is strongest and neighbors cancel.',
        'subtitle',
        max_width=1130,
        font_size=18,
        line_height=24,
    )
    svg.extend([
        f'<rect x="{top_panel[0]}" y="{top_panel[1]}" width="{top_panel[2]}" height="{top_panel[3]}" class="panel"/>',
        f'<rect x="{bottom_panel[0]}" y="{bottom_panel[1]}" width="{bottom_panel[2]}" height="{bottom_panel[3]}" class="panel"/>',
        text(80, 194, '1. Same matched-filter output, three different sampling phases', 'label'),
        text(80, 534, '2. Eye-diagram view: the best sample sits at the widest opening', 'label'),
        text(notes_left, 226, 'Sampling-phase cue', 'label'),
        text(notes_left, 566, 'Eye-opening cue', 'label'),
    ])

    for tick in range(0, 5):
        x = map_x(tick, top_left, top_right, x_min, x_max)
        svg.append(f'<line x1="{x:.1f}" y1="{top_top}" x2="{x:.1f}" y2="{top_bottom}" class="grid"/>')
        svg.append(text(x, top_bottom + 28, f'{tick}T', 'small', 'middle'))

    for tick, label in [(-1.0, '-T'), (0.0, '0'), (1.0, '+T')]:
        x = map_x(tick, bot_left, bot_right, eye_left, eye_right)
        svg.append(f'<line x1="{x:.1f}" y1="{bot_top}" x2="{x:.1f}" y2="{bot_bottom}" class="grid"/>')
        svg.append(text(x, bot_bottom + 28, label, 'small', 'middle'))

    zero_top = map_y(0.0, top_top, top_bottom, y_min, y_max)
    zero_bot = map_y(0.0, bot_top, bot_bottom, y_min, y_max)
    svg.extend([
        f'<line x1="{top_left}" y1="{zero_top:.1f}" x2="{top_right}" y2="{zero_top:.1f}" class="axis"/>',
        f'<line x1="{bot_left}" y1="{zero_bot:.1f}" x2="{bot_right}" y2="{zero_bot:.1f}" class="axis"/>',
        f'<line x1="{top_left}" y1="{top_bottom}" x2="{top_right}" y2="{top_bottom}" class="axis"/>',
        f'<line x1="{bot_left}" y1="{bot_bottom}" x2="{bot_right}" y2="{bot_bottom}" class="axis"/>',
        f'<line x1="{top_left}" y1="{top_top}" x2="{top_left}" y2="{top_bottom}" class="axis"/>',
        f'<line x1="{bot_left}" y1="{bot_top}" x2="{bot_left}" y2="{bot_bottom}" class="axis"/>',
    ])

    waveform_points = [(map_x(x, top_left, top_right, x_min, x_max), map_y(y, top_top, top_bottom, y_min, y_max)) for x, y in zip(xs, ys)]
    svg.append(polyline(waveform_points, '#60a5fa', width=3.5, clip_id='clip-top'))

    legend_y = 258.0
    for idx, (label, (offset, color)) in enumerate(sample_offsets.items()):
        x = map_x(offset, top_left, top_right, x_min, x_max)
        svg.append(vertical_line(x, top_top, top_bottom, color))
        sample_index = min(range(len(xs)), key=lambda i: abs(xs[i] - offset))
        y = map_y(ys[sample_index], top_top, top_bottom, y_min, y_max)
        svg.append(circle(x, y, 6.0, color))
        svg.append(circle(notes_left + 16.0, legend_y + idx * 32.0 - 6.0, 6.0, color))
        svg.append(text(notes_left + 34.0, legend_y + idx * 32.0, label, 'small'))

    add_wrapped_text(
        svg,
        notes_left,
        372,
        'Too early or too late still touches the same waveform. The loop is trying to hold the sampler at the flattest, most decisive instant.',
        'small',
        max_width=250,
        font_size=15,
        line_height=21,
    )

    for exs, eys in eye_paths:
        shifted_xs = [x - 1.0 for x in exs]
        eye_points = [(map_x(x, bot_left, bot_right, eye_left, eye_right), map_y(y, bot_top, bot_bottom, y_min, y_max)) for x, y in zip(shifted_xs, eys)]
        svg.append(polyline(eye_points, '#c084fc', opacity=0.48, width=2.8, clip_id='clip-bottom'))

    note_y = 598.0
    for idx, (label, (offset, color)) in enumerate(eye_sample_positions.items()):
        x = map_x(offset, bot_left, bot_right, eye_left, eye_right)
        svg.append(vertical_line(x, bot_top, bot_bottom, color))
        svg.append(circle(notes_left + 16.0, note_y + idx * 32.0 - 6.0, 6.0, color))
        svg.append(text(notes_left + 34.0, note_y + idx * 32.0, label, 'small'))

    add_wrapped_text(
        svg,
        notes_left,
        710,
        'The eye is widest at the centered instant. Timing recovery keeps the sampler there instead of letting it drift onto the slopes.',
        'small',
        max_width=250,
        font_size=15,
        line_height=21,
    )
    svg.append(text_block(80, 854, ['Layout rule used here: give the plot its own note column so legends and captions do not steal plotting space.'], 'small', 21))
    svg.append('</svg>')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(svg) + '\n')
    print(f'WROTE {OUT}')


if __name__ == '__main__':
    main()
