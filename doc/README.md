# Thin Wall Centreline Algorithm

## Overview

This module (`d3dslic3r/thin_wall.py`) computes the centreline (skeleton) of thin-walled polygon features in a sliced 3D print path. The approach is based on a hatch-line intersection method described in the reference paper below.

## How It Works

1. **Hatch sweeping** — a set of parallel hatch lines is projected through the polygon at incremental angles (0° to 180°, in configurable steps). At each angle the lines intersect the polygon boundary in pairs.
2. **Midpoint skeleton** — the midpoint of each pair of intersection points is recorded. Collected across all angles, these midpoints approximate the medial axis (skeleton) of the polygon.
3. **Central line path** — skeleton segments from different hatch angles are cross-intersected. Points where segments at one angle cross segments at another angle lie on the true centreline.
4. **Ordering** — the resulting cloud of centreline points is sorted into a continuous path using nearest-neighbour ordering (`scipy.spatial.distance.cdist`), then trimmed to remove duplicates and find the natural starting point.

## Reference

The algorithm is implemented from:

> Riskus, A. & Maketas, R. (2016).  
> **A Method for Finding the Centerline of a Convex or Concave Polygon**  
> *Information Technology and Control*, Vol. 45, No. 3.  
> ISSN 1392–124X (print) / 2335–884X (online)

- Article page (including figures and diagrams): <https://itc.ktu.lt/index.php/ITC/article/view/12964>

The paper contains step-by-step diagrams illustrating how hatch lines sweep across an example polygon and how their midpoints converge on the centreline — refer to Figures 1–4 in the paper for a visual walkthrough of the method.

## Key Functions

| Function | Description |
|---|---|
| `get_skeleton_dict` | Builds a dictionary of midpoint chains for each hatch angle |
| `get_central_line_path` | Finds cross-intersections between skeleton segments to produce centreline points |
| `order_points_cdist` | Sorts an unordered point cloud into a continuous path |
| `get_ordered_central_line_path` | Top-level entry point — runs the full pipeline for a single outline |

s
