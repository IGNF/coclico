import argparse
import json
import logging
from pathlib import Path
from typing import Dict

import pdal

from coclico.metrics.commons import (
    get_raster_geometry_from_las_bounds,
    split_composed_class,
)
from coclico.metrics.occupancy_map import create_multilayer_2d_occupancy_map


def create_multilayer_2d_mnx_map(las_file, class_weights, output_tif, pixel_size, no_data_value=-9999):
    reader = pdal.Reader.las(filename=str(las_file), tag="IN")
    pipeline = reader.pipeline()
    info = pipeline.quickinfo
    bounds = info["readers.las"]["bounds"]
    top_left, nb_pixels = get_raster_geometry_from_las_bounds(
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
        individual_classes = split_composed_class(k)
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
    class_weights: Dict,
    output_tif: Path,
    occupancy_tif: Path = None,
    pixel_size: float = 0.5,
    no_data_value=-9999,
):
    """Create 2d occupancy map for each classe that is in class_weights keys, and save result in a single output_tif
    file with one layer per class (the classes are sorted).

    Args:
        las_file (Path): path to the las file on which to generate mpla0 intrinsic metric
        class_weights (Dict): class weights dict (to know for which classes to generate the binary map)
        output_tif (Path): path to output
        pixel_size (float): size of the output raster pixels
    """
    if occupancy_tif:
        occupancy_tif.parent.mkdir(parents=True, exist_ok=True)
        create_multilayer_2d_occupancy_map(las_file, class_weights, occupancy_tif, pixel_size)

    output_tif.parent.mkdir(parents=True, exist_ok=True)
    create_multilayer_2d_mnx_map(las_file, class_weights, output_tif, pixel_size, no_data_value)


def parse_args():
    parser = argparse.ArgumentParser("Run malt0 intrinsic metric on one tile")
    parser.add_argument("-i", "--input-file", type=Path, required=True, help="Path to the LAS file")
    parser.add_argument("-o", "--output-mnx-file", type=Path, required=True, help="Path to the TIF output file")
    parser.add_argument(
        "-c",
        "--output-occupancy-file",
        type=Path,
        default=None,
        help="Path to the optional occupancy map TIF output file",
    )
    parser.add_argument(
        "-w",
        "--class-weights",
        type=json.loads,
        required=True,
        help="Dictionary of the classes weights for the metric (as a string)",
    )
    parser.add_argument("-p", "--pixel-size", type=float, required=True, help="Size of the output raster pixels")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    compute_metric_intrinsic(
        las_file=Path(args.input_file),
        class_weights=args.class_weights,
        output_tif=Path(args.output_mnx_file),
        occupancy_tif=Path(args.output_occupancy_file) if args.output_occupancy_file else None,
    )
