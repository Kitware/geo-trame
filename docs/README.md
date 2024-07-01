# Pan3D

<img style="display: inline-block;" src="images/kitware.svg" alt="Kitware Logo" href="https://kitware.com" width="100">

[![Documentation Status][docs-image]][docs-link]
[![Binder][binder-image]][binder-link]
[![Build Status][GHAction-image]][GHAction-link]
[![PyPI Version][pypi-v-image]][pypi-v-link]
[![License][apache-license-image]][license-link]

Pan3D aims to be an utility package for viewing and processing a wide variety of multidimensional datasets. Any dataset that can be interpreted with [xarray][xarray-link] can be explored and rendered with Pan3D.

GeoTrame is a Pan3D application focused on geospatial rendering use cases. This is a graphical user interface leveraging the Pan3D infrastructure to help geospatial scientists explore data.

![](images/0.png)

For an introduction to this project, check out our [blog post][blog-post-link].


## Installation

**Recommended**: To install all requirements, including optional packages:

    pip install pan3d[all]

To install requirements for the Pan3D DatasetBuilder class only:

    pip install pan3d

To install requirements for the GeoTrame user interface:

    pip install pan3d[geotrame]

**Optional**: to install requirements for Pangeo and ESGF catalogs, respectively:

    pip install pan3d[pangeo]

    pip install pan3d[esgf]

## Quick Start

`geotrame` is the main entrypoint for launching GeoTrame locally. Below are some example usages.

To launch GeoTrame without a target dataset to browse XArray examples:

    geotrame

To launch GeoTrame with a local path to a target dataset:

    geotrame --dataset=/path/to/dataset.zarr

To launch GeoTrame with a remote URL to a target dataset:

    geotrame --dataset=https://host.org/link/to/dataset.zarr

To launch GeoTrame with a compatible configuration file (see [examples][examples-link]):

    geotrame --config_path=/path/to/pan3d_state.json

To launch GeoTrame with the option to browse the Pangeo and ESGF Dataset Catalogs (see [Catalogs Tutorial](tutorials/catalogs.md)):

    geotrame --catalogs pangeo esgf

Or you may specify only one catalog:

    geotrame --catalogs pangeo

    geotrame --catalogs esgf


> The `geotrame` entrypoint will automatically launch your default browser to open `localhost:8080`.
>
> To launch without opening your browser, add the `--server` argument to your command.


## Tutorials

- [How to use GeoTrame](tutorials/dataset_viewer.md)
- [GeoTrame command line](tutorials/command_line.md)
- [Catalogs Tutorial](tutorials/catalogs.md)
- [How to use Pan3D in a Jupyter notebook](tutorials/jupyter_notebook.md)

## Examples

Pan3D comes with a set of example configuration files and example Jupyter notebooks in the [examples][examples-link] folder. You can checkout the repository to run these locally, or you can use the [Pan3D Binder instance][binder-link] to run these examples.


<!-- Links -->
[docs-image]: https://readthedocs.org/projects/pan3d/badge/?version=latest
[docs-link]: https://pan3d.readthedocs.io/en/latest
[binder-image]: https://mybinder.org/badge_logo.svg
[binder-link]: https://mybinder.org/v2/gh/Kitware/pan3d/main?labpath=examples%2Fjupyter
[GHAction-image]: https://github.com/Kitware/pan3d/workflows/Test/badge.svg
[GHAction-link]: https://github.com/Kitware/pan3d/actions?query=event%3Apush+branch%3Amain
[pypi-v-image]: https://img.shields.io/pypi/v/pan3d.svg
[pypi-v-link]: https://pypi.org/project/pan3d/
[apache-license-image]: https://img.shields.io/badge/license-Apache%202-blue.svg
[license-link]: https://raw.githubusercontent.com/Kitware/pan3d/main/LICENSE
[xarray-link]: https://docs.xarray.dev/en/stable/user-guide/io.html
[blog-post-link]: https://www.kitware.com/kitware-introduces-pan3d-a-collaborative-interoperable-visualization-tool/
[examples-link]: https://github.com/Kitware/pan3d/tree/main/examples
