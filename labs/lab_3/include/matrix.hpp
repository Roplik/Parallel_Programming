#ifndef MATRIX_HPP
#define MATRIX_HPP

#include <cstddef>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

class Matrix {
  size_t size;
  std::vector<double> data;

 public:
  Matrix(size_t s = 0) : size(s), data(s * s, 0) {}
  Matrix(const std::string& path) { loadFromFile(path); }

  void loadFromFile(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
      throw std::runtime_error("Failed to open file for reading: " + path);
    }
    if (!(file >> size)) {
      throw std::runtime_error("Error reading matrix size from file: " + path);
    }
    data.resize(size * size);
    for (size_t i = 0; i < size * size; ++i) {
      if (!(file >> data[i])) {
        throw std::runtime_error("Error reading data from file: " + path);
      }
    }
  }

  size_t get_size() const { return size; }

  double* get_data_ptr() { return data.data(); }
  const double* get_data_ptr() const { return data.data(); }

  void resize(size_t s) {
    size = s;
    data.assign(s * s, 0);
  }

  double& operator()(size_t row, size_t col) { return data[row * size + col]; }
  const double& operator()(size_t row, size_t col) const {
    return data[row * size + col];
  }

  static std::vector<double> multiply_strip(
      const std::vector<double>& local_A_rows, const Matrix& B,
      size_t num_rows) {
    size_t N = B.get_size();
    std::vector<double> local_C(num_rows * N, 0.0);
    const double* B_ptr = B.get_data_ptr();

    for (size_t i = 0; i < num_rows; ++i) {
      for (size_t k = 0; k < N; ++k) {
        double temp = local_A_rows[i * N + k];
        size_t row_i_offset = i * N;
        size_t row_k_offset = k * N;

        for (size_t j = 0; j < N; ++j) {
          local_C[row_i_offset + j] += temp * B_ptr[row_k_offset + j];
        }
      }
    }
    return local_C;
  }

  void saveToFile(const std::string& path) const {
    std::ofstream file(path);
    if (!file.is_open()) {
      throw std::runtime_error("Failed to open file for writing: " + path);
    }
    file << size << "\n";
    file << std::setprecision(10);
    for (size_t i = 0; i < size; ++i) {
      for (size_t j = 0; j < size; ++j) {
        file << operator()(i, j) << (j + 1 == size ? "" : " ");
      }
      file << "\n";
    }
  }
};

#endif
