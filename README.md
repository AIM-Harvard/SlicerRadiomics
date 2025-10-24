# About

SlicerRadiomics is an extension for [3D Slicer](http://slicer.org) that
encapsulates [pyradiomics](https://github.com/radiomics/pyradiomics) library that calculates a variety of
[radiomics](https://www.radiomics.io/) features.

See list and detailed description of computed features in **[pyradiomics library documentation](http://pyradiomics.readthedocs.io/en/latest/features.html)**.

If you publish any work which uses this package, please cite the following publication: 

_van Griethuysen, J. J. M., Fedorov, A., Parmar, C., Hosny, A., Aucoin, N., Narayan, V., Beets-Tan, R. G. H., Fillon-Robin, J. C., Pieper, S., Aerts, H. J. W. L. (2017). Computational Radiomics System to Decode the Radiographic Phenotype. Cancer Research, 77(21), e104–e107. [https://doi.org/10.1158/0008-5472.CAN-17-0339](https://doi.org/10.1158/0008-5472.CAN-17-0339)_

# Install instructions

SlicerRadiomics is currently distributed as an extension via the 3D Slicer ExtensionManager.
Follow these steps to install the extension:
1. Download the latest **nightly** release for your platform from http://download.slicer.org.
**Do NOT use installers tagged as "Stable Release"!**
If you use Mac, make sure you move the Slicer application to the Applications folder on your computer before launching it!
2. Once installed, open Extension Manager by clicking the icon as shown below.
![](https://qiicr.gitbooks.io/quantitativereporting-guide/content/docs/screenshots/extension_manager.png)
3. Search for `Radiomics` and install the extension by clicking the INSTALL
   button.
4. Once installation of `Radiomics` and dependencies is completed,
   you will need to restart Slicer application to access the module.
   If installation was successful, you should be able to see
   `Radiomics` module in the Slicer module list.

# Building `SlicerRadiomics` from source

In order to build this extension, you need to have a version of Slicer built from source.
You can build Slicer following [the
instructions](https://www.slicer.org/wiki/Documentation/Nightly/Developers/Build_Instructions).
Once you have done that, all you need to do are the following steps:

* Clone the source code of the repository.
```
$ git clone https://github.com/radiomics/SlicerRadiomics.git
```

* Create an empty directory for building the extension.
```
$ mkdir SlicerRadiomics-build
```

* Configure the build using cmake.
```
$ cd SlicerRadiomics-build
$ cmake -DSlicer_DIR:PATH=/path/to/Slicer-Release/Slicer-build ../SlicerRadiomics
```

* Build the extension.
```
$ make
```

*Note: cmake is one of the prerequisites for building 3D Slicer*

# Loading `SlicerRadiomics` from a build tree

There are two options:

## Start Slicer specifying command-line options

* Specify additonal launcher setting and module path.

```
cd SlicerRadiomics-build/inner-build/
build_dir=$pwd

./Slicer \
  --launcher-additional-settings $build_dir/AdditionalLauncherSettings.ini \
  --additional-module-path $build_dir
```

* Open `SlicerRadiomics` module.

## Package, install and restart Slicer

* Package the extension.
```
$ cd inner-build
$ make package
```

* Once completed, you can install the [extension from file](https://www.slicer.org/wiki/Documentation/Nightly/SlicerApplication/ExtensionsManager#Installing_an_extension_without_network_connection).

* Restart Slicer and open `SlicerRadiomics` module.

# Support

If you found a bug, or to report a reproducible problem, [submit an
issue](https://github.com/Radiomics/SlicerRadiomics/issues/new).

If you have a question about using the extension, please ask on the [Radiomics community section of the 3D Slicer Discourse](https://discourse.slicer.org/c/community/radiomics).

# Acknowledgments

This project is supported in part by the National Institutes of Health, National
Cancer Institute [Informatics Technology for Cancer Research (ITCR)
program](https://itcr.nci.nih.gov) via
grant U24 CA194354 (PI Hugo Aerts).
