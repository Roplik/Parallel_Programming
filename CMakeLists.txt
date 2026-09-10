cmake_minimum_required(VERSION 3.30)
project(pp_lab_1)



add_executable(${PROJECT_NAME} main.cpp)





target_include_directories(${PROJECT_NAME} 
    PRIVATE 
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)