import platform
import random
import subprocess
import sys
import re
from pathlib import Path

# Настройки
SIZES = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
THREADS_LIST = [1, 2, 4, 8]

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
    exe_name = "pp_lab_2.exe" if platform.system() == "Windows" else "pp_lab_2"
    return Path("build") / preset_name / "labs/lab_2" / exe_name


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
  try:
    import numpy as np

    return (np.array(A) @ np.array(B)).tolist()
  except ImportError:
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
  print("\nEXE PATH: ", exe_path)
  if not exe_path.exists():
    print(f"Error: Executable not found at {exe_path}")
    sys.exit(1)

  results = []

  print("\nSTEP 3: RUNNING OPENMP EXPERIMENTS")

  for MATRIX_SIZE in SIZES:
    print(f"\n================ Matrix Size N = {MATRIX_SIZE} ================")
    mat_A = generate_random_matrix(MATRIX_SIZE)
    mat_B = generate_random_matrix(MATRIX_SIZE)

    save_matrix_to_file(FILE_A, mat_A)
    save_matrix_to_file(FILE_B, mat_B)

    python_ref = python_matrix_multiply(mat_A, mat_B)

    time_t1 = None  

    print(
        f"{'Threads':>8} | {'Time (s)':>10} | {'GFLOPS':>9} | {'Speedup':>8} |"
        f" {'Eff':>6} | {'Status':>8}"
    )
    print("-" * 65)

    for threads in THREADS_LIST:
      run_cmd = [
          str(exe_path),
          str(FILE_A),
          str(FILE_B),
          str(FILE_OUT),
          str(threads),
      ]
      res = subprocess.run(run_cmd, capture_output=True, text=True)

      if res.returncode != 0:
        print(f"Error executing C++ program for N={MATRIX_SIZE}, T={threads}")
        print(res.stderr)
        continue

      stdout = res.stdout
      match_time = re.search(r"Execution Time\s+:\s+([\d\.]+)", stdout)

      if match_time:
        cpp_time = float(match_time.group(1))
      else:
        match_alt = re.search(r"TIME:([\d\.]+)", stdout)
        if match_alt:
          cpp_time = float(match_alt.group(1))
        else:
          print(f"Failed to parse time for N={MATRIX_SIZE}, T={threads}")
          continue

      if threads == 1:
        time_t1 = cpp_time

      speedup = time_t1 / cpp_time if cpp_time > 0 else 1.0
      efficiency = speedup / threads

      cpp_result = read_matrix_from_file(FILE_OUT)
      is_correct, max_diff = verify_results(cpp_result, python_ref)

      flops = 2.0 * (MATRIX_SIZE**3)
      gflops = (flops / cpp_time) / 1e9 if cpp_time > 0 else 0.0
      status = "OK" if is_correct else "FAIL"

      print(
          f"{threads:8d} | {cpp_time:10.4f} | {gflops:9.2f} | {speedup:8.2f}x |"
          f" {efficiency:6.2f} | {status:>8}"
      )

      results.append({
          "N": MATRIX_SIZE,
          "Threads": threads,
          "Time_sec": cpp_time,
          "GFLOPS": gflops,
          "Speedup": speedup,
          "Efficiency": efficiency,
          "Max_Diff": max_diff,
      })

  with open(RESULTS_CSV, "w") as f:
    f.write("N,Threads,Time_sec,GFLOPS,Speedup,Efficiency,Max_Diff\n")
    for r in results:
      f.write(
          f"{r['N']},{r['Threads']},{r['Time_sec']:.6f},{r['GFLOPS']:.4f},{r['Speedup']:.2f},{r['Efficiency']:.2f},{r['Max_Diff']:.2e}\n"
      )

  print(f"\nResults successfully saved to {RESULTS_CSV}")

if __name__ == "__main__":
    main()