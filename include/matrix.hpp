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
};

#endif