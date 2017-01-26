# About

SlicerRadiomics is an extension for [3D Slicer](http://slicer.org) that
encapsulates [pyradiomics](https://github.com/radiomics/pyradiomics) library,
which in turn implements calculation of a variety of
[radiomics](http://radiomics.github.io) features.

Pending resolution of packaging issues, SlicerRadiomics is not currently 
distributed as an extension via the 3D Slicer ExtensionManager (we expect to
have this resolved in the near future). You can however use this extension if
you build SlicerRadiomics from source.

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

Once the build is completed, you will need to add this path within your extension build tree
`SlicerRadiomics-build/inner-build/lib/Slicer-4.7/qt-scripted-modules` to the 3D
Slicer additional modules path (3D Slicer Settings > Modules > Additional module paths).

# Acknowledgments

This project is supported in part by the National Institutes of Health, National
Cancer Institute [Informatics Technology for Cancer Research (ITCR)
program](https://itcr.nci.nih.gov) via
grant U24 CA194354 (PI Hugo Aerts).
