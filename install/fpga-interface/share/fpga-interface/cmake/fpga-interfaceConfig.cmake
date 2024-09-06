# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_fpga-interface_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED fpga-interface_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(fpga-interface_FOUND FALSE)
  elseif(NOT fpga-interface_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(fpga-interface_FOUND FALSE)
  endif()
  return()
endif()
set(_fpga-interface_CONFIG_INCLUDED TRUE)

# output package information
if(NOT fpga-interface_FIND_QUIETLY)
  message(STATUS "Found fpga-interface: 0.0.0 (${fpga-interface_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'fpga-interface' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${fpga-interface_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(fpga-interface_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${fpga-interface_DIR}/${_extra}")
endforeach()
