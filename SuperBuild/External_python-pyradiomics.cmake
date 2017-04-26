set(proj python-pyradiomics)

# Set dependency list
set(${proj}_DEPENDENCIES "")

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj DEPENDS_VAR ${proj}_DEPENDENCIES)

if(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  # XXX - Add a test checking if <proj> is available
endif()

if(NOT DEFINED ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  set(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj} ${Slicer_USE_SYSTEM_python})
endif()

if(NOT ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})

  if(NOT DEFINED git_protocol)
    set(git_protocol "git")
  endif()

  ExternalProject_SetIfNotDefined(
    ${CMAKE_PROJECT_NAME}_${proj}_GIT_REPOSITORY
    "${git_protocol}://github.com/Radiomics/pyradiomics"
    QUIET
    )

  ExternalProject_SetIfNotDefined(
    ${CMAKE_PROJECT_NAME}_${proj}_GIT_TAG
    "origin/master"
    QUIET
    )

  set(python_pyradiomics_DIR "${CMAKE_BINARY_DIR}/${proj}-install")

  ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    GIT_REPOSITORY "${${CMAKE_PROJECT_NAME}_${proj}_GIT_REPOSITORY}"
    GIT_TAG "${${CMAKE_PROJECT_NAME}_${proj}_GIT_TAG}"
    SOURCE_DIR ${proj}
    BUILD_IN_SOURCE 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ${CMAKE_COMMAND}
      -E env
        PYTHONNOUSERSITE=1
      ${PYTHON_EXECUTABLE} -m pip install . --prefix ${python_pyradiomics_DIR}
    DEPENDS
      ${${proj}_DEPENDENCIES}
    )

  mark_as_superbuild(python_pyradiomics_DIR:PATH)

  #-----------------------------------------------------------------------------
  # Launcher setting specific to build tree

  set(${proj}_PYTHONPATH_LAUNCHER_BUILD
    ${python_pyradiomics_DIR}/${PYTHON_STDLIB_SUBDIR}
    ${python_pyradiomics_DIR}/${PYTHON_STDLIB_SUBDIR}/lib-dynload
    ${python_pyradiomics_DIR}/${PYTHON_SITE_PACKAGES_SUBDIR}
    )
  mark_as_superbuild(
    VARS ${proj}_PYTHONPATH_LAUNCHER_BUILD
    LABELS "PYTHONPATH_LAUNCHER_BUILD"
    )

else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDENCIES})
endif()

