from trame.widgets import html, vuetify


class MainDrawer(html.Div):
    def __init__(
        self,
        dataset_ready="dataset_ready",
        dataset_path="dataset_path",
        data_vars="data_vars",
        data_attrs="data_attrs",
        available_datasets="available_datasets",
        more_info_link="more_info_link",
        array_active="array_active",
        x_array="x_array",
        y_array="y_array",
        z_array="z_array",
        t_array="t_array",
        t_index="t_index",
    ):
        super().__init__(classes="pa-2")
        with self:
            vuetify.VSelect(
                label="Choose a dataset",
                v_model=dataset_path,
                items=(available_datasets,),
                item_text="name",
                item_value="url",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="pt-1",
            )

            html.A(
                "More information about this dataset",
                href=(more_info_link,),
                v_show=(more_info_link,),
                target="_blank",
            )

            vuetify.VCardText(
                "Available Arrays",
                v_show=dataset_ready,
                classes="font-weight-bold",
            )
            vuetify.VCardText(
                "No data variables found.",
                v_show=(f"{dataset_ready} && {data_vars}.length === 0",),
            )
            with vuetify.VTreeview(
                v_show=dataset_ready,
                dense=True,
                activatable=True,
                active=(f"[{array_active}]",),
                items=(data_vars,),
                item_key="name",
                update_active=f"""
                            {array_active} = $event[0];
                            {x_array} = null;
                            {y_array} = null;
                            {z_array} = null;
                            {t_array} = null;
                            {t_index} = 0;
                        """,
                multiple_active=False,
            ):
                with vuetify.Template(v_slot_label="{ item }"):
                    html.Span("{{ item?.name }}", classes="text-subtitle-2")

            attrs_headers = [
                {"text": "key", "value": "key"},
                {"text": "value", "value": "value"},
            ]
            vuetify.VCardText(
                "Data Attributes",
                v_show=f"{data_attrs}.length",
                classes="font-weight-bold",
            )
            vuetify.VDataTable(
                v_show=f"{data_attrs}.length",
                dense=True,
                items=(data_attrs,),
                headers=("headers", attrs_headers),
                hide_default_header=True,
            )
