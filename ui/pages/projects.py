from datetime import datetime
import dash
import dash_bootstrap_components as dbc
import requests
from dash import html, dcc, callback, Output, Input

dash.register_page(__name__, path="/projects", name="Projects")

API_URL = "http://localhost:8000"


def fetch_projects():
    """Fetch project list from FastAPI backend"""
    try:
        resp = requests.get(f"{API_URL}/projects/all_projects")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ Failed to fetch projects: {e}")
        return []


def status_color(status):
    return {
        "green": "#00a818",
        "yellow": "#f9c74f",
        "red": "#d62828",
    }.get(status, "#adb5bd")


# Layout with container for dynamic content
layout = html.Div([
    dcc.Interval(id="projects-refresh", interval=5 * 1000, n_intervals=0),  # auto-refresh every 5s
    html.Div(id="projects-content")
])


@callback(
    Output("projects-content", "children"),
    Input("projects-refresh", "n_intervals")
)
def render_projects(_):
    projects_data = fetch_projects()

    projects = []
    for proj in projects_data:
        last_status = (proj.get("last_status") or "grey").lower()
        projects.append({
            "id": proj.get("id"),
            "name": proj.get("name", "Unnamed Project"),
            "value": proj.get("id"),
            "last_status": last_status,
            "modules": proj.get("modules", 0),
            "last_run": proj.get("last_run", datetime.now().isoformat()),
            "pass_rate": proj.get("pass_rate", 0),
            "total_tests": proj.get("total_tests", 0),
            "owner": proj.get("owner", "Unknown"),
        })

    total_projects = len(projects)
    total_tests = sum(p["total_tests"] for p in projects)

    return html.Div([
        # Header
        html.Div([
            html.H3("Projects Overview", className="projects-header-title"),
            html.P("Monitor and manage your automation testing projects", className="projects-header-subtitle"),
        ]),

        # Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(total_projects, className="summary-card-number"),
                        html.P("Active Projects", className="summary-card-label")
                    ])
                ], className="summary-card")
            ], width=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{total_tests:,}", className="summary-card-number summary-card-number-blue"),
                        html.P("Total Test Cases", className="summary-card-label")
                    ])
                ], className="summary-card")
            ], width=6),
        ], className="summary-row"),

        # Projects Grid
        html.H4("Project Details", className="projects-section-title"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H4(proj["name"], className="project-card-title"),
                            html.Div([
                                html.Div(className="status-indicator",
                                         style={"backgroundColor": status_color(proj["last_status"])}),
                                html.Span(f" {proj['last_status'].title()}", className="status-text")
                            ], className="status-container")
                        ], className="project-card-header")
                    ], className="project-card-header-bg"),

                    dbc.CardBody([
                        # Key Metrics
                        dbc.Row([
                            dbc.Col([
                                html.Small("Pass Rate", className="metric-label"),
                                html.H5(f"{proj['pass_rate']}%",
                                        className="metric-value " +
                                                  ("metric-success" if proj['pass_rate'] >= 90 else
                                                   "metric-warning" if proj['pass_rate'] >= 70 else
                                                   "metric-danger"))
                            ], width=6),

                            dbc.Col([
                                html.Small("Total Tests", className="metric-label metric-label-right"),
                                html.H5(f"{proj['total_tests']}", className="metric-value metric-value-right")
                            ], width=6),
                        ], className="mb-3"),

                        # Additional Info
                        html.Div([
                            html.Small([
                                html.Strong("Owner: "), proj["owner"], " | ",
                                html.Strong("Modules: "), f"{proj['modules']}"
                            ], className="project-info-text"),
                            html.Br(),
                            html.Small([
                                html.Strong("Last Run: "), proj["last_run"]
                            ], className="project-info-text")
                        ], className="mb-3"),

                        # Action Buttons
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-chart-line me-1"),
                                    "Summary"
                                ],
                                    color="outline-primary",
                                    size="sm",
                                    className="w-100",
                                    href=f"/execution-summary?project={proj['value']}"
                                )
                            ], width=3),

                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-cog me-1"),
                                    "Modules"
                                ],
                                    color="outline-secondary",
                                    size="sm",
                                    className="w-100",
                                    href=f"/module-details?project_id={proj['value']}"
                                )
                            ], width=3),

                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-chart-bar me-1"),
                                    "Trends"
                                ],
                                    color="outline-info",
                                    size="sm",
                                    className="w-100",
                                    href=f"/trends?project={proj['value']}"
                                )
                            ], width=3),

                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-gear me-1"),
                                    "Settings"
                                ],
                                    color="outline-warning",
                                    size="sm",
                                    className="w-100",
                                    href=f"/settings?project={proj['value']}"
                                )
                            ], width=3)
                        ])
                    ])
                ], className="project-card")
            ], width=6, className="project-col")
            for proj in projects
        ], className="project-row"),

        # Footer
        html.Div([
            html.Hr(),
            html.P([
                html.I(className="fas fa-sync-alt me-2"),
                f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ], className="footer-text")
        ], className="mt-4")

    ], className="projects-container")
