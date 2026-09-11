import os
import platform
import random
import subprocess
import sys
from pathlib import Path

# Настройки
MATRIX_SIZE = 500  
FILE_A = "matrixA.txt"
FILE_B = "matrixB.txt"
FILE_OUT = "matrixC_res.txt"


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
    return Path("build") / preset_name / exe_name


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
    random.seed(42)
    return [
        [random.uniform(min_val, max_val) for _ in range(size)]
        for _ in range(size)
    ]


def save_matrix_to_file(filename, matrix):
    n = len(matrix)
    with open(filename, "w") as f:
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
    #tol=1e-5 это разница в 10^-5
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

    if not exe_path.exists():
        print(f"Error: Executable not found at {exe_path}")
        sys.exit(1)

    print(
        f"\nSTEP 3: Generating Input Matrices ({MATRIX_SIZE}x{MATRIX_SIZE})"
    )
    mat_A = generate_random_matrix(MATRIX_SIZE)
    mat_B = generate_random_matrix(MATRIX_SIZE)

    save_matrix_to_file(FILE_A, mat_A)
    save_matrix_to_file(FILE_B, mat_B)

    print(f"\nSTEP 4: Running C++ Program")
    run_cmd = [str(exe_path), FILE_A, FILE_B, FILE_OUT]
    if subprocess.run(run_cmd).returncode != 0:
        print("Error: C++ execution failed!")
        sys.exit(1)

    print("\nSTEP 5: Verifying Results")
    cpp_result = read_matrix_from_file(FILE_OUT)

    python_result = python_matrix_multiply(mat_A, mat_B)

    is_correct, max_diff = verify_results(cpp_result, python_result)

    print("\n========================================")
    if is_correct:
        print("VERIFICATION SUCCESSFUL! C++ matches Python.")
        print(f"Max Absolute Difference: {max_diff:.2e}")
    else:
        print("VERIFICATION FAILED! Results do NOT match.")
        print(f"Max Absolute Difference: {max_diff:.2e}")
    print("========================================\n")


if __name__ == "__main__":
    main()