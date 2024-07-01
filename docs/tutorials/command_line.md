# GeoTrame command line arguments

To use the GeoTrame CLI, be sure to install the Pan3D GeoTrame dependencies first. This includes Trame, a Kitware toolkit for Python servers. Learn more about Trame [here][trame-link].

        pip install pan3d[geotrame]

By default, the command `geotrame`  will launch GeoTrame as a local Python server and open a tab in your default browser and navigate to `localhost:8080`. You can change this behavior in a number of ways. For example, you can disable the browser tab launch by adding `--server` to the command.

In response, `geotrame` will display this message in the terminal:

        App running at:
        - Local:   http://localhost:8080/
        - Network: http://127.0.0.1:8080/

As the message indicates, pointing a browser to http://localhost:8080/ will open the application.

There are other arguments to initialize features and data. Here is the full list:

```bash
--help/-h:        Write command info including the list of options to the terminal and exit.
--server:      Launch in server mode, which disables the default behavior of opening a browser tab on startup.
--dataset:     Pass a string with this argument to specify a target dataset. This value can be either a local path or remote URL. This value must be readable by `xarray.open_dataset()`.
--config_path: Pass a string with this argument to specify a startup configuration. This value must be a local path to a JSON file which adheres to the schema specified in the [Configuration Files documentation](../api/configuration.md). A dataset specified in this configuration will override any value passed to `--dataset`.
--resolution:   Pass a numeric string with this argument to specify a default resolution for rendering data. This value defaults to 128. It is recommended that this value should be a power of 2, but it is not required. If the value is 1 or less, the full image resolution will be used, and interface options will become available for manually adjusting the slicing of each axis individually.
--catalogs:    Pass one or more strings which reference available catalog modules (options include "pangeo", "esgf"). If specified, the Catalog Search interface will become available in the left sidebar. See the Catalog Search Tutorial for more information.
--debug:       Launch in debug mode, which will include more terminal output. Intended for developer use.
```


<!-- Links -->
[trame-link]: https://trameapp.kitware.com/
