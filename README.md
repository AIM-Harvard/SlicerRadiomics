# About

SlicerRadiomics is an extension for [3D Slicer](http://slicer.org) that
encapsulates [pyradiomics](https://github.com/radiomics/pyradiomics) library,
which in turn implements calculation of a variety of
[radiomics](http://radiomics.github.io) features.

# Install instructions

SlicerRadiomics is currently distributed as an extension via the 3D Slicer ExtensionManager.

Note that due to a known issue #18, the module will fail to load. To fix this issue, you can find the folder called `site-packages` under the location of `SlicerRadiomics` extension installation on your computer to the list of additional directories (Slicer menu "Edit > Application settings > Modules", and restart the application after that.

# Build instructions

In order to build this extension, you need to have a version of Slicer built from source.
You can build Slicer following [the
instructions](https://www.slicer.org/wiki/Documentation/Nightly/Developers/Build_Instructions).
Once you have done that, all you need to do are the following steps:

* Clone the source code of the repository.
```
$ git clone https://github.com/radiomics/SlicerRadiomics.git
```

* Create an empty directory for building the extension
```
$ mkdir SlicerRadiomics-build
```

* Configure the build using cmake (you will have it installed as one of the
   prerequisites for building 3D Slicer)
```
$ cd SlicerRadiomics-build; ccmake ../SlicerRadiomics
```

* Build the extension
```
$ make
```

* Package the extension
```
$ cd inner-build
$ make package
```

Once completed, you can install the [extension from file](https://www.slicer.org/wiki/Documentation/Nightly/SlicerApplication/ExtensionsManager#Installing_an_extension_without_network_connection).

# Acknowledgments

This project is supported in part by the National Institutes of Health, National
Cancer Institute [Informatics Technology for Cancer Research (ITCR)
program](https://itcr.nci.nih.gov) via
grant U24 CA194354 (PI Hugo Aerts).
