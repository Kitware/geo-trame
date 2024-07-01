# How to use Pan3D and GeoTrame in a Jupyter Notebook

Running Pan3D in a Jupyter notebook allows data scientists to incorporate the tool into their existing workflows and can facilitate greater collaboration between teammates. This tutorial assumes you have a running Jupyter notebook. You can find examples at [notebook examples][notebook-examples-link] in the Pan3D code repository. You can run these examples on Binder [here][binder-link].

![](../images/20.png)

1. In your current kernel, install Pan3D:

        pip install pan3d[all]

2. In the first cell of your notebook, initialize Pan3D’s DatasetBuilder and GeoTrame.

        from pan3d import DatasetBuilder
        builder = DatasetBuilder()
        geotrame = builder.viewer

3. Prepare a configuration for the builder to import. This can come from a previously exported Pan3D configuration file. An example of this is shown in [`example_config_xarray.json`][config-xarray-link]:

        from pan3d import DatasetBuilder
        config_path = '../example_config_xarray.json'
        builder = DatasetBuilder()
        builder.import_config(config_path)

4. You can alternatively create a configuration dictionary. See [`url_config.ipynb`][url-config-notebook-link] for an example of this:

        from pan3d import DatasetBuilder
        config = {
            'data_origin': 'https://ncsa.osn.xsede.org/Pangeo/pangeo-forge/noaa-coastwatch-geopolar-sst-feedstock/noaa-coastwatch-geopolar-sst.zarr',
            'data_array': {
                'name': 'analysed_sst',
                'x': 'lon',
                'y': 'lat',
                't': 'time',
            },
            'data_slices': {
                'lon': [1000, 6000, 20],
                'lat': [500, 3000, 20],
            },
        }
        builder = DatasetBuilder()
        builder.import_config(config)

5. If you’d like finer control of the configuration process, you can call individual state setters on the builder by referring to the [API documentation](../api/dataset_builder.md) for the `DatasetBuilder` class. Refer to `manual_config.ipynb` for an example using these API methods:

        builder = DatasetBuilder()
        builder.dataset_path = '../example_dataset.nc'
        builder.data_array_name = 'density'
        builder.x = 'length'
        builder.y = 'width'
        builder.z = 'height'
        builder.t = 'second'
        builder.t_index = 2

6. After configuring the builder instance, you can show GeoTrame as cell output.

        geotrame = builder.viewer
        await geotrame.ready
        geotrame.ui

7. If you’d like to do more advanced rendering than GeoTrame allows, you can still use the DatasetBuilder class for mesh preparation. You can access the mesh with `builder.mesh` and use it in a PyVista rendering pipeline. Refer to `advanced_pyvista_rendering.ipynb` for an example of this technique, which leverages PyVista plotting to generate an animated GIF of timesteps in the dataset.


[notebook-examples-link]: https://github.com/Kitware/pan3d/tree/main/examples/jupyter
[binder-link]: https://mybinder.org/v2/gh/Kitware/pan3d/main?labpath=examples%2Fjupyter
[config-xarray-link]: https://github.com/Kitware/pan3d/blob/main/examples/example_config_xarray.json
[url-config-notebook-link]: https://github.com/Kitware/pan3d/blob/main/examples/jupyter/url_config.ipynb
