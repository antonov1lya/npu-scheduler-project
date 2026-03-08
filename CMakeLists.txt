cmake_minimum_required(VERSION 3.10.0)
project(npu_scheduler VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3")

add_executable(npu_scheduler src/main.cpp)
