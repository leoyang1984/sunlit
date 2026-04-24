from datetime import date
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from . import __version__
from .constants import DISCLAIMER_TEXT_ZH

app = typer.Typer(help="Design-stage ground sunlight analysis for CityJSON models.")
convert_app = typer.Typer(help="Convert common massing inputs to CityJSON.")
app.add_typer(convert_app, name="convert")
console = Console()


@app.command()
def version() -> None:
    """Print version and basic environment status."""
    console.print(f"sunlit {__version__}")


@app.command()
def inspect_cityjson(path: Path) -> None:
    """Inspect whether a CityJSON file can be loaded as building mesh."""
    from .geometry import GeometryLoadError, load_cityjson_building_mesh

    try:
        mesh, building_count, reference_system = load_cityjson_building_mesh(path)
    except GeometryLoadError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Loaded {building_count} buildings")
    console.print(f"Combined mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
    console.print(f"CRS: {reference_system or 'not declared'}")


@app.command()
def analyze(
    scheme: Optional[Path] = typer.Option(None, help="Scheme CityJSON."),
    context: Optional[Path] = typer.Option(None, help="Context CityJSON."),
    boundary: Optional[Path] = typer.Option(None, help="Site boundary GeoJSON."),
    points: Optional[Path] = typer.Option(None, help="Reserved for future point-level analysis."),
    lat: float = typer.Option(..., help="Latitude in decimal degrees."),
    lon: float = typer.Option(..., help="Longitude in decimal degrees."),
    analysis_date: str = typer.Option("2026-01-20", "--date", help="Analysis date YYYY-MM-DD."),
    time_start: str = typer.Option("09:00", help="Start time HH:MM."),
    time_end: str = typer.Option("15:00", help="End time HH:MM."),
    time_step: int = typer.Option(15, help="Time step in minutes."),
    grid_size: float = typer.Option(2.0, help="Grid size in meters."),
    threshold: float = typer.Option(2.0, help="Threshold in hours."),
    timezone: str = typer.Option("Asia/Shanghai", help="IANA timezone name."),
    output: Path = typer.Option(Path("sunlit-output"), help="Output directory."),
) -> None:
    """Run MVP ground-grid sunlight analysis and write analysis.json."""
    if points is not None:
        console.print("Not implemented in MVP. This interface is reserved for future point-level analysis.")
        raise typer.Exit(code=2)
    if scheme is None and context is None:
        console.print("Provide at least one of --scheme or --context.")
        raise typer.Exit(code=2)
    if boundary is None:
        console.print("Provide --boundary for the ground analysis area.")
        raise typer.Exit(code=2)

    try:
        parsed_date = date.fromisoformat(analysis_date)
    except ValueError as exc:
        console.print("Date must use YYYY-MM-DD format.")
        raise typer.Exit(code=2) from exc

    from .analyze import AnalysisError, analyze as run_analysis
    from .geometry import GeometryLoadError
    from .grid import GridError
    from .models import AnalysisConfig
    from .report import write_report_files

    config = AnalysisConfig(
        latitude=lat,
        longitude=lon,
        date=parsed_date,
        time_start=time_start,
        time_end=time_end,
        time_step_minutes=time_step,
        grid_size_meters=grid_size,
        threshold_hours=threshold,
    )
    try:
        result = run_analysis(
            scheme_path=scheme,
            context_path=context,
            boundary_path=boundary,
            config=config,
            timezone=timezone,
        )
    except (AnalysisError, GeometryLoadError, GridError) as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    output.mkdir(parents=True, exist_ok=True)
    analysis_path = output / "analysis.json"
    heatmap_path = output / "heatmap.png"
    analysis_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    try:
        from .render import RenderError, render_heatmap

        render_heatmap(result, boundary_path=boundary, output_path=heatmap_path)
    except RenderError as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    summary_path, metadata_path = write_report_files(
        result=result,
        output_dir=output,
        scheme_path=scheme,
        context_path=context,
        boundary_path=boundary,
        timezone_name=timezone,
    )
    console.print(f"Wrote {analysis_path}")
    console.print(f"Wrote {heatmap_path}")
    console.print(f"Wrote {summary_path}")
    console.print(f"Wrote {metadata_path}")
    console.print(DISCLAIMER_TEXT_ZH)


@convert_app.command("obj")
def convert_obj(
    obj_path: Path = typer.Argument(..., help="OBJ file with one o/g group per building footprint."),
    meta: Path = typer.Option(..., help="Meta JSON mapping OBJ groups to building attributes."),
    output: Optional[Path] = typer.Option(None, help="Output CityJSON path."),
    crs: Optional[str] = typer.Option(None, help="Optional CRS URI or identifier."),
) -> None:
    """Convert grouped OBJ footprint faces to CityJSON LOD1."""
    from .convert.obj_to_cityjson import ObjConversionError, convert_obj_to_cityjson

    output_path = output or obj_path.with_suffix(".cityjson")
    try:
        cityjson = convert_obj_to_cityjson(
            obj_path=obj_path,
            meta_path=meta,
            output_path=output_path,
            crs=crs,
        )
    except ObjConversionError as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    console.print(f"Wrote {output_path}")
    console.print(f"Buildings: {len(cityjson['CityObjects'])}")


@convert_app.command("footprint")
def convert_footprint(
    geojson_path: Path = typer.Argument(..., help="GeoJSON Polygon/MultiPolygon footprints."),
    height_field: str = typer.Option("height", help="Height property field name."),
    default_height: float = typer.Option(10.0, help="Default height when height field is missing."),
    output: Optional[Path] = typer.Option(None, help="Output CityJSON path."),
    crs: Optional[str] = typer.Option(None, help="Optional CRS URI or identifier."),
) -> None:
    """Convert projected GeoJSON building footprints to CityJSON LOD1."""
    from .convert.footprint_to_cityjson import FootprintConversionError, convert_footprint_to_cityjson

    output_path = output or geojson_path.with_suffix(".cityjson")
    try:
        cityjson = convert_footprint_to_cityjson(
            input_path=geojson_path,
            output_path=output_path,
            height_field=height_field,
            default_height=default_height,
            crs=crs,
        )
    except FootprintConversionError as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    console.print(f"Wrote {output_path}")
    console.print(f"Buildings: {len(cityjson['CityObjects'])}")
