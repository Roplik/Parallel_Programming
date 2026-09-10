#ifndef MATRIX_HPP
#define MATRIX_HPP

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

  double& operator()(size_t row, size_t col) { return data[row * size + col]; }

  const double& operator()(size_t row, size_t col) const {
    return data[row * size + col];
  }

  void printMatrix() const {
    for (size_t i = 0; i < data.size(); ++i) {
      if ((i % size) == 0 && i != 0) {
        std::cout << "\n";
      }
      std::cout << data[i] << " ";
    }
  }

  Matrix multiply(const Matrix& other) const {
    if (size != other.size) {
      throw std::invalid_argument("The matrix sizes do not match!");
    }

    Matrix result(size);

    // Порядок циклов i-k-j выбран для эфективности, помогает попадать в кеш.
    for (size_t i = 0; i < size; ++i) {
      for (size_t k = 0; k < size; ++k) {
        double temp = operator()(i, k);
        for (size_t j = 0; j < size; ++j) {
          result(i, j) += temp * other(k, j);
        }
      }
    }

    return result;
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