#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text
from waveform_carrier_front_ends import BandEdgeSlopeRow, sweep_band_edge_slopes, write_band_edge_slope_csv

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-20-band-edge-discriminant-slope-check.svg'
PNG_OUT = REPO / 'assets/2026-05-20-band-edge-discriminant-slope-check.png'
CSV_OUT = REPO / 'assets/2026-05-20-band-edge-discriminant-slope-check.csv'

WIDTH = 1980
HEIGHT = 1700
SAMPLES_PER_SYMBOL = 4
SYMBOL_COUNT = 1024
SEED = 19
TRIM = 160
ROLLOFFS = [0.05, 0.20, 0.35, 0.50]
TAP_COUNTS = [63, 127, 255]
COLORS = {
    63: '#fda4af',
    127: '#93c5fd',
    255: '#4ade80',
}


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round"{dash_attr}/>'


def rounded_rect(x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None, stroke_width: float = 0.0, opacity: float = 1.0, rx: float = 18.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"/>'


def polyline(points: list[tuple[float, float]], stroke: str, width: float = 3.0, opacity: float = 1.0) -> str:
    coords = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round" stroke-linejoin="round"/>'


def axis_x(value: float, left: float, width: float, minimum: float, maximum: float) -> float:
    return left + width * ((value - minimum) / (maximum - minimum))


def axis_y(value: float, top: float, height: float, minimum: float, maximum: float) -> float:
    return top + height - height * ((value - minimum) / (maximum - minimum))


def grouped_rows(rows: list[BandEdgeSlopeRow]) -> dict[int, list[BandEdgeSlopeRow]]:
    grouped: dict[int, list[BandEdgeSlopeRow]] = defaultdict(list)
    for row in rows:
        grouped[row.tap_count].append(row)
    return {tap_count: sorted(series, key=lambda row: row.rolloff) for tap_count, series in grouped.items()}


def row_lookup(rows: list[BandEdgeSlopeRow]) -> dict[tuple[int, float], BandEdgeSlopeRow]:
    return {(row.tap_count, row.rolloff): row for row in rows}


def top_panel(svg: list[str], rows: list[BandEdgeSlopeRow]) -> None:
    left = 60.0
    top = 150.0
    width = 1780.0
    height = 286.0
    lookup = row_lookup(rows)
    slope_low = lookup[(255, 0.20)].central_slope_wrt_deltaf_over_Rs
    slope_high = lookup[(255, 0.50)].central_slope_wrt_deltaf_over_Rs
    imbalance_low = lookup[(255, 0.05)].imbalance_at_0p10
    imbalance_high = lookup[(255, 0.50)].imbalance_at_0p10

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 26.0, top + 40.0, 'One fix to the previous band-edge panel: raw imbalance is not the same thing as calibrated near-lock gain', 'label'))
    add_wrapped_text(
        svg,
        left + 26.0,
        top + 74.0,
        'The first sidecar got the branch choice right: band-edge logic really does need excess bandwidth. This follow-up checks the narrower question that was still open — whether the height of the raw edge-energy panel should also be read as the actual FLL discriminant gain.',
        'small',
        max_width=1716.0,
        font_size=16.0,
        line_height=21.0,
    )

    cards = [
        (
            left + 28.0,
            '#3a1018',
            '#fda4af',
            'Raw panel still useful',
            f'At Δf / R_s = 0.10 and 255 taps, the bounded edge-energy imbalance grows from {imbalance_low:.3f} at α = 0.05 to {imbalance_high:.3f} at α = 0.50.',
        ),
        (
            left + 610.0,
            '#11263d',
            '#93c5fd',
            'But the slope story is tighter',
            f'With the same 255-tap filters, the near-zero slope only moves from {slope_low:.3f} at α = 0.20 to {slope_high:.3f} at α = 0.50. That is much less alpha-sensitive than the raw imbalance height.',
        ),
        (
            left + 1140.0,
            '#142f23',
            '#4ade80',
            'Low roll-off gets hit twice',
            'At α = 0.05 the slope stays soft even with longer filters. That looks like both a waveform problem — little excess bandwidth — and a filter-design problem, not just a vague lack-of-energy slogan.',
        ),
    ]
    for card_left, fill, stroke, title_text, body in cards:
        svg.append(rounded_rect(card_left, top + 128.0, 520.0, 124.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(card_left + 18.0, top + 158.0, title_text, 'label'))
        add_wrapped_text(svg, card_left + 18.0, top + 188.0, body, 'tiny', max_width=430.0, font_size=14.0, line_height=18.0)


def draw_chart_frame(svg: list[str], *, left: float, top: float, width: float, height: float, x_min: float, x_max: float, y_min: float, y_max: float, x_ticks: list[float], y_ticks: list[float], x_label: str, y_label: str, zero_y: float | None = None, target_y: float | None = None, target_label: str | None = None) -> None:
    svg.append(line(left, top + height, left + width, top + height, '#5d7fa3', 2.2))
    svg.append(line(left, top, left, top + height, '#5d7fa3', 2.2))
    for value in x_ticks:
        x = axis_x(value, left, width, x_min, x_max)
        svg.append(line(x, top + height - 6.0, x, top + height + 6.0, '#5d7fa3', 1.4))
        svg.append(text(x, top + height + 26.0, f'{value:.2f}', 'tiny', 'middle'))
        if value not in (x_ticks[0], x_ticks[-1]):
            svg.append(line(x, top, x, top + height, '#27415a', 1.0, 0.8, '4 8'))
    for value in y_ticks:
        y = axis_y(value, top, height, y_min, y_max)
        svg.append(line(left - 6.0, y, left + 6.0, y, '#5d7fa3', 1.4))
        label = f'{value:.2f}' if abs(value) < 10 else f'{value:.0f}'
        svg.append(text(left - 18.0, y + 4.0, label, 'tiny', 'end'))
        if value not in (y_ticks[0], y_ticks[-1]):
            svg.append(line(left, y, left + width, y, '#27415a', 1.0, 0.8, '4 8'))
    if zero_y is not None:
        y = axis_y(zero_y, top, height, y_min, y_max)
        svg.append(line(left, y, left + width, y, '#dce7f3', 1.8, 0.9, '8 8'))
    if target_y is not None:
        y = axis_y(target_y, top, height, y_min, y_max)
        svg.append(line(left, y, left + width, y, '#facc15', 2.0, 0.85, '8 8'))
        if target_label:
            svg.append(text(left + width - 10.0, y - 10.0, target_label, 'tiny', 'end'))
    svg.append(text(left + width / 2.0, top + height + 58.0, x_label, 'tiny', 'middle'))
    svg.append(text(left - 74.0, top + height / 2.0, y_label, 'tiny', 'middle'))


def raw_imbalance_panel(svg: list[str], rows: list[BandEdgeSlopeRow]) -> None:
    left = 60.0
    top = 480.0
    width = 870.0
    height = 650.0
    chart_left = left + 96.0
    chart_top = top + 126.0
    chart_width = 694.0
    chart_height = 388.0
    grouped = grouped_rows(rows)
    lookup = row_lookup(rows)

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, '1. The raw edge-energy cue still rises hard with roll-off', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 70.0,
        'This is the same bounded imbalance used in the earlier sidecar: upper edge energy minus lower edge energy, divided by total signal energy. It is a good intuition panel for whether excess bandwidth leaves a visible clue at all.',
        'small',
        max_width=810.0,
        font_size=15.0,
        line_height=20.0,
    )

    draw_chart_frame(
        svg,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        x_min=0.05,
        x_max=0.50,
        y_min=0.0,
        y_max=0.10,
        x_ticks=ROLLOFFS,
        y_ticks=[0.00, 0.02, 0.04, 0.06, 0.08, 0.10],
        x_label='SRRC roll-off  α',
        y_label='raw imbalance',
        zero_y=0.0,
    )

    for tap_count, series in grouped.items():
        points = [
            (axis_x(row.rolloff, chart_left, chart_width, 0.05, 0.50), axis_y(row.imbalance_at_0p10, chart_top, chart_height, 0.0, 0.10))
            for row in series
        ]
        svg.append(polyline(points, COLORS[tap_count], 3.0))
        for x, y in points:
            svg.append(circle(x, y, 5.0, COLORS[tap_count]))

    legend_left = left + 536.0
    legend_top = top + 544.0
    svg.append(rounded_rect(legend_left, legend_top, 294.0, 74.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0))
    for idx, tap_count in enumerate(TAP_COUNTS):
        y = legend_top + 24.0 + idx * 16.0
        svg.append(circle(legend_left + 18.0, y - 4.0, 5.0, COLORS[tap_count]))
        svg.append(text(legend_left + 32.0, y, f'{tap_count}-tap edge filters', 'tiny'))

    ratio = lookup[(255, 0.50)].imbalance_at_0p10 / max(lookup[(255, 0.05)].imbalance_at_0p10, 1.0e-9)
    card = rounded_rect(left + 24.0, top + 544.0, 472.0, 74.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0)
    svg.append(card)
    add_wrapped_text(
        svg,
        left + 44.0,
        top + 574.0,
        f'At 255 taps, α = 0.50 shows about {ratio:.1f}× the raw imbalance of α = 0.05. That is exactly why the earlier intuition panel still belongs in the repo.',
        'tiny',
        max_width=430.0,
        font_size=13.5,
        line_height=17.0,
    )


def slope_panel(svg: list[str], rows: list[BandEdgeSlopeRow]) -> None:
    left = 930.0
    top = 480.0
    width = 860.0
    height = 650.0
    chart_left = left + 96.0
    chart_top = top + 126.0
    chart_width = 650.0
    chart_height = 388.0
    grouped = grouped_rows(rows)
    lookup = row_lookup(rows)

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, '2. Near lock, the normalized slope tells a tighter story', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 70.0,
        'This panel switches to a central finite difference around zero CFO. The y-value is d(error) / d(Δf / R_s), so an idealized normalized slope of about 1 becomes the practical reference line instead of the raw imbalance height.',
        'small',
        max_width=810.0,
        font_size=15.0,
        line_height=20.0,
    )

    draw_chart_frame(
        svg,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        x_min=0.05,
        x_max=0.50,
        y_min=0.0,
        y_max=1.10,
        x_ticks=ROLLOFFS,
        y_ticks=[0.00, 0.20, 0.40, 0.60, 0.80, 1.00],
        x_label='SRRC roll-off  α',
        y_label='near-lock slope',
        zero_y=0.0,
        target_y=1.0,
        target_label='slope ≈ 1',
    )

    for tap_count, series in grouped.items():
        points = [
            (
                axis_x(row.rolloff, chart_left, chart_width, 0.05, 0.50),
                axis_y(row.central_slope_wrt_deltaf_over_Rs, chart_top, chart_height, 0.0, 1.10),
            )
            for row in series
        ]
        svg.append(polyline(points, COLORS[tap_count], 3.0))
        for x, y in points:
            svg.append(circle(x, y, 5.0, COLORS[tap_count]))

    card = rounded_rect(left + 24.0, top + 544.0, 520.0, 74.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0)
    svg.append(card)
    add_wrapped_text(
        svg,
        left + 44.0,
        top + 574.0,
        f'At 255 taps the slopes are {lookup[(255, 0.20)].central_slope_wrt_deltaf_over_Rs:.3f}, {lookup[(255, 0.35)].central_slope_wrt_deltaf_over_Rs:.3f}, and {lookup[(255, 0.50)].central_slope_wrt_deltaf_over_Rs:.3f} for α = 0.20, 0.35, and 0.50. That is much flatter than the raw imbalance panel.',
        'tiny',
        max_width=478.0,
        font_size=13.5,
        line_height=17.0,
    )

    card2 = rounded_rect(left + 540.0, top + 544.0, 290.0, 74.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0)
    svg.append(card2)
    add_wrapped_text(
        svg,
        left + 560.0,
        top + 574.0,
        f'α = 0.05 only climbs to {lookup[(255, 0.05)].central_slope_wrt_deltaf_over_Rs:.3f}, which is why the tiny-roll-off case still looks genuinely fragile.',
        'tiny',
        max_width=210.0,
        font_size=13.5,
        line_height=17.0,
    )


def bottom_panel(svg: list[str]) -> None:
    left = 60.0
    top = 1170.0
    width = 1780.0
    height = 470.0
    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, '3. The honest read: keep the old intuition panel, but stop treating it like a loop-gain calibration plot', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 70.0,
        'This follow-up does not retract the earlier waveform-domain comparison. It just makes the calibration claim precise enough to trust. The raw panel still answers whether excess bandwidth leaves a usable clue. The slope panel answers how close the near-lock discriminator is to its normalized target once the filters are long enough.',
        'small',
        max_width=1680.0,
        font_size=15.0,
        line_height=20.0,
    )

    columns = [
        (
            left + 28.0,
            '#14263a',
            '#93c5fd',
            'Keep',
            [
                'Band-edge logic belongs in the excess-bandwidth branch, not in the PSK-symmetry branch.',
                'A raw imbalance panel is still the clearest first intuition for that difference.',
            ],
        ),
        (
            left + 616.0,
            '#173126',
            '#4ade80',
            'Fix',
            [
                'Rename that panel as raw imbalance so readers do not mistake it for calibrated gain.',
                'Use the near-zero finite-difference slope when the question is loop sensitivity, not just visual clue strength.',
            ],
        ),
        (
            left + 1204.0,
            '#341c12',
            '#facc15',
            'Next bounded move',
            [
                'Swap in a band-edge design closer to the GNU Radio / fred harris construction and compare the slope again.',
                'Keep the same 4 sps setup so the repo stays about one clean distinction instead of sprawling into a modem survey.',
            ],
        ),
    ]
    for column_left, fill, stroke, title_text, bullets in columns:
        svg.append(rounded_rect(column_left, top + 126.0, 548.0, 206.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(column_left + 18.0, top + 158.0, title_text, 'label'))
        for idx, bullet in enumerate(bullets):
            y = top + 198.0 + idx * 72.0
            svg.append(circle(column_left + 20.0, y - 4.0, 4.5, stroke))
            add_wrapped_text(svg, column_left + 36.0, y, bullet, 'tiny', max_width=402.0, font_size=14.0, line_height=18.0)

    footer = rounded_rect(left + 24.0, top + 362.0, 1732.0, 78.0, '#13263b', '#4f8cc9', 1.6, 1.0, 14.0)
    svg.append(footer)
    add_wrapped_text(
        svg,
        left + 46.0,
        top + 392.0,
        'Bottom line: the old sidecar got the branch choice right, but this one closes the loophole. Raw band-edge imbalance gets much bigger with roll-off; the normalized near-lock slope gets far less alpha-sensitive once the filters are long enough. Those are related facts, not the same fact.',
        'small',
        max_width=1610.0,
        font_size=15.0,
        line_height=19.0,
    )


def build_svg(rows: list[BandEdgeSlopeRow]) -> str:
    svg: list[str] = [
        svg_root(WIDTH, HEIGHT),
        '<defs><style>'
        '.title { fill: #e6eef8; font: 700 38px Arial, sans-serif; }'
        '.subtitle { fill: #c8d8ea; font: 400 20px Arial, sans-serif; }'
        '.label { fill: #eef4fb; font: 700 24px Arial, sans-serif; }'
        '.small { fill: #d4e1ef; font: 400 17px Arial, sans-serif; }'
        '.tiny { fill: #d8e4f0; font: 400 14px Arial, sans-serif; }'
        '</style></defs>',
        '<rect width="100%" height="100%" fill="#08111c"/>',
        text(60.0, 72.0, 'Band-edge discriminant slope check', 'title'),
        text(60.0, 108.0, 'Raw edge-energy panels still matter, but near-lock slope is the honest quantity when the question is normalized loop gain.', 'subtitle'),
    ]
    top_panel(svg, rows)
    raw_imbalance_panel(svg, rows)
    slope_panel(svg, rows)
    bottom_panel(svg)
    svg.append('</svg>')
    return '\n'.join(svg) + '\n'


def main() -> None:
    rows = sweep_band_edge_slopes(
        ROLLOFFS,
        TAP_COUNTS,
        samples_per_symbol=SAMPLES_PER_SYMBOL,
        symbol_count=SYMBOL_COUNT,
        seed=SEED,
        trim=TRIM,
        normalized_cfo_step=0.01,
        reference_cfo=0.10,
    )
    write_band_edge_slope_csv(rows, CSV_OUT)
    SVG_OUT.write_text(build_svg(rows))
    export_png_from_svg(SVG_OUT, PNG_OUT, size=2200)
    print(f'wrote {SVG_OUT.relative_to(REPO)}')
    print(f'wrote {PNG_OUT.relative_to(REPO)}')
    print(f'wrote {CSV_OUT.relative_to(REPO)}')


if __name__ == '__main__':
    main()
