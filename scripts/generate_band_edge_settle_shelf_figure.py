#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text
from waveform_carrier_front_ends import BandEdgeSettleShelfRow, study_band_edge_settle_shelf, write_band_edge_settle_shelf_csv

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-27-band-edge-settle-shelf.svg'
PNG_OUT = REPO / 'assets/2026-05-27-band-edge-settle-shelf.png'
CSV_OUT = REPO / 'assets/2026-05-27-band-edge-settle-shelf.csv'

WIDTH = 2140
HEIGHT = 1700
SAMPLES_PER_SYMBOL = 4
SYMBOL_COUNT = 3072
ROLLOFF = 0.35
TAP_COUNT = 63
BLOCK_SYMBOLS = 96
TAIL_BLOCK_COUNT = 8
SETTLE_THRESHOLD = 0.05
ADJACENT_POWER_DB = 0.0
SPACINGS = [1.20, 1.22, 1.24, 1.26, 1.28, 1.30]
LOOP_GAINS = [0.002, 0.006, 0.010, 0.014, 0.018, 0.020, 0.022]
SHOW_GAINS = [0.002, 0.010, 0.020]

GAIN_COLORS = {
    0.002: '#4ade80',
    0.010: '#93c5fd',
    0.020: '#fda4af',
}


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round"{dash_attr}/>'


def rounded_rect(x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None, stroke_width: float = 0.0, rx: float = 18.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}"{stroke_attr}/>'


def circle(x: float, y: float, r: float, fill: str) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"/>'


def polyline(points: list[tuple[float, float]], stroke: str, width: float = 3.0) -> str:
    coords = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def heat(value: float, low: tuple[int, int, int], high: tuple[int, int, int], vmin: float, vmax: float) -> str:
    if vmax <= vmin:
        t = 0.0
    else:
        t = max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))
    rgb = tuple(round(lerp(a, b, t)) for a, b in zip(low, high))
    return '#%02x%02x%02x' % rgb


def settle_color(value: float) -> str:
    if value >= 0.999:
        return '#16a34a'
    return heat(value, (127, 29, 29), (245, 158, 11), 0.0, 1.0)


def settle_label(value: float) -> str:
    return '#ecfeff' if value < 0.8 else '#f8fafc'


def ratio_color(value: float, vmin: float, vmax: float) -> str:
    return heat(value, (30, 41, 59), (236, 72, 153), vmin, vmax)


def ratio_label(value: float, vmin: float, vmax: float) -> str:
    midpoint = (vmin + vmax) / 2.0
    return '#f8fafc' if value > midpoint else '#e2e8f0'


def axis_x(value: float, left: float, width: float, minimum: float, maximum: float) -> float:
    return left + width * ((value - minimum) / (maximum - minimum))


def axis_y(value: float, top: float, height: float, minimum: float, maximum: float) -> float:
    return top + height - height * ((value - minimum) / (maximum - minimum))


def lookup(rows: list[BandEdgeSettleShelfRow]) -> dict[tuple[float, float], BandEdgeSettleShelfRow]:
    return {(round(row.channel_spacing, 3), round(row.loop_gain, 3)): row for row in rows}


def main() -> None:
    rows = study_band_edge_settle_shelf(
        SPACINGS,
        LOOP_GAINS,
        adjacent_relative_power_db=ADJACENT_POWER_DB,
        samples_per_symbol=SAMPLES_PER_SYMBOL,
        symbol_count=SYMBOL_COUNT,
        tap_count=TAP_COUNT,
        rolloff=ROLLOFF,
        block_symbols=BLOCK_SYMBOLS,
        tail_block_count=TAIL_BLOCK_COUNT,
        settle_threshold=SETTLE_THRESHOLD,
    )
    write_band_edge_settle_shelf_csv(rows, CSV_OUT)
    data = lookup(rows)

    base_rows = [data[(round(spacing, 3), 0.020)] for spacing in SPACINGS]
    low_rows = [data[(round(spacing, 3), 0.002)] for spacing in SPACINGS]
    first_full_settle = next(row.channel_spacing for row in base_rows if row.half_sine_tail_within_threshold_fraction >= 0.999)
    low_gain_all_settle = all(row.half_sine_tail_within_threshold_fraction >= 0.999 for row in low_rows)
    ratio_min = min(row.residual_ratio_half_to_proxy for row in rows)
    ratio_max = max(row.residual_ratio_half_to_proxy for row in rows)

    svg: list[str] = [
        svg_root(WIDTH, HEIGHT),
        '<style>',
        'svg { background: #07111f; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }',
        '.title { fill: #e2e8f0; font-size: 34px; font-weight: 700; }',
        '.subtitle { fill: #94a3b8; font-size: 18px; }',
        '.label { fill: #e2e8f0; font-size: 22px; font-weight: 600; }',
        '.small { fill: #cbd5e1; font-size: 17px; }',
        '.tiny { fill: #cbd5e1; font-size: 15px; }',
        '.cell { font-size: 14px; font-weight: 600; }',
        '</style>',
        text(56, 60, 'Band-edge settle shelf: track-ready returns before the residual gap closes', 'title'),
        text(56, 92, 'A spacing-by-gain audit around 1.20–1.30 R_s. The half-sine lane can re-enter the settle band while the residual ratio keeps widening.', 'subtitle'),
    ]

    svg.append(rounded_rect(56, 126, 2028, 244, '#102031', '#4f8cc9', 2.0))
    add_wrapped_text(
        svg,
        82,
        162,
        'Same SRRC QPSK setup, same 63-tap band-edge filters, same 96-symbol loop update, same 0 dB adjacent interferer. Only spacing and loop gain move. The question is whether “track-ready again” already means competitive again, or only opens a longer settle shelf where the half-sine lane is calmer but still far behind.',
        'small',
        max_width=1960,
        font_size=16,
        line_height=22,
    )

    cards = [
        (
            82.0,
            '#163125',
            '#4ade80',
            'Low gain reopens the whole nearby band',
            f'At gain 0.002, every tested spacing from 1.20 to 1.30 R_s keeps the half-sine tail at 100% inside ±{SETTLE_THRESHOLD:.2f} R_s.' if low_gain_all_settle else 'The low-gain sweep did not fully reopen the nearby band.',
        ),
        (
            744.0,
            '#14263a',
            '#93c5fd',
            'Baseline full-settle returns near 1.24 R_s',
            f'At gain 0.020, the first tested spacing with a full half-sine settle band is {first_full_settle:.2f} R_s. The proxy lane stays at 100% for every tested spacing and gain.',
        ),
        (
            1406.0,
            '#341727',
            '#fda4af',
            'But the residual gulf widens inside that same shelf',
            f'At gain 0.020, the half-sine / proxy mean-residual ratio climbs from {base_rows[0].residual_ratio_half_to_proxy:.1f}x at 1.20 R_s to {base_rows[2].residual_ratio_half_to_proxy:.1f}x at 1.24 R_s and {base_rows[-1].residual_ratio_half_to_proxy:.1f}x at 1.30 R_s.',
        ),
    ]
    for left, fill, stroke, title_value, body in cards:
        svg.append(rounded_rect(left, 236, 596, 108, fill, stroke, 1.8, 16.0))
        svg.append(text(left + 18, 264, title_value, 'label'))
        add_wrapped_text(svg, left + 18, 292, body, 'tiny', max_width=560, font_size=14, line_height=18)

    # settle heatmap
    panel_left = 56.0
    panel_top = 406.0
    panel_width = 980.0
    panel_height = 568.0
    cell_w = 110.0
    cell_h = 52.0
    grid_left = panel_left + 128.0
    grid_top = panel_top + 164.0
    svg.append(rounded_rect(panel_left, panel_top, panel_width, panel_height, '#102031', '#4f8cc9', 2.0))
    svg.append(text(panel_left + 24, panel_top + 36, 'Half-sine settle fraction', 'label'))
    add_wrapped_text(svg, panel_left + 24, panel_top + 68, 'Each cell shows how much of the last eight loop blocks stay inside ±0.05 R_s. This is the “track-ready again” metric, not the residual ranking.', 'small', max_width=912, font_size=17, line_height=22)
    for index, spacing in enumerate(SPACINGS):
        x = grid_left + index * cell_w
        svg.append(text(x + cell_w / 2.0, grid_top - 24, f'{spacing:.2f}', 'tiny', 'middle'))
    svg.append(text(grid_left + (len(SPACINGS) * cell_w) / 2.0, grid_top - 56, 'channel spacing (R_s)', 'tiny', 'middle'))
    for index, gain in enumerate(LOOP_GAINS):
        y = grid_top + index * cell_h
        svg.append(text(grid_left - 18, y + cell_h / 2.0 + 5, f'{gain:.3f}', 'tiny', 'end'))
        for j, spacing in enumerate(SPACINGS):
            x = grid_left + j * cell_w
            row = data[(round(spacing, 3), round(gain, 3))]
            value = row.half_sine_tail_within_threshold_fraction
            svg.append(rounded_rect(x, y, cell_w - 8, cell_h - 8, settle_color(value), None, 0.0, 10.0))
            svg.append(f'<text x="{x + (cell_w - 8) / 2:.1f}" y="{y + cell_h / 2 + 5:.1f}" class="cell" text-anchor="middle" fill="{settle_label(value)}">{value:.3f}</text>')
    svg.append(text(grid_left - 34, grid_top - 56, 'loop gain', 'tiny', 'end'))
    svg.append(rounded_rect(panel_left + 24, panel_top + 498, 928, 44, '#13263b', '#4f8cc9', 1.2, 10.0))
    svg.append(text(panel_left + 44, panel_top + 526, 'Read:', 'tiny'))
    svg.append(text(panel_left + 92, panel_top + 526, 'the settle shelf opens near 1.24 R_s at the default gain, but lower gain pushes full-settle behavior back toward 1.20 R_s.', 'tiny'))

    # ratio heatmap
    panel_left = 1104.0
    panel_top = 406.0
    panel_width = 980.0
    panel_height = 568.0
    grid_left = panel_left + 128.0
    grid_top = panel_top + 164.0
    svg.append(rounded_rect(panel_left, panel_top, panel_width, panel_height, '#102031', '#4f8cc9', 2.0))
    svg.append(text(panel_left + 24, panel_top + 36, 'Residual ratio: half-sine / proxy', 'label'))
    add_wrapped_text(svg, panel_left + 24, panel_top + 68, 'This is the mean tail residual CFO ratio. Bigger means the half-sine lane is still farther from calm lock than the proxy lane, even when both are already inside the settle band.', 'small', max_width=912, font_size=17, line_height=22)
    for index, spacing in enumerate(SPACINGS):
        x = grid_left + index * cell_w
        svg.append(text(x + cell_w / 2.0, grid_top - 24, f'{spacing:.2f}', 'tiny', 'middle'))
    svg.append(text(grid_left + (len(SPACINGS) * cell_w) / 2.0, grid_top - 56, 'channel spacing (R_s)', 'tiny', 'middle'))
    for index, gain in enumerate(LOOP_GAINS):
        y = grid_top + index * cell_h
        svg.append(text(grid_left - 18, y + cell_h / 2.0 + 5, f'{gain:.3f}', 'tiny', 'end'))
        for j, spacing in enumerate(SPACINGS):
            x = grid_left + j * cell_w
            row = data[(round(spacing, 3), round(gain, 3))]
            value = row.residual_ratio_half_to_proxy
            svg.append(rounded_rect(x, y, cell_w - 8, cell_h - 8, ratio_color(value, ratio_min, ratio_max), None, 0.0, 10.0))
            svg.append(f'<text x="{x + (cell_w - 8) / 2:.1f}" y="{y + cell_h / 2 + 5:.1f}" class="cell" text-anchor="middle" fill="{ratio_label(value, ratio_min, ratio_max)}">{value:.1f}x</text>')
    svg.append(text(grid_left - 34, grid_top - 56, 'loop gain', 'tiny', 'end'))
    svg.append(rounded_rect(panel_left + 24, panel_top + 498, 928, 44, '#13263b', '#4f8cc9', 1.2, 10.0))
    svg.append(text(panel_left + 44, panel_top + 526, 'Read:', 'tiny'))
    svg.append(text(panel_left + 92, panel_top + 526, 'inside 1.24–1.30 R_s the ratio keeps rising, so track-ready again is not the same thing as catching up.', 'tiny'))

    # line plot
    panel_left = 56.0
    panel_top = 1022.0
    panel_width = 2028.0
    panel_height = 542.0
    chart_left = panel_left + 104.0
    chart_top = panel_top + 144.0
    chart_width = panel_width - 180.0
    chart_height = 320.0
    svg.append(rounded_rect(panel_left, panel_top, panel_width, panel_height, '#102031', '#4f8cc9', 2.0))
    svg.append(text(panel_left + 24, panel_top + 36, 'Residual ratio versus spacing for three gains', 'label'))
    add_wrapped_text(svg, panel_left + 24, panel_top + 68, 'All three gain curves rise across the nearby spacing band. Lower gain rescues settle fraction earlier, but it does not bend the residual-ratio story back toward parity.', 'small', max_width=1960, font_size=16, line_height=21)
    # axes
    svg.append(line(chart_left, chart_top + chart_height, chart_left + chart_width, chart_top + chart_height, '#5d7fa3', 2.0))
    svg.append(line(chart_left, chart_top, chart_left, chart_top + chart_height, '#5d7fa3', 2.0))
    for spacing in SPACINGS:
        x = axis_x(spacing, chart_left, chart_width, SPACINGS[0], SPACINGS[-1])
        svg.append(line(x, chart_top + chart_height - 6, x, chart_top + chart_height + 6, '#5d7fa3', 1.4))
        svg.append(text(x, chart_top + chart_height + 26, f'{spacing:.2f}', 'tiny', 'middle'))
    for value in [0, 10, 20, 30, 40, 50, 60]:
        y = axis_y(value, chart_top, chart_height, 0, 60)
        svg.append(line(chart_left - 6, y, chart_left + 6, y, '#5d7fa3', 1.4))
        svg.append(text(chart_left - 18, y + 5, f'{value:.0f}x', 'tiny', 'end'))
        if value not in (0, 250):
            svg.append(line(chart_left, y, chart_left + chart_width, y, '#27415a', 1.0, 0.9, '4 8'))
    svg.append(text(chart_left + chart_width / 2.0, chart_top + chart_height + 58, 'channel spacing (R_s)', 'tiny', 'middle'))
    svg.append(text(chart_left, chart_top - 14, 'mean residual ratio', 'tiny'))

    for gain in SHOW_GAINS:
        pts = []
        for spacing in SPACINGS:
            row = data[(round(spacing, 3), round(gain, 3))]
            pts.append((axis_x(spacing, chart_left, chart_width, SPACINGS[0], SPACINGS[-1]), axis_y(row.residual_ratio_half_to_proxy, chart_top, chart_height, 0, 60)))
        svg.append(polyline(pts, GAIN_COLORS[gain], 3.4))
        for x, y in pts:
            svg.append(circle(x, y, 5.0, GAIN_COLORS[gain]))

    # legend and bottom notes
    legend_left = panel_left + 1510.0
    legend_top = panel_top + 84.0
    svg.append(rounded_rect(legend_left, legend_top, 444, 120, '#13263b', '#4f8cc9', 1.4, 12.0))
    svg.append(text(legend_left + 20, legend_top + 28, 'gain slices', 'label'))
    y = legend_top + 58.0
    for gain in SHOW_GAINS:
        svg.append(line(legend_left + 22, y, legend_left + 80, y, GAIN_COLORS[gain], 3.0))
        svg.append(circle(legend_left + 51, y, 4.6, GAIN_COLORS[gain]))
        svg.append(text(legend_left + 96, y + 4, f'loop gain {gain:.3f}', 'tiny'))
        y += 26.0

    note_left = panel_left + 24.0
    note_top = panel_top + 470.0
    svg.append(rounded_rect(note_left, note_top, 1980, 64, '#13263b', '#4f8cc9', 1.2, 12.0))
    add_wrapped_text(svg, note_left + 18, note_top + 28, 'Sharper sentence: the first settle point opens a shelf, not a crossover ramp. Lower gain makes the half-sine lane track-ready earlier, but inside 1.20–1.30 R_s the proxy lane cools faster, so the residual gap widens before the much later crossover from the previous spacing note.', 'tiny', max_width=1940, font_size=14, line_height=18)

    svg.append('</svg>')
    SVG_OUT.write_text('\n'.join(svg) + '\n')
    export_png_from_svg(SVG_OUT, PNG_OUT, size=2100, dpi=300)


if __name__ == '__main__':
    main()
