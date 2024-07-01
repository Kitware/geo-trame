# Configuration Files

## Introduction

Pan3D uses JSON files to save an application state for reuse. The GeoTrame UI and the Pan3D DatasetBuilder API include access to import and export functions which read and write these configuration files, respectively. This documentation provides guidelines for reading and writing these files manually.

There are five sections available in the configuration file format: `data_origin`, `data_array`, `data_slices`, `ui`, and `render`. The values in these sections will be passed to various attributes on the current `DatasetBuilder` instance and, if applicable, the corresponding `DatasetViewer` instance state.

## Example

```
{
    "data_origin": "https://ncsa.osn.xsede.org/Pangeo/pangeo-forge/noaa-coastwatch-geopolar-sst-feedstock/noaa-coastwatch-geopolar-sst.zarr",
    "data_array": {
        "name": "analysed_sst",
        "x": "lon",
        "y": "lat",
        "t": "time",
        "t_index": 5
    },
    "data_slices": {
        "lon": [1000, 6000, 20],
        "lat": [500, 3000, 20],
    },
    "ui": {
        "main_drawer": false,
        "axis_drawer": false,
        "expanded_coordinates": []
    },
    "render": {
        "auto": false,
        "x_scale": 1,
        "y_scale": 1,
        "z_scale": 1,
        "scalar_warp": false,
        "cartographic": false,
        "transparency": false,
        "transparency_function": "linear",
        "colormap": "viridis"
    }
}
```

For more example configuration files, visit our [Examples on Github](https://github.com/Kitware/pan3d/tree/main/examples).


## `data_origin` (Required)
The value for this key may be a string or dictionary. If this value is a string, it should contain a local path or remote URL referencing a target dataset readable by `xarray.open_dataset`. If this value is a dictionary, it should adhere to the following schema.

| Key | Required? | Type | Value Description |
|-----|-----------|------|-------------------|
| `source` | NO (default="default") | `str` | A string specifying a module to interpret the value for `id`. Options include "default", "xarray", "pangeo", "esgf". |
| `id` | YES | `str` | A unique identifier of the target dataset. Depending on the value for `source`, this may be a path, url, name, or other unique id. |

## `data_array` (Required)
The value for this key should be a mapping specifying how to interpret the information in the target dataset. The following table describes keys available in this mapping schema.

| Key | Required? | Type | Value Description |
|-----|-----------|------|-------------------|
|`name`|YES     |`str` |The field that will be mapped onto a mesh for rendering. This should be a name of an array that exists in the current dataset. This value will be passed to `DatasetBuilder.data_array_name`. |
|`x`  |NO (default=None)  |`str`|The world coordinate value along X describing the grid/mesh. This should be the name of a coordinate that exists in the data array. This value will be passed to `DatasetBuilder.set_data_array_axis_names`.|
|`y`  |NO (default=None)  |`str`|The world coordinate value along Y describing the grid/mesh. This should be the name of a coordinate that exists in the data array. This value will be passed to `DatasetBuilder.set_data_array_axis_names`.|
|`z`  |NO (default=None)  |`str`|The world coordinate value along Z describing the grid/mesh. This should be the name of a coordinate that exists in the data array. This value will be passed to `DatasetBuilder.set_data_array_axis_names`.|
|`t`  |NO (default=None)  |`str`|The coordinate name that represents slices of data, which may be time. Unlike other axes, this axis can only show one index at a time. This should be the name of a coordinate that exists in the data array. This value will be passed to `DatasetBuilder.set_data_array_axis_names`.|
|`t_index` |NO (default=0)|`int`|The index of the current time slice. Must be an integer >= 0 and < the length of the current time coordinate.This value will be passed to `DatasetBuilder.set_data_array_time_index`.|

## `data_slices` (Optional)
The value for this key should be a mapping of coordinate names (which are likely used as values for `x` | `y` | `z` | `t` in the `data_array` section) to slicing arrays. This mapping will be formatted and passed to `DatasetBuilder.set_data_array_coordinates`.

Each slicing array should be a list of three values `[start, stop, step]`.

`start`: the index at which the sliced data should start (inclusive)

`stop`: the index at which the sliced data should stop (exclusive)

`step`: an integer > 0 which represents the number of items to skip when slicing the data (e.g. step=2 represents 0.5 resolution)

## `ui` (Optional)
The value for this key should be a mapping of any number of UI state values. The following table describes keys available in this mapping schema.


| Key | Required? | Type | Value Description |
|-----|-----------|------|-------------------|
|`main_drawer`|NO (default=False)|`bool`|If true, open the lefthand drawer for dataset and data array browsing/selection.|
|`axis_drawer`|NO (default=False)|`bool`|If true, open the righthand drawer for axis assignment/slicing. **Note:** By default, this becomes True when a data array is selected.|
|`unapplied_changes`|NO (default=False)|`bool`|If true, show "Apply and Render" button, which when clicked will apply any unapplied changes and rerender.|
|`error_message`|NO (default=None)|`str`|If not None, this string will show as the error message above the render area.|
|`more_info_link`|NO (default=None)|`str`|If not None, this string should contain a link to more information about the current dataset. This link will appear below the dataset selection box.|
|`expanded_coordinates`|NO (default=`[]`)|`list[str]`|This list should contain the names of all coordinates which should appear expanded in the righthand axis drawer. **Note:** By default, this list is populated with all available coordinate names once the data array is selected.|


## `render` (Optional)
The value for this key should be a mapping of any number of render state values. The following table describes keys available in this mapping schema.

| Key | Required? | Type | Value Description |
|-----|-----------|------|-------------------|
|`auto`|NO (default=True)|`bool`|If true, apply changes and rerender every time a configuration change is made.|
|`x_scale`|NO (default=1)|`int`|The relative scale of the X axis in the rendered scene.|
|`y_scale`|NO (default=1)|`int`|The relative scale of the Y axis in the rendered scene.|
|`z_scale`|NO (default=1)|`int`|The relative scale of the Z axis in the rendered scene.|
|`scalar_warp`|NO (default=False)|`bool`|If true, Apply scalar warping to the rendered mesh (extrude values in z-axis proportional to their magnitude).|
|`cartographic`|NO (default=False)|`bool`|If true, render the data wrapped around an earth sphere.|
|`transparency`|NO (default=False)|`bool`|If true, enable transparency mode for the rendered mesh, applying the current transparency function.|
|`transparency_function`|NO (default="linear")|`str`|The name of the transparency function to apply when transparency is enabled. Options are "linear", "linear_r", "geom", "geom_r", "sigmoid", and "sigmoid_r".|
|`colormap`|NO (default="viridis")|`str`|The name of the colormap to apply to the rendered mesh. Any matplotlib colormap name is a valid value.|
