from trame.widgets import html, vuetify3 as vuetify


class CoordinateConfigure(vuetify.VCard):
    def __init__(
        self,
        axes,
        coordinates,
        coordinate_info,
        expanded_coordinates,
        coordinate_select_axis_function,
        coordinate_change_slice_function,
        coordinate_toggle_expansion_function,
        axis_info=None,  # Defined only after an axis is selected for this coord
    ):
        super().__init__(width="95%", classes="ml-3 mb-1")

        with self:
            with vuetify.VExpansionPanels(
                model_value=(expanded_coordinates, []),
                accordion=True,
                multiple=True,
                v_show=coordinate_info,
                update_modelValue=(
                    coordinate_toggle_expansion_function,
                    f"[{coordinate_info}.name]",
                ),
            ):
                with vuetify.VExpansionPanel(value=(f"{coordinate_info}?.name", 0)):
                    vuetify.VExpansionPanelTitle("{{ %s?.name }}" % coordinate_info)
                    with vuetify.VExpansionPanelText():
                        vuetify.VCardSubtitle("Attributes")
                        with vuetify.VTable(density="compact", v_show=coordinate_info):
                            with html.Tbody():
                                with html.Tr(
                                    v_for=f"data_attr in {coordinate_info}?.attrs",
                                ):
                                    html.Td("{{ data_attr.key }}")
                                    html.Td("{{ data_attr.value }}")

                        if axis_info and axis_info["index_var"] != "undefined":
                            vuetify.VCardSubtitle("Select index", classes="mt-3")
                            with vuetify.VSlider(
                                v_model=axis_info["index_var"],
                                min=0,
                                max=(
                                    f"{coordinate_info}?.size - 1",
                                    0,
                                ),
                                step=(f"{coordinate_info}?.step", 0),
                                classes="mx-5",
                            ):
                                with vuetify.Template(
                                    v_slot_append="{ props, item, parent }"
                                ):
                                    vuetify.VTextField(
                                        v_model=axis_info["index_var"],
                                        min=0,
                                        max=(
                                            f"{coordinate_info}?.size - 1",
                                            0,
                                        ),
                                        step=(f"{coordinate_info}?.step", 0),
                                        hide_details=True,
                                        density="compact",
                                        style="width: 80px",
                                        type="number",
                                        __properties=["min", "max"],
                                    )

                        vuetify.VCardSubtitle("Select values", classes="mt-3")
                        with vuetify.VContainer(
                            classes="d-flex pa-0", style="column-gap: 3px"
                        ):
                            vuetify.VTextField(
                                model_value=(f"{coordinate_info}?.start", 0),
                                label="Start",
                                hide_details=True,
                                density="compact",
                                type="number",
                                min=(
                                    f"parseFloat(+ {coordinate_info}?.range[0].toFixed(2))",
                                    0,
                                ),
                                max=(
                                    f"parseFloat(+ {coordinate_info}?.stop.toFixed(2))",
                                    0,
                                ),
                                step="0.01",
                                __properties=["min", "max", "step"],
                                input=(
                                    coordinate_change_slice_function,
                                    f"[{coordinate_info}.name, 'start', $event.target.value]",
                                ),
                                __events=[("input", "input.prevent")],
                                style="flex-grow: 1",
                            )
                            vuetify.VTextField(
                                model_value=(f"{coordinate_info}?.stop", 0),
                                label="Stop",
                                hide_details=True,
                                density="compact",
                                type="number",
                                min=(
                                    f"parseFloat(+ {coordinate_info}?.start.toFixed(2))",
                                    0,
                                ),
                                max=(
                                    f"parseFloat(+ {coordinate_info}?.range[1].toFixed(2))",
                                    0,
                                ),
                                step="0.01",
                                __properties=["min", "max", "step"],
                                input=(
                                    coordinate_change_slice_function,
                                    f"[{coordinate_info}.name, 'stop', $event.target.value]",
                                ),
                                __events=[("input", "input.prevent")],
                                style="flex-grow: 1",
                            )
                            vuetify.VTextField(
                                model_value=(f"{coordinate_info}?.step", 0),
                                label="Step",
                                hide_details=True,
                                density="compact",
                                type="number",
                                min="1",
                                max=(f"{coordinate_info}?.size", 0),
                                __properties=["min", "max"],
                                input=(
                                    coordinate_change_slice_function,
                                    f"[{coordinate_info}.name, 'step', $event.target.value]",
                                ),
                                __events=[("input", "input.prevent")],
                                style="flex-grow: 1",
                            )

                        vuetify.VCardSubtitle("Assign axis", classes="mt-3")
                        with vuetify.VSelect(
                            items=(axes,),
                            item_title="label",
                            item_value="name_var",
                            model_value=(axis_info or "undefined",),
                            clearable=True,
                            click_clear=(
                                coordinate_select_axis_function,
                                # args: coord name, current axis, new axis
                                f"[{axis_info['name_var']}, '{axis_info['name_var']}', 'undefined']",
                            )
                            if axis_info
                            else "undefined",
                            update_modelValue=(
                                coordinate_select_axis_function,
                                # args: coord name, current axis, new axis
                                f"""[
                                    {coordinate_info}.name,
                                    '{axis_info["name_var"] if axis_info else "undefined"}',
                                    $event
                                ]""",
                            ),
                        ):
                            with vuetify.Template(
                                v_slot_selection="{ props, item, parent }"
                            ):
                                html.Span(axis_info["label"] if axis_info else "")
