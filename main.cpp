#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include "matrix.hpp"

int main() {
  Matrix math{"test.txt"};
  std::cout << math(0, 0) << std::endl;
  return 0;
}