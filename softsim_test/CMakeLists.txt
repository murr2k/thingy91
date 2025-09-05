cmake_minimum_required(VERSION 3.20.0)

# Explicitly add onomondo-softsim module
list(APPEND ZEPHYR_EXTRA_MODULES ${CMAKE_CURRENT_SOURCE_DIR}/../../../ncs/v3.1.0/modules/lib/onomondo-softsim)

# Force use of our custom static partition map
set(PM_STATIC_YML_FILE ${CMAKE_CURRENT_SOURCE_DIR}/pm_static.yml CACHE INTERNAL "")

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(softsim_working)

target_sources(app PRIVATE src/main.c)