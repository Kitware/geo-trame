# Configuration Files

## Introduction

Pan3D uses JSON files to save an application state for reuse. The UI and the API include access to import and export functions which read and write these configuration files, respectively. This documentation provides guidelines for reading and writing these files manually.

There are four sections available in the configuration file format: `data_origin`, `data_array`, `data_slices`, and `ui`. The values in these sections will be passed to various functions on the current `DatasetBuilder` instance, as referenced in the following sections. See `DatasetBuilder` documentation for details.

## Example

```
{
    "data_origin": "https://ncsa.osn.xsede.org/Pangeo/pangeo-forge/noaa-coastwatch-geopolar-sst-feedstock/noaa-coastwatch-geopolar-sst.zarr",
    "data_array": {
        "active": "analysed_sst",
        "x": "lon",
        "y": "lat",
        "t": "time",
        "t_index": 5
    },
    "data_slices": {
        "lat": [
            -45,
            45,
            100
        ],
        "lon": [
            -90,
            90,
            100
        ]
    },
    "ui": {
        "main_drawer": false,
        "axis_drawer": false,
        "expanded_coordinates": []
    }
}
```

For more example configuration files, visit our [Examples on Github](https://github.com/Kitware/pan3d/tree/main/examples).


## `data_origin` (Required)
The value for this key should be a string containing a local path or remote URL, referencing a target dataset readable by `xarray.open_dataset`. This value will be passed to `DatasetBuilder.set_dataset_path`.

## `data_array` (Required)
The value for this key should be a mapping specifying how to interpret the information in the target dataset. The following table describes keys available in this mapping schema.

| Key | Required? | Type | Value Description |
|-----|-----------|------|-------------------|
|`active`|YES     |`str` |This should be a name of an array that exists in the current dataset. This value will be passed to `DatasetBuilder.set_data_array_active_name`. |
|`x`  |NO (default=None)  |`str`|This should be the name of a coordinate that exists in the active data array. This value will be passed to `DatasetBuilder.set_data_array_axis_names`.|
|`y`  |NO (default=None)  |`str`|This should be the name of a coordinate that exists in the active data array. This value will be passed to `DatasetBuilder.set_data_array_axis_names`.|
|`z`  |NO (default=None)  |`str`|This should be the name of a coordinate that exists in the active data array. This value will be passed to `DatasetBuilder.set_data_array_axis_names`.|
|`t`  |NO (default=None)  |`str`|This should be the name of a coordinate that exists in the active data array. This value will be passed to `DatasetBuilder.set_data_array_axis_names`.|
|`t_index` |NO (default=0)|`int`|The index of the current time slice. Must be an integer >= 0 and < the length of the current time coordinate.This value will be passed to `DatasetBuilder.set_data_array_time_index`.|

## `data_slices` (Optional)
The value for this key should be a mapping of coordinate names (which are likely used as values for `x` | `y` | `z` | `t` in the `data_array` section) to slicing arrays. This mapping will be formatted and passed to `DatasetBuilder.set_data_array_coordinates`.

Each slicing array should be a list of three values `[start, stop, step]`.

`start`: the coordinate value at which the sliced data should start (inclusive)

`stop`: the coordinate value at which the sliced data should stop (exclusive)

`step`: an integer > 0 which represents the number of items to skip when slicing the data (e.g. step=2 represents 0.5 resolution)

## `ui` (Optional)
The value for this key should be a mapping of any number of UI state values. The following table describes keys available in this mapping schema.


| Key | Required? | Type | Value Description |
|-----|-----------|------|-------------------|
|`main_drawer`|NO (default=True)|`bool`|If true, open the lefthand drawer for dataset and data array browsing/selection.|
|`axis_drawer`|NO (default=False)|`bool`|If true, open the righthand drawer for axis assignment/slicing. **Note:** By default, this becomes True when an active data array is selected.|
|`unapplied_changes`|NO (default=False)|`bool`|If true, show "Apply and Render" button, which when clicked will apply any unapplied changes and rerender.|
|`error_message`|NO (default=None)|`str` | `None`|If not None, this string will show as the error message above the render area.|
|`more_info_link`|NO (default=None)|`str` | `None`| If not None, this string should contain a link to more information about the current dataset. This link will appear below the dataset selection box.|
|`expanded_coordinates`|NO (default=`[]`)|`list[str]`|This list should contain the names of all coordinates which should appear expanded in the righthand axis drawer. **Note:** By default, this list is populated with all available coordinate names once the active data array is selected.|