################################################################################
#
#  Program: SlicerRadiomics
#
#  Copyright (c) Kitware Inc.
#
#  See LICENSE.txt
#
#  This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
#  and was partially funded by NIH grant 1U24CA194354-01
#
################################################################################

# This CMake module defines the function SlicerRadiomicsAddCLI.

#
# SlicerRadiomicsAddCLI
# =====================
#
# Add a shell script-based Slicer CLI to the build system.
#
# SlicerRadiomicsAddCLI(
#   NAME <module_name>
#   )
#
# NAME This is the name of the CLI to configure and install. It expects the following
#      files to exist in the current directory:
#        <module_name>
#        <module_name>.bat
#        <module_name>.xml
#
# Notes:
#
#  * The function adds a custom target named ``Copy<module_name>Scripts``
#    responsible to copy module files into ``SlicerExecutionModel_DEFAULT_CLI_RUNTIME_OUTPUT_DIRECTORY``.
#
#  * The function adds an install rule associated with ``RuntimeLibraries`` component that will install
#    the module files into ``SlicerExecutionModel_DEFAULT_CLI_INSTALL_RUNTIME_DESTINATION``.
#
#  * The list of module files is composed differently based on the platform:
#    - Unix: <module_name> and <module_name>.xml
#    - Windows: <module_name>, <module_name>.bat and <module_name>.xml
#
function(SlicerRadiomicsAddCLI)
  set(options
    )
  set(oneValueArgs
    NAME
    )
  set(multiValueArgs
    )
  cmake_parse_arguments(MY
    "${options}"
    "${oneValueArgs}"
    "${multiValueArgs}"
    ${ARGN}
    )
  message(STATUS "Configuring SEM CLI module: ${MY_NAME}")

  # Sanity checks
  set(expected_defined_vars
    SlicerExecutionModel_DEFAULT_CLI_RUNTIME_OUTPUT_DIRECTORY
    SlicerExecutionModel_DEFAULT_CLI_INSTALL_RUNTIME_DESTINATION
    )
  foreach(var IN LISTS expected_defined_vars)
    if(NOT DEFINED ${var})
      message(FATAL_ERROR "Variable ${var} is not defined !")
    endif()
  endforeach()

  set(expected_parameters
    NAME
    )
  foreach(param IN ITEMS NAME)
    if(NOT MY_${param})
      message(FATAL_ERROR "Parameter ${param} is expected !")
    endif()
  endforeach()

  set(cli_file "${MY_NAME}.xml" )

  set(cli_script "${MY_NAME}.py")

  set(build_dir ${SlicerExecutionModel_DEFAULT_CLI_RUNTIME_OUTPUT_DIRECTORY}/${CMAKE_CFG_INTDIR})
  set(copy_commands )

  list(APPEND copy_commands
      COMMAND ${CMAKE_COMMAND} -E copy_if_different ${cli_file} ${build_dir}/${cli_file}
      )
  list(APPEND copy_commands
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${cli_script} ${build_dir}/${cli_script}
    )

  add_custom_target(Copy${MY_NAME}Scripts ALL
    ${copy_commands}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Copying ${MY_NAME} files into build directory"
    )

  install(FILES ${cli_file}
    DESTINATION ${SlicerExecutionModel_DEFAULT_CLI_INSTALL_RUNTIME_DESTINATION}
    COMPONENT RuntimeLibraries
    )

  install(PROGRAMS ${cli_script}
    DESTINATION ${SlicerExecutionModel_DEFAULT_CLI_INSTALL_RUNTIME_DESTINATION}
    COMPONENT RuntimeLibraries
    )

  if(NOT WIN32)
    add_custom_target(SetPermissions${MY_NAME}CLI ALL
      COMMAND chmod u+x ${build_dir}/${cli_script}
      WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
      COMMENT "Setting Executable (User) permission for ${cli_script} in build directory"
      DEPENDS Copy${MY_NAME}Scripts
    )
  endif()

endfunction()
