import csv
import math
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
RESULTS_CSV = SCRIPT_DIR / "results.csv"
FIGURES_DIR = SCRIPT_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)


def draw_svg_line_chart_dark(
    filepath, title, x_label, y_label, x_values, y_values, use_log_y=False
):
    width, height = 800, 500
    margin_left, margin_right, margin_top, margin_bottom = 90, 40, 60, 60
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    if use_log_y:
        processed_y = [math.log10(y) if y > 0 else 0 for y in y_values]
    else:
        processed_y = list(y_values)

    min_x, max_x = min(x_values), max(x_values)
    min_y, max_y = min(processed_y), max(processed_y)

    if min_y == max_y:
        max_y += 1.0

    def get_coords(x, y):
        px = margin_left + (x - min_x) / (max_x - min_x) * plot_width
        py = height - margin_bottom - (y - min_y) / (max_y - min_y) * plot_height
        return px, py

    points = [get_coords(x, y) for x, y in zip(x_values, processed_y)]
    polyline_points = " ".join([f"{px:.1f},{py:.1f}" for px, py in points])

    bg_color = "#121212"
    text_color = "#e0e0e0"
    grid_color = "#2a2a2a"
    axis_color = "#555555"
    line_color = "#00d2ff"
    point_color = "#00d2ff"

    svg = []
    svg.append(
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background:{bg_color}; font-family:sans-serif;">'
    )
    svg.append(
        f'<text x="{width/2}" y="35" text-anchor="middle" font-size="18" font-weight="bold" fill="{text_color}">{title}</text>'
    )

    # Сетка и метки по Y
    num_y_ticks = 5
    for i in range(num_y_ticks + 1):
        y_val_proc = min_y + i * (max_y - min_y) / num_y_ticks
        _, py = get_coords(min_x, y_val_proc)
        svg.append(
            f'<line x1="{margin_left}" y1="{py}" x2="{width - margin_right}" y2="{py}" stroke="{grid_color}" stroke-width="1"/>'
        )

        if use_log_y:
            label = f"10^{y_val_proc:.2f}"
        else:
            label = f"{y_val_proc:.4f}"
        svg.append(
            f'<text x="{margin_left - 10}" y="{py + 4}" text-anchor="end" font-size="12" fill="#aaaaaa">{label}</text>'
        )

    # Метки по X
    for x in x_values:
        px, _ = get_coords(x, min_y)
        svg.append(
            f'<line x1="{px}" y1="{height - margin_bottom}" x2="{px}" y2="{height - margin_bottom + 5}" stroke="{axis_color}" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{px}" y="{height - margin_bottom + 20}" text-anchor="middle" font-size="12" fill="#aaaaaa">{x}</text>'
        )

    # Оси координат
    svg.append(
        f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="{axis_color}" stroke-width="2"/>'
    )
    svg.append(
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="{axis_color}" stroke-width="2"/>'
    )

    # Подписи осей
    svg.append(
        f'<text x="{width/2}" y="{height - 15}" text-anchor="middle" font-size="14" fill="{text_color}">{x_label}</text>'
    )
    svg.append(
        f'<text x="25" y="{height/2}" text-anchor="middle" font-size="14" fill="{text_color}" transform="rotate(-90 25 {height/2})">{y_label}</text>'
    )

    # Линия и точки данных
    svg.append(
        f'<polyline fill="none" stroke="{line_color}" stroke-width="3" points="{polyline_points}"/>'
    )
    for px, py in points:
        svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{point_color}"/>')

    svg.append("</svg>")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))


def main():
    if not RESULTS_CSV.exists():
        print(f"Ошибка: файл {RESULTS_CSV} не найден!")
        return

    x_vals = []
    t_vals = []
    g_vals = []

    with open(RESULTS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            x_vals.append(int(row["N"]))
            t_vals.append(float(row["Time_sec"]))
            g_vals.append(float(row["GFLOPS"]))

    print(f"Generating dark SVG graphics in: {FIGURES_DIR}")

    draw_svg_line_chart_dark(
        FIGURES_DIR / "time_by_size.svg",
        "Sequential Execution Time vs Matrix Size (N)",
        "Matrix Size N (NxN)",
        "Time (seconds)",
        x_vals,
        t_vals,
    )

    draw_svg_line_chart_dark(
        FIGURES_DIR / "time_by_size_log.svg",
        "Sequential Execution Time (Log Scale)",
        "Matrix Size N (NxN)",
        "Log10(Time in seconds)",
        x_vals,
        t_vals,
        use_log_y=True,
    )

    draw_svg_line_chart_dark(
        FIGURES_DIR / "throughput_by_size.svg",
        "Performance (GFLOPS) vs Matrix Size (N)",
        "Matrix Size N (NxN)",
        "Performance (GFLOPS)",
        x_vals,
        g_vals,
    )
    print("Generation completed")


if __name__ == "__main__":
    main()