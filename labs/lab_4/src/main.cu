#include <cuda_runtime.h>

#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

template <int TILE_SIZE>
__global__ void matrixMulKernelShared(const float* A, const float* B, float* C,
                                      int N) {
  // Выделяем shared memory под размер текущего блока (TILE_SIZE)
  __shared__ float As[TILE_SIZE][TILE_SIZE];
  __shared__ float Bs[TILE_SIZE][TILE_SIZE];

  int bx = blockIdx.x;
  int by = blockIdx.y;
  int tx = threadIdx.x;
  int ty = threadIdx.y;

  int row = by * TILE_SIZE + ty;
  int col = bx * TILE_SIZE + tx;

  float sum = 0.0f;

  // Цикл по блокам (tiles) матриц
  for (int t = 0; t < (N + TILE_SIZE - 1) / TILE_SIZE; ++t) {
    int a_col = t * TILE_SIZE + tx;
    int b_row = t * TILE_SIZE + ty;

    // Загрузка блока A (с проверкой границ)
    if (row < N && a_col < N) {
      As[ty][tx] = A[row * N + a_col];
    } else {
      As[ty][tx] = 0.0f;
    }

    // Загрузка блока B (с проверкой границ)
    if (b_row < N && col < N) {
      Bs[ty][tx] = B[b_row * N + col];
    } else {
      Bs[ty][tx] = 0.0f;
    }

    // Синхронизация: ждем загрузки данных в shared memory
    __syncthreads();

    // Вычисление частичной суммы
    for (int k = 0; k < TILE_SIZE; ++k) {
      sum += As[ty][k] * Bs[k][tx];
    }

    // Синхронизация перед переходом к следующему блоку
    __syncthreads();
  }

  // Запись результата в глобальную память
  if (row < N && col < N) {
    C[row * N + col] = sum;
  }
}

// ==========================================
// КЛАСС MATRIX
// ==========================================
class Matrix {
 private:
  int size;
  std::vector<float> data;

 public:
  Matrix() : size(0) {}
  Matrix(int s) : size(s), data(s * s, 0.0f) {}
  Matrix(const std::string& path) : size(0) { loadFromFile(path); }

  void loadFromFile(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
      throw std::runtime_error("Failed to open file: " + path);
    }
    if (!(file >> size)) {
      throw std::runtime_error("Error reading size from: " + path);
    }
    data.resize(size * size);
    for (int i = 0; i < size * size; ++i) {
      if (!(file >> data[i])) {
        throw std::runtime_error("Error reading data from: " + path);
      }
    }
  }

  int get_size() const { return size; }

  float& operator()(int row, int col) { return data[row * size + col]; }
  const float& operator()(int row, int col) const {
    return data[row * size + col];
  }

  // Умножение с динамическим выбором размера блока (TILE_SIZE)
  Matrix multiply(const Matrix& other, int block_size = 16) const {
    if (size != other.size) {
      throw std::invalid_argument(
          "Matrix sizes do not match: " + std::to_string(size) + " vs " +
          std::to_string(other.size));
    }

    int num_elements = size * size;
    int bytes = num_elements * sizeof(float);
    Matrix result(size);

    float *d_A = nullptr, *d_B = nullptr, *d_C = nullptr;

    cudaMalloc(&d_A, bytes);
    cudaMalloc(&d_B, bytes);
    cudaMalloc(&d_C, bytes);

    cudaMemcpy(d_A, this->data.data(), bytes, cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, other.data.data(), bytes, cudaMemcpyHostToDevice);

    dim3 threadsPerBlock(block_size, block_size);
    dim3 numBlocks((size + block_size - 1) / block_size,
                   (size + block_size - 1) / block_size);

    // Запуск соответствующей версии шаблонного ядра в зависимости от block_size
    if (block_size == 8) {
      matrixMulKernelShared<8>
          <<<numBlocks, threadsPerBlock>>>(d_A, d_B, d_C, size);
    } else if (block_size == 32) {
      matrixMulKernelShared<32>
          <<<numBlocks, threadsPerBlock>>>(d_A, d_B, d_C, size);
    } else {
      matrixMulKernelShared<16>
          <<<numBlocks, threadsPerBlock>>>(d_A, d_B, d_C, size);
    }

    cudaDeviceSynchronize();

    cudaError_t err = cudaGetLastError();
    if (err != cudaSuccess) {
      cudaFree(d_A);
      cudaFree(d_B);
      cudaFree(d_C);
      throw std::runtime_error(std::string("CUDA Kernel Error: ") +
                               cudaGetErrorString(err));
    }

    cudaMemcpy(result.data.data(), d_C, bytes, cudaMemcpyDeviceToHost);

    cudaFree(d_A);
    cudaFree(d_B);
    cudaFree(d_C);

    return result;
  }

  void saveToFile(const std::string& path) const {
    std::ofstream file(path);
    if (!file.is_open()) {
      throw std::runtime_error("Failed to open file for writing: " + path);
    }
    file << size << "\n";
    file << std::setprecision(6);
    for (int i = 0; i < size; ++i) {
      for (int j = 0; j < size; ++j) {
        file << operator()(i, j);
        if (j + 1 < size) file << " ";
      }
      file << "\n";
    }
  }
};

// ==========================================
// ГЛАВНАЯ ФУНКЦИЯ
// ==========================================
int main(int argc, char* argv[]) {
  if (argc < 4) {
    std::cerr << "Usage: " << argv[0]
              << " <matrixA> <matrixB> <output> [block_size]\n";
    return 1;
  }

  std::string fileA = argv[1];
  std::string fileB = argv[2];
  std::string fileOut = argv[3];

  int block_size = 16;
  if (argc >= 5) {
    block_size = std::atoi(argv[4]);
    if (block_size < 4) block_size = 4;
    if (block_size > 32) block_size = 32;
  }

  try {
    Matrix A(fileA);
    Matrix B(fileB);

    int N = A.get_size();

    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);

    cudaEventRecord(start);
    Matrix C = A.multiply(B, block_size);
    cudaEventRecord(stop);
    cudaEventSynchronize(stop);

    float milliseconds = 0;
    cudaEventElapsedTime(&milliseconds, start, stop);
    double time_sec = milliseconds / 1000.0;

    C.saveToFile(fileOut);

    double total_flops = 2.0 * static_cast<double>(N) * static_cast<double>(N) *
                         static_cast<double>(N);
    double gflops = (time_sec > 0.0) ? (total_flops / time_sec / 1e9) : 0.0;

    std::cout << "=======================================\n";
    std::cout << "CUDA Matrix Multiplication Stats (Shared Memory)\n";
    std::cout << "=======================================\n";
    std::cout << "Matrix Size (N x N)  : " << N << " x " << N << "\n";
    std::cout << "Block Size           : " << block_size << " x " << block_size
              << "\n";
    std::cout << "Total Operations     : "
              << static_cast<long long>(total_flops) << " FLOPs\n";
    std::cout << "Execution Time       : " << std::fixed << std::setprecision(6)
              << time_sec << " seconds\n";
    std::cout << "Performance          : " << std::fixed << std::setprecision(3)
              << gflops << " GFLOPS\n";

    cudaEventDestroy(start);
    cudaEventDestroy(stop);

  } catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << "\n";
    return 1;
  }

  return 0;
}