# -------------------------------------------------------------
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# -------------------------------------------------------------

import numpy as np
import wsi.filter as filter
import wsi.slide as slide
import math
from PIL import Image, ImageDraw, ImageFont

ROW_TILE_SIZE = 128
COL_TILE_SIZE = 128
TISSUE_THRESHOLD_PERCENT = 50


def get_num_tiles(np_img, row_tile_size, col_tile_size):
  """
  Obtain the number of vertical and horizontal tiles that an image can be divided into given a row tile size and
  a column tile size.

  Args:
    np_img: Image as a NumPy array.
    row_tile_size: Number of pixels in a tile row.
    col_tile_size: Number of pixels in a tile column.

  Returns:
    Tuple consisting of the number of vertical tiles and the number of horizontal tiles that the image can be divided
    into given the row tile size and the column tile size.
  """
  rows, cols, _ = np_img.shape
  num_row_tiles = math.ceil(rows / row_tile_size)
  num_col_tiles = math.ceil(cols / col_tile_size)
  return num_row_tiles, num_col_tiles


def get_tile_indices(np_img, row_tile_size, col_tile_size):
  """
  Obtain a list of tile coordinates (starting row, ending row, starting column, ending column).

  Args:
    np_img: Image as a NumPy array.
    row_tile_size: Number of pixels in a tile row.
    col_tile_size: Number of pixels in a tile column.

  Returns:
    List of tuples representing tile coordinates consisting of starting row, ending row,
    starting column, ending column.
  """
  indices = list()
  rows, cols, _ = np_img.shape
  num_row_tiles, num_col_tiles = get_num_tiles(np_img, row_tile_size, col_tile_size)
  for r in range(0, num_row_tiles):
    start_r = r * row_tile_size
    end_r = ((r + 1) * row_tile_size) if (r < num_row_tiles - 1) else rows
    for c in range(0, num_col_tiles):
      start_c = c * col_tile_size
      end_c = ((c + 1) * col_tile_size) if (c < num_col_tiles - 1) else cols
      indices.append((start_r, end_r, start_c, end_c))
  return indices


def display_tile_summary(np_img, tile_indices, row_tile_size, col_tile_size, thresh_color=(0, 255, 0),
                         below_thresh_color=(255, 255, 0), no_tissue_color=(255, 0, 0), text_color=(255, 255, 255),
                         text_size=22,
                         font_path="/Library/Fonts/Arial Bold.ttf"):
  num_row_tiles, num_col_tiles = get_num_tiles(np_img, row_tile_size, col_tile_size)
  summary_img = np.zeros([ROW_TILE_SIZE * num_row_tiles, COL_TILE_SIZE * num_col_tiles, np_img.shape[2]],
                         dtype=np.uint8)
  # add gray edges so that summary text does not get cut off
  summary_img.fill(120)
  summary_img[0:np_img.shape[0], 0:np_img.shape[1]] = np_img
  summary = filter.np_to_pil(summary_img)
  draw = ImageDraw.Draw(summary)
  count = 0
  for t in tile_indices:
    count += 1
    r_s, r_e, c_s, c_e = t
    np_tile = np_img[r_s:r_e, c_s:c_e]
    tissue_percentage = filter.tissue_percent(np_tile)
    print("TILE [%d:%d, %d:%d]: Tissue %f%%" % (r_s, r_e, c_s, c_e, tissue_percentage))
    if (tissue_percentage >= TISSUE_THRESHOLD_PERCENT):
      draw.rectangle([(c_s, r_s), (c_e - 1, r_e - 1)], outline=thresh_color)
      draw.rectangle([(c_s + 1, r_s + 1), (c_e - 2, r_e - 2)], outline=thresh_color)
    elif (tissue_percentage > 0) and (tissue_percentage < TISSUE_THRESHOLD_PERCENT):
      draw.rectangle([(c_s, r_s), (c_e - 1, r_e - 1)], outline=below_thresh_color)
      draw.rectangle([(c_s + 1, r_s + 1), (c_e - 2, r_e - 2)], outline=below_thresh_color)
    else:
      draw.rectangle([(c_s, r_s), (c_e - 1, r_e - 1)], outline=no_tissue_color)
      draw.rectangle([(c_s + 1, r_s + 1), (c_e - 2, r_e - 2)], outline=no_tissue_color)
    # filter.display_img(np_tile, text=label, size=14, bg=True)
    label = "#%d\n%4.2f%%" % (count, tissue_percentage)
    font = ImageFont.truetype(font_path, size=text_size)
    draw.text((c_s + 2, r_s + 2), label, text_color, font=font)
  summary.show()


img_path = slide.get_filter_image_result(16)
img = slide.open_image(img_path)
np_img = filter.pil_to_np_rgb(img)

tile_indices = get_tile_indices(np_img, ROW_TILE_SIZE, COL_TILE_SIZE)
display_tile_summary(np_img, tile_indices, ROW_TILE_SIZE, COL_TILE_SIZE)