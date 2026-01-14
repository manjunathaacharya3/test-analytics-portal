# defect_management.py
import time
import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import html, dcc, dash_table, Input, Output, State, callback
from datetime import datetime, timedelta

dash.register_page(__name__, path="/defect-management", name="Defect Management")


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


# ---------------- Mock Data ---------------- #
@timed_cache(seconds=3600)
def get_mock_projects():
    return {
        "proj1": {"id": "proj1", "name": "Equity"},
        "proj2": {"id": "proj2", "name": "Fixed Income"},
        "proj3": {"id": "proj3", "name": "Currency Trading"},
    }


@timed_cache(seconds=3600)
def get_mock_defects(project_id=None):
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
    all_defects = [
        {"id": "DEF-001", "project_id": "proj1", "title": "Cart items disappear after login",
         "severity": "High", "priority": "P1", "status": "Open",
         "assigned_to": "John Smith", "reported_by": "Alice Johnson",
         "created_at": dates[2], "updated_at": dates[0], "module": "Shopping Cart",
         "description": "Items in cart disappear when users log in."},
        {"id": "DEF-002", "project_id": "proj1", "title": "Payment timeout issue",
         "severity": "Critical", "priority": "P0", "status": "In Progress",
         "assigned_to": "Emma Davis", "reported_by": "Bob Williams",
         "created_at": dates[5], "updated_at": dates[1], "module": "Payment Gateway",
         "description": "Payment process fails after 30s."},
        {"id": "DEF-004", "project_id": "proj2", "title": "Corrupted PDF in statements",
         "severity": "High", "priority": "P1", "status": "Open",
         "assigned_to": "Sarah Brown", "reported_by": "Michael Lee",
         "created_at": dates[3], "updated_at": dates[0], "module": "Reporting",
         "description": "Generated PDF files are corrupted."},
        {"id": "DEF-006", "project_id": "proj2", "title": "Incorrect balance after transfer",
         "severity": "High", "priority": "P1", "status": "Fixed",
         "assigned_to": "Robert Miller", "reported_by": "Patricia Rodriguez",
         "created_at": dates[15], "updated_at": dates[5], "module": "Transfers",
         "description": "Balance shows wrong amount after transfers."},
        {"id": "DEF-009", "project_id": "proj3", "title": "Lab results missing data",
         "severity": "Medium", "priority": "P2", "status": "In Progress",
         "assigned_to": "Kevin Moore", "reported_by": "Elizabeth Taylor",
         "created_at": dates[6], "updated_at": dates[2], "module": "Lab Results",
         "description": "Lab result PDFs missing reference ranges."},
    ]
    return [d for d in all_defects if not project_id or d["project_id"] == project_id]


# ---------------- Helpers ---------------- #
def get_status_color(status):
    colors = {"Open": "#dc2626", "In Progress": "#eab308", "Fixed": "#16a34a", "Closed": "#6b7280"}
    return colors.get(status, "#6b7280")


def get_severity_color(sev):
    colors = {"Critical": "#b91c1c", "High": "#f97316", "Medium": "#facc15", "Low": "#22c55e"}
    return colors.get(sev, "#94a3b8")


def get_defect_stats(defects):
    total = len(defects)
    open_ = sum(1 for d in defects if d["status"] == "Open")
    progress = sum(1 for d in defects if d["status"] == "In Progress")
    fixed = sum(1 for d in defects if d["status"] == "Fixed")
    return {"total": total, "open": open_, "progress": progress, "fixed": fixed}


# ---------------- Render ---------------- #
def render_header(show_back_button=False):
    return html.Div([
        html.Div([
            # html.I(className="fas fa-bug", style={"color": "#7c3aed", "fontSize": "26px", "marginRight": "10px"}),
            html.H2("Defect Management", className="module-header-title", style={"margin": 0})
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div([
            dbc.Button("← Back", href="/projects", size="sm", color="secondary")
        ], style={"marginLeft": "auto"}) if show_back_button else None
    ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"})


def render_filters(project_id=None):
    projects = get_mock_projects()
    return dbc.Row([
        dbc.Col([
            html.Label("Project", className="filter-label"),
            dcc.Dropdown(
                id="defect-project-dropdown",
                options=[{"label": p["name"], "value": pid} for pid, p in projects.items()],
                value=project_id, placeholder="Select project...", className="filter-dropdown"
            )
        ], width=6),
        dbc.Col([
            html.Label("Status", className="filter-label"),
            dcc.Dropdown(
                id="defect-status-dropdown",
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "Open", "value": "Open"},
                    {"label": "In Progress", "value": "In Progress"},
                    {"label": "Fixed", "value": "Fixed"},
                ],
                value="all", className="filter-dropdown"
            )
        ], width=6)
    ], className="g-3 mt-2")


def render_summary_cards(stats):
    cards = [
        ("Total", stats["total"], "#7c3aed", "fas fa-layer-group"),
        ("Open", stats["open"], "#dc2626", "fas fa-exclamation-circle"),
        ("In Progress", stats["progress"], "#eab308", "fas fa-spinner"),
        ("Fixed", stats["fixed"], "#16a34a", "fas fa-check-circle"),
    ]

    return dbc.Row([
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.Div([
                    # Text block (left)
                    html.Div([
                        html.H4(str(value), style={"margin": 0, "fontWeight": "600"}),
                        html.Small(label, style={"color": "#64748b"})
                    ]),
                    # Icon (right)
                    html.I(
                        className=icon,
                        style={
                            "color": color,
                            "fontSize": "22px",
                            "marginLeft": "auto"
                        }
                    )
                ], style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between"
                })
            ]), className="summary-card hover-shadow")
        ], width=3)
        for (label, value, color, icon) in cards
    ], className="g-3 mt-3")


def render_defect_table(df):
    return dash_table.DataTable(
        id="defect-table",
        columns=[
            {"name": "ID", "id": "id"},
            {"name": "Title", "id": "title"},
            {"name": "Severity", "id": "severity"},
            {"name": "Priority", "id": "priority"},
            {"name": "Status", "id": "status"},
            {"name": "Assigned To", "id": "assigned_to"},
            {"name": "Created", "id": "created_at"},
            {"name": "Module", "id": "module"},
        ],
        data=df.to_dict("records"),
        row_selectable="single",
        filter_action="native",
        sort_action="native",
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={
            "fontFamily": "inherit",
            "fontSize": "0.9rem",
            "textAlign": "left",
            "padding": "10px",
            "whiteSpace": "normal"
        },
        style_header={
            "backgroundColor": "#1e293b",
            "color": "white",
            "fontWeight": "bold",
            "textAlign": "center"
        },
        style_data_conditional=[
            {"if": {"filter_query": "{status} = 'Open'"}, "backgroundColor": "#fef2f2"},
            {"if": {"filter_query": "{status} = 'Fixed'"}, "backgroundColor": "#ecfdf5"},
        ]
    )


def render_defect_details(defect):
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-bug", style={"marginRight": "8px"}),
            html.Strong(f"{defect['id']}: {defect['title']}")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.P([html.Strong("Severity: "),
                            html.Span(defect["severity"], style={"color": get_severity_color(defect["severity"])})]),
                    html.P([html.Strong("Priority: "), defect["priority"]]),
                    html.P([html.Strong("Status: "),
                            html.Span(defect["status"], style={"color": get_status_color(defect["status"])})]),
                    html.P([html.Strong("Module: "), defect["module"]]),
                ], width=6),
                dbc.Col([
                    html.P([html.Strong("Assigned To: "), defect["assigned_to"]]),
                    html.P([html.Strong("Reported By: "), defect["reported_by"]]),
                    html.P([html.Strong("Created: "), defect["created_at"]]),
                    html.P([html.Strong("Updated: "), defect["updated_at"]]),
                ], width=6),
            ]),
            html.Hr(),
            html.P(defect["description"]),
            html.Div([
                dbc.Button("Edit", color="primary", size="sm", className="me-2"),
                dbc.Button("Reassign", color="info", size="sm", className="me-2"),
                dbc.Button("Change Status", color="secondary", size="sm"),
            ], className="d-flex justify-content-end")
        ])
    ], className="mt-4 defect-details-card")


# ---------------- Layout ---------------- #
layout = html.Div([
    dcc.Location(id="defect-management-url", refresh=False),
    html.Div(id="defect-management-container", className="defect-management-container")
])


# ---------------- Callbacks ---------------- #
@callback(Output("defect-management-container", "children"),
          Input("defect-management-url", "search"))
def initialize_page(search):
    from urllib.parse import parse_qs
    params = parse_qs(search[1:]) if search else {}
    project_key = params.get("project_id", [None])[0]
    return html.Div([
        render_header(show_back_button=True if project_key else False),
        render_filters(project_key),
        html.Div(id="defect-management-content", className="mt-4")
    ])


@callback(Output("defect-management-content", "children"),
          Input("defect-project-dropdown", "value"),
          Input("defect-status-dropdown", "value"))
def update_defect_content(project_id, status_filter):
    if not project_id:
        return html.P("Select a project to view defects.", className="empty-state-message")

    defects = get_mock_defects(project_id)
    if status_filter != "all":
        defects = [d for d in defects if d["status"] == status_filter]

    if not defects:
        return html.P("No defects found.", className="empty-state-message")

    stats = get_defect_stats(defects)
    df = pd.DataFrame(defects)
    return html.Div([
        render_summary_cards(stats),
        html.H4("Defect List", className="section-title mt-4"),
        render_defect_table(df),
        html.Div(id="defect-details-section")
    ])


@callback(Output("defect-details-section", "children"),
          Input("defect-table", "selected_rows"),
          State("defect-table", "data"),
          prevent_initial_call=True)
def show_defect_details(selected_rows, table_data):
    if not selected_rows:
        return html.Div()
    idx = selected_rows[0]
    if idx >= len(table_data):
        return html.P("Invalid selection.", className="error-message")
    defect = table_data[idx]
    return render_defect_details(defect)
