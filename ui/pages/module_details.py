import time

import dash
import dash_bootstrap_components as dbc
import httpx
import pandas as pd
from dash import html, dcc, dash_table, Input, Output, State, callback

dash.register_page(__name__, path="/module-details", name="Module Details")

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
        projects = resp.json()
        return {p["id"]: p for p in projects}
    except Exception:
        return {}


@timed_cache(seconds=3600)
def fetch_modules_by_project(project_id):
    if not project_id:
        return []
    try:
        resp = httpx.get(f"{API_BASE}/projects/{project_id}/modules")
        resp.raise_for_status()
        modules = resp.json()
        return [{"module_id": m["id"], "module_name": m["name"]} for m in modules]
    except Exception:
        return []


@timed_cache(seconds=3600)
def fetch_module_executions(module_id):
    if not module_id:
        return []
    try:
        resp = httpx.get(f"{API_BASE}/api/executions/module/{module_id}")
        resp.raise_for_status()
        data = resp.json()
        for d in data:
            if isinstance(d.get("module"), dict):
                d["module_name"] = d["module"].get("name", "")
            elif isinstance(d.get("module"), str):
                d["module_name"] = d["module"]
            else:
                d["module_name"] = ""
            d["run_id"] = d.get("id", "")
            d["passed"] = int(d.get("passed", 0))
            d["failed"] = int(d.get("failed", 0))
            d["total"] = int(d.get("total", 0))
            duration = d.get("duration", 0)
            if isinstance(duration, (int, float)):
                d["duration"] = f"{int(round(duration))}m"
            else:
                d["duration"] = str(duration)
            d["status"] = d.get("status", "")
            if "module" in d:
                del d["module"]
        return data
    except Exception:
        return []


@timed_cache(seconds=3600)
def fetch_run_scenarios(run_id):
    if not run_id:
        return []
    try:
        resp = httpx.get(f"{API_BASE}/api/executions/{run_id}/scenarios")
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


# ---------------- Render Functions ---------------- #
def render_module_selector(project_key=None, module_key=None, show_back_button=False):
    projects = fetch_projects()
    options = [{"label": p["name"], "value": pid} for pid, p in projects.items()]
    header = html.Div([
        html.H2("Module Details", className="module-header-title"),
        dbc.Button("← Back to Projects", href="/projects", color="secondary", size="sm", className="back-button")
    ], className="header-with-button") if show_back_button else html.H2("Module Details",
                                                                        className="module-header-title")

    module_options = fetch_modules_by_project(project_key) if project_key else []

    return html.Div([
        header,
        dbc.Row([
            dbc.Col([html.Label("Project:", className="filter-label"),
                     dcc.Dropdown(
                         id="module-details-project-dropdown",
                         options=options,
                         value=project_key,
                         placeholder="Choose a project...",
                         className="filter-dropdown"
                     )], width=6),
            dbc.Col([html.Label("Module:", className="filter-label"),
                     dcc.Dropdown(
                         id="module-details-module-dropdown",
                         options=[{"label": m["module_name"], "value": m["module_id"]} for m in module_options],
                         value=module_key,
                         placeholder="First select a project..." if not project_key else "Choose a module...",
                         disabled=not project_key,
                         className="filter-dropdown"
                     )], width=6)
        ], className="filter-row"),
        html.Div(id="module-details-dynamic-content")
    ], className="module-content")


def normalize_status(status: str) -> str:
    s = str(status).lower()
    if s in ["green", "passed", "success"]:
        return "✅"
    elif s in ["yellow", "warning", "partial"]:
        return "⚠️"
    elif s in ["red", "failed", "error"]:
        return "❌"
    return "⬜"


def render_module_details_content(module_id, project_id=None):
    executions = fetch_module_executions(module_id)
    df = pd.DataFrame(executions)

    total_executions = len(df)
    pass_rate = int(round(df["passed"].sum() / df["total"].sum() * 100)) if not df.empty else 0

    durations = []
    if not df.empty and "duration" in df.columns:
        for d in df["duration"]:
            if isinstance(d, str) and d.endswith("m"):
                try:
                    durations.append(int(d.replace("m", "")))
                except Exception:
                    continue
            elif isinstance(d, (int, float)):
                durations.append(int(d))
    avg_duration_val = round(sum(durations) / len(durations)) if durations else 0
    avg_duration = f"{avg_duration_val}m"

    projects = fetch_projects()
    project_name = projects.get(project_id, {}).get("name", "Unknown Project")
    available_dates = sorted(df['created_at'].apply(
        lambda x: x.split("T")[0]).unique()) if not df.empty and 'created_at' in df.columns else []

    # 🔥 Normalize statuses to icons (✅, ⚠️, ❌)
    if not df.empty and "status" in df.columns:
        df["status"] = df["status"].apply(normalize_status)

    return html.Div([
        html.Hr(className="section-divider"),
        dbc.Row([
            dbc.Col([dbc.Card(dbc.CardBody([
                html.Div([
                    html.Div([
                        html.H3(total_executions, className="summary-card-number"),
                        html.P("Total Executions", className="summary-card-label")
                    ]),
                    html.Div([
                        html.I(className="fas fa-play-circle", style={
                            "fontSize": "24px",
                            "color": "#6f42c1"
                        })
                    ])
                ], style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center"
                })
            ]), className="summary-card")], width=4),
            dbc.Col([dbc.Card(dbc.CardBody([
                html.Div([
                    html.Div([
                        html.H3(f"{pass_rate}%", className="summary-card-number summary-card-number-blue"),
                        html.P("Pass Rate", className="summary-card-label")
                    ]),
                    html.Div([
                        html.I(className="fas fa-chart-pie", style={
                            "fontSize": "24px",
                            "color": "#28a745"
                        })
                    ])
                ], style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center"
                })
            ]), className="summary-card")], width=4),
            dbc.Col([dbc.Card(dbc.CardBody([
                html.Div([
                    html.Div([
                        html.H3(avg_duration, className="summary-card-number summary-card-number-green"),
                        html.P("Avg Duration", className="summary-card-label")
                    ]),
                    html.Div([
                        html.I(className="fas fa-stopwatch", style={
                            "fontSize": "24px",
                            "color": "#fd7e14"
                        })
                    ])
                ], style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center"
                })
            ]), className="summary-card")], width=4),
        ], className="summary-row"),

        dbc.Row([dbc.Col([html.Label("Execution Date:", className="filter-label"),
                          dcc.Dropdown(
                              id="module-details-date-dropdown",
                              options=[{"label": "All Dates", "value": "all"}] + [{"label": d, "value": d} for d in
                                                                                  available_dates],
                              value="all",
                              placeholder="Select date",
                              className="filter-dropdown"
                          )], width=6)], className="filter-row"),

        html.H4("Execution Runs", className="section-title"),
        html.Div([dash_table.DataTable(
            id="module-details-runs-table",
            columns=[
                # {"name": "Run ID", "id": "run_id"},
                {"name": "Execution Date", "id": "created_at"},
                {"name": "Passed", "id": "passed"},
                {"name": "Failed", "id": "failed"},
                {"name": "Total", "id": "total"},
                {"name": "Duration", "id": "duration"},
                {"name": "Status", "id": "status"}
            ],
            data=df.to_dict("records"),
            row_selectable="single",

            # ✅ Match execution summary styles
            style_cell={"textAlign": "center", "fontFamily": "inherit", "fontSize": "0.9rem"},
            style_header={"backgroundColor": "#1e293b", "color": "white", "fontWeight": "bold",
                          "fontFamily": "inherit"},
            style_data={"whiteSpace": "normal", "height": "auto"},
            style_data_conditional=[
                {"if": {"column_id": "run_id"}, "fontWeight": "bold"},
                {"if": {"filter_query": "{status} = '✅'"}, "backgroundColor": "#e6f7ec"},
                {"if": {"filter_query": "{status} = '❌'"}, "backgroundColor": "#fdecea"},
                {"if": {"filter_query": "{status} = '⚠️'"}, "backgroundColor": "#fffbea"},
            ],

            page_size=10,
            style_table={"overflowX": "auto", "width": "100%"},
            tooltip_data=[
                {col: {"value": str(val), "type": "markdown"} for col, val in row.items()}
                for row in df.to_dict("records")
            ],
            tooltip_duration=None,
        )], className="table-container"),

        html.Div(id="module-details-scenarios-section", className="scenarios-section")
    ])


# ---------------- Layout ---------------- #
layout = html.Div([
    dcc.Location(id="module-details-url", refresh=False),
    html.Div(id="module-details-content", className="module-details-container"),
    dcc.Store(id="module-details-projects-store"),
])


# ---------------- Callbacks ---------------- #
@callback(
    Output("module-details-content", "children"),
    Input("module-details-url", "search")
)
def initialize_page(search):
    """Check URL params to preselect project/module from query string."""
    from urllib.parse import parse_qs
    project_key = None
    module_key = None
    params = parse_qs(search[1:]) if search else {}
    project_key = params.get("project_id", [None])[0]

    if project_key:
        modules = fetch_modules_by_project(project_key)
        if modules:
            module_key = modules[0]["module_id"]

    return render_module_selector(project_key=project_key, module_key=module_key,
                                  show_back_button=True if project_key else False)


@callback(
    Output("module-details-module-dropdown", "options"),
    Output("module-details-module-dropdown", "disabled"),
    Output("module-details-module-dropdown", "placeholder"),
    Output("module-details-module-dropdown", "value"),
    Input("module-details-project-dropdown", "value"),
    State("module-details-module-dropdown", "value")
)
def update_module_options(selected_project, current_module):
    if not selected_project:
        return [], True, "First select a project...", None
    modules = fetch_modules_by_project(selected_project)
    options = [{"label": m["module_name"], "value": m["module_id"]} for m in modules]
    value = current_module if current_module in [opt["value"] for opt in options] else (
        options[0]["value"] if options else None)
    return options, False, "Choose a module...", value


@callback(
    Output("module-details-dynamic-content", "children"),
    Input("module-details-project-dropdown", "value"),
    Input("module-details-module-dropdown", "value")
)
def update_dynamic_content(selected_project, selected_module):
    if not selected_project or not selected_module:
        return html.Div([html.P("Please select both a project and module.", className="empty-state-message")])
    return render_module_details_content(selected_module, selected_project)


@callback(
    Output("module-details-runs-table", "data"),
    Input("module-details-date-dropdown", "value"),
    State("module-details-module-dropdown", "value")
)
def filter_dynamic_runs_by_date(selected_date, selected_module):
    executions = fetch_module_executions(selected_module)
    if selected_date and selected_date != "all":
        executions = [e for e in executions if e.get("created_at", "").startswith(selected_date)]
    for e in executions:
        e["status"] = normalize_status(e.get("status", ""))
    return executions


@callback(
    Output("module-details-scenarios-section", "children"),
    Input("module-details-runs-table", "selected_rows"),
    Input("module-details-runs-table", "data")
)
def show_scenarios_dynamic(selected_rows, table_data):
    if not selected_rows or not table_data:
        return html.Div([html.P("Select a Run ID to see scenarios.", className="info-message")])

    try:
        # Make sure index is valid
        idx = selected_rows[0]
        if idx >= len(table_data):
            return html.Div([html.P("Invalid run selection.", className="info-message")])

        run_id = table_data[idx].get("run_id")
    except Exception:
        return html.Div([html.P("Error retrieving run ID.", className="error-message")])

    sc_data = fetch_run_scenarios(run_id)
    if not sc_data:
        return html.Div([html.P("No scenarios available for this run.", className="info-message")])

    normalized_data = []
    tooltip_rows = []

    for sc in sc_data:
        # --- status icon ---
        s = str(sc.get("status", "")).lower()
        if s in ["passed", "success", "green"]:
            status_icon = "✅"
        else:
            status_icon = "❌"

        # --- tags (string) ---
        tags = sc.get("tags")
        if isinstance(tags, list):
            tags_str = ", ".join([str(t) for t in tags])
        else:
            tags_str = str(tags) if tags is not None else "-"

        # --- attachments => markdown link string ---
        attachments = sc.get("attachments") or []
        if isinstance(attachments, list) and attachments:
            attachments_md = " | ".join([f"[{att}](/assets/{att})" for att in attachments])
        else:
            attachments_md = "-"

        # --- error cell (short label) and full error for tooltip ---
        error_text = sc.get("error") or ""
        error_cell = "View" if error_text else "-"

        normalized_row = {
            "scenario": str(sc.get("scenario", "")),
            "tags": tags_str,
            "duration": str(sc.get("duration", "")),
            "status": status_icon,
            "failed_step": str(sc.get("failed_step", "")),
            "error": error_cell,
            "attachments": attachments_md,
        }

        # Build tooltip row (all values stringified)
        tooltip_row = {}
        for col, val in normalized_row.items():
            # For the error column we want the full raw error text in the tooltip (not the 'View' label)
            if col == "error":
                tooltip_val = str(error_text)
            elif col == "attachments":
                tooltip_val = str(attachments_md)
            else:
                tooltip_val = str(val)
            tooltip_row[col] = {"value": tooltip_val, "type": "markdown"}

        normalized_data.append(normalized_row)
        tooltip_rows.append(tooltip_row)

    return html.Div([
        html.H5(f"Scenario wise execution details - ", className="scenarios-title"),
        dash_table.DataTable(
            id="module-details-scenarios-table",
            columns=[
                {"name": "Scenario", "id": "scenario"},
                {"name": "Tags", "id": "tags"},
                {"name": "Duration", "id": "duration"},
                {"name": "Status", "id": "status"},
                {"name": "Failed Step", "id": "failed_step"},
                {"name": "Error", "id": "error"},
                {"name": "Attachments", "id": "attachments", "presentation": "markdown"},
            ],
            data=normalized_data,
            markdown_options={"html": True},
            style_cell={
                "textAlign": "center",
                "fontFamily": "inherit",
                "fontSize": "0.9rem",
                "whiteSpace": "normal",
                "height": "auto",
            },
            style_header={
                "backgroundColor": "#1e293b",
                "color": "white",
                "fontWeight": "bold",
            },
            style_data={"whiteSpace": "normal", "height": "auto"},
            style_data_conditional=[
                {"if": {"column_id": "scenario"}},
                {"if": {"filter_query": "{status} = '✅'"}, "backgroundColor": "#e6f7ec"},
                {"if": {"filter_query": "{status} = '❌'"}, "backgroundColor": "#fdecea"}
            ],
            style_cell_conditional=[
                {"if": {"column_id": "scenario"}, "width": "30%"},
                {"if": {"column_id": "tags"}, "width": "10%"},
                {"if": {"column_id": "duration"}, "width": "10%"},
                {"if": {"column_id": "status"}, "width": "10%"},
                {"if": {"column_id": "failed_step"}, "width": "30%"},
                {"if": {"column_id": "error"}, "width": "10%"},
                {"if": {"column_id": "attachments"}, "width": "10%"},
            ],
            tooltip_data=tooltip_rows,
            tooltip_duration=None,
            page_size=10,
            style_table={"overflowX": "auto", "width": "100%"},
        )
    ])