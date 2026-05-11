#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO / 'assets/2026-05-11-srrc-rolloff-and-matched-filter.svg'
SPS = 64
SPAN = 8
BETAS = [0.2, 0.5, 0.8]
COLORS = {
    0.2: '#60a5fa',
    0.5: '#f97316',
    0.8: '#22c55e',
}


def srrc(beta: float, t: float) -> float:
    if abs(t) < 1e-12:
        return 1.0 + beta * (4.0 / math.pi - 1.0)

    if beta > 0 and abs(abs(t) - 1.0 / (4.0 * beta)) < 1e-9:
        a = (1.0 + 2.0 / math.pi) * math.sin(math.pi / (4.0 * beta))
        b = (1.0 - 2.0 / math.pi) * math.cos(math.pi / (4.0 * beta))
        return beta / math.sqrt(2.0) * (a + b)

    numerator = math.sin(math.pi * t * (1.0 - beta)) + 4.0 * beta * t * math.cos(math.pi * t * (1.0 + beta))
    denominator = math.pi * t * (1.0 - (4.0 * beta * t) ** 2)
    return numerator / denominator


def discrete_srrc(beta: float, span: int = SPAN, sps: int = SPS) -> tuple[list[float], list[float]]:
    times = [n / sps for n in range(-span * sps // 2, span * sps // 2 + 1)]
    taps = [srrc(beta, t) for t in times]
    energy = math.sqrt(sum(value * value for value in taps))
    taps = [value / energy for value in taps]
    return times, taps


def convolve(a: list[float], b: list[float]) -> list[float]:
    out = [0.0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        for j, bv in enumerate(b):
            out[i + j] += av * bv
    return out


def windowed_pairs(times: list[float], values: list[float], left: float, right: float) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for x, y in zip(times, values):
        if left <= x <= right:
            xs.append(x)
            ys.append(y)
    return xs, ys


def polyline(xs: list[float], ys: list[float], *, left: float, right: float, top: float, bottom: float, stroke: str, width: float = 3.0) -> str:
    ymin = min(ys)
    ymax = max(ys)
    span = ymax - ymin or 1.0

    def map_x(x: float) -> float:
        return left + (x - xs[0]) / (xs[-1] - xs[0]) * (right - left)

    def map_y(y: float) -> float:
        return bottom - (y - ymin) / span * (bottom - top)

    points = ' '.join(f'{map_x(x):.1f},{map_y(y):.1f}' for x, y in zip(xs, ys))
    return f'<polyline points="{points}" fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'


def line(x1: float, y1: float, x2: float, y2: float, klass: str) -> str:
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{klass}"/>'


def text(x: float, y: float, value: str, klass: str, anchor: str = 'start') -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{klass}" text-anchor="{anchor}">{value}</text>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"/>'


def map_linear(value: float, src_left: float, src_right: float, dst_left: float, dst_right: float) -> float:
    return dst_left + (value - src_left) / (src_right - src_left) * (dst_right - dst_left)


def main() -> None:
    top_left, top_right = 80.0, 1120.0
    top_top, top_bottom = 170.0, 390.0
    bot_top, bot_bottom = 500.0, 720.0
    left_bound, right_bound = -4.0, 4.0

    series: dict[float, tuple[list[float], list[float]]] = {}
    for beta in BETAS:
        times, taps = discrete_srrc(beta)
        series[beta] = windowed_pairs(times, taps, left_bound, right_bound)

    ref_times, ref_taps = discrete_srrc(0.35)
    combined = convolve(ref_taps, ref_taps)
    dt = 1.0 / SPS
    combined_times = [2.0 * ref_times[0] + i * dt for i in range(len(combined))]
    match_xs, match_ys = windowed_pairs(combined_times, combined, left_bound, right_bound)

    top_ymin = min(min(ys) for _, ys in series.values())
    top_ymax = max(max(ys) for _, ys in series.values())
    top_span = top_ymax - top_ymin
    bot_ymin = min(match_ys)
    bot_ymax = max(match_ys)
    bot_span = bot_ymax - bot_ymin

    def top_map_y(y: float) -> float:
        return top_bottom - (y - top_ymin) / top_span * (top_bottom - top_top)

    def bot_map_y(y: float) -> float:
        return bot_bottom - (y - bot_ymin) / bot_span * (bot_bottom - bot_top)

    svg: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 780">',
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#081018"/>',
        '    <stop offset="100%" stop-color="#101d2a"/>',
        '  </linearGradient>',
        '  <style>',
        '    .title { font: 700 34px Helvetica, Arial, sans-serif; fill: #e6edf3; }',
        '    .subtitle { font: 500 18px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .panel { fill: #122131; stroke: #5e7fa3; stroke-width: 2; rx: 18; }',
        '    .label { font: 600 18px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .small { font: 500 15px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .axis { stroke: #39516a; stroke-width: 2; }',
        '    .grid { stroke: #223445; stroke-width: 1; opacity: 0.8; }',
        '    .sample { stroke: #94a3b8; stroke-width: 1.5; stroke-dasharray: 5 5; opacity: 0.7; }',
        '  </style>',
        '</defs>',
        '<rect width="1200" height="780" fill="url(#bg)"/>',
        text(60, 60, 'SRRC rolloff and matched-filter response', 'title'),
        text(60, 92, 'Lower beta buys tighter spectrum. Higher beta buys a shorter, more timing-friendly pulse. Matched filtering makes the zero-ISI sampling view visible.', 'subtitle'),
        '<rect x="50" y="130" width="1100" height="280" class="panel"/>',
        '<rect x="50" y="460" width="1100" height="280" class="panel"/>',
        text(80, 160, '1. Time-domain SRRC pulses for three rolloff values', 'label'),
        text(80, 490, '2. Tx pulse convolved with the matched Rx pulse (beta = 0.35)', 'label'),
    ]

    for integer in range(int(left_bound), int(right_bound) + 1):
        x = map_linear(integer, left_bound, right_bound, top_left, top_right)
        svg.append(line(x, top_top, x, top_bottom, 'grid'))
        svg.append(line(x, bot_top, x, bot_bottom, 'grid'))
        if integer < right_bound:
            mid_x = map_linear(integer + 0.5, left_bound, right_bound, top_left, top_right)
            svg.append(line(mid_x, bot_top, mid_x, bot_bottom, 'sample'))
        svg.append(text(x, top_bottom + 24, f'{integer:+d}T', 'small', 'middle'))
        svg.append(text(x, bot_bottom + 24, f'{integer:+d}T', 'small', 'middle'))

    zero_top = top_map_y(0.0)
    zero_bot = bot_map_y(0.0)
    svg.append(line(top_left, zero_top, top_right, zero_top, 'axis'))
    svg.append(line(top_left, top_bottom, top_right, top_bottom, 'axis'))
    svg.append(line(top_left, top_top, top_left, top_bottom, 'axis'))
    svg.append(line(top_left, bot_bottom, top_right, bot_bottom, 'axis'))
    svg.append(line(top_left, bot_top, top_left, bot_bottom, 'axis'))
    svg.append(line(top_left, zero_bot, top_right, zero_bot, 'axis'))

    for beta in BETAS:
        xs, ys = series[beta]
        shifted_points = ' '.join(
            f'{map_linear(x, left_bound, right_bound, top_left, top_right):.1f},{top_map_y(y):.1f}'
            for x, y in zip(xs, ys)
        )
        svg.append(
            f'<polyline points="{shifted_points}" fill="none" stroke="{COLORS[beta]}" stroke-width="3.5" '
            'stroke-linejoin="round" stroke-linecap="round"/>'
        )

    legend_x = 930.0
    legend_y = 190.0
    for index, beta in enumerate(BETAS):
        y = legend_y + index * 28.0
        svg.append(circle(legend_x, y - 5.0, 6.0, COLORS[beta]))
        svg.append(text(legend_x + 18.0, y, f'beta = {beta:.1f}', 'small'))

    svg.append(text(80, 438, 'Small beta rings longer in time. Large beta settles faster but spends more bandwidth.', 'small'))

    match_points = ' '.join(
        f'{map_linear(x, left_bound, right_bound, top_left, top_right):.1f},{bot_map_y(y):.1f}'
        for x, y in zip(match_xs, match_ys)
    )
    svg.append(
        '<polyline points="' + match_points + '" fill="none" stroke="#c084fc" stroke-width="4" '
        'stroke-linejoin="round" stroke-linecap="round"/>'
    )

    for integer in range(-3, 4):
        x = map_linear(integer, left_bound, right_bound, top_left, top_right)
        sample_index = min(range(len(match_xs)), key=lambda idx: abs(match_xs[idx] - integer))
        y = bot_map_y(match_ys[sample_index])
        fill = '#f8fafc' if integer == 0 else '#cbd5e1'
        radius = 6.0 if integer == 0 else 4.5
        svg.append(circle(x, y, radius, fill, 0.95))

    svg.append(text(80, 770, 'Neighboring symbol instants land near zero. The center sample gets the clean decision peak.', 'small'))
    svg.append(text(860, 530, 'matched response', 'small'))
    svg.append(circle(840, 525, 6.0, '#c084fc'))
    svg.append('</svg>')

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text('\n'.join(svg) + '\n')
    print(f'WROTE {OUTPUT}')


if __name__ == '__main__':
    main()
