# Set the minimum CMake version
cmake_minimum_required(VERSION 3.1.0)

# Set C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_BUILD_TYPE Debug)



# Set warning flags for the compiler
if ( "${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU" )
  add_compile_options(
    -pedantic
    -fPIC
    -Wall
    -Wextra
    -Wcast-align
    # -Wcast-qual
    -Wdisabled-optimization
    -Wformat=2
    -Winit-self
    -Wlogical-op
    -Wmissing-declarations
    -Wmissing-include-dirs
    -Wredundant-decls
    -Wshadow
#    -Wsign-conversion
    -Wstrict-overflow=5
    -Wswitch-default
    -Wundef
    -Werror
    -Wunused-parameter)
#-Wold-style-cast
  set(CMAKE_CXX_FLAGS "-Wctor-dtor-privacy -Wnoexcept  -Woverloaded-virtual -Wsign-promo -Wstrict-null-sentinel -Wsuggest-override -fpermissive")
endif()
if ( "${CMAKE_CXX_COMPILER_ID}" STREQUAL "AppleClang" )
  add_compile_options(-pedantic
    -fPIC
    -Wall
    -Wextra
    -Wcast-align
    -Wcast-qual
    -Wctor-dtor-privacy
    -Wdisabled-optimization
    -Wformat=2
    -Winit-self
    -Wmissing-declarations
    -Wmissing-include-dirs
#    -Wold-style-cast
    -Woverloaded-virtual
    -Wredundant-decls
    -Wshadow
    -Wsign-conversion
    -Wsign-promo
    -Wstrict-overflow=5
    -Wswitch-default
    -Wundef
    -Werror)
endif()
if ( MSVC )
  add_compile_options(/W4 /WX)
endif()

# Add the source to the shared library
add_library(TmpShared SHARED
  IOManager.cpp
  StringUtility.cpp
  popenRWE.c
  CLICodec.cpp
  )



install(
  FILES ${INSTALL_HEADERS}
    DESTINATION include
    COMPONENT devel)

#set(INSTALL_TARGETS
#  PluginCommsTwoSixCore
#  )

install(
  TARGETS ${INSTALL_TARGETS}
  LIBRARY
    DESTINATION lib
  PUBLIC_HEADER
    DESTINATION include)


