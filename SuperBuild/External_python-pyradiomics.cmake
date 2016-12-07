# Project that will add pyradiomics
set(proj pyradiomics)

#------------------------------------------------------------------------------
# Put CMake in the path

include(ExternalProjectForNonCMakeProject)

get_filename_component(CMAKE_COMMAND_DIR "${CMAKE_COMMAND}" DIRECTORY)

set(pathsep ":")
if(WIN32)
  set(pathsep ";")
endif()
# environment
set(_env_script ${CMAKE_BINARY_DIR}/${proj}_Env.cmake)
MESSAGE(STATUS "env script = ${_env_script}")
ExternalProject_Write_SetBuildEnv_Commands(${_env_script})
ExternalProject_Write_SetPythonSetupEnv_Commands(${_env_script} APPEND)
file(APPEND ${_env_script}
"#------------------------------------------------------------------------------
# Added by '${CMAKE_CURRENT_LIST_FILE}'
set(ENV{PATH} \"${CMAKE_COMMAND_DIR}${pathsep}$ENV{PATH}\")
")

# Build the full path to setup.py
set(SETUPPATH "${CMAKE_BINARY_DIR}/${proj}")
message(STATUS "External_pyradiomics: path to setup.py = ${SETUPPATH}")
set(INSTALL_COMMAND ${PYTHON_EXECUTABLE} ${SETUPPATH}/setup.py install -G ${CMAKE_GENERATOR})


if(NOT DEFINED git_protocol)
  set(git_protocol "git")
endif()

# ToDo: update this when the repo is public and the branch with CMakeLists
# has been integrated
set(git_protocol "https")
# Select the master branch by default
# set (tag master)
# set (repo "${git_protocol}://github.com/Radiomics/${proj}.git")
set(tag c-matrices)
set(repo "${git_protocol}://github.com/JoostJM/${proj}.git")

# Install pyradiomics
ExternalProject_Add(python-${proj}
    GIT_REPOSITORY ${repo}
    GIT_TAG ${tag}
    SOURCE_DIR ${CMAKE_BINARY_DIR}/${proj}
    # Building in source allows the install command to work as you need to be in the
    # directory with setup.py for it to work correctly
    BUILD_IN_SOURCE 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ${INSTALL_COMMAND}
    )

# pyradiomics gets installed where the SlicerPyhon can find it
get_filename_component(PYTHON_LIB_DIR "${PYTHON_LIBRARY}" DIRECTORY)
set(PYTHON_PACKAGES_DIR "${PYTHON_LIB_DIR}/python2.7/site-packages")
MESSAGE(STATUS "Setting proj dir, python lib dir = ${PYTHON_LIB_DIR}, PYTHON_PACKAGES_DIR = ${PYTHON_PACKAGES_DIR}")

set(${proj}_DIR ${PYTHON_PACKAGES_DIR})
mark_as_superbuild(${proj}_DIR:PATH)
