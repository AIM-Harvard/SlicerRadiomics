set(proj python-pyyaml)

# Set dependency list
set(${proj}_DEPENDENCIES "")

if(NOT DEFINED ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  set(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj} ${${CMAKE_PROJECT_NAME}_USE_SYSTEM_python})
endif()

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj DEPENDS_VAR ${proj}_DEPENDENCIES)

if(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  ExternalProject_FindPythonPackage(
    MODULE_NAME "yaml"
    REQUIRED
    )
endif()

if(NOT ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})

  set(_version "3.12")

  ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    URL "https://pypi.python.org/packages/4a/85/db5a2df477072b2902b0eb892feb37d88ac635d36245a72a6a69b23b383a/PyYAML-${_version}.tar.gz"
    URL_MD5 "4c129761b661d181ebf7ff4eb2d79950"
    SOURCE_DIR ${proj}
    BUILD_IN_SOURCE 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ${PYTHON_EXECUTABLE} setup.py --without-libyaml install
    DEPENDS
      ${${proj}_DEPENDENCIES}
    )

  ExternalProject_GenerateProjectDescription_Step(${proj}
    VERSION ${_version}
    )

else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDENCIES})
endif()
