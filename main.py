import glob
import os
import shutil

import networkx as nx
import osmnx as ox
import pandas as pd
from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeFloat,
    PositiveInt,
    model_validator,
)
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

import src.stressmodel as sm
from util import extract_width, sanitize_for_frontend

console = Console()

OUT_PATH = "data/out/main"


class Place(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    """OSM geocoder query, e.g. "Somerville, Massachusetts, USA"."""
    residential_default_mph: PositiveInt
    """Speed limit for residential-class streets without a posted `maxspeed`."""

    @property
    def city(self) -> str:
        """First component of `name`, e.g. "Somerville"."""
        return self.name.split(",")[0].strip()

    @property
    def slug(self) -> str:
        """File-name prefix for this place's outputs, e.g. "somerville"."""
        return self.city.replace(" ", "_").lower()


class CompositeWeights(BaseModel):
    """Weights of each model score in `composite_score`.

    Weights are renormalized per edge over the non-missing scores, so they need
    not sum to 1.
    """

    model_config = ConfigDict(frozen=True)

    separation_level_score: NonNegativeFloat = 0.60
    maxspeed_int_score: NonNegativeFloat = 0.20
    street_classification_score: NonNegativeFloat = 0.20

    @model_validator(mode="after")
    def _any_positive(self) -> "CompositeWeights":
        if not any(self.model_dump().values()):
            raise ValueError("at least one weight must be positive")
        return self


class CitySummary(BaseModel):
    """One row of the pipeline summary table."""

    city: str
    nodes: int
    edges: int
    length_km: float
    mean_score: float
    median_score: float
    geojson: str


PLACES: list[Place] = [
    Place(name="Somerville, Massachusetts, USA", residential_default_mph=20),
    Place(name="Cambridge, Massachusetts, USA", residential_default_mph=20),
    Place(name="Everett, Massachusetts, USA", residential_default_mph=25),
    Place(name="Malden, Massachusetts, USA", residential_default_mph=25),
]


# add cycleway to useful tags
ox.settings.useful_tags_way += [
    "massgis:way_id",
    "condition",
    "smoothness",
    "surface",
    "bicycle",
    "cycleway",
    "cycleway:left",
    "cycleway:right",
    "cycleway:both",
    "cycleway:buffer",
    "cycleway:separation",
    "sidewalk:left",
    "sidewalk:right",
    "sidewalk:both",
    "parking:left",
    "parking:right",
    "parking:both",
]

OUTPUT_COLUMNS = [
    "name",
    # --- maxspeed ---
    "maxspeed_0",
    "maxspeed_int",
    "maxspeed_int_score",
    # --- separation level ---
    "separation_level",
    "separation_level_score",
    # --- street classification ---
    "street_0",
    "street_classification",
    "street_classification_score",
    # --- lanes ---
    "lanes_0",
    "lanes_int",
    "lanes_int_score",
    # --- composite ---
    "composite_score",
    # --- basics ---
    "length",
    "width_float",
    "width_half",
    "geometry",
]


def get_network(place: str, network_type: str = "bike"):
    G = ox.graph_from_place(place, network_type=network_type)

    # project graph to UTM
    G = ox.project_graph(G)

    # consolidate intersections within 10 meters
    G = ox.consolidate_intersections(G, tolerance=10)
    assert isinstance(G, nx.MultiDiGraph)

    # project back to WGS84
    G = ox.project_graph(G, to_crs="EPSG:4326")

    nodes, edges = ox.graph_to_gdfs(G)
    return nodes, edges


def process_network(edges: pd.DataFrame) -> pd.DataFrame:
    # drop some unneeded columns
    edges = edges.drop(
        ["ref", "service", "access", "bridge", "tunnel", "junction"],
        axis=1,
        errors="ignore",
    )

    # parse width
    edges["width_float"] = edges["width"].apply(extract_width).astype("Float64")

    # if width is missing, set to 10 meters
    edges["width_float"] = edges["width_float"].fillna(10.0)

    # add buffer column (half of width)
    edges["width_half"] = edges["width_float"] / 2.0

    # sort columns alphabetically
    edges = edges.reindex(sorted(edges.columns), axis=1)

    return edges


def prepare_data_for_place(place: Place, console: Console | None = None):
    c = console or globals().get("console", Console())

    with c.status(
        f"[cyan]Downloading bike network for {place.name}...[/cyan]", spinner="dots"
    ):
        nodes, edges = get_network(place.name, "bike")
    c.print(
        f"  [green]✓[/green] Network downloaded: [bold]{len(nodes):,}[/bold] nodes, [bold]{len(edges):,}[/bold] edges"
    )

    with c.status(
        f"[cyan]Processing network and running stress models for {place.name}...[/cyan]",
        spinner="dots",
    ):
        edges = process_network(edges)

        # MODEL - CATEGORY: classify street types
        edges["street_classification"], edges["street_classification_score"] = (
            sm.classification.run(edges)
        )

        # MODEL - SPEED: parse maxspeed, default residential-class streets
        edges["maxspeed_int"], edges["maxspeed_int_score"] = sm.speed.run(
            edges, place.residential_default_mph, edges["street_classification"]
        )

        # MODEL - SEPARATION LEVEL: combine cycleway types for separation level
        edges["separation_level"], edges["separation_level_score"] = (
            sm.separation_level.run(edges)
        )

        # MODEL - LANES: parse number of lanes
        edges["lanes_int"], edges["lanes_int_score"] = sm.lanes.run(edges)

        # copy some OG vals so they are easy to compare with new vals
        edges["street_0"] = edges["highway"]
        edges["maxspeed_0"] = edges["maxspeed"]
        edges["lanes_0"] = edges["lanes"]

        # sort columns alphabetically again
        edges = edges.reindex(sorted(edges.columns), axis=1)

        # compute composite score
        edges["composite_score"] = compute_composite_score(edges)

    mean_score = float(edges["composite_score"].mean())
    median_score = float(edges["composite_score"].median())
    c.print(
        f"  [green]✓[/green] Stress models evaluated (mean | median: [bold]{mean_score:.2f} | {median_score:.2f}[/bold] / 4.00)"
    )

    return nodes, edges


COMPOSITE_WEIGHTS = CompositeWeights()


def compute_composite_score(edges: pd.DataFrame) -> pd.Series:
    weights = pd.Series(COMPOSITE_WEIGHTS.model_dump())

    # Compute weighted sum using dot, ignoring NaNs
    weighted_sum = edges[weights.index].fillna(0).dot(weights)

    # Compute sum of weights for non-missing values
    sum_weights = edges[weights.index].notna().dot(weights)

    # Normalize
    return weighted_sum / sum_weights


def save_data_for_place(
    place: Place, out_path: str, nodes, edges, console: Console | None = None
):
    c = console or globals().get("console", Console())
    city_out = f"{out_path}/{place.slug}"
    os.makedirs(out_path, exist_ok=True)

    # save to GeoPackage
    edges.to_file(f"{city_out}_streets.gpkg", layer="streets", driver="GPKG")
    nodes.to_file(f"{city_out}_streets.gpkg", layer="nodes", driver="GPKG")

    # also save geojson (sanitized and compacted for frontend performance)
    geojson_out = f"{city_out}_streets.geojson"
    sanitize_for_frontend(edges, out_path=geojson_out)

    c.print(f"  [green]✓[/green] Exported [bold]{place.slug}[/bold] (GPKG, GeoJSON)")


def copy_to_frontend(
    places: list[Place] = PLACES,
    out_path: str = OUT_PATH,
    dest_dir: str = "frontend/public/data",
    chart_dest_dir: str = "deployed-charts",
    console: Console | None = None,
) -> list[str]:
    """Copy generated *_streets.geojson files to frontend/public/data, and any charts to deployed-charts."""
    c = console or globals().get("console", Console())
    os.makedirs(dest_dir, exist_ok=True)
    copied_files: list[str] = []

    for place in places:
        filename = f"{place.slug}_streets.geojson"
        src_file = os.path.join(out_path, filename)
        dest_file = os.path.join(dest_dir, filename)

        if os.path.exists(src_file):
            shutil.copy2(src_file, dest_file)
            copied_files.append(dest_file)
            c.print(
                f"  [green]✓[/green] Copied [bold]{filename}[/bold] → [dim]{dest_file}[/dim]"
            )
        else:
            c.print(
                f"  [yellow]⚠[/yellow] Source file not found: [dim]{src_file}[/dim]"
            )

    # copy charts if any exist (matching copy.sh: for f in data/out/notebook/chart*.html(N))
    chart_files = glob.glob("data/out/notebook/chart*.html")
    if chart_files:
        os.makedirs(chart_dest_dir, exist_ok=True)
        for chart in chart_files:
            dest_file = os.path.join(chart_dest_dir, os.path.basename(chart))
            shutil.copy2(chart, dest_file)
            copied_files.append(dest_file)
            c.print(
                f"  [green]✓[/green] Copied [bold]{os.path.basename(chart)}[/bold] → [dim]{dest_file}[/dim]"
            )

    if copied_files:
        c.print(
            f"\n[bold green]Successfully copied {len(copied_files)} file(s) to frontend![/bold green]"
        )
    else:
        c.print("[yellow]No files were copied.[/yellow]")
    return copied_files


def main():
    c = console

    c.print(
        Panel.fit(
            "[bold cyan]🚲 Bike Stress Model Pipeline[/bold cyan]\n"
            "[dim]Processing OpenStreetMap networks & calculating cycling stress scores[/dim]",
            border_style="cyan",
        )
    )

    # delete contents of data/out directory
    c.print(f"[dim]Clearing [bold]{OUT_PATH}[/bold]...[/dim]")
    if os.path.exists(OUT_PATH):
        shutil.rmtree(OUT_PATH)
    os.makedirs(OUT_PATH, exist_ok=True)

    summaries: list[CitySummary] = []

    for place in PLACES:
        c.rule(f"[bold cyan]📍 {place.name}[/bold cyan]")

        nodes, edges = prepare_data_for_place(place, console=c)

        # also get boundary polygon
        with c.status(
            f"[cyan]Geocoding city boundary for {place.city}...[/cyan]", spinner="dots"
        ):
            city_gdf = ox.geocode_to_gdf(place.name)

        # filter down to output columns
        filtered_edges = edges[OUTPUT_COLUMNS]

        # save data
        save_data_for_place(place, OUT_PATH, nodes, filtered_edges, console=c)

        # also save boundary polygon
        boundary_file = f"{OUT_PATH}/{place.slug}_boundary.geojson"
        city_gdf.to_file(boundary_file, driver="GeoJSON")
        c.print(
            f"  [green]✓[/green] Saved boundary polygon → [dim]{boundary_file}[/dim]"
        )

        summaries.append(
            CitySummary(
                city=place.city,
                nodes=len(nodes),
                edges=len(edges),
                length_km=float(edges["length"].sum() / 1000),
                mean_score=float(edges["composite_score"].mean()),
                median_score=float(edges["composite_score"].median()),
                geojson=f"{place.slug}_streets.geojson",
            )
        )

    # Summary table
    c.print()
    table = Table(
        title="Pipeline Execution Summary",
        box=box.ROUNDED,
        header_style="bold cyan",
    )
    table.add_column("City", style="bold")
    table.add_column("Nodes", justify="right")
    table.add_column("Segments", justify="right")
    table.add_column("Length", justify="right")
    table.add_column("Stress (Mean | Median)", justify="right")
    table.add_column("GeoJSON File", style="dim")

    def _format_score(score: float) -> str:
        if score < 1.5:
            return f"[green]{score:.2f}[/green]"
        elif score < 2.5:
            return f"[yellow]{score:.2f}[/yellow]"
        else:
            return f"[red]{score:.2f}[/red]"

    for item in summaries:
        score_str = (
            f"{_format_score(item.mean_score)} | {_format_score(item.median_score)}"
        )
        table.add_row(
            item.city,
            f"{item.nodes:,}",
            f"{item.edges:,}",
            f"{item.length_km:.1f} km",
            score_str,
            item.geojson,
        )

    c.print(table)

    # Ask user to copy files to frontend
    c.print()
    try:
        should_copy = Confirm.ask(
            "[bold cyan]Do you want to copy the GeoJSON files to the frontend?[/bold cyan]",
            default=True,
            console=c,
        )
    except (EOFError, KeyboardInterrupt):
        c.print()
        should_copy = False

    if should_copy:
        c.print()
        copy_to_frontend(places=PLACES, out_path=OUT_PATH, console=c)
    else:
        c.print("[yellow]Skipped copying GeoJSON files to frontend.[/yellow]")


if __name__ == "__main__":
    main()
