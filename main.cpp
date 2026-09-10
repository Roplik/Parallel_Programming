#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

#include "matrix.hpp"

int main() {
  Matrix first{"test.txt"};
  Matrix second{"test.txt"};

  Matrix result = first.multiply(second);
  result.saveToFile("result.txt");
  return 0;
}