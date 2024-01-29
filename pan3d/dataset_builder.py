import os
import json
import pyvista
import xarray

from pan3d.utils import coordinate_auto_selection
from pathlib import Path
from pvxarray.vtk_source import PyVistaXarraySource
from typing import Any, Dict, List, Optional, Union, Tuple


class DatasetBuilder:
    """Manage data structure, slicing, and mesh creation for a target N-D dataset."""

    def __init__(
        self,
        dataset_path: str = None,
        server: Any = None,
        pangeo: bool = False,
    ) -> None:
        """Create an instance of the DatasetBuilder class.

        Parameters:
            dataset_path: A path or URL referencing a dataset readable by xarray.open_dataset()
            server: Trame server name or instance.
            pangeo: If true, use a list of example datasets from Pangeo Forge (examples/pangeo_catalog.json).
        """
        self._algorithm = PyVistaXarraySource()
        self._viewer = None
        self._dataset = None
        self._dataset_path = None
        self._da_name = None

        self._server = server
        self._pangeo = pangeo

        self.dataset_path = dataset_path

    # -----------------------------------------------------
    # Properties
    # -----------------------------------------------------

    @property
    def viewer(self):
        from pan3d.dataset_viewer import DatasetViewer

        if self._viewer is None:
            self._viewer = DatasetViewer(
                builder=self,
                server=self._server,
                pangeo=self._pangeo,
                state=dict(
                    dataset_path=self.dataset_path,
                    da_active=self.data_array_name,
                    da_x=self.x,
                    da_y=self.y,
                    da_z=self.z,
                    da_t=self.t,
                    da_t_index=self.t_index,
                ),
            )
        return self._viewer

    @property
    def dataset_path(self) -> Optional[str]:
        return self._dataset_path

    @dataset_path.setter
    def dataset_path(self, dataset_path: Optional[str]) -> None:
        """Set the path to the current target dataset.

        Parameters:
            dataset_path: A local path or remote URL referencing a dataset readable by xarray.open_dataset()
        """
        if dataset_path != self._dataset_path:
            self._dataset_path = dataset_path
            self._set_state_values(dataset_path=dataset_path)
            ds = None
            if dataset_path is not None:
                self._set_state_values(ui_loading=True)

                if "https://" in dataset_path or os.path.exists(dataset_path):
                    engine = None
                    if ".zarr" in dataset_path:
                        engine = "zarr"
                    if ".nc" in dataset_path:
                        engine = "netcdf4"
                    try:
                        ds = xarray.open_dataset(dataset_path, engine=engine, chunks={})
                    except Exception as e:
                        if self._viewer:
                            self._set_state_values(ui_error_message=str(e))
                        else:
                            raise e
                        return
                else:
                    # Assume it is a named tutorial dataset
                    ds = xarray.tutorial.load_dataset(dataset_path)
            self.dataset = ds
            self._set_state_values(ui_loading=False)

    @property
    def dataset(self) -> Optional[xarray.Dataset]:
        return self._dataset

    @dataset.setter
    def dataset(self, dataset: Optional[xarray.Dataset]) -> None:
        self._dataset = dataset
        if dataset is not None:
            vars = list(dataset.data_vars.keys())
            if len(vars) > 0:
                self.data_array_name = vars[0]
        else:
            self.data_array_name = None
        if self._viewer:
            self._viewer._dataset_changed()
            self._viewer._mesh_changed()

    @property
    def data_array_name(self) -> Optional[str]:
        return self._da_name

    @data_array_name.setter
    def data_array_name(self, data_array_name: Optional[str]) -> None:
        """Set the name of the current data array within the current dataset.

        Parameters:
            data_array_name: The name of a data array that exists in the current dataset.
        """
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
            self._algorithm.data_array = da
            if self._viewer:
                self._viewer._data_array_changed()
                self._viewer._mesh_changed()
            self._auto_select_coordinates()

    @property
    def data_array(self) -> Optional[xarray.DataArray]:
        """Returns the current Xarray data array with current slicing applied."""
        return self._algorithm.sliced_data_array

    @property
    def data_range(self) -> Tuple[Any]:
        if self.dataset is None:
            return None
        return self._algorithm.data_range

    @property
    def x(self) -> Optional[str]:
        return self._algorithm.x

    @x.setter
    def x(self, x: Optional[str]) -> None:
        if self._algorithm.x != x:
            self._algorithm.x = x
            self._set_state_values(da_x=x)
            if self._viewer:
                self._viewer._mesh_changed()

    @property
    def y(self) -> Optional[str]:
        return self._algorithm.y

    @y.setter
    def y(self, y: Optional[str]) -> None:
        if self._algorithm.y != y:
            self._algorithm.y = y
            self._set_state_values(da_y=y)
            if self._viewer:
                self._viewer._mesh_changed()

    @property
    def z(self) -> Optional[str]:
        return self._algorithm.z

    @z.setter
    def z(self, z: Optional[str]) -> None:
        if self._algorithm.z != z:
            self._algorithm.z = z
            self._set_state_values(da_z=z)
            if self._viewer:
                self._viewer._mesh_changed()

    @property
    def t(self) -> Optional[str]:
        return self._algorithm.time

    @t.setter
    def t(self, t: Optional[str]) -> None:
        if self._algorithm.time != t:
            self._algorithm.time = t
            self._set_state_values(da_t=t)
            if self._viewer:
                self._viewer._time_index_changed()
                self._viewer._mesh_changed()

    @property
    def t_index(self) -> int:
        return self._algorithm.time_index

    @t_index.setter
    def t_index(self, t_index: int) -> None:
        if self._algorithm.time_index != t_index:
            self._algorithm.time_index = int(t_index)
            self._set_state_values(da_t_index=t_index)
            if self._viewer:
                self._viewer._time_index_changed()
                self._viewer._mesh_changed()

    @property
    def slicing(self) -> Dict[str, List]:
        return self._algorithm.slicing

    @slicing.setter
    def slicing(self, slicing: Dict[str, List]) -> None:
        self._algorithm.slicing = slicing
        if self._viewer:
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
                    if len(name_match) > 0:
                        setattr(self, axis, coord_name)
                        assigned_coords.append(coord_name)
            # Then assign any remaining by index
            unassigned_axes = [
                a for a in ["x", "y", "z", "t"] if getattr(self, a) is None
            ]
            unassigned_coords = [d for d in da.dims if d not in assigned_coords]
            for i, d in enumerate(unassigned_coords):
                if i < len(unassigned_axes):
                    setattr(self, unassigned_axes[i], d)

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
            self._set_state_values(ui_action_message="Invalid format of import file.")
            return

        self.dataset_path = origin_config
        self.data_array_name = array_config.pop("name")
        for key, value in array_config.items():
            setattr(self, key, value)
        self.slicing = config.get("data_slices")

        ui_config = {f"ui_{k}": v for k, v in config.get("ui", {}).items()}
        self._set_state_values(**ui_config)

    def export_config(self, config_file: Union[str, Path, None] = None) -> None:
        """Export the current state to a JSON configuration file.

        Parameters:
            config_file: Can be a string or Path representing the destination of the JSON configuration file.
                If None, a dictionary containing the current configuration will be returned.
                For details, see Configuration Files documentation.
        """
        config = {
            "data_origin": self.dataset_path,
            "data_array": {
                "name": self.data_array_name,
                **{
                    key: getattr(self, key)
                    for key in ["x", "y", "z", "t", "t_index"]
                    if getattr(self, key) is not None
                },
            },
            "data_slices": self.slicing,
        }
        if self._viewer:
            state_items = list(self._viewer.state.to_dict().items())
            config["ui"] = {
                k.replace("ui_", ""): v
                for k, v in state_items
                if k.startswith("ui_") and "action_" not in k
            }

        if config_file:
            Path(config_file).write_text(json.dumps(config))
        return config
