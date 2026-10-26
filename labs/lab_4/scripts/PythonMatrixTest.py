import platform
import subprocess
import sys
import re
import numpy as np
from pathlib import Path

# Настройки эксперимента
SIZES = [128, 256, 512, 1024, 2048, 4096]
BLOCK_SIZES = [8, 16, 32]

def find_project_root():
    """Ищем корень проекта (папку с CMakeLists.txt)"""
    current = Path(__file__).parent.resolve()
    for parent in [current] + list(current.parents):
        if (parent / "CMakeLists.txt").exists():
            return parent
    raise FileNotFoundError("CMakeLists.txt not found!")

def find_cmake_presets(project_root):
    """Проверяем наличие CMakePresets.json"""
    presets_file = project_root / "CMakePresets.json"
    if presets_file.exists():
        import json
        with open(presets_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for preset in data.get("configurePresets", []):
            name = preset.get("name", "")
            if "release" in name.lower():
                return name
        if data.get("configurePresets"):
            return data["configurePresets"][0]["name"]
    return None

# Папка, где лежит скрипт
SCRIPT_DIR = Path(__file__).parent.resolve()
SCRIPT_DIR.mkdir(parents=True, exist_ok=True)

# Корень проекта
PROJECT_ROOT = find_project_root()

# Файлы для тестов
FILE_A = SCRIPT_DIR / "matrixA.txt"
FILE_B = SCRIPT_DIR / "matrixB.txt"
FILE_OUT = SCRIPT_DIR / "matrixC_res.txt"
RESULTS_CSV = SCRIPT_DIR / "results_cuda.csv"

def get_executable_path():
    """Поиск скомпилированного исполняемого файла"""
    exe_name = "pp_lab_4.exe" if platform.system() == "Windows" else "pp_lab_4"
    
    possible_paths = [
        PROJECT_ROOT / "build" / "Release" / exe_name,
        PROJECT_ROOT / "build" / "windows-release" / exe_name,
        PROJECT_ROOT / "build" / "RelWithDebInfo" / exe_name,
        PROJECT_ROOT / "build" / exe_name,
        PROJECT_ROOT / exe_name,
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Рекурсивный поиск
    build_dir = PROJECT_ROOT / "build"
    if build_dir.exists():
        for found in build_dir.rglob(exe_name):
            return found
            
    raise FileNotFoundError(
        f"Executable '{exe_name}' not found.\n"
        f"Checked:\n" + "\n".join(f"  - {p}" for p in possible_paths)
    )

def build_project():
    """Сборка проекта через CMake"""
    print("STEP 1: Building project with CMake...")
    print(f"Project root: {PROJECT_ROOT}")
    
    preset = find_cmake_presets(PROJECT_ROOT)
    
    if preset:
        print(f"Using CMake Preset: {preset}")
        config_cmd = ["cmake", "--preset", preset]
        if subprocess.run(config_cmd, cwd=PROJECT_ROOT).returncode != 0:
            print("Error: CMake configuration failed!")
            sys.exit(1)

        build_cmd = ["cmake", "--build", "--preset", preset]
        if subprocess.run(build_cmd, cwd=PROJECT_ROOT).returncode != 0:
            print("Error: Build failed!")
            sys.exit(1)
    else:
        print("No CMake Presets found. Using standard build...")
        config_cmd = ["cmake", "-DCMAKE_BUILD_TYPE=Release", "-B", "build", "-S", "."]
        if subprocess.run(config_cmd, cwd=PROJECT_ROOT).returncode != 0:
            print("Error: CMake configuration failed!")
            sys.exit(1)

        build_cmd = ["cmake", "--build", "build", "--config", "Release"]
        if subprocess.run(build_cmd, cwd=PROJECT_ROOT).returncode != 0:
            print("Error: Build failed!")
            sys.exit(1)
    
    print("Build successful!\n")
    return get_executable_path()

def generate_random_matrix(size, min_val=-10.0, max_val=10.0):
    """Генерация случайной матрицы float32"""
    return np.random.uniform(min_val, max_val, (size, size)).astype(np.float32)

def save_matrix_to_file(filename, matrix):
    """Сохранение матрицы в файл"""
    n = matrix.shape[0]
    with open(filename, "w") as f:
        f.write(f"{n}\n")
        for row in matrix:
            f.write(" ".join(f"{val:.6f}" for val in row) + "\n")

def verify_results(cpp_mat, reference_mat, tol=1e-2):
    """Проверка корректности результатов"""
    diff = np.abs(cpp_mat - reference_mat)
    max_diff = np.max(diff)
    rel_diff = max_diff / (np.max(np.abs(reference_mat)) + 1e-10)
    is_correct = (max_diff <= tol) or (rel_diff <= 1e-3)
    return is_correct, max_diff

def main():
    """Главная функция"""
    try:
        exe_path = build_project()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    print(f"Using executable: {exe_path}\n")
    results = []

    print("STEP 2: RUNNING CUDA EXPERIMENTS")
    print(f"{'N':>5} | {'Block':>5} | {'Time (s)':>9} | {'GFLOPS':>8} | {'Speedup':>7} | {'Max Diff':>10} | {'Status':>6}")
    print("-" * 75)

    for N in SIZES:
        # Генерация матриц
        mat_A = generate_random_matrix(N)
        mat_B = generate_random_matrix(N)
        reference_result = np.matmul(mat_A, mat_B)
        
        # Сохранение
        save_matrix_to_file(FILE_A, mat_A)
        save_matrix_to_file(FILE_B, mat_B)

        baseline_time = None

        for block_size in BLOCK_SIZES:
            run_cmd = [
                str(exe_path),
                str(FILE_A),
                str(FILE_B),
                str(FILE_OUT),
                str(block_size)
            ]
            
            res = subprocess.run(run_cmd, capture_output=True, text=True)

            if res.returncode != 0:
                print(f"Error for N={N}, Block={block_size}:\n{res.stderr}")
                continue

            # Парсинг вывода
            match_time = re.search(r"Execution Time\s+:\s+([\d\.]+)", res.stdout)
            match_gflops = re.search(r"Performance\s+:\s+([\d\.]+)", res.stdout)

            if not match_time or not match_gflops:
                print(f"Failed to parse output for N={N}, Block={block_size}")
                print(f"Output was:\n{res.stdout}")
                continue

            cpp_time = float(match_time.group(1))
            cpp_gflops = float(match_gflops.group(1))

            if baseline_time is None:
                baseline_time = cpp_time
            
            speedup = baseline_time / cpp_time if cpp_time > 0 else 1.0

            # Чтение и проверка результата
            cpp_result = np.loadtxt(FILE_OUT, skiprows=1, dtype=np.float32)
            is_correct, max_diff = verify_results(cpp_result, reference_result)
            status = "OK" if is_correct else "FAIL"

            print(f"{N:5d} | {block_size:5d} | {cpp_time:9.4f} | {cpp_gflops:8.1f} | {speedup:7.2f}x | {max_diff:10.2e} | {status:>6}")

            results.append({
                "N": N,
                "Block_Size": block_size,
                "Time_sec": cpp_time,
                "GFLOPS": cpp_gflops,
                "Speedup_vs_8x8": speedup,
                "Max_Diff": max_diff,
                "Status": status
            })

    # Сохранение результатов
    with open(RESULTS_CSV, "w") as f:
        f.write("N,Block_Size,Time_sec,GFLOPS,Speedup_vs_8x8,Max_Diff,Status\n")
        for r in results:
            f.write(f"{r['N']},{r['Block_Size']},{r['Time_sec']:.6f},{r['GFLOPS']:.2f},{r['Speedup_vs_8x8']:.2f},{r['Max_Diff']:.2e},{r['Status']}\n")

    print(f"\nResults successfully saved to {RESULTS_CSV}")

if __name__ == "__main__":
    try:
        import numpy
    except ImportError:
        print("Error: numpy is required. Install it via: pip install numpy")
        sys.exit(1)
    
    main()