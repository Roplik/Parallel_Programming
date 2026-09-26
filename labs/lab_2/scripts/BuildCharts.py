import csv
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
RESULTS_CSV = SCRIPT_DIR / "results.csv"
FIGURES_DIR = SCRIPT_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Цветовая палитра для разного количества потоков
COLOR_MAP = {
    1: "#ff5252",  # Красный
    2: "#ffb142",  # Оранжевый
    4: "#2ed573",  # Зеленый
    8: "#1e90ff",  # Голубой
    12: "#a55eea", # Фиолетовый
    16: "#ff7979"  # Розовый
}

def draw_svg_multi_line_dark(
    filepath: Path,
    title: str,
    x_label: str,
    y_label: str,
    x_values: list,
    series_data: dict,  # {threads_count: [y_value1, y_value2, ...]}
    ideal_line: list = None # Опциональная эталонная линия (для Speedup)
):
    width, height = 850, 520
    margin_left, margin_right, margin_top, margin_bottom = 90, 160, 60, 60
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    # Вычисление границ по Y
    all_y = [val for y_list in series_data.values() for val in y_list]
    if ideal_line:
        all_y.extend(ideal_line)

    min_x, max_x = min(x_values), max(x_values)
    min_y, max_y = 0.0, max(all_y) * 1.05  # Начинаем Y с 0 для честного наглядного масштаба

    if min_y == max_y:
        max_y += 1.0

    def get_coords(x, y):
        px = margin_left + (x - min_x) / (max_x - min_x) * plot_width
        py = height - margin_bottom - (y - min_y) / (max_y - min_y) * plot_height
        return px, py

    bg_color = "#121212"
    text_color = "#e0e0e0"
    grid_color = "#2a2a2a"
    axis_color = "#555555"

    svg = []
    svg.append(
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background:{bg_color}; font-family:sans-serif;">'
    )
    # Заголовок
    svg.append(
        f'<text x="{width/2}" y="35" text-anchor="middle" font-size="18" font-weight="bold" fill="{text_color}">{title}</text>'
    )

    # Сетка и метки Y
    num_y_ticks = 6
    for i in range(num_y_ticks + 1):
        y_val = min_y + i * (max_y - min_y) / num_y_ticks
        _, py = get_coords(min_x, y_val)
        svg.append(
            f'<line x1="{margin_left}" y1="{py}" x2="{width - margin_right}" y2="{py}" stroke="{grid_color}" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{margin_left - 10}" y="{py + 4}" text-anchor="end" font-size="12" fill="#aaaaaa">{y_val:.2f}</text>'
        )

    # Метки X
    for x in x_values:
        px, _ = get_coords(x, min_y)
        svg.append(
            f'<line x1="{px}" y1="{height - margin_bottom}" x2="{px}" y2="{height - margin_bottom + 5}" stroke="{axis_color}" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{px}" y="{height - margin_bottom + 20}" text-anchor="middle" font-size="11" fill="#aaaaaa">{x}</text>'
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
        f'<text x="{(margin_left + width - margin_right)/2}" y="{height - 15}" text-anchor="middle" font-size="14" fill="{text_color}">{x_label}</text>'
    )
    svg.append(
        f'<text x="25" y="{height/2}" text-anchor="middle" font-size="14" fill="{text_color}" transform="rotate(-90 25 {height/2})">{y_label}</text>'
    )

    if ideal_line:
        ideal_points = [get_coords(x, y) for x, y in zip(x_values, ideal_line)]
        polyline = " ".join([f"{px:.1f},{py:.1f}" for px, py in ideal_points])
        svg.append(
            f'<polyline fill="none" stroke="#777777" stroke-width="1.5" stroke-dasharray="5,5" points="{polyline}"/>'
        )

    # Отрисовка графиков по потокам
    legend_y = margin_top + 10
    for threads, y_vals in series_data.items():
        color = COLOR_MAP.get(threads, "#ffffff")
        points = [get_coords(x, y) for x, y in zip(x_values, y_vals)]
        polyline_points = " ".join([f"{px:.1f},{py:.1f}" for px, py in points])

        # Линия
        svg.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{polyline_points}"/>'
        )
        # Точки
        for px, py in points:
            svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{color}"/>')

        # Легенда
        leg_x = width - margin_right + 20
        svg.append(f'<line x1="{leg_x}" y1="{legend_y}" x2="{leg_x + 20}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        svg.append(f'<circle cx="{leg_x + 10}" cy="{legend_y}" r="3.5" fill="{color}"/>')
        svg.append(f'<text x="{leg_x + 28}" y="{legend_y + 4}" font-size="12" fill="{text_color}">{threads} thread(s)</text>')
        legend_y += 25

    if ideal_line:
        leg_x = width - margin_right + 20
        svg.append(f'<line x1="{leg_x}" y1="{legend_y}" x2="{leg_x + 20}" y2="{legend_y}" stroke="#777777" stroke-width="1.5" stroke-dasharray="4,4"/>')
        svg.append(f'<text x="{leg_x + 28}" y="{legend_y + 4}" font-size="12" fill="#aaaaaa">Ideal</text>')

    svg.append("</svg>")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))


def main():
    if not RESULTS_CSV.exists():
        print(f"Ошибка: файл {RESULTS_CSV} не найден!")
        return

    # Структуры для группировки данных: {threads: {N: value}}
    times_data = {}
    gflops_data = {}
    speedup_data = {}
    eff_data = {}
    
    sizes_set = set()

    with open(RESULTS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row["N"])
            t = int(row["Threads"])
            time_sec = float(row["Time_sec"])
            gflops = float(row["GFLOPS"])
            speedup = float(row["Speedup"])
            eff = float(row["Efficiency"])

            sizes_set.add(n)

            times_data.setdefault(t, {})[n] = time_sec
            gflops_data.setdefault(t, {})[n] = gflops
            speedup_data.setdefault(t, {})[n] = speedup
            eff_data.setdefault(t, {})[n] = eff

    x_values = sorted(list(sizes_set))

    # Формируем списки Y для каждой серии потоков
    def build_series(data_dict):
        series = {}
        for threads in sorted(data_dict.keys()):
            series[threads] = [data_dict[threads][n] for n in x_values]
        return series

    print(f"Generating SVG OpenMP charts in: {FIGURES_DIR}")

    # 1. Время выполнения
    draw_svg_multi_line_dark(
        FIGURES_DIR / "omp_time.svg",
        "Execution Time vs Matrix Size (OpenMP)",
        "Matrix Size N (NxN)",
        "Time (seconds)",
        x_values,
        build_series(times_data)
    )

    # 2. Производительность (GFLOPS)
    draw_svg_multi_line_dark(
        FIGURES_DIR / "omp_gflops.svg",
        "Performance (GFLOPS) vs Matrix Size (OpenMP)",
        "Matrix Size N (NxN)",
        "GFLOPS",
        x_values,
        build_series(gflops_data)
    )

    # 3. Ускорение (Speedup)
    draw_svg_multi_line_dark(
        FIGURES_DIR / "omp_speedup.svg",
        "Speedup vs Matrix Size (OpenMP)",
        "Matrix Size N (NxN)",
        "Speedup (S_p)",
        x_values,
        build_series(speedup_data)
    )

    # 4. Эффективность (Efficiency)
    draw_svg_multi_line_dark(
        FIGURES_DIR / "omp_efficiency.svg",
        "Efficiency vs Matrix Size (OpenMP)",
        "Matrix Size N (NxN)",
        "Efficiency (E_p)",
        x_values,
        build_series(eff_data)
    )

    print("SVG Generation completed successfully!")


if __name__ == "__main__":
    main()