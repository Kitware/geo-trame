import asyncio
import concurrent.futures
import itertools
import json
import pandas
import pyvista
import geovista
import numpy
import base64
from io import BytesIO
from PIL import Image
from pathlib import Path
from typing import Dict, List, Optional, Union

from trame.decorators import TrameApp, change
from trame.app import get_server
from trame.widgets import html, client
from trame.widgets import vuetify3 as vuetify
from trame_server.core import Server
from trame_server.state import State
from trame_server.controller import Controller
from trame_vuetify.ui.vuetify3 import VAppLayout

from pan3d import catalogs as pan3d_catalogs
from pan3d.dataset_builder import DatasetBuilder
from pan3d.ui import AxisDrawer, MainDrawer, Toolbar, RenderOptions, BoundsConfigure
from pan3d.utils import (
    initial_state,
    has_gpu_rendering,
)

BASE_DIR = Path(__file__).parent
CSS_FILE = BASE_DIR / "ui" / "custom.css"


@TrameApp()
class DatasetViewer:
    """Create a Trame GUI for a DatasetBuilder instance and manage rendering"""

    def __init__(
        self,
        builder: Optional[DatasetBuilder] = None,
        server: Union[Server, str] = None,
        state: dict = None,
        catalogs: List[str] = [],
    ) -> None:
        """Create an instance of the DatasetViewer class.

        Parameters:
            builder: Pan3D DatasetBuilder instance.
            server: Trame server name or instance.
            state:  A dictionary of initial state values.
            catalogs: A list of strings referencing available catalog modules (options include 'pangeo', 'esgf'). Each included catalog will be available to search in the GeoTrame UI.
        """
        if builder is None:
            builder = DatasetBuilder()
            builder._viewer = self
        self.builder = builder
        self.server = get_server(server, client_type="vue3")
        self.current_event_loop = asyncio.get_event_loop()
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._ui = None
        self._default_style = CSS_FILE.read_text()
        self._preview_slicing = None

        self.plotter = geovista.GeoPlotter(off_screen=True, notebook=False)
        self.plotter.set_background("lightgrey")
        self.reset_camera = True
        self.plot_view = None
        self.actor = None
        self.ctrl.get_plotter = lambda: self.plotter
        self.ctrl.on_client_connected.add(self._on_ready)

        self.state.update(initial_state)
        self.state.ready()
        if state:
            self.state.update(state)

        if catalogs:
            self.state.available_catalogs = [
                pan3d_catalogs.get(catalog_name) for catalog_name in catalogs
            ]

        self._force_local_rendering = not has_gpu_rendering()
        if self._force_local_rendering:
            pyvista.global_theme.trame.default_mode = "client"

        self._dataset_changed()
        self._data_array_changed()
        self._time_index_changed()
        self._mesh_changed()

    def _on_ready(self, **kwargs):
        self.state.render_auto = True
        self.reset_camera = True
        self._mesh_changed()

    def start(self, **kwargs):
        """Initialize the UI and start the server for GeoTrame."""
        self.ui.server.start(**kwargs)

    @property
    async def ready(self) -> None:
        """Coroutine to wait for the GeoTrame server to be ready."""
        await self.ui.ready

    @property
    def state(self) -> State:
        """Returns the current State of the Trame server."""
        return self.server.state

    @property
    def ctrl(self) -> Controller:
        """Returns the Controller for the Trame server."""
        return self.server.controller

    @property
    def ui(self) -> VAppLayout:
        """Constructs and returns a Trame UI for managing and viewing the current data."""
        if self._ui is None:
            # Build UI
            self._ui = VAppLayout(self.server)
            with self._ui:
                with client.Style(self._default_style) as style:
                    self.ctrl.update_style = style.update
                Toolbar(
                    self.apply_and_render,
                    self._submit_import,
                    self.builder.export_config,
                )
                MainDrawer(
                    update_catalog_search_term_function=self._update_catalog_search_term,
                    catalog_search_function=self._catalog_search,
                    catalog_term_search_function=self._catalog_term_option_search,
                    switch_data_group_function=self._switch_data_group,
                )
                AxisDrawer(
                    coordinate_select_axis_function=self._coordinate_select_axis,
                    coordinate_change_slice_function=self._coordinate_change_slice,
                    coordinate_toggle_expansion_function=self._coordinate_toggle_expansion,
                )
                with vuetify.VMain():
                    vuetify.VBanner(
                        "{{ ui_error_message }}",
                        v_show=("ui_error_message",),
                    )
                    with html.Div(
                        v_if=("da_active",), style="height: 100%; position: relative"
                    ):
                        BoundsConfigure(
                            coordinate_change_bounds_function=self._coordinate_change_bounds,
                            snap_camera_function=self._snap_camera_view_face,
                        )
                        RenderOptions()
                        with pyvista.trame.ui.plotter_ui(
                            self.ctrl.get_plotter(),
                            interactive_ratio=1,
                            collapse_menu=True,
                        ) as plot_view:
                            self.ctrl.view_update = plot_view.update
                            self.ctrl.reset_camera = plot_view.reset_camera
                            self.ctrl.push_camera = plot_view.push_camera
                            self.plot_view = plot_view
        # turn on axis orientation widget by default with state var from pyvista
        # (typo in visibility is intentional, done to match pyvista)
        self.state[f"{self.ctrl.get_plotter()._id_name}_axis_visiblity"] = True
        return self._ui

    # -----------------------------------------------------
    # UI bound methods
    # -----------------------------------------------------
    def _update_catalog_search_term(self, term_key, term_value):
        self.state.catalog_current_search[term_key] = term_value
        self.state.dirty("catalog_current_search")

    def _catalog_search(self):
        def load_results():
            catalog_id = self.state.catalog.get("id")
            results, group_name, message = pan3d_catalogs.search(
                catalog_id, **self.state.catalog_current_search
            )

            if len(results) > 0:
                self.state.available_data_groups.append(
                    {"name": group_name, "value": group_name}
                )
                self.state.available_datasets[group_name] = results
                self.state.ui_catalog_search_message = message
                self.state.dirty("available_data_groups", "available_datasets")
            else:
                self.state.ui_catalog_search_message = (
                    "No results found for current search criteria."
                )

        self.run_as_async(
            load_results,
            loading_state="ui_catalog_term_search_loading",
            error_state="ui_catalog_search_message",
            unapplied_changes_state=None,
        )

    def _catalog_term_option_search(self):
        def load_terms():
            catalog_id = self.state.catalog.get("id")
            search_options = pan3d_catalogs.get_search_options(catalog_id)
            self.state.available_catalogs = [
                {
                    **catalog,
                    "search_terms": [
                        {"key": k, "options": v} for k, v in search_options.items()
                    ],
                }
                if catalog.get("id") == catalog_id
                else catalog
                for catalog in self.state.available_catalogs
            ]
            for catalog in self.state.available_catalogs:
                if catalog.get("id") == catalog_id:
                    self.state.catalog = catalog

        self.run_as_async(
            load_terms,
            loading_state="ui_catalog_term_search_loading",
            error_state="ui_catalog_search_message",
            unapplied_changes_state=None,
        )

    def _switch_data_group(self):
        # Setup from previous group needs to be cleared
        self.state.dataset_info = None
        self.state.da_attrs = {}
        self.state.da_vars = {}
        self.state.da_vars_attrs = {}
        self.state.da_coordinates = []
        self.state.ui_expanded_coordinates = []
        self.state.da_active = None
        self.state.da_x = None
        self.state.da_y = None
        self.state.da_z = None
        self.state.da_t = None
        self.state.da_t_index = 0
        self.plotter.clear()
        self.plotter.view_isometric()

    def _coordinate_select_axis(
        self, coordinate_name, current_axis, new_axis, **kwargs
    ):
        if current_axis and self.state[current_axis]:
            self.state[current_axis] = None
        if new_axis and new_axis != "undefined":
            self.state[new_axis] = coordinate_name
        self.reset_camera = True

    def _coordinate_change_slice(self, coordinate_name, slice_attribute_name, value):
        value = int(value)
        for coord in self.state.da_coordinates:
            if coord["name"] == coordinate_name:
                bounds = coord.get("bounds")
                if slice_attribute_name == "start":
                    bounds[0] = value
                elif slice_attribute_name == "stop":
                    bounds[1] = value
                elif slice_attribute_name == "step":
                    coord.update(dict(step=value))
                coord.update(dict(bounds=bounds))
                self.state.dirty("da_coordinates")

    def _coordinate_change_bounds(self, coordinate_name, bounds):
        for coord in self.state.da_coordinates:
            if coord["name"] == coordinate_name:
                coord.update(dict(bounds=bounds))
                self.state.dirty("da_coordinates")

    def _coordinate_toggle_expansion(self, coordinate_name):
        if coordinate_name in self.state.ui_expanded_coordinates:
            self.state.ui_expanded_coordinates.remove(coordinate_name)
        else:
            self.state.ui_expanded_coordinates.append(coordinate_name)
        self.state.dirty("ui_expanded_coordinates")

    def _submit_import(self):
        def submit():
            files = self.state["ui_action_config_file"]
            if files and len(files) > 0:
                file_content = files[0]["content"]
                self.plotter.clear()
                self.plotter.view_isometric()

                self.builder.import_config(json.loads(file_content.decode()))
                self._mesh_changed()
                self.reset_camera = True

        self.run_as_async(
            submit, loading_state="ui_import_loading", unapplied_changes_state=None
        )

    def _snap_camera_view_face(self):
        face = self.state.cube_preview_face
        if "X" in face:
            viewUp = [0, 0, 1]
            vector = [-1, -1, 1] if "+" in face else [1, 1, 1]
            self.plotter.view_vector(vector, viewUp)
        if "Y" in face:
            viewUp = [0, 0, 1]
            vector = [1, -1, 1] if "+" in face else [-1, 1, 1]
            self.plotter.view_vector(vector, viewUp)
        if "Z" in face:
            viewUp = [0, 1, 0]
            vector = [-1, 1, -1] if "+" in face else [1, 1, 1]
            self.plotter.view_vector(vector, viewUp)

    # -----------------------------------------------------
    # Rendering methods
    # -----------------------------------------------------

    def set_render_scales(self, **kwargs: Dict[str, str]) -> None:
        """Set the scales at which each axis (x, y, and/or z) should be rendered.

        Parameters:
            kwargs: A dictionary mapping of axis names to integer scales.\n
                Keys must be 'x' | 'y' | 'z'.\n
                Values must be integers > 0.
        """
        if "x" in kwargs and kwargs["x"] != self.state.render_x_scale:
            self.state.render_x_scale = int(kwargs["x"])
        if "y" in kwargs and kwargs["y"] != self.state.render_y_scale:
            self.state.render_y_scale = int(kwargs["y"])
        if "z" in kwargs and kwargs["z"] != self.state.render_z_scale:
            self.state.render_z_scale = int(kwargs["z"])
        self.plotter.set_scale(
            xscale=self.state.render_x_scale or 1,
            yscale=self.state.render_y_scale or 1,
            zscale=self.state.render_z_scale or 1,
        )

    def set_render_options(
        self,
        colormap: str = "viridis",
        transparency: bool = False,
        transparency_function: str = None,
        scalar_warp: bool = False,
        cartographic: bool = False,
        render: bool = True,
    ) -> None:
        """Set available options for rendering data.

        Parameters:
            colormap: A colormap name from Matplotlib (https://matplotlib.org/stable/users/explain/colors/colormaps.html)
            transparency: If true, enable transparency and use transparency_function.
            transparency_function: One of PyVista's opacity transfer functions (https://docs.pyvista.org/version/stable/examples/02-plot/opacity.html#transfer-functions)
            scalar_warp: If true, warp the mesh proportional to its scalars.
            cartographic: If true, wrap the mesh around an earth sphere.
            render: If true, update current render with new values (default=True)
        """
        if self.state.render_colormap != colormap:
            self.state.render_colormap = colormap
        if self.state.render_transparency != transparency:
            self.state.render_transparency = transparency
        if self.state.render_transparency_function != transparency_function:
            self.state.render_transparency_function = transparency_function
        if self.state.render_scalar_warp != scalar_warp:
            self.state.render_scalar_warp = scalar_warp
        if self.state.render_cartographic != cartographic:
            self.state.render_cartographic = cartographic

        if (
            render
            and self.builder.mesh is not None
            and self.builder.data_array is not None
        ):
            self.apply_and_render()

    def plot_mesh(self) -> None:
        """Render current cached mesh in GeoTrame plotter."""
        if self.builder.data_array is None:
            return

        self.plotter.clear()
        args = dict(
            cmap=self.state.render_colormap,
            clim=self.builder.data_range,
            scalar_bar_args=dict(interactive=True),
        )
        if self.state.render_transparency:
            args["opacity"] = self.state.render_transparency_function

        if self.state.render_cartographic:
            self.plotter.add_base_layer(texture=geovista.blue_marble())
            da = self.builder.data_array  # slicing already applied
            mesh = geovista.Transform.from_1d(
                da[self.builder.x],  # lon coordinates
                da[self.builder.y],  # lat coordinates
                da,
            )
            mesh = mesh.threshold()  # make NaN values transparent

            # position camera
            camera = self.plotter.camera
            camera.focal_point = [0, 0, 0]
            camera.position = mesh.center
            self.plotter.reset_camera(bounds=mesh.bounds)
        else:
            mesh = self.builder.mesh

        if self.state.render_scalar_warp:
            mesh = mesh.warp_by_scalar()
        self.actor = self.plotter.add_mesh(
            mesh,
            **args,
        )
        if self.reset_camera:
            if len(self.builder.data_array.shape) > 2:
                self.plotter.view_vector([1, 1, 1], [0, 1, 0])
            elif not self.state.render_cartographic:
                self.plotter.view_xy()
            self.reset_camera = False

        if self.plot_view:
            self.ctrl.push_camera()
            self.ctrl.view_update()

    def apply_and_render(self, **kwargs) -> None:
        """Asynchronously reset and update cached mesh and render to viewer's plotter."""

        self.run_as_async(self.plot_mesh)

    def run_as_async(
        self,
        function,
        loading_state="ui_loading",
        error_state="ui_error_message",
        unapplied_changes_state="ui_unapplied_changes",
    ):
        async def run():
            with self.state:
                if loading_state is not None:
                    self.state[loading_state] = True
                if error_state is not None:
                    self.state[error_state] = None
                if unapplied_changes_state is not None:
                    self.state[unapplied_changes_state] = False

            await asyncio.sleep(0.001)

            with self.state:
                try:
                    function()
                except Exception as e:
                    if error_state is not None:
                        self.state[error_state] = str(e)
                    else:
                        raise e
                if loading_state is not None:
                    self.state[loading_state] = False

            await asyncio.sleep(0.001)

        if self.current_event_loop.is_running():
            asyncio.run_coroutine_threadsafe(run(), self.current_event_loop)
        else:
            # Pytest environment needs synchronous execution
            function()

    # -----------------------------------------------------
    # State sync with Builder
    # -----------------------------------------------------
    def _dataset_changed(self) -> None:
        self.state.ui_more_info_link = None
        self.state.da_attrs = {}
        self.state.da_vars = {}
        self.state.da_vars_attrs = {}

        dataset = self.builder.dataset
        if dataset:
            if self._ui is not None:
                self.state.ui_main_drawer = True

            self.state.da_attrs = [
                {"key": str(k), "value": str(v)} for k, v in dataset.attrs.items()
            ]
            self.state.da_attrs.insert(
                0,
                {
                    "key": "dimensions",
                    "value": str(dict(dataset.sizes)),
                },
            )
            self.state.da_vars = [
                {"name": k, "id": i} for i, k in enumerate(dataset.data_vars.keys())
            ]
            self.state.da_vars_attrs = {
                var["name"]: [
                    {"key": str(k), "value": str(v)}
                    for k, v in dataset.data_vars[var["name"]].attrs.items()
                ]
                for var in self.state.da_vars
            }
            if len(self.state.da_vars) == 0:
                self.state.no_da_vars = True
            self.state.dataset_ready = True
        else:
            self.state.dataset_ready = False

    def _data_array_changed(self) -> None:
        dataset = self.builder.dataset
        da_name = self.builder.data_array_name
        self.state.da_coordinates = []
        self.state.ui_expanded_coordinates = []
        self.reset_camera = True

        if dataset is None or da_name is None:
            return
        da = dataset[da_name]
        for key in da.dims:
            if key not in [c["name"] for c in self.state.da_coordinates]:
                current_coord = da.coords[key]
                values = list(current_coord.values)
                reverse_order = values[0] > values[-1]
                size = current_coord.size
                dtype = current_coord.dtype
                labels = [
                    (pandas.to_datetime(v).strftime("%b %d %Y %H:%M"))
                    if dtype.kind in ["O", "M"]  # is datetime
                    else (f"{pandas.to_timedelta(v).total_seconds()} seconds")
                    if dtype.kind in ["m"]  # is timedelta
                    else str(round(v))
                    if isinstance(v, float)
                    else str(v)
                    for v in values
                ]
                coord_attrs = [
                    {"key": str(k), "value": str(v)}
                    for k, v in da.coords[key].attrs.items()
                ]
                coord_attrs.append({"key": "dtype", "value": str(dtype)})
                coord_attrs.append({"key": "length", "value": int(size)})
                coord_attrs.append(
                    {"key": "range", "value": f"{labels[0]} - {labels[-1]}"}
                )
                bounds = [0, size - 1]
                self.state.da_coordinates.append(
                    {
                        "name": key,
                        "attrs": coord_attrs,
                        "labels": labels,
                        "full_bounds": bounds,
                        "bounds": bounds,
                        "step": 1,
                        "reverse_order": str(reverse_order),
                    }
                )
        self.state.dirty("da_coordinates")
        self.plotter.clear()
        self.plotter.view_isometric()

    def _data_slicing_changed(self) -> None:
        if self.builder.slicing is None:
            return
        for coord in self.state.da_coordinates:
            slicing = self.builder.slicing.get(coord["name"])
            if slicing:
                bounds = [slicing[0], slicing[1] - 1]  # stop is exclusive
                if bounds != coord.get("bounds"):
                    coord.update(dict(bounds=bounds))
                    self.state.dirty("da_coordinates")

                if slicing[2] != coord.get("step"):
                    coord.update(dict(step=slicing[2]))
                    self.state.dirty("da_coordinates")
        self._generate_preview()

    def _time_index_changed(self) -> None:
        self._generate_preview()

    def _generate_preview(self) -> None:
        if (
            self.builder.dataset is None
            or self.builder.data_array_name is None
            or self.builder.slicing is None
            or self._ui is None
        ):
            return
        if not self.state.cube_view_mode:
            self.ctrl.update_style(self._default_style)
            return
        preview_slicing = {}
        if self.builder.t is not None and self.builder.t_index is not None:
            preview_slicing[self.builder.t] = self.builder.t_index

        face_options = []
        if self.builder.x is not None and self.builder.y is not None:
            face_options += ["+Z", "-Z"]
        if self.builder.x is not None and self.builder.z is not None:
            face_options += ["+Y", "-Y"]
        if self.builder.y is not None and self.builder.z is not None:
            face_options += ["+X", "-X"]
        self.state.cube_preview_face_options = face_options
        if self.state.cube_preview_face not in face_options and len(face_options):
            self.state.cube_preview_face = face_options[0]

        axis_name = None
        if "X" in self.state.cube_preview_face:
            self.state.cube_preview_axes = dict(
                x=self.builder.y,
                y=self.builder.z,
            )
            axis_name = self.builder.x
        elif "Y" in self.state.cube_preview_face:
            self.state.cube_preview_axes = dict(
                x=self.builder.x,
                y=self.builder.z,
            )
            axis_name = self.builder.y
        elif "Z" in self.state.cube_preview_face:
            self.state.cube_preview_axes = dict(
                x=self.builder.x,
                y=self.builder.y,
            )
            axis_name = self.builder.z

        if axis_name is not None:
            axis_slicing = self.builder.slicing.get(axis_name)
            if axis_slicing is not None:
                preview_slicing[axis_name] = (
                    axis_slicing[0]
                    if "+" in self.state.cube_preview_face
                    else axis_slicing[1] - 1  # stop is exclusive
                )

            # update CSS to make blue slider thumb match preview outline
            thumb_selector = f'.{axis_name}-slider .v-slider-thumb[aria-valuenow="{preview_slicing[axis_name]}"]'
            thumb_style = thumb_selector + " { color: rgb(0, 100, 255) }"
            self.ctrl.update_style(self._default_style + thumb_style)

        if preview_slicing == self._preview_slicing:
            return
        self._preview_slicing = preview_slicing

        data = numpy.nan_to_num(
            self.builder.dataset[self.builder.data_array_name]
            .isel(preview_slicing)
            .to_numpy()
        )
        # if any dimensions are too small, increase size with gradients between values
        min_dim_length = 50
        for axis_index in range(len(data.shape)):
            length = data.shape[axis_index]
            if length < min_dim_length:
                gradient_steps = int(min_dim_length / (length - 1))
                gradients = []
                slices = list(
                    itertools.product(
                        *[
                            [slice(None)] if i == axis_index else list(range(l))
                            for i, l in enumerate(data.shape)
                        ]
                    )
                )
                for s in slices:
                    sdata = data[s]
                    gradient = []
                    for i in range(len(sdata) - 1):
                        gradient_portion = list(
                            numpy.linspace(
                                sdata[i], sdata[i + 1], gradient_steps, endpoint=False
                            )
                        )
                        gradient += gradient_portion
                    gradient.append(sdata[-1])
                    gradients.append(gradient)
                stack_axis = next(i for i in range(len(data.shape)) if i != axis_index)
                data = numpy.stack(gradients, axis=stack_axis)

        normalized_data = numpy.vectorize(
            lambda x, x_min, x_max: (x - x_min) / (x_max - x_min) * 255
        )(data, numpy.min(data), numpy.max(data)).astype(numpy.uint8)
        img = Image.fromarray(normalized_data)

        # apply transposes to match rendering orientation
        reverse_x = False
        reverse_y = False
        for coord in self.state.da_coordinates:
            if coord.get("name") == self.state.cube_preview_axes["x"]:
                reverse_x = coord.get("reverse_order") == "True"
            if coord.get("name") == self.state.cube_preview_axes["y"]:
                reverse_y = coord.get("reverse_order") == "True"
        if not reverse_y:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        if reverse_x != "+" in self.state.cube_preview_face:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)

        # encode image data
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

        # save encoded to state
        self.state.cube_preview = f"data:image/png;base64,{encoded}"

    def _mesh_changed(self) -> None:
        da = self.builder.data_array
        if da is None:
            self.state.da_size = 0
            self.state.ui_unapplied_changes = False
            return
        total_bytes = da.size * da.dtype.itemsize
        if total_bytes == 0:
            self.state.da_size = "0 bytes"
        exponents_map = {0: "bytes", 1: "KB", 2: "MB", 3: "GB"}
        for exponent in sorted(exponents_map.keys(), reverse=True):
            divisor = 1024**exponent
            suffix = exponents_map[exponent]
            if total_bytes > divisor:
                self.state.da_size = f"{round(total_bytes / divisor)} {suffix}"
                break
        self.state.ui_unapplied_changes = True

        if self.state.render_auto:
            self.apply_and_render()

    # -----------------------------------------------------
    # State change callbacks
    # -----------------------------------------------------
    @change("ui_search_catalogs")
    def _on_change_ui_search_catalogs(self, ui_search_catalogs, **kwargs):
        if ui_search_catalogs:
            self.state.catalog = self.state.available_catalogs[0]
        else:
            self.state.catalog = None

    @change("catalog")
    def _on_change_catalog(self, catalog, **kwargs):
        self.state.catalog_current_search = {}
        self.state.ui_catalog_search_message = None

    @change("dataset_info")
    def _on_change_dataset_info(self, dataset_info, **kwargs):
        self.plotter.clear()
        self.plotter.view_isometric()

        if dataset_info is not None:
            dataset_exists = False
            for dataset_group in self.state.available_datasets.values():
                for d in dataset_group:
                    if d["value"] == dataset_info:
                        dataset_exists = True
                        self.state.ui_more_info_link = d.get("link")
            if not dataset_exists:
                self.state.available_data_groups = [
                    "default",
                    *self.state.available_data_groups,
                ]
                self.state.data_group = "default"
                self.state.available_datasets["default"] = [
                    {
                        "value": dataset_info,
                        "name": dataset_info["id"],
                    }
                ]
                self.state.dirty("available_datasets")

        def load_dataset():
            self.builder.dataset_info = dataset_info

        self.run_as_async(load_dataset, unapplied_changes_state=None)

    @change("da_active")
    def _on_change_da_active(self, da_active, **kwargs):
        self.builder.data_array_name = da_active

    @change("da_x")
    def _on_change_da_x(self, da_x, **kwargs):
        self.builder.x = da_x

    @change("da_y")
    def _on_change_da_y(self, da_y, **kwargs):
        self.builder.y = da_y

    @change("da_z")
    def _on_change_da_z(self, da_z, **kwargs):
        self.builder.z = da_z

    @change("da_t")
    def _on_change_da_t(self, da_t, **kwargs):
        self.builder.t = da_t

    @change("da_t_index")
    def _on_change_da_t_index(self, da_t_index, **kwargs):
        self.builder.t_index = da_t_index

    @change("da_coordinates")
    def _on_change_da_coordinates(self, da_coordinates, **kwargs):
        bounds = {
            c.get("name"): [c["bounds"][0], c["bounds"][1] + 1]  # stop is exclusive
            for c in da_coordinates
        }
        steps = {c.get("name"): c.get("step") for c in da_coordinates}
        self.builder._auto_select_slicing(bounds, steps)

    @change("ui_action_name")
    def _on_change_action_name(self, ui_action_name, **kwargs):
        self.state.ui_action_message = None
        self.state.ui_action_config_file = None
        if ui_action_name == "Export":
            self.state.state_export = self.builder.export_config(None)

    @change("render_x_scale", "render_y_scale", "render_z_scale")
    def _on_change_render_scales(
        self, render_x_scale, render_y_scale, render_z_scale, **kwargs
    ):
        self.set_render_scales(
            x=int(render_x_scale), y=int(render_y_scale), z=int(render_z_scale)
        )

    @change(
        "render_colormap",
        "render_transparency",
        "render_transparency_function",
        "render_scalar_warp",
        "render_cartographic",
    )
    def _on_change_render_options(
        self,
        render_colormap,
        render_transparency,
        render_transparency_function,
        render_scalar_warp,
        render_cartographic,
        **kwargs,
    ):
        self.set_render_options(
            colormap=render_colormap,
            transparency=render_transparency,
            transparency_function=render_transparency_function,
            scalar_warp=render_scalar_warp,
            cartographic=render_cartographic,
        )

    @change("cube_view_mode", "cube_preview_face")
    def _on_change_cube_view(self, cube_view_mode, cube_preview_face, **kwargs):
        self._generate_preview()
