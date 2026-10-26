cmake_minimum_required(VERSION 3.18)
project(pp_lab_4 LANGUAGES CXX CUDA)

set(CMAKE_CUDA_ARCHITECTURES 86)

add_executable(${PROJECT_NAME} src/main.cu)

# Оптимизация для релизной сборки
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(${PROJECT_NAME} PRIVATE $<$<COMPILE_LANGUAGE:CUDA>:-O3>)
endif()