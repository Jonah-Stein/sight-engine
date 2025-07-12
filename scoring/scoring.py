import rasterio
from rasterio.windows import Window
import torch
import torch.nn.functional as F
import numpy as np


TILE_SIZE = 512
# Only use odd values
MAX_WINDOW_SIZE = 5
RASTER_NAN_VALUE = -32767
RASTER_BANDS = [1]
weights = {
    "roughness": 0,
    "slope": 0,
}
"""
Sliding window size should be bigger with altitude and distance (distance should automatically be filtered in)
"""


# All of these notes still apply. This function though isn't scalable since it takes entire raster into memory
# going to leave out altitutde at first
# Need to create a distance band
# Going to calculate the calculations for every pixel on range of window sizes. Weight the score of each window size differently based on distance from line
def score_pixels(raster, device):
    with rasterio.open(raster) as src:
        elevation = src.read(1)
        out_meta = src.meta.copy()
    out_meta.update(dtype="float32")

    elevation_tensor = torch.from_numpy(elevation).to(
        device=device, dtype=torch.float32
    )
    mask = elevation_tensor != RASTER_NAN_VALUE

    elevation_tensor = torch.where(
        mask, elevation_tensor, torch.tensor(0.0, device=elevation_tensor.device)
    )

    pad = MAX_WINDOW_SIZE // 2
    x = elevation_tensor.unsqueeze(0).unsqueeze(0)
    mask = mask.unsqueeze(0).unsqueeze(0)

    x_padded = F.pad(x, (pad, pad, pad, pad), mode="reflect")
    mask_padded = F.pad(mask, (pad, pad, pad, pad), mode="reflect")

    patches = F.unfold(x_padded, kernel_size=MAX_WINDOW_SIZE)
    masks = F.unfold(mask_padded, kernel_size=MAX_WINDOW_SIZE)
    mean = (patches * masks).sum(dim=1) / masks.sum(dim=1).clamp(min=1)

    # Compute variance (ignore NaNs using mask)
    mean_expanded = mean.unsqueeze(1)  # [1, 1, H*W]
    diffsq = ((patches - mean_expanded) ** 2) * masks
    var = diffsq.sum(dim=1) / masks.sum(dim=1).clamp(min=1)
    std = torch.sqrt(var)

    # Reshape back to H, W
    H, W = elevation_tensor.shape
    if MAX_WINDOW_SIZE % 2 == 0:
        H += 1
        W += 1

    # TODO: Make the slicing variable
    std_map = std.view(H, W)[:10801, :3601]

    np_array = std_map.cpu().numpy().astype("float32")
    with rasterio.open("test_scoring.tif", "w", **out_meta) as f:
        f.write(np_array[np.newaxis, :, :])


# Does the same thing as above but only stores maxiumum of ~512x512 pixels in memory
def score_pixels_windowed(raster_file, device):
    PADDING = MAX_WINDOW_SIZE // 2
    with rasterio.open(raster_file, "r") as src:
        profile = src.profile.copy()
        profile.update(dtype="float32", count=1)

        with rasterio.open("tiled_scoring.tif", "w", **profile) as dst:
            for y in range(0, src.height, TILE_SIZE):
                tile_h = min(src.height - y, TILE_SIZE)
                for x in range(0, src.width, TILE_SIZE):
                    tile_w = min(src.width - x, TILE_SIZE)
                    # Get window
                    y0 = max(y - PADDING, 0)
                    x0 = max(x - PADDING, 0)
                    y1 = min(y + PADDING + tile_h, src.height)
                    x1 = min(x + PADDING + tile_w, src.width)
                    window = Window(x0, y0, x1 - x0, y1 - y0)

                    # change 1 to list if multiple bands are desired
                    # Reads the tile from the file
                    banded_tile = torch.from_numpy(
                        src.read(RASTER_BANDS, window=window)
                    ).to(device=device, dtype=torch.float32)

                    # TODO: Rework how mask is fetched. Should eventually be its own boolean layer
                    elevation = banded_tile[0]
                    mask_tensor = (
                        (elevation != RASTER_NAN_VALUE).unsqueeze(0).unsqueeze(0)
                    )

                    y_crop = y - y0
                    x_crop = x - x0

                    for band in range(len(RASTER_BANDS)):
                        tile_tensor = banded_tile[band].unsqueeze(0).unsqueeze(0)
                        _, _, initial_h, initial_w = tile_tensor.shape

                        # Pad if needed (at edges)
                        pad_top = min(y - y0, initial_h - 1)
                        pad_bottom = min((y + tile_h + PADDING) - y1, initial_h - 1)
                        pad_left = min(x - x0, initial_w - 1)
                        pad_right = min((x + tile_w + PADDING) - x1, initial_w - 1)

                        padding = (
                            pad_left,
                            pad_right,
                            pad_top,
                            pad_bottom,
                        )  # (L, R, T, B)
                        if any(p > 0 for p in padding):
                            tile_tensor = F.pad(tile_tensor, padding, mode="reflect")
                            mask_tensor = F.pad(mask_tensor, padding, mode="reflect")

                        # Get padded dimensions
                        _, _, H, W = tile_tensor.shape
                        H_out = H - MAX_WINDOW_SIZE + 1
                        W_out = W - MAX_WINDOW_SIZE + 1

                        patches = F.unfold(tile_tensor, kernel_size=MAX_WINDOW_SIZE)
                        masks = F.unfold(mask_tensor, kernel_size=MAX_WINDOW_SIZE)

                        # Compute variance (ignore NaNs using mask)
                        # This mean won't work in the future since it is local to the tile
                        mean = (patches * masks).sum(dim=1) / masks.sum(dim=1).clamp(
                            min=1
                        )
                        mean_expanded = mean.unsqueeze(1)  # [1, 1, H*W]
                        diffsq = ((patches - mean_expanded) ** 2) * masks
                        var = diffsq.sum(dim=1) / masks.sum(dim=1).clamp(min=1)
                        std = torch.sqrt(var)

                        std_map = std.view(H_out, W_out)

                        std_cropped = std_map[
                            y_crop : y_crop + TILE_SIZE, x_crop : x_crop + TILE_SIZE
                        ]

                        np_array = std_cropped.cpu().numpy().astype("float32")
                        dst.write(
                            np_array,
                            band + 1,
                            window=Window(x, y, np_array.shape[1], np_array.shape[0]),
                        )


# Not really sure what this does
# Think I made this to separate out the code
def score_tile(data_tile, mask_tile, window_size):
    """
    Scores an already padded tile
    """
    x = data_tile.unsqueeze(0).unsqueeze(0)
    mask = mask_tile.unsqueeze(0).unsqueeze(0)

    patches = F.unfold(x, kernel_size=window_size)
    masks = F.unfold(mask, kernel_size=window_size)
    mean = (patches * masks).sum(dim=1) / masks.sum(dim=1).clamp(min=1)

    # Compute variance (ignore NaNs using mask)
    mean_expanded = mean.unsqueeze(1)  # [1, 1, H*W]
    diffsq = ((patches - mean_expanded) ** 2) * masks
    var = diffsq.sum(dim=1) / masks.sum(dim=1).clamp(min=1)
    std = torch.sqrt(var)

    std_map = std.view()
    return std.squeeze()


if __name__ == "__main__":
    if torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    print("here")
    print(torch.backends.mps.is_available())
    # score_pixels("test_masked_raster.tif", device)
    score_pixels_windowed("test_masked_raster.tif", device)
