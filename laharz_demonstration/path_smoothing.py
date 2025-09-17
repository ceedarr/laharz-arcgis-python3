"""
Local path smoothing utilities for LaharZ PoC (no changes to original codebase).
- Estimate tangent angle along a stream path from recent cell coordinates.
- Compute normal angle with optional angular velocity limiting.

Angles are in radians by default.
This module is self-contained and does not import arcpy.
"""
from __future__ import annotations
import math
from typing import Iterable, List, Optional, Sequence, Tuple

PointRC = Tuple[int, int]  # (row, col)


def _atan2(dy: float, dx: float) -> float:
    """atan2 wrapper returning angle in [-pi, pi]."""
    return math.atan2(dy, dx)


def normalize_angle(theta: float) -> float:
    """Normalize angle to [-pi, pi]."""
    while theta > math.pi:
        theta -= 2 * math.pi
    while theta <= -math.pi:
        theta += 2 * math.pi
    return theta


def angle_diff(a: float, b: float) -> float:
    """Smallest signed difference a-b in [-pi, pi]."""
    d = normalize_angle(a - b)
    return d


def estimate_tangent_angle(points_window: Sequence[PointRC]) -> Optional[float]:
    """
    Estimate tangent angle from a short window of grid indices using simple linear regression.
    - points_window: sequence of (row, col) with chronological order (oldest -> newest)
    Returns angle in radians (direction of increasing index along path), or None if not enough points.

    We fit col = a*row + b (or row = a'*col + b') depending on variance to reduce numerical issues.
    The tangent direction is along the vector of increasing index from the first to last point when regression is degenerate.
    """
    n = len(points_window)
    if n < 2:
        return None

    rows = [p[0] for p in points_window]
    cols = [p[1] for p in points_window]

    mean_r = sum(rows) / n
    mean_c = sum(cols) / n

    # Compute variances
    var_r = sum((r - mean_r) ** 2 for r in rows)
    var_c = sum((c - mean_c) ** 2 for c in cols)

    if var_r + var_c == 0:
        # All same point; fallback to direction between endpoints
        dr = rows[-1] - rows[0]
        dc = cols[-1] - cols[0]
        if dr == 0 and dc == 0:
            return None
        return _atan2(dr, dc)

    # Prefer regressing the variable with smaller variance as dependent to reduce instability
    if var_r > var_c:
        # regress row = a*col + b
        Scc = var_c
        Sc = sum(cols)
        Sr = sum(rows)
        Sc2 = sum(c * c for c in cols)
        Scr = sum(c * r for c, r in zip(cols, rows))
        denom = (n * Sc2 - Sc * Sc)
        if denom == 0:
            dr = rows[-1] - rows[0]
            dc = cols[-1] - cols[0]
            if dr == 0 and dc == 0:
                return None
            return _atan2(dr, dc)
        a = (n * Scr - Sc * Sr) / denom
        # Direction vector along increasing col: drow/dcol = a -> (dr, dc) ~ (a, 1)
        dr, dc = a, 1.0
    else:
        # regress col = a*row + b
        Srr = var_r
        Sr = sum(rows)
        Sc = sum(cols)
        Sr2 = sum(r * r for r in rows)
        Src = sum(r * c for r, c in zip(rows, cols))
        denom = (n * Sr2 - Sr * Sr)
        if denom == 0:
            dr = rows[-1] - rows[0]
            dc = cols[-1] - cols[0]
            if dr == 0 and dc == 0:
                return None
            return _atan2(dr, dc)
        a = (n * Src - Sr * Sc) / denom
        # Direction vector along increasing row: dcol/drow = a -> (dr, dc) ~ (1, a)
        dr, dc = 1.0, a

    theta = _atan2(dr, dc)

    # Orient angle from first to last point when possible
    v_dr = rows[-1] - rows[0]
    v_dc = cols[-1] - cols[0]
    if v_dr != 0 or v_dc != 0:
        theta_v = _atan2(v_dr, v_dc)
        # Choose orientation minimizing difference to endpoint vector
        if abs(angle_diff(theta + math.pi, theta_v)) < abs(angle_diff(theta, theta_v)):
            theta = normalize_angle(theta + math.pi)

    return theta


def compute_normal_angle(tangent_angle: float, max_delta_deg: Optional[float] = None, prev_normal: Optional[float] = None) -> float:
    """
    Compute normal angle (tangent + 90 deg), optionally limiting angular velocity vs previous normal.
    - tangent_angle: radians
    - max_delta_deg: if provided, clamp angle change per step to this value
    - prev_normal: previous normal angle (radians) for smoothing
    Returns: normal angle in radians.
    """
    normal = normalize_angle(tangent_angle + math.pi / 2.0)
    if prev_normal is None or max_delta_deg is None:
        return normal
    max_delta = math.radians(max_delta_deg)
    d = angle_diff(normal, prev_normal)
    if abs(d) <= max_delta:
        return normal
    return normalize_angle(prev_normal + math.copysign(max_delta, d))


def window_push(window: List[PointRC], point: PointRC, maxlen: int) -> None:
    """Push a point to the window list with bounded length."""
    window.append(point)
    if len(window) > maxlen:
        del window[0]
