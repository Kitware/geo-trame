import os


def has_gpu_rendering():
    # Detect known environments without gpu rendering
    target_env_vars = ["BINDER_REQUEST"]
    return not any(os.environ.get(k) for k in target_env_vars)


XARRAY_EXAMPLES = [
    # from https://docs.xarray.dev/en/stable/generated/xarray.tutorial.open_dataset.html
    {
        "name": "XArray Examples - Air Temperature",
        "value": {"source": "xarray", "id": "air_temperature"},
    },
    {
        "name": "XArray Examples - Ocean Basins",
        "value": {"source": "xarray", "id": "basin_mask"},
    },
    {
        "name": "XArray Examples - Ice Velocity",
        "value": {"source": "xarray", "id": "ASE_ice_velocity"},
    },
    {
        "name": "XArray Examples - Regional Arctic System Model",
        "value": {"source": "xarray", "id": "rasm"},
    },
    {
        "name": "XArray Examples - Regional Ocean Model System",
        "value": {"source": "xarray", "id": "ROMS_example"},
    },
    {
        "name": "XArray Examples - ERA-Interim analysis",
        "value": {"source": "xarray", "id": "eraint_uvz"},
    },
    {
        "name": "XArray Examples - NOAA Sea Surface Temperatures",
        "value": {"source": "xarray", "id": "ersstv5"},
    },
]


initial_state = {
    "trame__title": "GeoTrame",
    "dataset_ready": False,
    "state_export": None,
    "available_catalogs": [],
    "catalog": None,
    "catalog_current_search": {},
    "available_data_groups": [
        {"name": "Xarray", "value": "xarray"},
    ],
    "data_group": "xarray",
    "ui_group_loading": False,
    "available_datasets": {"xarray": XARRAY_EXAMPLES},
    "dataset_info": None,
    "da_active": None,
    "da_vars": [],
    "da_attrs": [],
    "da_coordinates": [],
    "da_x": None,
    "da_y": None,
    "da_z": None,
    "da_t": None,
    "da_t_index": 0,
    "da_size": None,
    "da_auto_slicing": True,
    "cube_view_mode": False,
    "cube_preview": None,
    "cube_preview_face": "-Z",
    "cube_preview_face_options": [],
    "cube_preview_axes": None,
    "ui_loading": False,
    "ui_import_loading": False,
    "ui_main_drawer": False,
    "ui_axis_drawer": False,
    "ui_unapplied_changes": False,
    "ui_error_message": None,
    "ui_more_info_link": None,
    "ui_expanded_coordinates": [],
    "ui_action_name": None,
    "ui_action_message": None,
    "ui_action_config_file": None,
    "ui_search_catalogs": False,
    "ui_catalog_term_search_loading": False,
    "ui_catalog_search_message": None,
    "render_auto": False,
    "render_x_scale": 1,
    "render_y_scale": 1,
    "render_z_scale": 1,
    "render_scalar_warp": False,
    "render_cartographic": False,
    "render_transparency": False,
    "render_transparency_function": "linear",
    "render_transparency_function_options": [
        "linear",
        "linear_r",
        "geom",
        "geom_r",
        "sigmoid",
        "sigmoid_r",
    ],
    "render_colormap": "viridis",
    "render_colormap_options": [
        "viridis",
        "plasma",
        "inferno",
        "magma",
        "terrain",
        "ocean",
        "cividis",
        "seismic",
        "rainbow",
        "jet",
        "turbo",
        "gray",
        "cool",
        "hot",
        "coolwarm",
        "hsv",
    ],
}

coordinate_auto_selection = {
    "x": ["x", "i", "lon", "len", "nx"],
    "y": ["y", "j", "lat", "width", "ny"],
    "z": ["z", "k", "depth", "height", "nz", "level"],
    "t": ["t", "time", "year", "month", "date", "day", "hour", "minute", "second"],
}
