# SlicerRadiomics
A Slicer extension wrapping pyradiomics.

This relies on the pyradiomics repository:
https://github.com/Radiomics/pyradiomics
First developed in conjunction with a branch that includes a CMakeLists.txt file:
https://github.com/JoostJM/pyradiomics/tree/c-matrices

In order to build this extension, beyond having a version of Slicer available to build
against, the following are requirements (written for Mac):

- The path to the Slicer python executable:
  [path to Slicer top level build]/python-install/bin/SlicerPython

- Install scikit for the Slicer version of python:
  Download at least version 0.4-2.0. You can get it from https://github.com/scikit-build/scikit-build/archive/9ee9f6f.tar.gz or use the master: https://github.com/scikit-build/scikit-build/archive/master.tar.gz
  Expand the tar.gz
  cd into the directory that includes setup.py
  [path to]/SlicerPython setup.py install

- Install CMake if you didn't already use it to build Slicer
  pip install cmake

- Use cmake to configure and generate make files for SlicerRadiomics, make sure thate Slicer_DIR is set to the Slicer build you installed scikit to.

- make. The pyradiomics package will get installed in the Slicer python install directory. You can then add the Slicer Radiomics extension as a Qt scripted module.
