from trame.ui.vuetify import SinglePageWithDrawerLayout
from trame.widgets import html, vtk, vuetify


# Create single page layout type
# (FullScreenPage, SinglePage, SinglePageWithDrawer)
def initialize(server):
    state, ctrl = server.state, server.controller
    state.trame__title = "Pan3D Viewer"

    with SinglePageWithDrawerLayout(server) as layout:
        # Toolbar
        layout.title.set_text("Pan3D Viewer")
        with layout.toolbar:
            layout.toolbar.dense = True
            layout.toolbar.align = "center"
            vuetify.VSpacer()

            vuetify.VCheckbox(
                v_model=("view_edge_visiblity", True),
                dense=True,
                hide_details=True,
                on_icon="mdi-border-all",
                off_icon="mdi-border-outside",
            )

            with vuetify.VBtn(
                icon=True,
                click=ctrl.reset,
            ):
                vuetify.VIcon("mdi-crop-free")

            vuetify.VSlider(
                label="Resolution",
                v_model=("resolution", 1.0),
                min=0.5,
                max=1,
                step=0.25,
                hide_details=True,
                dense=True,
                style="max-width: 300px",
            )

        # Drawer
        with layout.drawer:
            with vuetify.VForm(classes="pa-1"):
                datasets = [
                    "air_temperature",
                    "basin_mask",
                    "eraint_uvz",
                ]
                vuetify.VSelect(
                    label="Choose a dataset",
                    v_model="dataset_path",
                    items=("datasets", datasets),
                    hide_details=True,
                    dense=True,
                    clearable=True,
                    outlined=True,
                    classes="pt-1",
                    click_clear=ctrl.clear_dataset,
                )

            vuetify.VCardText(
                "Available Arrays",
                v_show="dataset_ready",
            )

            with vuetify.VTreeview(
                v_show="dataset_ready",
                dense=True,
                activatable=True,
                active=("active_tree_nodes",),
                items=("data_vars",),
                item_key="name",
                update_active="array_active = $event[0]",
                multiple_active=False,
            ):
                with vuetify.Template(v_slot_label="{ item }"):
                    html.Span("{{ item?.name }}", classes="text-subtitle-2")

        # Content
        with layout.content:
            with html.Div(
                classes="d-flex",
                style="flex-direction: column; height: 100%",
            ):
                with vuetify.VContainer(
                    v_show="array_active",
                    classes="pa-2",
                    fluid=True,
                ):
                    with vuetify.VCol():
                        with vuetify.VRow():
                            html.Div("X:", classes="text-subtitle-2 pr-2")
                            vuetify.VSelect(
                                v_model=("grid_x_array", None),
                                items=("coordinates",),
                                hide_details=True,
                                dense=True,
                                clearable="True",
                                clear="grid_x_array = undefined",
                                style="max-width: 250px;",
                            )
                            vuetify.VSlider(
                                v_show="grid_x_array",
                                v_model=("x_scale", 0),
                                classes="ml-2",
                                label="Scale",
                                min=1,
                                max=1000,
                                step=10,
                                dense=True,
                                hide_details=True,
                                style="max-width: 250px;",
                            )

                        with vuetify.VRow():
                            html.Div("Y:", classes="text-subtitle-2 pr-2")
                            vuetify.VSelect(
                                v_model=("grid_y_array", None),
                                items=("coordinates",),
                                hide_details=True,
                                dense=True,
                                clearable="True",
                                clear="grid_y_array = undefined",
                                style="max-width: 250px;",
                            )
                            vuetify.VSlider(
                                v_show="grid_y_array",
                                v_model=("y_scale", 0),
                                classes="ml-2",
                                label="Scale",
                                min=1,
                                max=1000,
                                step=10,
                                dense=True,
                                hide_details=True,
                                style="max-width: 250px;",
                            )

                        with vuetify.VRow():
                            html.Div("Z:", classes="text-subtitle-2 pr-2")
                            vuetify.VSelect(
                                v_model=("grid_z_array", None),
                                items=("coordinates",),
                                hide_details=True,
                                dense=True,
                                clearable="True",
                                clear="grid_z_array = undefined",
                                style="max-width: 250px;",
                            )
                            vuetify.VSlider(
                                v_show="grid_z_array",
                                v_model=("z_scale", 0),
                                classes="ml-2",
                                label="Scale",
                                min=1,
                                max=1000,
                                step=10,
                                dense=True,
                                hide_details=True,
                                style="max-width: 250px;",
                            )

                        with vuetify.VRow():
                            html.Div("T:", classes="text-subtitle-2 pr-2")
                            vuetify.VSelect(
                                v_model=("grid_t_array", None),
                                items=("coordinates",),
                                hide_details=True,
                                dense=True,
                                clearable="True",
                                clear="grid_t_array = undefined",
                                style="max-width: 250px;",
                            )
                            vuetify.VSlider(
                                v_show="grid_t_array && time_max > 0",
                                v_model=("time_index", 0),
                                classes="ml-2",
                                label="Scale",
                                min=0,
                                max=("time_max", 0),
                                step=1,
                                dense=True,
                                hide_details=True,
                                style="max-width: 250px;",
                            )

                with html.Div(
                    v_show="array_active",
                    style="height: 100%",
                ):
                    with vtk.VtkRemoteView(
                        ctrl.get_render_window(),
                        interactive_ratio=1,
                    ) as vtk_view:
                        ctrl.view_update = vtk_view.update
                        ctrl.reset_camera = vtk_view.reset_camera

        # Footer
        # layout.footer.hide()
