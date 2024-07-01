import json
import tempfile
from pathlib import Path
import pytest

from pan3d import DatasetBuilder


def test_import_config():
    builder = DatasetBuilder()
    builder.import_config("examples/example_config_noaa.json")
    # With slicing, data_array has shape (100, 100)
    assert builder.data_array.size == 10000


def test_export_config():
    builder = DatasetBuilder()
    import_path = "examples/example_config_xarray.json"
    builder.import_config(import_path)
    with tempfile.TemporaryDirectory() as temp_dir:
        export_path = Path(temp_dir, "exported.json")
        builder.export_config(export_path)
        with open(import_path) as f:
            imported = json.load(f)
        with open(export_path) as f:
            exported = json.load(f)

        # Disregard ui section
        imported.pop("ui", None)
        exported.pop("ui", None)
        assert imported == exported


def test_setters():
    builder = DatasetBuilder()

    builder.dataset_info = {"source": "xarray", "id": "eraint_uvz"}
    # builder will auto select the following:
    # builder.data_array_name = 'z'
    # builder.x = 'longitude'
    # builder.y = 'latitude'
    builder.z = "level"
    builder.t = "month"
    builder.t_index = 1
    builder.slicing = {"longitude": [0, 90, 2]}

    assert builder.dataset_info == {"source": "xarray", "id": "eraint_uvz"}
    assert builder.dataset is not None
    assert builder.data_array_name == "z"
    assert builder.x == "longitude"
    assert builder.y == "latitude"
    assert builder.z == "level"
    assert builder.t == "month"
    assert builder.t_index == 1


def test_setters_invalid_values():
    builder = DatasetBuilder()

    # Setting wrong types
    with pytest.raises(TypeError) as e:
        builder.dataset_info = "foo"
    assert str(e.value) == "Type of dataset_info must be Dict or None."
    with pytest.raises(TypeError) as e:
        builder.dataset = "foo"
    assert str(e.value) == "Type of dataset must be xarray.Dataset or None."
    with pytest.raises(TypeError) as e:
        builder.data_array_name = 2
    assert str(e.value) == "Type of data_array_name must be str or None."
    with pytest.raises(TypeError) as e:
        builder.x = 2
    assert str(e.value) == "Type of x must be str or None."
    with pytest.raises(TypeError) as e:
        builder.y = 2
    assert str(e.value) == "Type of y must be str or None."
    with pytest.raises(TypeError) as e:
        builder.z = 2
    assert str(e.value) == "Type of z must be str or None."
    with pytest.raises(TypeError) as e:
        builder.t = 2
    assert str(e.value) == "Type of t must be str or None."
    with pytest.raises(TypeError) as e:
        builder.t_index = None
    assert str(e.value) == "Type of t_index must be int."
    with pytest.raises(TypeError) as e:
        builder.slicing = "foo"
    assert str(e.value) == "Type of slicing must be Dict or None."

    # Setting in the wrong order
    with pytest.raises(ValueError) as e:
        builder.t_index = 5
    assert str(e.value) == "Cannot set time index > 0 without setting t array first."
    with pytest.raises(ValueError) as e:
        builder.t = "foo"
    assert str(e.value) == "Cannot set t without setting data array name first."
    with pytest.raises(ValueError) as e:
        builder.z = "foo"
    assert str(e.value) == "Cannot set z without setting data array name first."
    with pytest.raises(ValueError) as e:
        builder.y = "foo"
    assert str(e.value) == "Cannot set y without setting data array name first."
    with pytest.raises(ValueError) as e:
        builder.x = "foo"
    assert str(e.value) == "Cannot set x without setting data array name first."
    with pytest.raises(ValueError) as e:
        builder.slicing = {"foo": [0, 1, 1]}
    assert str(e.value) == "Cannot set slicing without setting data array name first."
    with pytest.raises(ValueError) as e:
        builder.data_array_name = "foo"
    assert (
        str(e.value) == "Cannot set data array name without setting dataset info first."
    )

    # Setting wrong values for dataset_info
    with pytest.raises(ValueError) as e:
        builder.dataset_info = {}
    assert str(e.value) == 'Dataset info must contain key "id" with string value.'
    with pytest.raises(ValueError) as e:
        builder.dataset_info = {"id": "foo", "source": "bar"}
    assert (
        str(e.value)
        == "Invalid source value. Must be one of [default, xarray, pangeo, esgf]."
    )

    # Set a valid value to proceed
    builder.dataset_info = {"source": "xarray", "id": "eraint_uvz"}

    # Setting wrong values for data_array_name
    with pytest.raises(ValueError) as e:
        builder.data_array_name = "foo"
    assert (
        str(e.value) == "foo does not exist on dataset. Must be one of ['z', 'u', 'v']."
    )

    # Set a valid value to proceed
    builder.data_array_name = "v"

    acceptable_coord_names = ["latitude", "level", "longitude", "month"]
    # Setting wrong values for x, y, z, t
    with pytest.raises(ValueError) as e:
        builder.x = "foo"
    assert (
        str(e.value)
        == f"foo does not exist on data array. Must be one of {acceptable_coord_names}."
    )
    with pytest.raises(ValueError) as e:
        builder.y = "foo"
    assert (
        str(e.value)
        == f"foo does not exist on data array. Must be one of {acceptable_coord_names}."
    )
    with pytest.raises(ValueError) as e:
        builder.z = "foo"
    assert (
        str(e.value)
        == f"foo does not exist on data array. Must be one of {acceptable_coord_names}."
    )
    with pytest.raises(ValueError) as e:
        builder.t = "foo"
    assert (
        str(e.value)
        == f"foo does not exist on data array. Must be one of {acceptable_coord_names}."
    )

    # Set valid values to proceed
    builder.x = "longitude"
    builder.y = "latitude"
    builder.z = "level"
    builder.t = "month"

    # Setting wrong values for t_index
    with pytest.raises(ValueError) as e:
        builder.t_index = -1
    assert str(e.value) == "Time index must be a positive integer."
    with pytest.raises(ValueError) as e:
        builder.t_index = 100
    assert str(e.value) == "Time index must be less than size of t coordinate (2)."

    # Setting wrong values for slicing
    with pytest.raises(ValueError) as e:
        builder.slicing = {0: []}
    assert str(e.value) == "Keys in slicing must be strings."
    with pytest.raises(ValueError) as e:
        builder.slicing = {"foo": []}
    assert (
        str(e.value)
        == "Values in slicing must be lists of 3 integers ([start, stop, step])."
    )
    with pytest.raises(ValueError) as e:
        builder.slicing = {"foo": [0, 1, 1]}
    assert (
        str(e.value)
        == f"Key foo not found in data array. Must be one of {acceptable_coord_names}."
    )
    with pytest.raises(ValueError) as e:
        builder.slicing = {"month": [-1, 10, 10]}
    assert (
        str(e.value)
        == "Value [-1, 10, 10] not applicable for Key month. Step value must be <= 2."
    )


def test_import_error():
    # This will only succeed in an environment where
    # pan3d is installed but pan3d[geotrame] is not installed.
    builder = DatasetBuilder()
    with pytest.raises(ImportError):
        builder.viewer
