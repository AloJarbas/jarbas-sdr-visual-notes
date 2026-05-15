#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

from svg_layout import add_wrapped_text, svg_root, text, text_block

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / 'assets/2026-05-11-gardner-vs-mueller-muller.svg'
BETA = 0.35
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


def waveform(symbols: list[float], start: float, end: float, dt: float = DT) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    t = start
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


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, dash: str | None = None, opacity: float = 1.0) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"{dash_attr}/>'


def polyline(points: list[tuple[float, float]], stroke: str, opacity: float = 1.0, width: float = 3.0, clip_id: str | None = None) -> str:
    clip_attr = f' clip-path="url(#{clip_id})"' if clip_id else ''
    coords = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return (
        f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-opacity="{opacity}" '
        f'stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"{clip_attr}/>'
    )


def panel(svg: list[str], left: float, top: float, width: float, height: float, title: str, subtitle: str) -> None:
    svg.append(f'<rect x="{left:.1f}" y="{top:.1f}" width="{width:.1f}" height="{height:.1f}" class="panel"/>')
    svg.append(text(left + 24, top + 36, title, 'label'))
    add_wrapped_text(svg, left + 24, top + 62, subtitle, 'small', max_width=width - 48, font_size=15, line_height=20)


def sample_y(xs: list[float], ys: list[float], x_target: float) -> float:
    idx = min(range(len(xs)), key=lambda i: abs(xs[i] - x_target))
    return ys[idx]


def main() -> None:
    width, height = 1320, 940
    panel_left = 50.0
    panel_width = 1220.0
    panel_height = 330.0
    top_panel_top = 160.0
    bottom_panel_top = 530.0

    plot_left, plot_right = 86.0, 790.0
    upper_top, upper_bottom = 250.0, 420.0
    lower_top, lower_bottom = 620.0, 790.0
    note_x = 836.0
    x_min, x_max = -0.5, 3.5
    y_min, y_max = -1.6, 1.6

    symbols = [-1.0, 1.0, -1.0, 1.0]
    xs, ys = waveform(symbols, x_min, x_max)

    svg: list[str] = [
        svg_root(width, height),
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#071018"/>',
        '    <stop offset="100%" stop-color="#0f1d2b"/>',
        '  </linearGradient>',
        '  <clipPath id="clip-upper"><rect x="86" y="250" width="704" height="170" rx="12"/></clipPath>',
        '  <clipPath id="clip-lower"><rect x="86" y="620" width="704" height="170" rx="12"/></clipPath>',
        '  <style>',
        '    .title { font: 700 34px Helvetica, Arial, sans-serif; fill: #e6edf3; }',
        '    .subtitle { font: 500 18px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .label { font: 700 20px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .small { font: 500 15px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .tiny { font: 500 13px Helvetica, Arial, sans-serif; fill: #8aa3bc; }',
        '    .panel { fill: #122131; stroke: #5e7fa3; stroke-width: 2; rx: 18; }',
        '    .grid { stroke: #223445; stroke-width: 1; opacity: 0.75; }',
        '    .axis { stroke: #39516a; stroke-width: 2; }',
        '  </style>',
        '</defs>',
        f'<rect width="{width}" height="{height}" fill="url(#bg)"/>',
        text(60, 58, 'Gardner vs Mueller and Muller', 'title'),
    ]
    add_wrapped_text(
        svg,
        60,
        92,
        'Both loops chase symbol timing, but they read different clues from the waveform.',
        'subtitle',
        max_width=1140,
        font_size=18,
        line_height=24,
    )

    panel(svg, panel_left, top_panel_top, panel_width, panel_height, '1. Gardner TED: watch the midpoint between symbols', 'Non-data-aided intuition at about 2 samples per symbol.')
    panel(svg, panel_left, bottom_panel_top, panel_width, panel_height, '2. Mueller and Muller: compare adjacent symbol-spaced samples', 'Decision-directed intuition at 1 sample per symbol after the matched filter.')

    for plot_top, plot_bottom in ((upper_top, upper_bottom), (lower_top, lower_bottom)):
        zero_y = map_y(0.0, plot_top, plot_bottom, y_min, y_max)
        svg.append(line(plot_left, zero_y, plot_right, zero_y, '#39516a', 2.0))
        svg.append(line(plot_left, plot_top, plot_left, plot_bottom, '#39516a', 2.0))
        svg.append(line(plot_left, plot_bottom, plot_right, plot_bottom, '#39516a', 2.0))
        for tick in range(0, 4):
            x = map_x(float(tick), plot_left, plot_right, x_min, x_max)
            svg.append(line(x, plot_top, x, plot_bottom, '#223445', 1.0))
            svg.append(text(x, plot_bottom + 26, f'{tick}T', 'tiny', 'middle'))

    waveform_points_upper = [(map_x(x, plot_left, plot_right, x_min, x_max), map_y(y, upper_top, upper_bottom, y_min, y_max)) for x, y in zip(xs, ys)]
    waveform_points_lower = [(map_x(x, plot_left, plot_right, x_min, x_max), map_y(y, lower_top, lower_bottom, y_min, y_max)) for x, y in zip(xs, ys)]
    svg.append(polyline(waveform_points_upper, '#60a5fa', width=3.5, clip_id='clip-upper'))
    svg.append(polyline(waveform_points_lower, '#a78bfa', width=3.5, clip_id='clip-lower'))

    gardner_samples = [0.5, 1.0, 1.5]
    gardner_colors = ['#f97316', '#f8fafc', '#22c55e']
    gardner_labels = ['early', 'prompt', 'late']
    for x_t, color, label in zip(gardner_samples, gardner_colors, gardner_labels):
        x = map_x(x_t, plot_left, plot_right, x_min, x_max)
        y = map_y(sample_y(xs, ys, x_t), upper_top, upper_bottom, y_min, y_max)
        svg.append(line(x, upper_top, x, upper_bottom, color, 2.0, '8 8', 0.9))
        svg.append(circle(x, y, 6.0, color))
        svg.append(text(x, upper_bottom + 46, label, 'tiny', 'middle'))

    svg.append(text(note_x, 255, 'Gardner cue', 'label'))
    add_wrapped_text(svg, note_x, 286, 'Use the midpoint sample against the two neighbors. If the zero crossing leans left or right, the error sign tells the loop which way to move.', 'small', max_width=360, font_size=15, line_height=21)
    svg.append(text(note_x, 347, 'Why it helps', 'small'))
    add_wrapped_text(svg, note_x, 368, 'No symbol decisions required yet, so it is useful early in the receive chain.', 'tiny', max_width=360, font_size=13, line_height=18)
    svg.append(text(note_x, 402, 'Tradeoff', 'small'))
    add_wrapped_text(svg, note_x, 423, 'It wants at least about 2 samples per symbol because it explicitly watches the midpoint.', 'tiny', max_width=360, font_size=13, line_height=18)

    mm_positions = [1.0, 2.0]
    mm_colors = ['#f8fafc', '#22c55e']
    mm_labels = ['prev sample', 'current sample']
    for x_t, color, label in zip(mm_positions, mm_colors, mm_labels):
        x = map_x(x_t, plot_left, plot_right, x_min, x_max)
        y = map_y(sample_y(xs, ys, x_t), lower_top, lower_bottom, y_min, y_max)
        svg.append(line(x, lower_top, x, lower_bottom, color, 2.0, '8 8', 0.9))
        svg.append(circle(x, y, 6.0, color))
        svg.append(text(x, lower_bottom + 46, label, 'tiny', 'middle'))

    for x_t, decision in ((1.0, '+1 decision'), (2.0, '-1 decision')):
        x = map_x(x_t, plot_left, plot_right, x_min, x_max)
        y = lower_bottom + 62
        svg.append(circle(x, y - 8.0, 5.0, '#f97316'))
        svg.append(text(x, y + 12.0, decision, 'tiny', 'middle'))

    svg.append(text(note_x, 625, 'Mueller and Muller cue', 'label'))
    add_wrapped_text(svg, note_x, 656, 'Compare adjacent symbol-spaced matched-filter samples after slicing. It uses pulse symmetry: with correct timing, neighboring sidelobe contributions balance.', 'small', max_width=360, font_size=15, line_height=21)
    svg.append(text(note_x, 717, 'Why it helps', 'small'))
    add_wrapped_text(svg, note_x, 738, 'It can work at 1 sample per symbol, so it fits a later decision-directed stage.', 'tiny', max_width=360, font_size=13, line_height=18)
    svg.append(text(note_x, 772, 'Tradeoff', 'small'))
    add_wrapped_text(svg, note_x, 793, 'Bad decisions or the wrong pulse shape can poison the timing cue. Gardner reads the midpoint; M&M reads adjacent decided symbols.', 'tiny', max_width=360, font_size=13, line_height=18)

    svg.append(text_block(86, 892, ['Layout rule used here: the notes now live in a dedicated column, so explanatory copy cannot collide with the waveform.'], 'small', 21))
    svg.append('</svg>')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(svg) + '\n')
    print(f'WROTE {OUT}')


if __name__ == '__main__':
    main()
