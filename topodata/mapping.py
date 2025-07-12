import json
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from glob import glob
from shapely.geometry import MultiPoint
from shapely.geometry import mapping
from rasterio.plot import show


# Ideas: Can check whether the boundaries of each map tile are contained within the polygon and sort of
# binary search through the thing by continuously cutting map tile in half. While cutting map tile, we can
# calculate the distance from the tile

# Need to figure out how to store the polygon borders


# Fetch the map tiles that are contained within the sight polygon
# Assumptions: All tiles contain a portion of the polygon
def fetch_map_tiles():
    """
    return type: glob of filepaths
    """
    return


# Need to find the edges of the sight polygon that are contained within the map tile
# Recursive algorithm
def is_contained_in_sight_polygon():
    return


# Not useful (using shapely now)
def sight_file_to_geojson(file_path):
    with open(file_path, "r") as f:
        sight_data = json.load(f)

    # 1 = lon, 2 = lat
    coordinates = list(map(lambda x: [x[1], x[0]], sight_data["sightPoints"]))

    geojson_data = {"type": "Polygon", "coordinates": [coordinates]}

    with open("data/sight_polygon.geojson", "w") as f:
        json.dump(geojson_data, f, indent=2)
    print(geojson_data)


# Combine all the map files into one raster
def get_master_raster(sight_polygon):
    # Fetch map tiles
    # tile_files = fetch_map_tiles()
    tile_files = glob("data/sandboxarea/*.tif")
    print(tile_files)

    tile_files_to_merge = [rasterio.open(t) for t in tile_files]

    master_raster, transform = merge(tile_files_to_merge)

    out_meta = tile_files_to_merge[0].meta.copy()
    out_meta.update(
        {
            "driver": "GTiff",
            "height": master_raster.shape[1],
            "width": master_raster.shape[2],
            "transform": transform,
        }
    )

    with rasterio.open("data/test_full_map.tif", "w", **out_meta) as full_map:
        full_map.write(master_raster)

    return "success"


# Mask the raster
def get_polygon_mask(tile, polygon_file):
    """
    Tile is rasterio dataset
    Returns a rasterio dataset
    """
    uncut_map = rasterio.open(tile, "r")
    print(uncut_map.bounds)

    # Need to form polygon from the shape file
    with open(polygon_file, "r") as f:
        sight_polygon = json.load(f)

    # TODO: need to format the polygon files to be ordered because polygons can't be made in a zig zag manner (might as well close the polygon as well)
    coordinates = sight_polygon.get("coordinates")[0]
    coordinates.append(coordinates[0])
    polygon = MultiPoint(coordinates).convex_hull
    polygon_points = mapping(polygon)

    masked_map, masked_transform = mask(uncut_map, [polygon_points])

    out_meta = uncut_map.meta.copy()
    out_meta.update(
        {
            "height": masked_map.shape[1],
            "width": masked_map.shape[2],
            "transformm": masked_transform,
        }
    )

    # TODO: write in chunks/blocks (use smaller size than window reading)
    with rasterio.open("test_masked_raster.tif", "w", **out_meta) as f:
        f.write(masked_map)

    print("success")


if __name__ == "__main__":
    # get_master_raster("a")
    sight_file_to_geojson("data/test_sight_points.json")
    get_polygon_mask("data/test_full_map.tif", "data/sight_polygon.geojson")
    # show("test_masked_raster.tif")

    # bounds are in lat and lon
    # data1 = rasterio.open('data/sandboxarea/n54_e036_1arc_v3.tif')
    # print(data1.count)
    # print(data1.width)
    # print(data1.height)
    # print(data1.dtypes)
    # print(data1.transform)

    # print(f"Bounds: {data1.bounds}")
    # print(data1.indexes)

    # print(data1.transform * (0,0))

    # data2 = rasterio.open('data/sandboxarea/n54_e037_1arc_v3.tif')
    # print(data2.width)
    # print(data2.height)
