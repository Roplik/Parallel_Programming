#include <mpi.h>

#include <iomanip>
#include <iostream>
#include <random>
#include <string>
#include <vector>

#include "matrix.hpp"

int main(int argc, char* argv[]) {
  MPI_Init(&argc, &argv);

  int rank, num_procs;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &num_procs);

  if (argc < 2) {
    if (rank == 0) {
      std::cerr << "Usage: " << argv[0] << " <matrix_size_N>\n";
    }
    MPI_Finalize();
    return 1;
  }

  size_t N = 0;
  try {
    N = std::stoull(argv[1]);
  } catch (const std::exception& e) {
    if (rank == 0) {
      std::cerr << "Error parsing matrix size: " << e.what() << "\n";
    }
    MPI_Finalize();
    return 1;
  }

  Matrix A, B, C;

  if (rank == 0) {
    A.resize(N);
    B.resize(N);

    std::mt19937 gen(1337);
    std::uniform_real_distribution<double> dis(1.0, 10.0);

    double* ptr_A = A.get_data_ptr();
    double* ptr_B = B.get_data_ptr();

    for (size_t i = 0; i < N * N; ++i) {
      ptr_A[i] = dis(gen);
      ptr_B[i] = dis(gen);
    }
  }

  if (rank != 0) {
    B.resize(N);
  }

  MPI_Bcast(B.get_data_ptr(), N * N, MPI_DOUBLE, 0, MPI_COMM_WORLD);

  std::vector<int> send_counts(num_procs);
  std::vector<int> displacements(num_procs);

  int r_offset = 0;
  for (int i = 0; i < num_procs; ++i) {
    int rows_for_proc = (N / num_procs) + (i < (int)(N % num_procs) ? 1 : 0);
    send_counts[i] = rows_for_proc * N;
    displacements[i] = r_offset;
    r_offset += send_counts[i];
  }

  int local_elements = send_counts[rank];
  int local_rows = local_elements / N;
  std::vector<double> local_A(local_elements);

  MPI_Barrier(MPI_COMM_WORLD);

  double start_time = 0.0;
  if (rank == 0) {
    start_time = MPI_Wtime();
  }

  MPI_Scatterv(A.get_data_ptr(), send_counts.data(), displacements.data(),
               MPI_DOUBLE, local_A.data(), local_elements, MPI_DOUBLE, 0,
               MPI_COMM_WORLD);

  std::vector<double> local_C = Matrix::multiply_strip(local_A, B, local_rows);

  if (rank == 0) {
    C.resize(N);
  }

  MPI_Gatherv(local_C.data(), local_elements, MPI_DOUBLE, C.get_data_ptr(),
              send_counts.data(), displacements.data(), MPI_DOUBLE, 0,
              MPI_COMM_WORLD);

  if (rank == 0) {
    double end_time = MPI_Wtime();
    double time_sec = end_time - start_time;

    double total_flops = 2.0 * static_cast<double>(N) * static_cast<double>(N) *
                         static_cast<double>(N);
    double gflops = (time_sec > 0.0) ? ((total_flops / time_sec) / 1e9) : 0.0;

    std::cout << "=======================================\n";
    std::cout << "MPI Matrix Multiplication Performance  \n";
    std::cout << "=======================================\n";
    std::cout << "Matrix Size (N x N)  : " << N << " x " << N << "\n";
    std::cout << "MPI Processes Used    : " << num_procs << "\n";
    std::cout << "Execution Time       : " << std::fixed << std::setprecision(6)
              << time_sec << " seconds\n";
    std::cout << "Performance          : " << std::fixed << std::setprecision(3)
              << gflops << " GFLOPS\n";
  }

  MPI_Finalize();
  return 0;
}
