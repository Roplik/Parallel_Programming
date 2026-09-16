import platform
import random
import subprocess
import sys
import re
from pathlib import Path

# Настройки
SIZES = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

SCRIPT_DIR = Path(__file__).parent.resolve()
FILE_A = SCRIPT_DIR / "matrixA.txt"
FILE_B = SCRIPT_DIR / "matrixB.txt"
FILE_OUT = SCRIPT_DIR / "matrixC_res.txt"
RESULTS_CSV = SCRIPT_DIR / "results.csv"

def get_preset_name():
    system = platform.system()
    if system == "Linux":
        return "linux-release"
    elif system == "Darwin":
        return "macos-release"
    elif system == "Windows":
        return "windows-release"
    else:
        raise RuntimeError(f"Unsupported OS: {system}")


def get_executable_path(preset_name):
    exe_name = "pp_lab_1.exe" if platform.system() == "Windows" else "pp_lab_1"
    return Path("build") / preset_name / "labs/lab_1" / exe_name


def build_with_preset():
    preset = get_preset_name()
    print(f"STEP 1: Configuring with CMake Preset [{preset}]")

    config_cmd = ["cmake", "--preset", preset]
    if subprocess.run(config_cmd).returncode != 0:
        print("Error: CMake configuration failed!")
        sys.exit(1)

    print(f"\nSTEP 2: Building Preset [{preset}]")
    build_cmd = ["cmake", "--build", "--preset", preset]
    if subprocess.run(build_cmd).returncode != 0:
        print("Error: Build failed!")
        sys.exit(1)

    return get_executable_path(preset)


def generate_random_matrix(size, min_val=-10.0, max_val=10.0):
    return [
        [random.uniform(min_val, max_val) for _ in range(size)]
        for _ in range(size)
    ]


def save_matrix_to_file(filename, matrix):
    n = len(matrix)
    script_dir = Path(__file__).parent.resolve()
    full_path = script_dir / filename

    with open(full_path, "w") as f:
        f.write(f"{n}\n")
        for row in matrix:
            f.write(" ".join(f"{val:.10f}" for val in row) + "\n")

def read_matrix_from_file(filename):
    with open(filename, "r") as f:
        lines = f.readlines()
    n = int(lines[0].strip())
    data = []
    for line in lines[1:]:
        data.extend([float(x) for x in line.split()])

    return [data[i * n : (i + 1) * n] for i in range(n)]


def python_matrix_multiply(A, B):
    n = len(A)
    C = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for k in range(n):
            temp = A[i][k]
            for j in range(n):
                C[i][j] += temp * B[k][j]
    return C


def verify_results(cpp_mat, reference_mat, tol=1e-5):
    # tol=1e-5 это разница в 10^-5
    n = len(cpp_mat)
    max_diff = 0.0

    for i in range(n):
        for j in range(n):
            diff = abs(cpp_mat[i][j] - reference_mat[i][j])
            if diff > max_diff:
                max_diff = diff
            if diff > tol:
                return False, max_diff
    return True, max_diff


def main():
    exe_path = build_with_preset()
    print("EXE PATH: ", exe_path)
    if not exe_path.exists():
        print(f"Error: Executable not found at {exe_path}")
        sys.exit(1)

    results = []
    print(f"\nSTEP 4: Running C++ Program")
    print(f"{'N':>6} | {'Time (s)':>10} | {'GFLOPS':>10} | {'Status':>8}")
    print("-" * 42)

    for MATRIX_SIZE in SIZES:
        mat_A = generate_random_matrix(MATRIX_SIZE)
        mat_B = generate_random_matrix(MATRIX_SIZE)

        save_matrix_to_file(FILE_A, mat_A)
        save_matrix_to_file(FILE_B, mat_B)

        run_cmd = [str(exe_path), str(FILE_A), str(FILE_B), str(FILE_OUT)]
        res = subprocess.run(run_cmd, capture_output=True, text=True)
        #print(res.stdout)
        if res.returncode != 0:
            print(f"Error executing C++ program for N={MATRIX_SIZE}")
            print(res.stderr)
            continue


        stdout = res.stdout
        match_time = re.search(r"Execution Time\s+:\s+([\d\.]+)", stdout)
        match_gflops = re.search(r"Performance\s+:\s+([\d\.]+)", stdout)
        if match_time and match_gflops:
            cpp_time = float(match_time.group(1))
            gflops = float(match_gflops.group(1))
        else:
            print(f"Failed to parse time output from C++ binary for N={MATRIX_SIZE}")
            continue


        cpp_result = read_matrix_from_file(FILE_OUT)

        python_result = python_matrix_multiply(mat_A, mat_B)

        is_correct, max_diff = verify_results(cpp_result, python_result)

        flops = 2 * (MATRIX_SIZE**3)
        gflops = (flops / cpp_time) / 1e9 if cpp_time > 0 else 0

        status = "OK" if is_correct else "FAIL"
        print(
            f"{MATRIX_SIZE:6d} | {cpp_time:10.4f} | {gflops:10.4f} | {max_diff:12.2e} | {status:>8}"
        )

        results.append((MATRIX_SIZE, cpp_time, gflops, max_diff))

    with open(RESULTS_CSV, "w") as f:
        f.write("N,Time_sec,GFLOPS,Max_Diff\n")
        for r in results:
            f.write(f"{r[0]},{r[1]:.6f},{r[2]:.4f},{r[3]:.2e}\n")

if __name__ == "__main__":
    main()