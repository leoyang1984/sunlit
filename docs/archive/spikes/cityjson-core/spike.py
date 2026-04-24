import math
import time

import numpy as np
import pandas as pd
import pvlib
import trimesh
from cjio import cityjson


def transformed_vertices(cj):
    vertices = np.array(cj.j["vertices"], dtype=float)
    transform = cj.j.get("transform", {})
    scale = np.array(transform.get("scale", [1, 1, 1]), dtype=float)
    translate = np.array(transform.get("translate", [0, 0, 0]), dtype=float)
    return vertices * scale + translate


def surfaces_for_geometry(geom):
    boundaries = geom.get("boundaries", [])
    gtype = geom.get("type")
    if gtype in ("MultiSurface", "CompositeSurface"):
        return boundaries
    if gtype == "Solid":
        return [surface for shell in boundaries for surface in shell]
    if gtype in ("MultiSolid", "CompositeSolid"):
        return [surface for solid in boundaries for shell in solid for surface in shell]
    return []


def mesh_from_cityjson(cj):
    vertices = transformed_vertices(cj)
    faces = []
    building_count = 0
    building_bounds = []
    for obj in cj.j["CityObjects"].values():
        if obj.get("type") != "Building":
            continue
        building_count += 1
        used = set()
        for geom in obj.get("geometry", []):
            for surface in surfaces_for_geometry(geom):
                if not surface:
                    continue
                ring = surface[0]
                used.update(ring)
                for i in range(1, len(ring) - 1):
                    faces.append([ring[0], ring[i], ring[i + 1]])
        if used:
            pts = vertices[list(used)]
            building_bounds.append((pts.min(axis=0), pts.max(axis=0)))
    mesh = trimesh.Trimesh(vertices=vertices, faces=np.array(faces), process=False)
    return mesh, building_count, building_bounds


def sun_direction(azimuth, altitude):
    az = math.radians(azimuth)
    alt = math.radians(altitude)
    return np.array([
        math.sin(az) * math.cos(alt),
        math.cos(az) * math.cos(alt),
        math.sin(alt),
    ])


with open("sample.cityjson") as f:
    cm = cityjson.reader(f)
mesh, building_count, building_bounds = mesh_from_cityjson(cm)
print(f"Loaded {building_count} buildings from CityJSON")
print(f"Combined mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")

target_min, target_max = max(building_bounds, key=lambda b: b[1][2] - b[0][2])
point = np.array([(target_min[0] + target_max[0]) / 2, target_max[1] + 3.0, 1.5])
print(f"Test point: ({point[0]:.3f}, {point[1]:.3f}, {point[2]:.3f})")

when = pd.Timestamp("2026-01-20 12:00:00", tz="Europe/Amsterdam")
solar = pvlib.solarposition.get_solarposition(when, latitude=52.0, longitude=4.36)
azimuth = float(solar.iloc[0]["azimuth"])
altitude = float(solar.iloc[0]["apparent_elevation"])
print(f"Sun azimuth: {azimuth:.2f}°, altitude: {altitude:.2f}°")

direction = sun_direction(azimuth, altitude)
print(f"Ray direction: ({direction[0]:.6f}, {direction[1]:.6f}, {direction[2]:.6f})")

start = time.perf_counter()
shadowed = bool(mesh.ray.intersects_any([point], [direction])[0])
single_ms = (time.perf_counter() - start) * 1000
print(f"Shadowed: {shadowed}, ray intersection took {single_ms:.3f} ms")

rng = np.random.default_rng(42)
mins, maxs = mesh.bounds
points = rng.uniform(mins, maxs, size=(1000, 3))
points[:, 2] = 1.5
directions = np.repeat(direction.reshape(1, 3), len(points), axis=0)
start = time.perf_counter()
hits = mesh.ray.intersects_any(points, directions)
batch_ms = (time.perf_counter() - start) * 1000
rays_per_sec = len(points) / (batch_ms / 1000)
print(f"Batch 1000 rays took {batch_ms:.3f} ms, {rays_per_sec:.0f} rays/sec")
