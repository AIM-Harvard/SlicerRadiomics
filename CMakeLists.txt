cmake_minimum_required(VERSION 3.1)

project(SlicerRadiomics)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/Radiomics")
set(EXTENSION_CATEGORY "Informatics")
set(EXTENSION_CONTRIBUTORS "Andrey Fedorov (SPL), Joost van Griethuysen (NKI), Nicole Aucoin (SPL), Jean-Christophe Fillion-Robin (Kitware), Steve Pieper (Isomics), Hugo Aerts (DFCI)")
set(EXTENSION_DESCRIPTION "Radiomics extension provides a 3D Slicer interface to the pyradiomics library. pyradiomics is an open-source python package for the extraction of Radiomics features from medical imaging.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/AIM-Harvard/SlicerRadiomics/master/resources/radiomics_icon128.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/AIM-Harvard/SlicerRadiomics/master/resources/SlicerRadiomics-lung.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)

set(SUPERBUILD_TOPLEVEL_PROJECT inner)

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)

find_package(Git REQUIRED)
mark_as_superbuild(GIT_EXECUTABLE)

#-----------------------------------------------------------------------------
# SuperBuild setup
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()

#-----------------------------------------------------------------------------
list(INSERT CMAKE_MODULE_PATH 0 ${CMAKE_CURRENT_SOURCE_DIR}/cmake)
include(SlicerRadiomicsAddCLI)

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(SlicerRadiomics)
add_subdirectory(SlicerRadiomicsCLI)
## NEXT_MODULE

#-----------------------------------------------------------------------------
# Install extension python packages
install(CODE "message(\"CPack: - Install directory: ${python_packages_DIR}\")")
install(
    DIRECTORY "${python_packages_DIR}/"
    DESTINATION ${Slicer_INSTALL_ROOT}${Slicer_BUNDLE_EXTENSIONS_LOCATION}
    COMPONENT RuntimeLibraries
    )

#-----------------------------------------------------------------------------
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
include(${Slicer_EXTENSION_CPACK})
