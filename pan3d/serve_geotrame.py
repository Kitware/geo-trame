from argparse import ArgumentParser, BooleanOptionalAction
from pan3d.dataset_builder import DatasetBuilder


def serve():
    parser = ArgumentParser(
        prog="Pan3D",
        description="Launch the Pan3D GeoTrame App",
    )

    parser.add_argument("--config_path")
    parser.add_argument("--dataset")
    parser.add_argument("--resolution", type=int)
    parser.add_argument("--catalogs", nargs="+")
    parser.add_argument("--server", action=BooleanOptionalAction)
    parser.add_argument("--debug", action=BooleanOptionalAction)

    args = parser.parse_args()

    builder = DatasetBuilder(
        dataset=args.dataset,
        catalogs=args.catalogs,
        resolution=args.resolution,
    )
    if args.config_path:
        builder.import_config(args.config_path)
    builder.viewer.start(debug=args.debug)


if __name__ == "__main__":
    serve()
