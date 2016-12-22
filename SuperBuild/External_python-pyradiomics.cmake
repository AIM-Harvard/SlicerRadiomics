# Project that will add pyradiomics
set(proj pyradiomics)

#------------------------------------------------------------------------------
# Put CMake in the path

include(ExternalProjectForNonCMakeProject)

get_filename_component(CMAKE_COMMAND_DIR "${CMAKE_COMMAND}" DIRECTORY)

# Build the full path to setup.py
set(SETUPPATH "${CMAKE_BINARY_DIR}/${proj}")
message(STATUS "External_pyradiomics: path to setup.py = ${SETUPPATH}")
set(INSTALL_COMMAND ${PYTHON_EXECUTABLE} ${SETUPPATH}/setup.py install)



if(NOT DEFINED git_protocol)
  set(git_protocol "git")
endif()

# ToDo: remove hard coded git protocol this when the repo is public
set(git_protocol "https")
# Select the master branch by default
set (tag master)
set (repo "${git_protocol}://github.com/Radiomics/${proj}.git")

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
