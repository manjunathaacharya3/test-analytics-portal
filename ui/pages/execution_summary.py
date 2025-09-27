import time
from datetime import datetime
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import requests
from dash import html, dcc, dash_table, callback, Input, Output, State

dash.register_page(__name__, path="/execution-summary", name="Execution Summary")

# ---------------- Configuration ----------------
API_BASE_URL = "http://localhost:8000"
PROJECTS_API = f"{API_BASE_URL}/projects/all_projects"


# ---------------- Simple Cache ----------------
def timed_cache(seconds=30):
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


# ---------------- Helper Functions ----------------
@timed_cache(seconds=60)
def fetch_projects():
    """Fetch projects dynamically from API"""
    try:
        response = requests.get(PROJECTS_API)
        response.raise_for_status()
        projects = response.json()
        return [{"label": p.get("name", "Unknown"), "value": p.get("id")} for p in projects]
    except Exception as e:
        print("Error fetching projects:", e)
        return []


@timed_cache(seconds=30)
def fetch_project_execution_data(project_key):
    """Fetch only the latest execution per module for a project"""
    try:
        url = f"{API_BASE_URL}/api/executions/{project_key}/executions"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data)
        if not df.empty:
            # Assume there's a column like 'start_time' or 'created_at' to sort by
            sort_col = "start_time" if "start_time" in df.columns else "created_at"

            # Convert to datetime if needed
            df[sort_col] = pd.to_datetime(df[sort_col], errors="coerce")

            # Sort and keep the latest execution for each module
            df = df.sort_values(by=sort_col, ascending=False).groupby("module_name", as_index=False).first()

            # Precompute status & actions once
            df["status"] = df.apply(lambda row: get_status_color(row["passed"], row["total"]), axis=1)
            df["actions"] = df["module_name"].apply(
                lambda m: f'<div style="text-align: center;">'
                          f'<a href="/module-details?module={m.replace(" ", "%20")}&project_id={project_key}">'
                          f'<button class="view-module-btn">View Module</button>'
                          f'</a></div>'
            )
        return df.to_dict("records")

    except Exception as e:
        print(f"Error fetching execution data for project {project_key}: {e}")
        return []


def get_status_color(passed, total):
    if total == 0:
        return "⚪️ Grey"
    ratio = (passed / total) * 100
    if ratio >= 90:
        return "✅ Green"
    elif ratio >= 60:
        return "⚠️ Yellow"
    else:
        return "❌ Red"


def filter_data_by_criteria(project_df, selected_date, selected_module, selected_status):
    filtered_df = project_df.copy()
    if selected_date:
        filtered_df = filtered_df[filtered_df['created_at'].str.startswith(selected_date)]
    if selected_module and selected_module != "all":
        filtered_df = filtered_df[filtered_df['module_name'] == selected_module]
    if selected_status and selected_status != 'all':
        status_map = {'green': '✅ Green', 'yellow': '⚠️ Yellow', 'red': '❌ Red'}
        target_status = status_map.get(selected_status)
        if target_status:
            filtered_df = filtered_df[filtered_df['status'] == target_status]
    return filtered_df


def calculate_summary_metrics(project_df):
    if project_df.empty:
        return {"pass_rate": 0, "total_tests": 0, "total_minutes": 0}

    total_tests = project_df["total"].sum()
    passed_tests = project_df["passed"].sum()
    pass_rate = int((passed_tests / total_tests) * 100) if total_tests > 0 else 0

    total_minutes = sum(
        float(d[:-1]) for d in project_df["duration"] if isinstance(d, str) and d.endswith("m")
    )
    return {"pass_rate": pass_rate, "total_tests": total_tests, "total_minutes": round(total_minutes, 2)}


# ---------------- Layout ----------------
layout = html.Div([
    dcc.Location(id="exec-url", refresh=False),
    dcc.Store(id="project-data-store"),  # cache execution data client-side
    html.Div(id="execution-summary-content", className="execution-summary-container")
])


# ---------------- Rendering ----------------
def render_project_selector():
    projects = fetch_projects()
    return html.Div([
        html.H2("Execution Summary", className="exec-header-title"),
        dbc.Row([
            dbc.Col([
                html.Label("Project:", className="filter-label"),
                dcc.Dropdown(
                    id="project-selector-dropdown",
                    options=projects,
                    placeholder="Choose a project to view execution summary...",
                    className="filter-dropdown"
                )
            ], width=6)
        ], className="filter-row"),
        html.Div(id="dynamic-execution-content")
    ], className="execution-content")


def render_execution_summary_content(project_name, project_key, project_df):
    metrics = calculate_summary_metrics(project_df)
    available_dates = (
        sorted(project_df["created_at"].dt.strftime("%Y-%m-%d").unique())
        if not project_df.empty
        else []
    )

    return html.Div([
        html.H3(f"Execution Summary: {project_name}", className="exec-header-title"),

        # Summary cards
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(f"{metrics['pass_rate']}%", className="summary-card-number"),
                html.P("Overall Pass Rate", className="summary-card-label")
            ]), className="summary-card shadow-sm p-3"), width=4),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(f"{metrics['total_tests']}", className="summary-card-number summary-card-number-blue"),
                html.P("Total Test Cases", className="summary-card-label")
            ]), className="summary-card shadow-sm p-3"), width=4),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(f"{metrics['total_minutes']}m", className="summary-card-number summary-card-number-green"),
                html.P("Total Duration", className="summary-card-label")
            ]), className="summary-card shadow-sm p-3"), width=4),
        ], className="summary-row"),

        # Filters
        dbc.Row([
            dbc.Col([dcc.Dropdown(
                id="date-dropdown-dynamic",
                options=[{"label": date, "value": date} for date in available_dates],
                value=available_dates[-1],
                placeholder="Select date",
                className="filter-dropdown"
            )], width=4),
            dbc.Col([dcc.Dropdown(
                id="module-dropdown-dynamic",
                options=[{"label": "All Modules", "value": "all"}] +
                        [{"label": m, "value": m} for m in
                         project_df["module_name"].unique()] if not project_df.empty else [],
                value="all",
                className="filter-dropdown"
            )], width=4),
            dbc.Col([dcc.Dropdown(
                id="status-dropdown-dynamic",
                options=[
                    {"label": "All Statuses", "value": "all"},
                    {"label": "✅ Passed", "value": "green"},
                    {"label": "⚠️ Warning", "value": "yellow"},
                    {"label": "❌ Failed", "value": "red"}
                ],
                value="all",
                className="filter-dropdown"
            )], width=4),
        ], className="filter-row"),

        # Execution table
        html.Div([
            dash_table.DataTable(
                id="exec-table-dynamic",
                columns=[
                    # {"name": "ID", "id": "id"},
                    {"name": "Module Name", "id": "module_name"},
                    {"name": "Passed", "id": "passed"},
                    {"name": "Failed", "id": "failed"},
                    {"name": "Total", "id": "total"},
                    {"name": "Duration", "id": "duration"},
                    {"name": "Status", "id": "status"},
                    {"name": "Actions", "id": "actions", "presentation": "markdown"},
                ],
                data=project_df.to_dict("records"),
                markdown_options={"html": True},
                style_cell={"textAlign": "center"},
                style_header={"backgroundColor": "#1e293b", "color": "white", "fontWeight": "bold"},
                style_data_conditional=[
                    {"if": {"filter_query": "{status} contains 'Green'"}, "backgroundColor": "#e6f4ea",
                     "color": "#1f2937"},
                    {"if": {"filter_query": "{status} contains 'Yellow'"}, "backgroundColor": "#fff9db",
                     "color": "#1f2937"},
                    {"if": {"filter_query": "{status} contains 'Red'"}, "backgroundColor": "#fdecea",
                     "color": "#1f2937"},
                    {"if": {"column_id": "module_name"}, "fontWeight": "bold"},
                ],
                page_size=10,
                style_table={"overflowX": "auto", "width": "100%"}
            ),
        ], className="table-container"),

        # Footer
        html.Div([
            html.Hr(),
            html.P([html.I(className="fas fa-sync-alt me-2"),
                    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], className="footer-text")
        ], className="footer-container")
    ], className="execution-content")


# ---------------- Callbacks ----------------
@callback(
    [Output("execution-summary-content", "children"),
     Output("project-data-store", "data")],
    Input("exec-url", "search")
)
def render_summary(search):
    projects = fetch_projects()
    if search:
        params = parse_qs(search.lstrip("?"))
        project = params.get("project", [None])[0]
        if project:
            project_name = next((p["label"] for p in projects if p["value"] == project), project)
            project_data = fetch_project_execution_data(project)
            df = pd.DataFrame(project_data)
            return html.Div([
                html.Div([dbc.Button("← Back to Projects", href="/projects", color="secondary", size="sm")],
                         style={"text-align": "right", "margin-bottom": "20px"}),
                render_execution_summary_content(project_name, project, df)
            ]), project_data
    return render_project_selector(), None


@callback(
    [Output("dynamic-execution-content", "children"),
     Output("project-data-store", "data", allow_duplicate=True)],  # 👈 here
    Input("project-selector-dropdown", "value"),
    prevent_initial_call=True
)
def update_dynamic_execution_content(selected_project):
    if not selected_project:
        return html.Div([
            html.P("Please select a project to view execution summary.", className="empty-state-message")
        ]), None

    projects = fetch_projects()
    project_name = next((p["label"] for p in projects if p["value"] == selected_project), selected_project)
    project_data = fetch_project_execution_data(selected_project)
    df = pd.DataFrame(project_data)
    return render_execution_summary_content(project_name, selected_project, df), project_data


@callback(
    [Output("exec-table-dynamic", "data"),
     Output("exec-table-dynamic", "columns")],
    [Input("date-dropdown-dynamic", "value"),
     Input("module-dropdown-dynamic", "value"),
     Input("status-dropdown-dynamic", "value")],
    State("project-data-store", "data")
)
def update_table_data(selected_date, selected_module, selected_status, project_data):
    if not project_data:
        return [], []
    project_df = pd.DataFrame(project_data)
    filtered_df = filter_data_by_criteria(project_df, selected_date, selected_module, selected_status)
    columns = [
        # {"name": "ID", "id": "id"},
        {"name": "Module Name", "id": "module_name"},
        {"name": "Passed", "id": "passed"},
        {"name": "Failed", "id": "failed"},
        {"name": "Total", "id": "total"},
        {"name": "Duration", "id": "duration"},
        {"name": "Status", "id": "status"},
        {"name": "Actions", "id": "actions", "presentation": "markdown"},
    ]
    return filtered_df.to_dict("records"), columns
