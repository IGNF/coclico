import argparse
import logging
from pathlib import Path

import pdal

import coclico.io
import coclico.metrics.commons as commons
import coclico.metrics.occupancy_map as occupancy_map
from coclico.malt0.malt0 import MALT0


def create_mnx_map(las_file, class_weights, output_tif, pixel_size, no_data_value=-9999):
    reader = pdal.Reader.las(filename=str(las_file), tag="IN")
    pipeline = reader.pipeline()
    info = pipeline.quickinfo
    bounds = info["readers.las"]["bounds"]
    top_left, nb_pixels = commons.get_raster_geometry_from_las_bounds(
        (
            bounds["minx"],
            bounds["miny"],
            bounds["maxx"],
            bounds["maxy"],
        ),
        pixel_size,
    )
    lower_left = (top_left[0], top_left[1] - nb_pixels[1] * pixel_size)

    raster_tags = []
    for k in sorted(class_weights.keys()):
        individual_classes = commons.split_composed_class(k)
        raster_tag = f"RASTER_{k.replace(' ', '')}"
        raster_tags.append(raster_tag)
        pipeline |= pdal.Filter.range(
            limits=",".join(f"Classification[{c}:{c}]" for c in individual_classes), inputs=["IN"]
        )

        pipeline |= pdal.Filter.delaunay()

        pipeline |= pdal.Filter.faceraster(
            resolution=str(pixel_size),
            origin_x=str(lower_left[0] - pixel_size / 2),
            origin_y=str(lower_left[1] + pixel_size / 2),
            width=str(nb_pixels[0]),
            height=str(nb_pixels[1]),
            tag=raster_tag,
        )

    pipeline |= pdal.Writer.raster(
        gdaldriver="GTiff",
        nodata=no_data_value,
        data_type="float32",
        filename=str(output_tif),
        inputs=raster_tags,
        rasters=["faceraster"],
    )
    pipeline.execute()


def compute_metric_intrinsic(
    las_file: Path,
    config_file: Path,
    output_tif: Path,
    occupancy_tif: Path = None,
    pixel_size: float = 0.5,
    no_data_value=-9999,
):
    """
    Create for each class that is in config_file keys:
    - a height raster (kind of digital surface model for a single class, called mnx here)
    - if "occupancy_tif" has a value, a 2d occupancy map

    both are saved single output_tif files with one layer per class (the classes are sorted alphabetically).

    Args:
        las_file (Path): path to the las file on which to generate malt0 intrinsic metric
        config_file (Path): class weights dict in the config file (to know for which classes to generate the rasters)
        output_tif (Path): path to output height raster
        occupancy_tif (Path, optional): path to the optional occupancy map tif (Leave it to None except for the
        reference folder). Defaults to None.
        pixel_size (float, optional): size of the output rasters pixels. Defaults to 0.5.
        no_data_value (int, optional): no_data value for the output raster. Defaults to -9999.
    """
    config_dict = coclico.io.read_config_file(config_file)
    class_weights = config_dict[MALT0.metric_name]["weights"]

    if occupancy_tif:
        occupancy_tif.parent.mkdir(parents=True, exist_ok=True)
        occupancy_map.create_occupancy_map(las_file, class_weights, occupancy_tif, pixel_size)

    output_tif.parent.mkdir(parents=True, exist_ok=True)
    create_mnx_map(las_file, class_weights, output_tif, pixel_size, no_data_value)


def parse_args():
    parser = argparse.ArgumentParser("Run malt0 intrinsic metric on one tile")
    parser.add_argument("-i", "--input-file", type=Path, required=True, help="Path to the LAS file")
    parser.add_argument("-o", "--output-mnx-file", type=Path, required=True, help="Path to the TIF output file")
    parser.add_argument(
        "-oc",
        "--output-occupancy-file",
        type=Path,
        default=None,
        help="Path to the optional occupancy map TIF output file",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        type=Path,
        required=True,
        help="Coclico configuration file",
    )
    parser.add_argument("-p", "--pixel-size", type=float, required=True, help="Size of the output raster pixels")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    compute_metric_intrinsic(
        las_file=Path(args.input_file),
        config_file=args.config_file,
        output_tif=Path(args.output_mnx_file),
        occupancy_tif=Path(args.output_occupancy_file) if args.output_occupancy_file else None,
    )
