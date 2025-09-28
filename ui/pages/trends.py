# trends.py
import time
from datetime import timedelta
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
import httpx
import pandas as pd
import plotly.express as px
from dash import html, dcc, Input, Output, State, callback

dash.register_page(__name__, path="/trends", name="Trends")

API_BASE = "http://localhost:8000"


# ---------------- Simple Cache ---------------- #
def timed_cache(seconds=3600):
    """Time-based cache decorator."""

    def wrapper(func):
        cache = {}

        def inner(*args):
            now = time.time()
            if args in cache:
                value, timestamp = cache[args]
                if now - timestamp < seconds:
                    return value
            value = func(*args)
            cache[args] = (value, now)
            return value

        return inner

    return wrapper


# ---------------- Helper Functions ---------------- #
@timed_cache(seconds=3600)
def fetch_projects():
    try:
        resp = httpx.get(f"{API_BASE}/projects/all_projects")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching projects: {e}")
        return []


@timed_cache(seconds=3600)  # Cache modules for 2 minutes
def fetch_modules(project_id):
    if not project_id:
        return []
    try:
        resp = httpx.get(f"{API_BASE}/projects/{project_id}/modules")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching modules: {e}")
        return []


@timed_cache(seconds=3600)  # Cache executions for 1 minute
def fetch_executions(project_id):
    """Fetch all executions for a project (do NOT collapse by module)."""
    if not project_id:
        return []
    try:
        # hit the /project/{project_id} endpoint to get *all* executions
        resp = httpx.get(f"{API_BASE}/api/executions/project/{project_id}")
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()

        if not data:
            return []

        df = pd.DataFrame(data)

        # Ensure expected cols
        for col in ["module_id", "module_name", "created_at", "passed", "total", "duration"]:
            if col not in df.columns:
                df[col] = None

        # Parse dates
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        df = df.dropna(subset=["created_at"])
        if df.empty:
            return []

        # Normalize duration: backend gives "5m" already
        def normalize_duration(x):
            if pd.isna(x):
                return 0
            if isinstance(x, str) and x.endswith("m"):
                try:
                    return float(x.rstrip("m"))
                except ValueError:
                    return 0
            return 0

        df["avg_duration"] = df["duration"].apply(normalize_duration)

        # Fill numbers
        df["passed"] = pd.to_numeric(df["passed"], errors="coerce").fillna(0).astype(int)
        df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0).astype(int)

        # Add convenience fields
        df["date"] = df["created_at"]
        df["day"] = df["date"].dt.date

        return df.to_dict("records")

    except Exception as e:
        print(f"Error fetching executions for {project_id}: {e}")
        return []


# ---------------- Layout ---------------- #
layout = html.Div([
    dcc.Location(id="trends-url", refresh=False),
    html.Div(id="trends-content")
])


def render_trends_page(projects_options=None, selected_project=None):
    default_project = selected_project or (projects_options[0]["id"] if projects_options else None)
    return html.Div([
        # Header
        html.Div([
            html.H2("Quality Trends", className="trends-header-title"),
            dbc.Button("← Back to Projects", href="/projects", color="secondary", size="sm", className="back-button")
        ], className="header-with-button"),

        # View Mode Toggle
        dbc.Row([
            dbc.Col([
                html.Label("View Mode:", className="filter-label"),
                dbc.ButtonGroup([
                    dbc.Button("Project", id="btn-project", color="success", active=True),
                    dbc.Button("Module", id="btn-module", color="secondary", active=False)
                ], id="view-mode-toggle", className="d-flex")
            ], width=3),
        ], className="mb-3"),

        # Filters
        dbc.Row([
            dbc.Col([
                html.Label("Project:", className="filter-label"),
                dcc.Dropdown(
                    id="trend-project-dropdown",
                    options=[{"label": p["name"], "value": p["id"]} for p in
                             projects_options] if projects_options else [],
                    value=default_project,
                    clearable=False,
                    className="filter-dropdown"
                )
            ], width=3),
            dbc.Col([
                html.Label("Module:", className="filter-label"),
                dcc.Dropdown(id="trend-module-dropdown", placeholder="All Modules", clearable=True, disabled=True)
            ], width=3),
            dbc.Col([
                html.Label("Time Period:", className="filter-label"),
                dcc.Dropdown(
                    id="time-period-dropdown",
                    options=[
                        {"label": "Last 7 Days", "value": 7},
                        {"label": "Last 14 Days", "value": 14},
                        {"label": "Last 30 Days", "value": 30}
                    ],
                    value=14,
                    clearable=False
                )
            ], width=3),
        ], className="filter-row"),

        # Charts
        dbc.Row([
            dbc.Col(dcc.Graph(id="pass-rate-trend"), width=6),
            dbc.Col(dcc.Graph(id="duration-trend"), width=6)
        ])
    ], className="trends-content")


# ---------------- Callbacks ---------------- #
@callback(
    Output("trends-content", "children"),
    Input("trends-url", "search")
)
def render_trends_main(search):
    projects = fetch_projects()
    selected_project = None
    if search:
        params = parse_qs(search.lstrip("?"))
        project_id = params.get("project", [None])[0]
        if project_id:
            selected_project = project_id
    return render_trends_page(projects_options=projects, selected_project=selected_project)


@callback(
    Output("trend-module-dropdown", "options"),
    Output("trend-module-dropdown", "value"),
    Input("trend-project-dropdown", "value")
)
def update_modules_dropdown(project_id):
    if not project_id:
        return [], None
    modules = fetch_modules(project_id)
    options = [{"label": m["name"], "value": m["id"]} for m in modules]
    return options, None


@callback(
    Output("btn-project", "active"),
    Output("btn-module", "active"),
    Output("trend-module-dropdown", "disabled"),
    Input("btn-project", "n_clicks"),
    Input("btn-module", "n_clicks"),
    State("btn-project", "active"),
    State("btn-module", "active"),
)
def toggle_view_mode(n1, n2, proj_active, mod_active):
    ctx = dash.callback_context
    if not ctx.triggered:
        return True, False, True
    clicked = ctx.triggered[0]["prop_id"].split(".")[0]
    if clicked == "btn-project":
        return True, False, True
    elif clicked == "btn-module":
        if mod_active:
            return True, False, True
        return False, True, False
    return proj_active, mod_active, not mod_active


@callback(
    Output("pass-rate-trend", "figure"),
    Output("duration-trend", "figure"),
    Input("trend-project-dropdown", "value"),
    Input("trend-module-dropdown", "value"),
    Input("btn-project", "active"),
    Input("btn-module", "active"),
    Input("time-period-dropdown", "value"),
)
def update_trends(project_id, module_id, proj_active, mod_active, time_period):
    if not project_id:
        empty_fig = px.line(title="No data")
        return empty_fig, empty_fig

    executions = fetch_executions(project_id)
    if not executions:
        empty_fig = px.line(title="No data")
        return empty_fig, empty_fig

    df = pd.DataFrame(executions)
    mode = "project" if proj_active else "module"
    if mode == "module" and module_id:
        df = df[df["module_id"] == module_id]
        title_suffix = f"Module: {df['module_name'].iloc[0]}" if not df.empty else ""
    else:
        title_suffix = f"Project" if not df.empty else ""

    # Filter by time range
    end_date = df["date"].max()
    start_date = end_date - timedelta(days=time_period - 1)
    df = df[df["date"] >= start_date]

    if df.empty:
        empty_fig = px.line(title=f"No data for {title_suffix}")
        return empty_fig, empty_fig

    # 🔹 Aggregate by day
    df["day"] = df["date"].dt.date

    # Pass Rate Trend
    pass_data = df.groupby("day")[["passed", "total"]].sum().reset_index()
    pass_data["pass_rate"] = (pass_data["passed"] / pass_data["total"]) * 100
    pass_fig = px.line(pass_data, x="day", y="pass_rate", markers=True,
                       title=f"Pass Rate Over Time ({title_suffix})", line_shape="spline")
    pass_fig.update_traces(line_color="#10b981", marker_color="#10b981")
    pass_fig.update_yaxes(range=[0, 100], title="Pass Rate (%)")

    # Duration Trend
    duration_data = df.groupby("day")["avg_duration"].mean().reset_index()
    duration_fig = px.line(duration_data, x="day", y="avg_duration", markers=True,
                           title=f"Avg Duration Over Time ({title_suffix})", line_shape="spline")
    duration_fig.update_yaxes(title="Duration (Minutes)")

    return pass_fig, duration_fig
