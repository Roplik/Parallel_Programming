#include <omp.h>

#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

#include "matrix.hpp"

int main(int argc, char* argv[]) {
  if (argc < 4) {
    std::cerr << "Usage: " << argv[0]
              << " <matrixA_file> <matrixB_file> <output_file>\n";
    return 1;
  }

  std::string fileA = argv[1];
  std::string fileB = argv[2];
  std::string fileOut = argv[3];
  int threads = (argc >= 5) ? std::atoi(argv[4]) : omp_get_max_threads();

  try {
    Matrix A(fileA);
    Matrix B(fileB);

    if (A.get_size() != B.get_size()) {
      std::cerr << "Error: Input matrices must have the same dimension!\n";
      return 1;
    }

    size_t N = A.get_size();

    double start = omp_get_wtime();
    Matrix C = A.multiply(B, threads);
    double end = omp_get_wtime();

    double time_sec = end - start;

    C.saveToFile(fileOut);

    double total_flops = 2.0 * static_cast<double>(N) * static_cast<double>(N) *
                         static_cast<double>(N);
    double gflops = (time_sec > 0.0) ? ((total_flops / time_sec) / 1e9) : 0.0;

    std::cout << "=======================================\n";
    std::cout << "Matrix Multiplication Performance Stats \n";
    std::cout << "=======================================\n";
    std::cout << "Matrix Size (N x N)  : " << N << " x " << N << "\n";
    std::cout << "Threads Used          : " << threads << "\n";
    std::cout << "Total Operations     : " << static_cast<size_t>(total_flops)
              << " FLOPs\n";
    std::cout << "Execution Time       : " << std::fixed << std::setprecision(6)
              << time_sec << " seconds\n";
    std::cout << "Performance          : " << std::fixed << std::setprecision(3)
              << gflops << " GFLOPS\n";
    std::cout << "Result saved to      : " << fileOut << "\n";

  } catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << "\n";
    return 1;
  }

  return 0;
}