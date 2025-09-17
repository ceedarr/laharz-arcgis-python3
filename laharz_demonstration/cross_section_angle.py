"""
Angle-based cross section tracing for LaharZ PoC (no changes to original codebase).
This module provides a grid-walking DDA along a given normal angle from a center cell,
expanding symmetrically to both sides to accumulate area until targets are met.

- Pure NumPy-less implementation for portability; expects array-like A with __getitem__.
- Coordinates are integer (row, col). Bounds are inclusive [min, max] for both axes.
- Cell area is provided by caller (cell_size^2).

Note: This is a conceptual PoC; production integration will need alignment with
original CalcCrossSection semantics (elevation fill levels, pop rules, etc.).
"""
from __future__ import annotations
import math
from typing import Dict, List, Sequence, Tuple

PointRC = Tuple[int, int]


def _sign(x: float) -> int:
    return -1 if x < 0 else (1 if x > 0 else 0)


def _in_bounds(r: int, c: int, wXmin: int, wXmax: int, wYmin: int, wYmax: int) -> bool:
    return (wXmin <= r <= wXmax) and (wYmin <= c <= wYmax)


def dda_ray(rc: PointRC, angle: float, wXmin: int, wXmax: int, wYmin: int, wYmax: int, max_steps: int = 10000) -> List[PointRC]:
    """
    Integer grid DDA from a start cell center along a direction angle (radians),
    returning visited cells (including the start cell). Stops at bounds or max_steps.
    Row increases downward; angle measured with (dr, dc) = (sin, cos).
    """
    r_f = float(rc[0])
    c_f = float(rc[1])
    dr = math.sin(angle)
    dc = math.cos(angle)

    step_r = _sign(dr)
    step_c = _sign(dc)

    tDeltaR = abs(1.0 / dr) if dr != 0 else float('inf')
    tDeltaC = abs(1.0 / dc) if dc != 0 else float('inf')

    # Distance to first grid boundary from the center of the starting cell
    # Using cell-centered coordinates; we step to the next cell boundary in the direction of travel.
    r_boundary = (math.floor(r_f) + (1 if step_r > 0 else 0))
    c_boundary = (math.floor(c_f) + (1 if step_c > 0 else 0))

    tMaxR = ((r_boundary - r_f) / dr) if dr != 0 else float('inf')
    tMaxC = ((c_boundary - c_f) / dc) if dc != 0 else float('inf')

    visited: List[PointRC] = []

    curr_r = int(rc[0])
    curr_c = int(rc[1])
    if _in_bounds(curr_r, curr_c, wXmin, wXmax, wYmin, wYmax):
        visited.append((curr_r, curr_c))

    steps = 0
    while steps < max_steps:
        if tMaxR < tMaxC:
            r_f += step_r
            tMaxR += tDeltaR
        else:
            c_f += step_c
            tMaxC += tDeltaC
        curr_r = int(round(r_f))
        curr_c = int(round(c_f))
        if not _in_bounds(curr_r, curr_c, wXmin, wXmax, wYmin, wYmax):
            break
        if not visited or visited[-1] != (curr_r, curr_c):
            visited.append((curr_r, curr_c))
        steps += 1

    return visited


def trace_cross_section_symmetric(center: PointRC, normal_angle: float, wXmin: int, wXmax: int, wYmin: int, wYmax: int,
                                   targets: Sequence[float], cell_area: float, max_steps: int = 10000) -> Dict[str, object]:
    """
    Trace symmetric cross section around a center cell along +/- normal_angle, accumulating area
    until each target (list of planimetric areas) is reached.

    Returns dict with:
      - 'cells_left': List[PointRC]
      - 'cells_right': List[PointRC]
      - 'hits': List[int] (index in the sequence where each target was met; -1 if not met)
    """
    visited_left = dda_ray(center, normal_angle + math.pi, wXmin, wXmax, wYmin, wYmax, max_steps)
    visited_right = dda_ray(center, normal_angle, wXmin, wXmax, wYmin, wYmax, max_steps)

    area_cum = 0.0
    hits = [-1 for _ in targets]
    t_index = 0

    i = 0
    # Interleave expansion: left then right by rings of one cell each
    while t_index < len(targets) and (i < len(visited_left) or i < len(visited_right)):
        progressed = False
        if i < len(visited_left):
            area_cum += cell_area
            progressed = True
            while t_index < len(targets) and area_cum >= targets[t_index]:
                if hits[t_index] == -1:
                    hits[t_index] = i  # mark step index
                t_index += 1
        if i < len(visited_right):
            area_cum += cell_area
            progressed = True
            while t_index < len(targets) and area_cum >= targets[t_index]:
                if hits[t_index] == -1:
                    hits[t_index] = i
                t_index += 1
        if not progressed:
            break
        i += 1

    return {
        'cells_left': visited_left,
        'cells_right': visited_right,
        'hits': hits,
    }
