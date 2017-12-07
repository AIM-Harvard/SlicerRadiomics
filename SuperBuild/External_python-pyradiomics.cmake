set(proj python-pyradiomics)

# Set dependency list
set(${proj}_DEPENDENCIES "")

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj DEPENDS_VAR ${proj}_DEPENDENCIES)

if(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  ExternalProject_FindPythonPackage(
    MODULE_NAME "pyradiomics"
    REQUIRED
    )
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

  set(wrapper_script)
  if(MSVC)
    find_package(Vcvars REQUIRED)
    set(wrapper_script ${Vcvars_WRAPPER_BATCH_FILE})
  endif()

  # Alternative python prefix for installing extension python packages
  set(python_packages_DIR "${CMAKE_BINARY_DIR}/python-packages-install")
  file(TO_NATIVE_PATH ${python_packages_DIR} python_packages_DIR_NATIVE_DIR)

  set(_install_pyyaml)
  set(_no_binary "")

  if(WIN32)
    # Install PyYAML without libyaml to ensure it can be imported.
    set(_install_pyyaml COMMAND ${CMAKE_COMMAND}
      -E env
        PYTHONNOUSERSITE=1
      ${PYTHON_EXECUTABLE} -m pip install PyYAML>=3.12 --global-option=--without-libyaml
        --prefix ${python_packages_DIR_NATIVE_DIR}
      )
    # Build "PyWavelets" from source to ensure it can be imported
    set(_no_binary --no-binary "PyWavelets")
  endif()

  # Install pyradiomics and its requirement
  set(_install_pyradiomics COMMAND ${CMAKE_COMMAND}
      -E env
        PYTHONNOUSERSITE=1
      ${wrapper_script} ${PYTHON_EXECUTABLE} -m pip install . ${_no_binary}
        --prefix ${python_packages_DIR_NATIVE_DIR}
    )

  ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    GIT_REPOSITORY "${${CMAKE_PROJECT_NAME}_${proj}_GIT_REPOSITORY}"
    GIT_TAG "${${CMAKE_PROJECT_NAME}_${proj}_GIT_TAG}"
    SOURCE_DIR ${proj}
    BUILD_IN_SOURCE 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ${CMAKE_COMMAND} -E  echo_append ""
    ${_install_pyyaml}
    ${_install_pyradiomics}
    DEPENDS
      ${${proj}_DEPENDENCIES}
    )

  ExternalProject_GenerateProjectDescription_Step(${proj})

  #-----------------------------------------------------------------------------
  # Launcher setting specific to build tree
  set(${proj}_PYTHONPATH_LAUNCHER_BUILD
    ${python_packages_DIR}/${PYTHON_STDLIB_SUBDIR}
    ${python_packages_DIR}/${PYTHON_STDLIB_SUBDIR}/lib-dynload
    ${python_packages_DIR}/${PYTHON_SITE_PACKAGES_SUBDIR}
    )
  mark_as_superbuild(
    VARS ${proj}_PYTHONPATH_LAUNCHER_BUILD
    LABELS "PYTHONPATH_LAUNCHER_BUILD"
    )

  mark_as_superbuild(python_packages_DIR:PATH)

else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDENCIES})
endif()
