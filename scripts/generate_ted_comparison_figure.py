#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

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


def text(x: float, y: float, value: str, klass: str, anchor: str = 'start') -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{klass}" text-anchor="{anchor}">{value}</text>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"/>'


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, dash: str | None = None, opacity: float = 1.0) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"{dash_attr}/>'


def polyline(xs: list[float], ys: list[float], *, left: float, right: float, top: float, bottom: float, x_min: float, x_max: float, y_min: float, y_max: float, stroke: str, opacity: float = 1.0, width: float = 3.0) -> str:
    points = ' '.join(
        f'{map_x(x, left, right, x_min, x_max):.1f},{map_y(y, top, bottom, y_min, y_max):.1f}'
        for x, y in zip(xs, ys)
    )
    return f'<polyline points="{points}" fill="none" stroke="{stroke}" stroke-opacity="{opacity}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'


def panel(svg: list[str], left: float, top: float, width: float, height: float, title: str, subtitle: str) -> None:
    svg.append(f'<rect x="{left:.1f}" y="{top:.1f}" width="{width:.1f}" height="{height:.1f}" class="panel"/>')
    svg.append(text(left + 24, top + 34, title, 'label'))
    svg.append(text(left + 24, top + 58, subtitle, 'small'))


def sample_y(xs: list[float], ys: list[float], x_target: float) -> float:
    idx = min(range(len(xs)), key=lambda i: abs(xs[i] - x_target))
    return ys[idx]


def main() -> None:
    width, height = 1320, 860
    panel_left, panel_right = 60.0, 1260.0
    upper_top, upper_bottom = 150.0, 430.0
    lower_top, lower_bottom = 500.0, 790.0
    x_min, x_max = -0.5, 3.5
    y_min, y_max = -1.6, 1.6

    symbols = [-1.0, 1.0, -1.0, 1.0]
    xs, ys = waveform(symbols, x_min, x_max)

    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#071018"/>',
        '    <stop offset="100%" stop-color="#0f1d2b"/>',
        '  </linearGradient>',
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
        text(60, 88, 'Both loops chase symbol timing, but they read different clues from the waveform.', 'subtitle'),
    ]

    panel(svg, 50, 130, 1220, 330, '1. Gardner TED: watch the midpoint between symbols', 'Non-data-aided intuition at about 2 samples per symbol.')
    panel(svg, 50, 480, 1220, 330, '2. Mueller and Muller: compare adjacent symbol-spaced samples', 'Decision-directed intuition at 1 sample per symbol after the matched filter.')

    for bounds in ((upper_top, upper_bottom), (lower_top, lower_bottom)):
        top, bottom = bounds
        zero_y = map_y(0.0, top + 40, bottom - 40, y_min, y_max)
        svg.append(line(panel_left, zero_y, panel_right, zero_y, '#39516a', 2.0))
        svg.append(line(panel_left, top + 40, panel_left, bottom - 40, '#39516a', 2.0))
        for tick in range(0, 4):
            x = map_x(float(tick), panel_left, panel_right, x_min, x_max)
            svg.append(line(x, top + 40, x, bottom - 40, '#223445', 1.0))

    svg.append(polyline(xs, ys, left=panel_left, right=panel_right, top=upper_top + 40, bottom=upper_bottom - 40, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, stroke='#60a5fa', width=3.5))
    svg.append(polyline(xs, ys, left=panel_left, right=panel_right, top=lower_top + 40, bottom=lower_bottom - 40, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, stroke='#a78bfa', width=3.5))

    gardner_samples = [0.5, 1.0, 1.5]
    gardner_colors = ['#f97316', '#f8fafc', '#22c55e']
    gardner_labels = ['early', 'prompt', 'late']
    for x_t, color, label in zip(gardner_samples, gardner_colors, gardner_labels):
        x = map_x(x_t, panel_left, panel_right, x_min, x_max)
        y = map_y(sample_y(xs, ys, x_t), upper_top + 40, upper_bottom - 40, y_min, y_max)
        svg.append(line(x, upper_top + 40, x, upper_bottom - 40, color, 2.0, '8 8', 0.9))
        svg.append(circle(x, y, 6.0, color))
        svg.append(text(x, upper_top + 255, label, 'tiny', 'middle'))

    svg.append(text(900, 205, 'Gardner cue', 'label'))
    svg.append(text(900, 232, 'Use the midpoint sample against the two neighbors.', 'small'))
    svg.append(text(900, 256, 'If the zero crossing leans left or right, the sign of the error tells the loop which way to move.', 'tiny'))
    svg.append(text(900, 282, 'Why it helps:', 'small'))
    svg.append(text(900, 304, 'No symbol decisions required yet, so it is useful early in the receive chain.', 'tiny'))
    svg.append(text(900, 328, 'Tradeoff:', 'small'))
    svg.append(text(900, 350, 'It wants at least about 2 samples per symbol because it explicitly watches the midpoint.', 'tiny'))

    mm_positions = [1.0, 2.0]
    mm_colors = ['#f8fafc', '#22c55e']
    mm_labels = ['prev sample', 'current sample']
    for x_t, color, label in zip(mm_positions, mm_colors, mm_labels):
        x = map_x(x_t, panel_left, panel_right, x_min, x_max)
        y = map_y(sample_y(xs, ys, x_t), lower_top + 40, lower_bottom - 40, y_min, y_max)
        svg.append(line(x, lower_top + 40, x, lower_bottom - 40, color, 2.0, '8 8', 0.9))
        svg.append(circle(x, y, 6.0, color))
        svg.append(text(x, lower_top + 255, label, 'tiny', 'middle'))

    for x_t, decision in ((1.0, '+1 decision'), (2.0, '-1 decision')):
        x = map_x(x_t, panel_left, panel_right, x_min, x_max)
        y = lower_bottom - 26
        svg.append(circle(x, y, 5.0, '#f97316'))
        svg.append(text(x, y + 22, decision, 'tiny', 'middle'))

    svg.append(text(900, 555, 'Mueller and Muller cue', 'label'))
    svg.append(text(900, 582, 'Compare adjacent symbol-spaced matched-filter samples after slicing.', 'small'))
    svg.append(text(900, 606, 'It uses pulse symmetry: if timing is right, the neighboring sidelobe contributions balance.', 'tiny'))
    svg.append(text(900, 632, 'Why it helps:', 'small'))
    svg.append(text(900, 654, 'It can work at 1 sample per symbol, so it fits a later decision-directed stage.', 'tiny'))
    svg.append(text(900, 678, 'Tradeoff:', 'small'))
    svg.append(text(900, 700, 'Bad decisions or the wrong pulse shape can poison the timing cue.', 'tiny'))
    svg.append(text(900, 724, 'Rule of thumb:', 'small'))
    svg.append(text(900, 746, 'Gardner reads the midpoint. M&M reads adjacent decided symbols.', 'tiny'))

    svg.append(text(88, 447, 'Gardner is about the zero crossing between symbols.', 'small'))
    svg.append(text(88, 797, 'Mueller and Muller is about balance across neighboring symbol-spaced samples.', 'small'))
    svg.append('</svg>')

    OUT.write_text('\n'.join(svg) + '\n')
    print(f'WROTE {OUT}')


if __name__ == '__main__':
    main()
