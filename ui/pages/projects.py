import time
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
import requests
from dash import html, dcc, callback, Output, Input, State

dash.register_page(__name__, path="/projects", name="Projects")

API_URL = "http://localhost:8000"


def timed_cache(seconds=3600):
    """Time-based cache decorator."""

    def wrapper(func):
        cache = {}

        def inner(*args):
            now = time.time()
            if args in cache:
                value, timestamp = cache[args]
                if seconds is None or now - timestamp < seconds:
                    return value
            value = func(*args)
            cache[args] = (value, now)
            return value

        return inner

    return wrapper


@timed_cache(seconds=3600)
def fetch_projects():
    """Fetch project list from FastAPI backend"""
    try:
        resp = requests.get(f"{API_URL}/projects/all_projects", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ Failed to fetch projects: {e}")
        return []


def status_color(status):
    return {
        "green": "#10b981",
        "yellow": "#f59e0b",
        "red": "#ef4444",
    }.get(status, "#94a3b8")


def status_bg_color(status):
    return {
        "green": "#ecfdf5",
        "yellow": "#fffbeb",
        "red": "#fef2f2",
    }.get(status, "#f1f5f9")


def pass_rate_color(rate):
    if rate >= 90:
        return "#10b981"
    elif rate >= 70:
        return "#f59e0b"
    else:
        return "#ef4444"


# Layout
layout = html.Div([
    dcc.Interval(id="projects-refresh", interval=15 * 1000, n_intervals=0),
    dcc.Store(id="projects-store"),
    html.Div(id="projects-content")
])


@callback(
    Output("projects-store", "data"),
    Input("projects-refresh", "n_intervals"),
    prevent_initial_call=False
)
def update_projects_store(_):
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
            "last_run": proj.get("last_run") or datetime.now().isoformat(),
            "pass_rate": proj.get("pass_rate", 0),
            "total_tests": proj.get("total_tests", 0),
            "owner": proj.get("owner", "Unknown"),
            "defects": 12  # 🔹 Hardcoded defect count for now
        })
    return projects


@callback(
    Output("projects-content", "children"),
    Input("projects-store", "data"),
    State("projects-content", "children")
)
def render_projects(projects, old_content):
    if not projects:
        return html.Div([
            html.Div([
                html.I(className="fas fa-folder-open", style={
                    "fontSize": "64px",
                    "color": "#cbd5e1",
                    "marginBottom": "16px"
                }),
                html.H4("No Projects Available", style={
                    "color": "#64748b",
                    "fontWeight": "600",
                    "marginBottom": "8px"
                }),
                html.P("Start by creating your first automation project", style={
                    "color": "#94a3b8",
                    "fontSize": "14px"
                })
            ], className="empty-state")
        ], style={"maxWidth": "1400px", "margin": "0 auto", "padding": "40px 24px"})

    total_projects = len(projects)
    total_tests = sum(p["total_tests"] for p in projects)

    return html.Div([
        # Header Section
        html.Div([
            html.Div([
                html.Div([
                    html.H3("Projects", style={
                        "fontSize": "32px",
                        "fontWeight": "700",
                        "color": "#0f172a",
                        "margin": "0",
                        "letterSpacing": "-0.5px"
                    }),
                    html.P("Monitor and manage your automation testing projects", style={
                        "fontSize": "15px",
                        "color": "#64748b",
                        "margin": "8px 0 0 0"
                    })
                ]),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-sync-alt", style={
                            "fontSize": "12px",
                            "marginRight": "8px",
                            "color": "#64748b"
                        }),
                        html.Span(f"Updated {datetime.now().strftime('%H:%M:%S')}", style={
                            "fontSize": "13px",
                            "color": "#64748b"
                        })
                    ], style={
                        "padding": "8px 16px",
                        "backgroundColor": "#f1f5f9",
                        "borderRadius": "8px",
                        "display": "inline-flex",
                        "alignItems": "center"
                    })
                ])
            ], style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "marginBottom": "32px"
            })
        ], style={"padding": "40px 0 0"}),

        # Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.H3(total_projects, style={
                                    "fontWeight": "700",
                                    "fontSize": "28px",
                                    "margin": "0"
                                }),
                                html.P("Active Projects", style={
                                    "margin": "0",
                                    "color": "#64748b",
                                    "fontSize": "14px"
                                })
                            ]),
                            html.I(className="fas fa-check-circle", style={
                                "fontSize": "28px",
                                "color": "#28a745"
                            })
                        ], style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center"
                        })
                    ])
                ], className="summary-card")
            ], width=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.H3(f"{total_tests:,}", style={
                                    "fontWeight": "700",
                                    "fontSize": "28px",
                                    "margin": "0",
                                    "color": "#2563eb"
                                }),
                                html.P("Total Test Cases", style={
                                    "margin": "0",
                                    "color": "#64748b",
                                    "fontSize": "14px"
                                })
                            ]),
                            html.I(className="fas fa-vials", style={
                                "fontSize": "28px",
                                "color": "#17a2b8"
                            })
                        ], style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center"
                        })
                    ])
                ], className="summary-card")
            ], width=6)
        ], style={"marginBottom": "32px"}),

        # All projects header
        html.Div([html.H5("All projects")], style={"margin": "20px 0"}),

        # Projects Grid
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Div([
                        # Project Header
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-cube", style={
                                    "fontSize": "16px",
                                    "color": "#6366f1",
                                    "marginRight": "10px"
                                }),
                                html.Span(proj["name"], style={
                                    "fontSize": "16px",
                                    "fontWeight": "700",
                                    "color": "#0f172a",
                                    "letterSpacing": "-0.2px"
                                })
                            ], style={"display": "flex", "alignItems": "center"}),

                            html.Div([
                                html.Div(style={
                                    "width": "8px",
                                    "height": "8px",
                                    "borderRadius": "50%",
                                    "backgroundColor": status_color(proj["last_status"]),
                                    "boxShadow": f"0 0 8px {status_color(proj['last_status'])}",
                                    "animation": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite"
                                }),
                                html.Span(proj['last_status'].title(), style={
                                    "fontSize": "11px",
                                    "fontWeight": "600",
                                    "color": status_color(proj["last_status"]),
                                    "marginLeft": "6px",
                                    "textTransform": "uppercase",
                                    "letterSpacing": "0.5px"
                                })
                            ], style={
                                "display": "flex",
                                "alignItems": "center",
                                "padding": "4px 10px",
                                "backgroundColor": status_bg_color(proj["last_status"]),
                                "borderRadius": "12px"
                            })
                        ], className="project-card-header"),

                        # KPI Row (Added Defect Count)
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-chart-pie", style={
                                        "fontSize": "22px",
                                        "color": pass_rate_color(proj['pass_rate'])
                                    }),
                                    html.Div(f"{proj['pass_rate']}%", style={
                                        "fontSize": "20px",
                                        "fontWeight": "700",
                                        "color": pass_rate_color(proj['pass_rate'])
                                    }),
                                    html.Small("Pass Rate", style={"color": "#64748b"})
                                ], className="kpi-card")
                            ], width=3),
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-cubes", style={
                                        "fontSize": "22px",
                                        "color": "#6366f1"
                                    }),
                                    html.Div(f"{proj['modules']}", style={
                                        "fontSize": "20px",
                                        "fontWeight": "700"
                                    }),
                                    html.Small("Modules", style={"color": "#64748b"})
                                ], className="kpi-card")
                            ], width=3),
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-vials", style={
                                        "fontSize": "22px",
                                        "color": "#6366f1"
                                    }),
                                    html.Div(f"{proj['total_tests']}", style={
                                        "fontSize": "20px",
                                        "fontWeight": "700"
                                    }),
                                    html.Small("Total Tests", style={"color": "#64748b"})
                                ], className="kpi-card")
                            ], width=3),
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-bug", style={
                                        "fontSize": "22px",
                                        "color": "#ef4444"
                                    }),
                                    html.Div(f"{proj['defects']}", style={
                                        "fontSize": "20px",
                                        "fontWeight": "700",
                                        "color": "#ef4444"
                                    }),
                                    html.Small("Defects", style={"color": "#64748b"})
                                ], className="kpi-card")
                            ], width=3)
                        ], className="g-3", style={"padding": "16px"}),

                        # Owner & Last Run
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Small("Owner", style={
                                        "color": "#64748b",
                                        "fontSize": "10px"
                                    }),
                                    html.H6(proj["owner"], style={
                                        "margin": "0",
                                        "color": "#64748b",
                                        "fontSize": "12px"
                                    })
                                ], style={"textAlign": "left"})
                            ], width=6),
                            dbc.Col([
                                html.Div([
                                    html.Small("Last Run", style={
                                        "color": "#64748b",
                                        "fontSize": "10px"
                                    }),
                                    html.H6(
                                        (
                                            datetime.fromisoformat(proj["last_run"])
                                            if isinstance(proj["last_run"], str)
                                            else proj["last_run"]
                                        ).strftime("%d %b %Y, %H:%M"),
                                        style={
                                            "margin": "0",
                                            "color": "#64748b",
                                            "fontSize": "12px"
                                        }
                                    )
                                ], style={"textAlign": "right"})
                            ], width=6)
                        ], className="g-3", style={"padding": "0 16px", "marginBottom": "12px"}),

                        # Action Buttons
                        dbc.Row([
                            dbc.Col(dbc.Button(
                                [html.I(className="fas fa-chart-line me-1"), "Summary"],
                                color="outline-primary", size="sm", className="w-100",
                                href=f"/execution-summary?project={proj['value']}"
                            ), width=3),
                            dbc.Col(dbc.Button(
                                [html.I(className="fas fa-cog me-1"), "Modules"],
                                color="outline-secondary", size="sm", className="w-100",
                                href=f"/module-details?project_id={proj['value']}"
                            ), width=3),
                            dbc.Col(dbc.Button(
                                [html.I(className="fas fa-chart-bar me-1"), "Trends"],
                                color="outline-info", size="sm", className="w-100",
                                href=f"/trends?project={proj['value']}"
                            ), width=3),
                            dbc.Col(dbc.Button(
                                [html.I(className="fas fa-gear me-1"), "Settings"],
                                color="outline-warning", size="sm", className="w-100",
                                href=f"/settings?project={proj['value']}"
                            ), width=3)
                        ], style={
                            "marginBottom": "8px",
                            "padding": "12px 14px",
                            "borderTop": "1px solid #f1f5f9",
                            "backgroundColor": "#f9fafb"
                        })
                    ], className="project-card")
                ]),
                width=6, className="mb-3"
            )
            for proj in projects
        ])
    ], className="projects-container")
