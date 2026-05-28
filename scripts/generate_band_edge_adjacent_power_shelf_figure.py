#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text
from waveform_carrier_front_ends import (
    BandEdgeSettleShelfRow,
    study_band_edge_adjacent_power_shelf,
    write_band_edge_settle_shelf_csv,
)

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-28-band-edge-adjacent-power-shelf.svg'
PNG_OUT = REPO / 'assets/2026-05-28-band-edge-adjacent-power-shelf.png'
CSV_OUT = REPO / 'assets/2026-05-28-band-edge-adjacent-power-shelf.csv'

WIDTH = 2140
HEIGHT = 1780
SAMPLES_PER_SYMBOL = 4
SYMBOL_COUNT = 3072
ROLLOFF = 0.35
TAP_COUNT = 63
BLOCK_SYMBOLS = 96
TAIL_BLOCK_COUNT = 8
SETTLE_THRESHOLD = 0.05
LOOP_GAIN = 0.020
SPACINGS = [1.20, 1.22, 1.24, 1.26, 1.28, 1.30]
ADJACENT_POWERS_DB = [3.0, 0.0, -3.0, -6.0, -9.0]
LINE_POWERS_DB = [3.0, 0.0, -3.0, -9.0]

POWER_COLORS = {
    3.0: '#f97316',
    0.0: '#facc15',
    -3.0: '#38bdf8',
    -6.0: '#4ade80',
    -9.0: '#c084fc',
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
    return '#f8fafc' if value > (vmin + vmax) / 2.0 else '#e2e8f0'


def gap_color(value: float, vmax: float) -> str:
    return heat(value, (15, 23, 42), (251, 146, 60), 0.0, vmax)


def axis_x(value: float, left: float, width: float, minimum: float, maximum: float) -> float:
    return left + width * ((value - minimum) / (maximum - minimum))


def axis_y(value: float, top: float, height: float, minimum: float, maximum: float) -> float:
    return top + height - height * ((value - minimum) / (maximum - minimum))


def lookup(rows: list[BandEdgeSettleShelfRow]) -> dict[tuple[float, float], BandEdgeSettleShelfRow]:
    return {(round(row.adjacent_relative_power_db, 3), round(row.channel_spacing, 3)): row for row in rows}


def power_label(value: float) -> str:
    return f'+{value:.0f} dB' if value > 0 else f'{value:.0f} dB'


def first_full_settle_spacing(data: dict[tuple[float, float], BandEdgeSettleShelfRow], power: float) -> float | None:
    for spacing in SPACINGS:
        row = data[(round(power, 3), round(spacing, 3))]
        if row.half_sine_tail_within_threshold_fraction >= 0.999:
            return spacing
    return None


def draw_chart_frame(
    svg: list[str],
    *,
    left: float,
    top: float,
    width: float,
    height: float,
    x_ticks: list[float],
    y_ticks: list[float],
    y_min: float,
    y_max: float,
    x_label: str,
    y_label: str,
    y_suffix: str = '',
    y_decimals: int = 0,
) -> None:
    svg.append(line(left, top + height, left + width, top + height, '#5d7fa3', 2.0))
    svg.append(line(left, top, left, top + height, '#5d7fa3', 2.0))
    for value in x_ticks:
        x = axis_x(value, left, width, SPACINGS[0], SPACINGS[-1])
        svg.append(line(x, top + height - 6, x, top + height + 6, '#5d7fa3', 1.4))
        svg.append(text(x, top + height + 26, f'{value:.2f}', 'tiny', 'middle'))
        if value not in (x_ticks[0], x_ticks[-1]):
            svg.append(line(x, top, x, top + height, '#27415a', 1.0, 0.8, '4 8'))
    for value in y_ticks:
        y = axis_y(value, top, height, y_min, y_max)
        svg.append(line(left - 6, y, left + 6, y, '#5d7fa3', 1.4))
        label = f'{value:.{y_decimals}f}{y_suffix}'
        svg.append(text(left - 18, y + 5, label, 'tiny', 'end'))
        if value not in (y_ticks[0], y_ticks[-1]):
            svg.append(line(left, y, left + width, y, '#27415a', 1.0, 0.8, '4 8'))
    svg.append(text(left + width / 2.0, top + height + 58.0, x_label, 'tiny', 'middle'))
    svg.append(text(left, top - 14.0, y_label, 'tiny'))


def write_notebook(rows: list[BandEdgeSettleShelfRow], path: Path) -> None:
    import json

    notebook = {
        'cells': [
            {
                'cell_type': 'markdown',
                'metadata': {},
                'source': [
                    '# Band-edge adjacent-power shelf\n',
                    '\n',
                    'This notebook is the slower companion to `notes/band-edge-adjacent-power-shelf.md`. It holds loop gain fixed at `0.020` and checks whether lowering adjacent power erases the nearby-spacing residual gap or only makes the threshold metric look healthy earlier.\n',
                ],
            },
            {
                'cell_type': 'code',
                'execution_count': None,
                'metadata': {},
                'outputs': [],
                'source': [
                    'from pathlib import Path\n',
                    'import csv\n',
                    '\n',
                    "repo = Path('..').resolve()\n",
                    "csv_path = repo / 'assets' / '2026-05-28-band-edge-adjacent-power-shelf.csv'\n",
                    'with csv_path.open() as handle:\n',
                    '    rows = list(csv.DictReader(handle))\n',
                    '[(row[\'adjacent_relative_power_db\'], row[\'channel_spacing\'], row[\'half_sine_tail_within_threshold_fraction\'], row[\'residual_ratio_half_to_proxy\']) for row in rows[:6]]\n',
                ],
            },
            {
                'cell_type': 'markdown',
                'metadata': {},
                'source': [
                    '## Figure\n',
                    '\n',
                    '![Band-edge adjacent-power shelf](../assets/2026-05-28-band-edge-adjacent-power-shelf.png)\n',
                    '\n',
                    'Read the upper-left heatmap first. Lower adjacent power clears the settle threshold quickly. Then read the ratio heatmap on the right: the ranking survives much longer than the threshold failure.\n',
                ],
            },
            {
                'cell_type': 'code',
                'execution_count': None,
                'metadata': {},
                'outputs': [],
                'source': [
                    'interesting = [row for row in rows if row[\'adjacent_relative_power_db\'] in {\'0.0\', \'-3.0\', \'-9.0\'} and row[\'channel_spacing\'] in {\'1.2\', \'1.24\', \'1.3\'}]\n',
                    '[(row[\'adjacent_relative_power_db\'], row[\'channel_spacing\'], round(float(row[\'absolute_gap_half_minus_proxy\']), 4), round(float(row[\'residual_ratio_half_to_proxy\']), 2)) for row in interesting]\n',
                ],
            },
            {
                'cell_type': 'markdown',
                'metadata': {},
                'source': [
                    '## Practical read\n',
                    '\n',
                    '- `-3 dB` adjacent power is already enough to make the whole `1.20–1.30 R_s` band look fully settled on the threshold metric.\n',
                    '- That does **not** erase the residual ranking: the half-sine lane still carries a much larger mean tail residual than the proxy lane.\n',
                    '- `-9 dB` weakens the gap further, but the ranking still does not flip in this bounded pass.\n',
                ],
            },
        ],
        'metadata': {
            'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
            'language_info': {'name': 'python', 'version': '3.11'},
        },
        'nbformat': 4,
        'nbformat_minor': 5,
    }
    path.write_text(json.dumps(notebook, indent=2) + '\n')


def main() -> None:
    rows = study_band_edge_adjacent_power_shelf(
        SPACINGS,
        ADJACENT_POWERS_DB,
        loop_gain=LOOP_GAIN,
        samples_per_symbol=SAMPLES_PER_SYMBOL,
        symbol_count=SYMBOL_COUNT,
        tap_count=TAP_COUNT,
        rolloff=ROLLOFF,
        block_symbols=BLOCK_SYMBOLS,
        tail_block_count=TAIL_BLOCK_COUNT,
        settle_threshold=SETTLE_THRESHOLD,
    )
    write_band_edge_settle_shelf_csv(rows, CSV_OUT)
    write_notebook(rows, REPO / 'notebooks' / 'band_edge_adjacent_power_shelf.ipynb')
    data = lookup(rows)

    stronger_settle = first_full_settle_spacing(data, 3.0)
    base_settle = first_full_settle_spacing(data, 0.0)
    relief_settle = first_full_settle_spacing(data, -3.0)
    base_120 = data[(0.0, 1.20)]
    base_124 = data[(0.0, 1.24)]
    stronger_124 = data[(3.0, 1.24)]
    relief_120 = data[(-3.0, 1.20)]
    relief_124 = data[(-3.0, 1.24)]
    relief_130 = data[(-3.0, 1.30)]
    weak_124 = data[(-9.0, 1.24)]

    ratio_min = min(row.residual_ratio_half_to_proxy for row in rows)
    ratio_max = max(row.residual_ratio_half_to_proxy for row in rows)
    gap_max = max(row.absolute_gap_half_minus_proxy for row in rows)

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
        text(56, 60, 'Band-edge adjacent-power relief clears the settle shelf before the residual gap', 'title'),
        text(56, 92, 'Hold loop gain fixed at 0.020. Lower adjacent power restores the threshold metric quickly, but the half-sine residual ranking survives much longer.', 'subtitle'),
    ]

    svg.append(rounded_rect(56, 126, 2028, 248, '#102031', '#4f8cc9', 2.0))
    add_wrapped_text(
        svg,
        82,
        162,
        'Same SRRC QPSK setup, same 63-tap band-edge filters, same 96-symbol loop update, same 1.20–1.30 R_s nearby-spacing band. This pass freezes loop gain at 0.020 and moves only adjacent relative power. The question is whether making the adjacent channel weaker turns the settle-shelf return into a real catch-up instead of just a cleaner threshold read.',
        'small',
        max_width=1960,
        font_size=16,
        line_height=22,
    )

    cards = [
        (
            82.0,
            '#341727',
            '#f97316',
            'A stronger adjacent pushes the first full settle point later',
            f'At +3 dB, the half-sine lane is still not fully settled at 1.24 R_s: its tail fraction is only {stronger_124.half_sine_tail_within_threshold_fraction:.3f}, and the first full-settle point moves out to {stronger_settle:.2f} R_s instead of the 0 dB baseline at {base_settle:.2f} R_s.',
        ),
        (
            744.0,
            '#163125',
            '#4ade80',
            'A modest relief already clears the whole threshold shelf',
            f'At -3 dB, every tested spacing from 1.20 through 1.30 R_s is fully settled. The 1.20 R_s cell jumps from {base_120.half_sine_tail_within_threshold_fraction:.3f} at 0 dB to {relief_120.half_sine_tail_within_threshold_fraction:.3f}.',
        ),
        (
            1406.0,
            '#14263a',
            '#93c5fd',
            'But the residual ranking does not vanish with that relief',
            f'At -3 dB, the half-sine / proxy mean-tail residual ratio is still {relief_120.residual_ratio_half_to_proxy:.1f}x at 1.20 R_s, {relief_124.residual_ratio_half_to_proxy:.1f}x at 1.24 R_s, and {relief_130.residual_ratio_half_to_proxy:.1f}x at 1.30 R_s. Even at -9 dB, the 1.24 R_s ratio still sits at {weak_124.residual_ratio_half_to_proxy:.1f}x.',
        ),
    ]
    for left, fill, stroke, title_value, body in cards:
        svg.append(rounded_rect(left, 236, 596, 110, fill, stroke, 1.8, 16.0))
        svg.append(text(left + 18, 264, title_value, 'label'))
        add_wrapped_text(svg, left + 18, 292, body, 'tiny', max_width=560, font_size=14, line_height=18)

    cell_w = 126.0
    cell_h = 58.0

    # settle heatmap
    panel_left = 56.0
    panel_top = 406.0
    panel_width = 980.0
    panel_height = 500.0
    grid_left = panel_left + 140.0
    grid_top = panel_top + 150.0
    svg.append(rounded_rect(panel_left, panel_top, panel_width, panel_height, '#102031', '#4f8cc9', 2.0))
    svg.append(text(panel_left + 24, panel_top + 36, 'Half-sine settle fraction at fixed gain 0.020', 'label'))
    add_wrapped_text(svg, panel_left + 24, panel_top + 68, 'Each cell is the share of the last eight loop blocks inside ±0.05 R_s. Lower adjacent power clears this threshold quickly.', 'small', max_width=912, font_size=17, line_height=22)
    for index, spacing in enumerate(SPACINGS):
        x = grid_left + index * cell_w
        svg.append(text(x + cell_w / 2.0, grid_top - 24, f'{spacing:.2f}', 'tiny', 'middle'))
    svg.append(text(grid_left + (len(SPACINGS) * cell_w) / 2.0, grid_top - 56, 'channel spacing (R_s)', 'tiny', 'middle'))
    for index, power in enumerate(ADJACENT_POWERS_DB):
        y = grid_top + index * cell_h
        svg.append(text(grid_left - 18, y + cell_h / 2.0 + 5.0, power_label(power), 'tiny', 'end'))
        for j, spacing in enumerate(SPACINGS):
            x = grid_left + j * cell_w
            row = data[(round(power, 3), round(spacing, 3))]
            value = row.half_sine_tail_within_threshold_fraction
            svg.append(rounded_rect(x, y, cell_w - 10, cell_h - 8, settle_color(value), None, 0.0, 10.0))
            svg.append(f'<text x="{x + (cell_w - 10) / 2:.1f}" y="{y + cell_h / 2 + 5:.1f}" class="cell" text-anchor="middle" fill="{settle_label(value)}">{value:.3f}</text>')
    svg.append(text(grid_left - 36, grid_top - 56, 'adjacent power', 'tiny', 'end'))
    svg.append(rounded_rect(panel_left + 24, panel_top + 432, 928, 44, '#13263b', '#4f8cc9', 1.2, 10.0))
    svg.append(text(panel_left + 44, panel_top + 460, 'Read:', 'tiny'))
    svg.append(text(panel_left + 92, panel_top + 460, f'the threshold shelf survives 0 dB, shifts later at +3 dB, and is already fully open across the band by {relief_settle:.2f} R_s at -3 dB.', 'tiny'))

    # ratio heatmap
    panel_left = 1104.0
    panel_top = 406.0
    panel_width = 980.0
    panel_height = 500.0
    grid_left = panel_left + 140.0
    grid_top = panel_top + 150.0
    svg.append(rounded_rect(panel_left, panel_top, panel_width, panel_height, '#102031', '#4f8cc9', 2.0))
    svg.append(text(panel_left + 24, panel_top + 36, 'Residual ratio: half-sine / proxy', 'label'))
    add_wrapped_text(svg, panel_left + 24, panel_top + 68, 'This is the mean tail residual CFO ratio. Bigger means the half-sine lane still tracks less cleanly than the proxy lane even after the threshold metric looks healthy.', 'small', max_width=912, font_size=17, line_height=22)
    for index, spacing in enumerate(SPACINGS):
        x = grid_left + index * cell_w
        svg.append(text(x + cell_w / 2.0, grid_top - 24, f'{spacing:.2f}', 'tiny', 'middle'))
    svg.append(text(grid_left + (len(SPACINGS) * cell_w) / 2.0, grid_top - 56, 'channel spacing (R_s)', 'tiny', 'middle'))
    for index, power in enumerate(ADJACENT_POWERS_DB):
        y = grid_top + index * cell_h
        svg.append(text(grid_left - 18, y + cell_h / 2.0 + 5.0, power_label(power), 'tiny', 'end'))
        for j, spacing in enumerate(SPACINGS):
            x = grid_left + j * cell_w
            row = data[(round(power, 3), round(spacing, 3))]
            value = row.residual_ratio_half_to_proxy
            svg.append(rounded_rect(x, y, cell_w - 10, cell_h - 8, ratio_color(value, ratio_min, ratio_max), None, 0.0, 10.0))
            svg.append(f'<text x="{x + (cell_w - 10) / 2:.1f}" y="{y + cell_h / 2 + 5:.1f}" class="cell" text-anchor="middle" fill="{ratio_label(value, ratio_min, ratio_max)}">{value:.1f}x</text>')
    svg.append(text(grid_left - 36, grid_top - 56, 'adjacent power', 'tiny', 'end'))
    svg.append(rounded_rect(panel_left + 24, panel_top + 432, 928, 44, '#13263b', '#4f8cc9', 1.2, 10.0))
    svg.append(text(panel_left + 44, panel_top + 460, 'Read:', 'tiny'))
    svg.append(text(panel_left + 92, panel_top + 460, 'lower adjacent power cools the ratio, but it stays far above 1x across this grid.', 'tiny'))

    # ratio lines
    panel_left = 56.0
    panel_top = 948.0
    panel_width = 980.0
    panel_height = 542.0
    chart_left = panel_left + 96.0
    chart_top = panel_top + 136.0
    chart_width = panel_width - 154.0
    chart_height = 314.0
    svg.append(rounded_rect(panel_left, panel_top, panel_width, panel_height, '#102031', '#4f8cc9', 2.0))
    svg.append(text(panel_left + 24, panel_top + 36, 'Residual ratio versus spacing', 'label'))
    add_wrapped_text(svg, panel_left + 24, panel_top + 68, 'Weaker adjacent power shifts the whole ratio family downward, but the curves still stay far above parity. The settle shelf clears long before the ranking disappears.', 'small', max_width=912, font_size=17, line_height=22)
    draw_chart_frame(
        svg,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        x_ticks=SPACINGS,
        y_ticks=[0, 10, 20, 30, 40, 50, 60, 70],
        y_min=0.0,
        y_max=70.0,
        x_label='channel spacing (R_s)',
        y_label='mean residual ratio',
        y_suffix='x',
        y_decimals=0,
    )
    for power in LINE_POWERS_DB:
        points = [
            (
                axis_x(spacing, chart_left, chart_width, SPACINGS[0], SPACINGS[-1]),
                axis_y(data[(round(power, 3), round(spacing, 3))].residual_ratio_half_to_proxy, chart_top, chart_height, 0.0, 70.0),
            )
            for spacing in SPACINGS
        ]
        svg.append(polyline(points, POWER_COLORS[power], 3.2))
        for x, y in points:
            svg.append(circle(x, y, 4.8, POWER_COLORS[power]))
    svg.append(rounded_rect(panel_left + 24, panel_top + 468, 928, 44, '#13263b', '#4f8cc9', 1.2, 10.0))
    svg.append(text(panel_left + 44, panel_top + 496, 'Read:', 'tiny'))
    svg.append(text(panel_left + 92, panel_top + 496, 'the whole family stays above 1x; weaker adjacent power helps, but it does not turn the nearby band into a residual crossover.', 'tiny'))

    # absolute gap lines
    panel_left = 1104.0
    panel_top = 948.0
    panel_width = 980.0
    panel_height = 542.0
    chart_left = panel_left + 96.0
    chart_top = panel_top + 136.0
    chart_width = panel_width - 154.0
    chart_height = 314.0
    svg.append(rounded_rect(panel_left, panel_top, panel_width, panel_height, '#102031', '#4f8cc9', 2.0))
    svg.append(text(panel_left + 24, panel_top + 36, 'Absolute residual gap versus spacing', 'label'))
    add_wrapped_text(svg, panel_left + 24, panel_top + 68, 'This is the direct mean tail-residual difference (half-sine minus proxy). The gap really does shrink with weaker adjacent power. It just never flips sign in this bounded pass.', 'small', max_width=912, font_size=17, line_height=22)
    draw_chart_frame(
        svg,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        x_ticks=SPACINGS,
        y_ticks=[0.00, 0.02, 0.04, 0.06, 0.08],
        y_min=0.0,
        y_max=0.08,
        x_label='channel spacing (R_s)',
        y_label='absolute mean-gap',
        y_suffix='',
        y_decimals=2,
    )
    for power in LINE_POWERS_DB:
        points = [
            (
                axis_x(spacing, chart_left, chart_width, SPACINGS[0], SPACINGS[-1]),
                axis_y(data[(round(power, 3), round(spacing, 3))].absolute_gap_half_minus_proxy, chart_top, chart_height, 0.0, 0.08),
            )
            for spacing in SPACINGS
        ]
        svg.append(polyline(points, POWER_COLORS[power], 3.2))
        for x, y in points:
            svg.append(circle(x, y, 4.8, POWER_COLORS[power]))
    svg.append(rounded_rect(panel_left + 24, panel_top + 468, 928, 44, '#13263b', '#4f8cc9', 1.2, 10.0))
    svg.append(text(panel_left + 44, panel_top + 496, 'Read:', 'tiny'))
    svg.append(text(panel_left + 92, panel_top + 496, 'adjacent-power relief is real; the absolute gap cools a lot, but it never flips sign here.', 'tiny'))

    # legend
    legend_left = 1404.0
    legend_top = 1512.0
    svg.append(rounded_rect(legend_left, legend_top, 612.0, 82.0, '#13263b', '#4f8cc9', 1.4, 12.0))
    for idx, power in enumerate(LINE_POWERS_DB):
        x = legend_left + 28.0 + idx * 146.0
        y = legend_top + 34.0
        svg.append(line(x, y, x + 52.0, y, POWER_COLORS[power], 3.0))
        svg.append(circle(x + 26.0, y, 4.8, POWER_COLORS[power]))
        svg.append(text(x + 64.0, y + 5.0, power_label(power), 'tiny'))

    svg.append(text(56.0, 1718.0, f'Bounded pass: gain = {LOOP_GAIN:.3f}, settle threshold = ±{SETTLE_THRESHOLD:.2f} R_s, tail = last {TAIL_BLOCK_COUNT} loop blocks, adjacent power sweep = +3 to -9 dB.', 'tiny'))
    svg.append('</svg>')

    SVG_OUT.write_text('\n'.join(svg))
    export_png_from_svg(SVG_OUT, PNG_OUT, size=2200)


if __name__ == '__main__':
    main()
