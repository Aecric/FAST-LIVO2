cmake_minimum_required(VERSION 3.10)
project(fast_livo)

set(CMAKE_BUILD_TYPE "Release")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
option(FAST_LIVO_NATIVE_ARCH "Tune binaries for the build host CPU" ON)

# Set common compile options
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pthread -fexceptions")

# Specific settings for Debug build
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0 -g")

# Detect CPU architecture
message(STATUS "Current CPU architecture: ${CMAKE_SYSTEM_PROCESSOR}")

# Specific settings for Release build
if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm|aarch64|ARM|AARCH64)")
  if(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64")
    if(FAST_LIVO_NATIVE_ARCH)
      # 64-bit ARM optimizations (e.g., RK3588 and Jetson Orin NX)
      set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -mcpu=native -mtune=native -ffast-math")
      message(STATUS "Using native 64-bit ARM optimizations")
    else()
      set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -march=armv8-a -ffast-math")
      message(STATUS "Using portable 64-bit ARM optimizations: -march=armv8-a")
    endif()
  else()
    # 32-bit ARM optimizations with NEON support
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -mcpu=native -mtune=native -mfpu=neon -ffast-math")
    message(STATUS "Using 32-bit ARM optimizations: -O3 -mcpu=native -mtune=native -mfpu=neon -ffast-math")
  endif()
  add_definitions(-DARM_ARCH)
else()
  # x86-64 (Intel/AMD) optimizations
  if(FAST_LIVO_NATIVE_ARCH)
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -march=native -mtune=native -funroll-loops") #-flto
    message(STATUS "Using native x86-64 optimizations")
  else()
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -march=x86-64 -mtune=generic -funroll-loops")
    message(STATUS "Using portable x86-64 optimizations: -march=x86-64 -mtune=generic")
  endif()
  add_definitions(-DX86_ARCH)
endif()

# Define project root directory
add_definitions(-DROOT_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}/\")

# Detect CPU core count for potential multithreading optimization
include(ProcessorCount)
ProcessorCount(N)
message(STATUS "Processor count: ${N}")

# Set the number of cores for multithreading
if(N GREATER 4)
  math(EXPR PROC_NUM "4")
  add_definitions(-DMP_EN -DMP_PROC_NUM=${PROC_NUM})
  message(STATUS "Multithreading enabled. Cores: ${PROC_NUM}")
elseif(N GREATER 1)
  math(EXPR PROC_NUM "${N}")
  add_definitions(-DMP_EN -DMP_PROC_NUM=${PROC_NUM})
  message(STATUS "Multithreading enabled. Cores: ${PROC_NUM}")
else()
  add_definitions(-DMP_PROC_NUM=1)
  message(STATUS "Single core detected. Multithreading disabled.")
endif()

# Check for OpenMP support
find_package(OpenMP QUIET)
if(OpenMP_CXX_FOUND)
  message(STATUS "OpenMP found")
  add_compile_options(${OpenMP_CXX_FLAGS})
else()
  message(STATUS "OpenMP not found, proceeding without it")
endif()

# Check for mimalloc support
find_package(mimalloc QUIET)
if(mimalloc_FOUND)
  message(STATUS "mimalloc found")
else()
  message(STATUS "mimalloc not found, proceeding without it")
endif()

# Find ament and required dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(pcl_ros REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(livox_ros_driver2 REQUIRED)
find_package(vikit_common REQUIRED)
find_package(vikit_ros REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(image_transport REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(PCL REQUIRED)
find_package(OpenCV REQUIRED)
find_package(Sophus REQUIRED)
add_compile_definitions(SOPHUS_USE_BASIC_LOGGING=1)
find_package(Boost REQUIRED COMPONENTS thread)
find_package(fmt REQUIRED)

# Include directories for dependencies
include_directories(
  ${EIGEN3_INCLUDE_DIR}
  ${PCL_INCLUDE_DIRS}
  ${OpenCV_INCLUDE_DIRS}
  ${Sophus_INCLUDE_DIRS}
  ${vikit_common_INCLUDE_DIRS}
  ${vikit_ros_INCLUDE_DIRS}
  include
)

set(dependencies
  rclcpp
  rclpy
  geometry_msgs
  nav_msgs
  sensor_msgs
  visualization_msgs
  cv_bridge
  vikit_common
  vikit_ros
  image_transport
  pcl_ros
  pcl_conversions
  tf2_ros
  livox_ros_driver2
)

set(COMMON_DEPENDENCIES OpenMP::OpenMP_CXX fmt::fmt Sophus::Sophus)

# link_directories(${COMMON_DEPENDENCIES}
#   ${vikit_common_LIBRARIES}/libvikit_common.so
#   ${vikit_ros_LIBRARIES}/libvikit_ros.so
# )

# Add libraries
add_library(vio src/vio.cpp src/frame.cpp src/visual_point.cpp)
add_library(lio src/voxel_map.cpp)
add_library(pre src/preprocess.cpp)
add_library(imu_proc src/IMU_Processing.cpp)
add_library(laser_mapping src/LIVMapper.cpp)
add_library(utils src/utils.cpp)

ament_target_dependencies(vio ${dependencies} )
ament_target_dependencies(lio ${dependencies})
ament_target_dependencies(pre ${dependencies})
ament_target_dependencies(imu_proc ${dependencies})
ament_target_dependencies(laser_mapping ${dependencies})

# Find vikit shared libraries explicitly (vikit_common_LIBRARIES is empty in its config)
find_library(VIKIT_COMMON_LIB vikit_common
  HINTS
    ${CMAKE_PREFIX_PATH}
    ${CMAKE_SOURCE_DIR}/../../install/vikit_common
    ${CMAKE_SOURCE_DIR}/../../rpg_vikit/vikit_common
    /home/anaple/slamtest/install/vikit_common
    ./install/vikit_common
    /usr/local
  PATH_SUFFIXES lib
)
find_library(VIKIT_ROS_LIB vikit_ros
  HINTS
    ${CMAKE_PREFIX_PATH}
    ${CMAKE_SOURCE_DIR}/../../install/vikit_ros
    /home/anaple/slamtest/install/vikit_ros
    /usr/local
  PATH_SUFFIXES lib
)
if(NOT VIKIT_COMMON_LIB)
  message(FATAL_ERROR "libvikit_common.so not found. Build vikit_common first.")
endif()
if(NOT VIKIT_ROS_LIB)
  message(FATAL_ERROR "libvikit_ros.so not found. Build vikit_ros first.")
endif()
message(STATUS "Found vikit_common: ${VIKIT_COMMON_LIB}")
message(STATUS "Found vikit_ros:    ${VIKIT_ROS_LIB}")

# linking libraries or executables to public dependencies
target_link_libraries(laser_mapping
    ${VIKIT_COMMON_LIB}
    ${VIKIT_ROS_LIB}
    ${COMMON_DEPENDENCIES}
)
target_link_libraries(vio ${COMMON_DEPENDENCIES})
target_link_libraries(lio utils ${COMMON_DEPENDENCIES})
target_link_libraries(pre ${COMMON_DEPENDENCIES})
target_link_libraries(imu_proc ${COMMON_DEPENDENCIES})

# Add the main executable
add_executable(fastlivo_mapping src/main.cpp)

ament_target_dependencies(fastlivo_mapping ${dependencies})

# Link libraries to the executable
target_link_libraries(fastlivo_mapping
  laser_mapping
  vio
  lio
  pre
  imu_proc
  ${PCL_LIBRARIES}
  ${OpenCV_LIBRARIES}
  ${Sophus_LIBRARIES}
  ${Boost_LIBRARIES}
)

# Link mimalloc if found
if(mimalloc_FOUND)
  target_link_libraries(fastlivo_mapping mimalloc)
endif()

# Install the executable
install(TARGETS
  fastlivo_mapping
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY config launch rviz_cfg
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_odin_preprocess test/test_odin_preprocess.cpp)
  target_link_libraries(test_odin_preprocess pre)
  ament_target_dependencies(test_odin_preprocess sensor_msgs)
endif()

# Export dependencies
ament_export_dependencies(
  rclcpp
  rclpy
  geometry_msgs
  nav_msgs
  sensor_msgs
  pcl_ros
  pcl_conversions
  tf2_ros
  livox_ros_driver2
  Eigen3
  PCL
  OpenCV 
  Sophus
)

ament_package()
