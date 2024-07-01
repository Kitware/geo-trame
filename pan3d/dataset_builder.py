import os
import math
import json
import pyvista
import xarray

from pan3d.utils import coordinate_auto_selection
from pan3d import catalogs as pan3d_catalogs
from pathlib import Path
from pvxarray.vtk_source import PyVistaXarraySource
from typing import Any, Dict, List, Optional, Union, Tuple


class DatasetBuilder:
    """Manage data structure, slicing, and mesh creation for a target N-D dataset."""

    def __init__(
        self,
        dataset: str = None,
        server: Any = None,
        viewer: bool = False,
        catalogs: List[str] = [],
        resolution: int = None,
    ) -> None:
        """Create an instance of the DatasetBuilder class.

        Parameters:
            dataset: A path or URL referencing a dataset readable by xarray.open_dataset()
            server: Trame server name or instance.
            catalogs: A list of strings referencing available catalog modules (options include 'pangeo', 'esgf'). Each included catalog will be available to search in the GeoTrame UI.
        """
        self._algorithm = PyVistaXarraySource()
        self._viewer = None
        self._dataset = None
        self._dataset_info = None
        self._da_name = None
        self._resolution = resolution or 2**7
        self._import_mode = False
        self._import_viewer_state = {}

        self._server = server
        self._catalogs = catalogs

        if viewer:
            # Access to instantiate
            self.viewer

        if dataset:
            self.dataset_info = {
                "source": "default",
                "id": dataset,
            }

    # -----------------------------------------------------
    # Properties
    # -----------------------------------------------------

    @property
    def viewer(self):
        """Return the GeoTrame instance for this DatasetBuilder.
        If none exists, create a new one and synchronize state.
        """
        from pan3d.dataset_viewer import DatasetViewer

        if self._viewer is None:
            self._viewer = DatasetViewer(
                builder=self,
                server=self._server,
                catalogs=self._catalogs,
                state=dict(
                    dataset_info=self.dataset_info,
                    da_active=self.data_array_name,
                    da_x=self.x,
                    da_y=self.y,
                    da_z=self.z,
                    da_t=self.t,
                    da_t_index=self.t_index,
                    da_auto_slicing=self._resolution > 1,
                    **self._import_viewer_state,
                ),
            )
        return self._viewer

    @property
    def dataset_info(self) -> Optional[Dict]:
        """A dictionary referencing the current dataset.
        This dictionary should adhere to the following schema:

        | Key | Required? | Default | Type | Value Description |
        |-----|-----------|---------|------|-------------------|
        | `id` | Yes |  | string | A unique identifier that will be used to load the dataset
        |`source`| No | "default" | string | Name of a module to load the dataset (options: "default", "xarray", "pangeo", "esgf")

        With the default source, the id value must be readable with xarray.open_dataset().
        """
        return self._dataset_info

    @dataset_info.setter
    def dataset_info(self, dataset_info: Optional[Dict]) -> None:
        if dataset_info is not None:
            if not isinstance(dataset_info, dict):
                raise TypeError("Type of dataset_info must be Dict or None.")
            source = dataset_info.get("source")
            id = dataset_info.get("id")
            if not isinstance(id, str):
                raise ValueError(
                    'Dataset info must contain key "id" with string value.'
                )
            if source is None:
                dataset_info["source"] = "default"
            elif source not in ["default", "xarray", "pangeo", "esgf"]:
                raise ValueError(
                    "Invalid source value. Must be one of [default, xarray, pangeo, esgf]."
                )
        if dataset_info != self._dataset_info:
            self._dataset_info = dataset_info
            self._set_state_values(dataset_info=dataset_info)
            self._load_dataset(dataset_info)

    @property
    def dataset(self) -> Optional[xarray.Dataset]:
        """Xarray.Dataset object read from the current dataset_info."""
        return self._dataset

    @dataset.setter
    def dataset(self, dataset: Optional[xarray.Dataset]) -> None:
        if dataset is not None and not isinstance(dataset, xarray.Dataset):
            raise TypeError("Type of dataset must be xarray.Dataset or None.")
        self._dataset = dataset
        if dataset is not None:
            vars = list(
                k
                for k in dataset.data_vars.keys()
                if not k.endswith("_bnds") and not k.endswith("_bounds")
            )
            if len(vars) > 0:
                self.data_array_name = vars[0]
        else:
            self.data_array_name = None
        if self._viewer:
            self._viewer._dataset_changed()
            self._viewer._mesh_changed()

    @property
    def data_array_name(self) -> Optional[str]:
        """String name of an array that exists on the current dataset."""
        return self._da_name

    @data_array_name.setter
    def data_array_name(self, data_array_name: Optional[str]) -> None:
        if data_array_name is not None:
            if not isinstance(data_array_name, str):
                raise TypeError("Type of data_array_name must be str or None.")
            if self.dataset is None:
                raise ValueError(
                    "Cannot set data array name without setting dataset info first."
                )
            if data_array_name not in self.dataset.data_vars:
                acceptable_values = list(self.dataset.data_vars.keys())
                raise ValueError(
                    f"{data_array_name} does not exist on dataset. Must be one of {acceptable_values}."
                )
        if data_array_name != self._da_name:
            self._da_name = data_array_name
            self._set_state_values(da_active=data_array_name)
            da = None
            self.x = None
            self.y = None
            self.z = None
            self.t = None
            self.t_index = 0
            if data_array_name is not None and self.dataset is not None:
                da = self.dataset[data_array_name]
                if len(da.indexes.variables.mapping) == 0:
                    da = da.assign_coords({d: range(s) for d, s in da.sizes.items()})
            self._algorithm.data_array = da
            if self._viewer:
                self._viewer._data_array_changed()
                self._viewer._mesh_changed()
            if not self._import_mode:
                self._auto_select_coordinates()
                self._auto_select_slicing()

    @property
    def data_array(self) -> Optional[xarray.DataArray]:
        """Return the current Xarray data array with current slicing applied."""
        return self._algorithm.sliced_data_array

    @property
    def data_range(self) -> Tuple[Any]:
        """Return the minimum and maximum of the current Xarray data array with current slicing applied."""
        if self.dataset is None:
            return None
        return self._algorithm.data_range

    @property
    def x(self) -> Optional[str]:
        """String name of a coordinate that should be rendered on the X axis.
        Value must exist in coordinates of current data array."""
        return self._algorithm.x

    @x.setter
    def x(self, x: Optional[str]) -> None:
        if x is not None:
            if not isinstance(x, str):
                raise TypeError("Type of x must be str or None.")
            if self.data_array_name is None:
                raise ValueError("Cannot set x without setting data array name first.")
            acceptable_values = self.dataset[self.data_array_name].dims
            if x not in acceptable_values:
                raise ValueError(
                    f"{x} does not exist on data array. Must be one of {sorted(acceptable_values)}."
                )
        if self._algorithm.x != x:
            self._algorithm.x = x
            self._set_state_values(da_x=x)
            if self._viewer:
                self._viewer._mesh_changed()

    @property
    def y(self) -> Optional[str]:
        """String name of a coordinate that should be rendered on the Y axis.
        Value must exist in coordinates of current data array."""
        return self._algorithm.y

    @y.setter
    def y(self, y: Optional[str]) -> None:
        if y is not None:
            if not isinstance(y, str):
                raise TypeError("Type of y must be str or None.")
            if self.data_array_name is None:
                raise ValueError("Cannot set y without setting data array name first.")
            acceptable_values = self.dataset[self.data_array_name].dims
            if y not in acceptable_values:
                raise ValueError(
                    f"{y} does not exist on data array. Must be one of {sorted(acceptable_values)}."
                )
        if self._algorithm.y != y:
            self._algorithm.y = y
            self._set_state_values(da_y=y)
            if self._viewer:
                self._viewer._mesh_changed()

    @property
    def z(self) -> Optional[str]:
        """String name of a coordinate that should be rendered on the Z axis.
        Value must exist in coordinates of current data array."""
        return self._algorithm.z

    @z.setter
    def z(self, z: Optional[str]) -> None:
        if z is not None:
            if not isinstance(z, str):
                raise TypeError("Type of z must be str or None.")
            if self.data_array_name is None:
                raise ValueError("Cannot set z without setting data array name first.")
            acceptable_values = self.dataset[self.data_array_name].dims
            if z not in acceptable_values:
                raise ValueError(
                    f"{z} does not exist on data array. Must be one of {sorted(acceptable_values)}."
                )
        if self._algorithm.z != z:
            self._algorithm.z = z
            self._set_state_values(da_z=z)
            if self._viewer:
                self._viewer._mesh_changed()

    @property
    def t(self) -> Optional[str]:
        """String name of a coordinate that represents time or some other fourth dimension.
        Only one slice may be viewed at once.
        Value must exist in coordinates of current data array."""
        return self._algorithm.time

    @t.setter
    def t(self, t: Optional[str]) -> None:
        if t is not None:
            if not isinstance(t, str):
                raise TypeError("Type of t must be str or None.")
            if self.data_array_name is None:
                raise ValueError("Cannot set t without setting data array name first.")
            acceptable_values = self.dataset[self.data_array_name].dims
            if t not in acceptable_values:
                raise ValueError(
                    f"{t} does not exist on data array. Must be one of {sorted(acceptable_values)}."
                )
        if self._algorithm.time != t:
            self._algorithm.time = t
            self._set_state_values(da_t=t)
            if self._viewer:
                self._viewer._time_index_changed()
                self._viewer._mesh_changed()

    @property
    def t_index(self) -> int:
        """Integer representing the index of the current time slice."""
        return self._algorithm.time_index

    @t_index.setter
    def t_index(self, t_index: int) -> None:
        if not isinstance(t_index, int):
            raise TypeError("Type of t_index must be int.")
        if t_index < 0:
            raise ValueError("Time index must be a positive integer.")
        if t_index > 0:
            if not self.t:
                raise ValueError(
                    "Cannot set time index > 0 without setting t array first."
                )
            max_value = self.dataset[self.data_array_name].coords[self.t].size
            if t_index >= max_value:
                raise ValueError(
                    f"Time index must be less than size of t coordinate ({max_value})."
                )
        if self._algorithm.time_index != t_index:
            self._algorithm.time_index = int(t_index)
            self._set_state_values(da_t_index=t_index)
            if self._viewer:
                self._viewer._time_index_changed()
                self._viewer._mesh_changed()

    @property
    def slicing(self) -> Dict[str, List]:
        """Dictionary mapping of coordinate names to slice arrays.
        Each key should exist in the coordinates of the current data array.
        Each value should be an array consisting of three
        integers or floats representing start value, stop value, and step.
        """
        return self._algorithm.slicing

    @slicing.setter
    def slicing(self, slicing: Dict[str, List]) -> None:
        if slicing is not None:
            if not isinstance(slicing, Dict):
                raise TypeError("Type of slicing must be Dict or None.")
            if self.data_array_name is None:
                raise ValueError(
                    "Cannot set slicing without setting data array name first."
                )
            for key, value in slicing.items():
                if not isinstance(key, str):
                    raise ValueError("Keys in slicing must be strings.")
                if (
                    not isinstance(value, list)
                    or len(value) != 3
                    or any(not isinstance(v, int) for v in value)
                ):
                    raise ValueError(
                        "Values in slicing must be lists of 3 integers ([start, stop, step])."
                    )
                da = self.dataset[self.data_array_name]
                acceptable_coords = da.dims
                if key not in acceptable_coords:
                    raise ValueError(
                        f"Key {key} not found in data array. Must be one of {sorted(acceptable_coords)}."
                    )
                key_coord = da[key]

                step = value[2]
                if step > key_coord.size:
                    raise ValueError(
                        f"Value {value} not applicable for Key {key}. Step value must be <= {key_coord.size}."
                    )

        self._algorithm.slicing = slicing
        if self._viewer:
            self._viewer._data_slicing_changed()
            self._viewer._mesh_changed()

    @property
    def mesh(
        self,
    ) -> Union[pyvista.core.grid.RectilinearGrid, pyvista.StructuredGrid]:
        """Returns the PyVista Mesh derived from the current data array."""
        if self.data_array is None:
            return None
        return self._algorithm.mesh

    # -----------------------------------------------------
    # Internal methods
    # -----------------------------------------------------

    def _load_dataset(self, dataset_info):
        ds = None
        if dataset_info is not None:
            source = dataset_info.get("source")
            if source in ["pangeo", "esgf"]:
                ds = pan3d_catalogs.load_dataset(source, id=dataset_info["id"])
            elif source == "xarray":
                ds = xarray.tutorial.load_dataset(dataset_info["id"])
            else:
                ds = self._load_dataset_default(dataset_info)

        if ds is not None:
            self.dataset = ds

    def _load_dataset_default(self, dataset_info):
        # Assume 'id' in dataset_info is a path or url
        if "https://" in dataset_info["id"] or os.path.exists(dataset_info["id"]):
            engine = None
            if ".zarr" in dataset_info["id"]:
                engine = "zarr"
            if ".nc" in dataset_info["id"]:
                engine = "netcdf4"
            ds = xarray.open_dataset(dataset_info["id"], engine=engine, chunks={})
            return ds
        else:
            raise ValueError(f'Could not find dataset at {dataset_info["id"]}')

    def _set_state_values(self, **kwargs):
        if self._viewer is not None:
            for k, v in kwargs.items():
                if self._viewer.state[k] != v:
                    self._viewer.state[k] = v

    def _auto_select_coordinates(self) -> None:
        """Automatically assign available coordinates to available axes.
        Automatic assignment is done according to the following expected coordinate names:\n
        X: "x" | "i" | "lon" | "len"\n
        Y: "y" | "j" | "lat" | "width"\n
        Z: "z" | "k" | "depth" | "height"\n
        T: "t" | "time"
        """
        if self.x or self.y or self.z or self.t:
            # Some coordinates already assigned, don't auto-assign
            return
        if self.dataset is not None and self.data_array_name is not None:
            da = self.dataset[self.data_array_name]
            assigned_coords = []
            unassigned_axes = [
                a for a in ["x", "y", "z", "t"] if getattr(self, a) is None
            ]
            # Prioritize assignment by known names
            for coord_name in da.dims:
                name = coord_name.lower()
                for axis, accepted_names in coordinate_auto_selection.items():
                    # If accepted name is longer than one letter, look for contains match
                    name_match = [
                        accepted
                        for accepted in accepted_names
                        if (len(accepted) == 1 and accepted == name)
                        or (len(accepted) > 1 and accepted in name)
                    ]
                    if len(name_match) > 0 and axis in unassigned_axes:
                        setattr(self, axis, coord_name)
                        assigned_coords.append(coord_name)
            # Update list of unassigned axes
            unassigned_axes = [
                a for a in ["x", "y", "z", "t"] if getattr(self, a) is None
            ]
            # Then assign any remaining by index
            unassigned_coords = [d for d in da.dims if d not in assigned_coords]
            for i, d in enumerate(unassigned_coords):
                if i < len(unassigned_axes):
                    setattr(self, unassigned_axes[i], d)

    def _auto_select_slicing(
        self,
        bounds: Optional[Dict] = None,
        steps: Optional[Dict] = None,
    ) -> None:
        """Automatically select slicing for selected data array."""
        if not self.dataset or not self.data_array_name or self._resolution <= 1:
            return
        if not bounds:
            da = self.dataset[self.data_array_name]
            bounds = {k: [0, da[k].size] for k in da.dims}
        self.slicing = {
            k: [
                v[0],
                v[1],
                math.ceil((v[1] - v[0]) / self._resolution)
                if self._resolution > 1 and v[1] - v[0] > 0 and k != self.t
                else steps.get(k, 1)
                if steps is not None and k != self.t
                else 1,
            ]
            for k, v in bounds.items()
        }
        if self._viewer:
            self._viewer._data_slicing_changed()

    # -----------------------------------------------------
    # Config logic
    # -----------------------------------------------------

    def import_config(self, config_file: Union[str, Path, None]) -> None:
        """Import state from a JSON configuration file.

        Parameters:
            config_file: Can be a dictionary containing state information,
                or a string or Path referring to a JSON file which contains state information.
                For details, see Configuration Files documentation.
        """
        if isinstance(config_file, dict):
            config = config_file
        elif isinstance(config_file, str):
            path = Path(config_file)
            if path.exists():
                config = json.loads(path.read_text())
            else:
                config = json.loads(config_file)
        origin_config = config.get("data_origin")
        array_config = config.get("data_array")

        if not origin_config or not array_config:
            raise ValueError("Invalid format of import file.")

        if isinstance(origin_config, str):
            origin_config = {
                "source": "default",
                "id": origin_config,
            }
        self._import_mode = True
        self.dataset_info = origin_config
        self.data_array_name = array_config.pop("name")
        for key, value in array_config.items():
            setattr(self, key, value)
        if config.get("data_slices"):
            self._resolution = 1  # disable auto slicing
            self.slicing = config.get("data_slices")
        self._import_mode = False

        ui_config = {f"ui_{k}": v for k, v in config.get("ui", {}).items()}
        render_config = {f"render_{k}": v for k, v in config.get("render", {}).items()}
        if self._viewer:
            self._set_state_values(
                **ui_config,
                **render_config,
                ui_action_name=None,
            )
        else:
            self._import_viewer_state = dict(
                **ui_config,
                **render_config,
            )

    def export_config(self, config_file: Union[str, Path, None] = None) -> None:
        """Export the current state to a JSON configuration file.

        Parameters:
            config_file: Can be a string or Path representing the destination of the JSON configuration file.
                If None, a dictionary containing the current configuration will be returned.
                For details, see Configuration Files documentation.
        """
        data_origin = self.dataset_info
        if data_origin.get("source") == "default":
            data_origin = data_origin.get("id")
        config = {
            "data_origin": data_origin,
            "data_array": {
                "name": self.data_array_name,
                **{
                    key: getattr(self, key)
                    for key in ["x", "y", "z", "t", "t_index"]
                    if getattr(self, key) is not None
                },
            },
        }
        if self._algorithm.slicing:
            config["data_slices"] = self._algorithm.slicing
        if self._viewer:
            state_items = list(self._viewer.state.to_dict().items())
            config["ui"] = {
                k.replace("ui_", ""): v
                for k, v in state_items
                if k.startswith("ui_")
                and "action" not in k
                and "loading" not in k
                and "catalog" not in k
            }
            config["render"] = {
                k.replace("render_", ""): v
                for k, v in state_items
                if k.startswith("render_") and "_options" not in k
            }

        if config_file:
            Path(config_file).write_text(json.dumps(config))
        return config
