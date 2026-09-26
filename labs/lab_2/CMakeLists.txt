cmake_minimum_required(VERSION 3.30)
project(pp_lab_2)



add_executable(${PROJECT_NAME} src/main.cpp)






target_include_directories(${PROJECT_NAME} 
    PRIVATE 
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

find_package(OpenMP REQUIRED)
if(NOT OpenMP_CXX_FOUND)
	message(SEND_ERROR "Failed to find OpenMP.")
	return()
else()
	include_directories(${OpenMP_INCLUDE_DIRS})
    message("OpenMP FOUND dir is ${OpenMP_INCLUDE_DIRS}.")
endif()
set(CMAKE_CXX_FLAGS "-fopenmp")

target_link_libraries(${PROJECT_NAME} OpenMP::OpenMP_CXX)

if(MSVC)
    target_compile_options(pp_lab_2 PRIVATE /EHsc)
endif()
