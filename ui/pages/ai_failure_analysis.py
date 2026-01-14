import asyncio
import hashlib
import logging
import os
import time
from datetime import datetime, timedelta

import aiohttp
import dash
import dash_bootstrap_components as dbc
import httpx
import pandas as pd
import requests
from dash import html, dcc, dash_table, callback, Input, Output, State

dash.register_page(__name__, path="/ai-failure-analysis", name="AI Failure Analysis")

API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
PROJECTS_API = f"{API_BASE_URL}/projects/all_projects"

PROJECT_RELATED_MODULES = None

logging.basicConfig(
    level=logging.INFO,  # Minimum level to log
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    filename="app.log",  # Optional: write to a file
    filemode="a"  # Append mode
)


# -----------------------------------------------------------
# Simple Cache
# -----------------------------------------------------------
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


async def fetch_data(url, token, payload):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    print(payload)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                raise Exception(f"Failed to fetch data: {response.status}")


async def call_API(context_string):
    pass


# -----------------------------------------------------------
# Intelligent Analysis Functions
# -----------------------------------------------------------
def calculate_failure_signature(error_log, stack_trace):
    """Generate unique signature for failure pattern matching"""
    # Extract key parts and create hash
    combined = f"{error_log[:100]}|{stack_trace[:200]}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]


def detect_flakiness(failure_history):
    """Analyze test stability over time"""
    total_runs = failure_history.get("total_runs", 0)
    failures = failure_history.get("failures", 0)

    if total_runs == 0:
        return {"status": "unknown", "rate": 0, "label": "Insufficient Data"}

    failure_rate = (failures / total_runs) * 100

    if failure_rate == 100:
        return {"status": "consistent", "rate": failure_rate, "label": "Consistently Failing"}
    elif failure_rate >= 70:
        return {"status": "critical", "rate": failure_rate, "label": "Critical Instability"}
    elif failure_rate >= 30:
        return {"status": "flaky", "rate": failure_rate, "label": "Highly Flaky"}
    elif failure_rate >= 10:
        return {"status": "unstable", "rate": failure_rate, "label": "Intermittent"}
    else:
        return {"status": "stable", "rate": failure_rate, "label": "Rare Failure"}


# -----------------------------------------------------------
# Enhanced Dummy Data Generation
# -----------------------------------------------------------
def generate_enhanced_failures(project_id, module_name):
    """Generate realistic failures with historical context"""
    base_failures = [
        {
            "id": f"FAIL-{project_id}-001",
            "test_name": f"{module_name}.LoginTest.test_invalid_password",
            "test_suite": f"{module_name} - Authentication Suite",
            "error_log": "ElementNotInteractableException: Element is not clickable at point (120, 320)\n  at LoginPage.clickSubmit (LoginPage.py:45)\n  at test_invalid_password (test_login.py:78)",
            "stack_trace": "Traceback (most recent call last):\n  File 'test_login.py', line 78, in test_invalid_password\n    login_page.click_submit()\n  File 'LoginPage.py', line 45, in click_submit\n    self.submit_btn.click()\nElementNotInteractableException: Element not clickable",
            "category": "Locator Issue",
            "suggested_fix": "Element appears to be overlapped by a modal or loading spinner. Implement WebDriverWait with expected_conditions.element_to_be_clickable() before interaction.",
            "confidence": 0.91,
            "severity": "High",
            "timestamp": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "execution_time": "3.2s",
            "retry_count": 2,
            "module_name": module_name,
            "project_id": project_id,
            "history": {
                "total_runs": 50,
                "failures": 8,
                "first_failure": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "stable_period": "45 days",
                "related_commits": [
                    {"hash": "a3f2e1b", "message": "Update login modal UI", "author": "John Doe", "date": "3 days ago"}
                ]
            },
            "similar_failures": ["LoginTest.test_valid_credentials", "ProfileTest.test_edit_profile"],
            "impact": "Blocks 3 dependent tests",
            "failed_step": "click_submit",
            "scenario": "test_invalid_password"
        }
    ]

    # Add signatures and enhanced analysis
    for failure in base_failures:
        failure["signature"] = calculate_failure_signature(failure["error_log"], failure["stack_trace"])
        failure["flakiness_analysis"] = detect_flakiness(failure["history"])

    return base_failures


# -----------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------
@timed_cache(seconds=3600)
def fetch_projects():
    """Fetch projects dynamically from API"""
    try:
        response = requests.get(PROJECTS_API)
        response.raise_for_status()
        projects = response.json()
        return [{"label": p.get("name", "Unknown"), "value": p.get("id")} for p in projects]
    except Exception as e:
        print("Error fetching projects:", e)
        return [
            {"label": "E-Commerce Platform", "value": "proj-001"},
            {"label": "Mobile Banking App", "value": "proj-002"},
            {"label": "Healthcare Portal", "value": "proj-003"}
        ]


@timed_cache(seconds=3600)
def fetch_modules_for_project(project_id):
    """Fetch modules for a specific project"""
    try:
        url = f"{API_BASE_URL}/api/executions/{project_id}/executions"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        if not df.empty and "module_name" in df.columns:
            return sorted(df["module_name"].unique().tolist())
        return []
    except Exception as e:
        print(f"Error fetching modules for project {project_id}: {e}")
        return ["Authentication Module", "Payment Module", "Search Module", "Dashboard Module", "API Module"]


def calculate_ai_metrics(failures):
    """Calculate summary metrics for AI analysis"""
    if not failures:
        return {
            "total_failures": 0,
            "avg_confidence": 0,
            "critical_count": 0,
            "patterns_detected": 0,
            "flaky_tests": 0,
            "recent_regressions": 0
        }

    total = len(failures)
    avg_conf = sum(f["confidence"] for f in failures) / total * 100
    critical = sum(1 for f in failures if f["severity"] in ["Critical", "High"])

    # Count unique patterns
    patterns = len(set(f["signature"] for f in failures))

    # Count flaky tests
    flaky = sum(1 for f in failures if f["flakiness_analysis"]["status"] in ["flaky", "unstable"])

    # Count recent regressions (failures in last 3 days after stable period)
    recent = sum(1 for f in failures
                 if (datetime.now() - datetime.strptime(f["timestamp"], "%Y-%m-%d %H:%M:%S")).days < 3
                 and f["history"]["stable_period"] != "Never stable")

    return {
        "total_failures": total,
        "avg_confidence": round(avg_conf, 1),
        "critical_count": critical,
        "patterns_detected": patterns,
        "flaky_tests": flaky,
        "recent_regressions": recent
    }


def get_severity_badge_color(severity):
    """Get Bootstrap color for severity badge"""
    colors = {
        "Critical": "danger",
        "High": "warning",
        "Medium": "info",
        "Low": "secondary"
    }
    return colors.get(severity, "secondary")


def get_flakiness_color(status):
    """Get color for flakiness status"""
    colors = {
        "consistent": "danger",
        "critical": "danger",
        "flaky": "warning",
        "unstable": "info",
        "stable": "success",
        "unknown": "secondary"
    }
    return colors.get(status, "secondary")


# -----------------------------------------------------------
# Layout
# -----------------------------------------------------------
layout = html.Div([
    dcc.Location(id="ai-failure-url", refresh=False),
    dcc.Store(id="ai-failures-store"),
    dcc.Store(id="selected-failure-store"),
    dcc.Store(id="generate-fix-store", data=False),  # store to coordinate immediate loading UI
    dcc.Interval(id="insight-interval", interval=5000, n_intervals=0, disabled=True),

    # ✅ Fixed: use html.Tag("style", ...) instead of html.Style(...)
    html.Div([
        dcc.Markdown(
            """
            <style>
            .view-ai-insight-btn:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.5) !important;
                filter: brightness(1.1);
            }

            .ai-output-container {
                animation: slideIn 0.4s ease-out;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            /* Pulse animation for loading */
            @keyframes pulse {
                0%, 100% {
                    opacity: 1;
                }
                50% {
                    opacity: 0.5;
                }
            }
            </style>
            """,
            dangerously_allow_html=True
        )
    ]),

    html.Div([
        # Header
        html.Div([
            html.Div([
                html.H3("AI-Powered Failure Analysis", className="exec-header-title"),
                html.P(
                    "Intelligent pattern detection, root cause analysis, and predictive insights",
                    style={"color": "#64748b", "marginBottom": "20px"}
                )
            ], style={"flex": "1"}),
            html.Div([
                dbc.Badge("Live Analysis", color="success", className="me-2", pill=True),
                dbc.Badge("ML Insights Active", color="primary", pill=True)
            ], style={"display": "flex", "alignItems": "center"})
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "flex-start",
            "marginBottom": "20px"
        }),

        # Filters Section
        dbc.Row([
            dbc.Col([
                html.Label("Project:", className="filter-label"),
                dcc.Dropdown(
                    id="ai-project-dropdown",
                    options=fetch_projects(),
                    placeholder="Choose a project...",
                    className="filter-dropdown"
                )
            ], width=6),
            dbc.Col([
                html.Label("Module:", className="filter-label"),
                dcc.Dropdown(
                    id="ai-module-dropdown",
                    options=[],
                    placeholder="Choose a module...",
                    className="filter-dropdown",
                    disabled=True
                )
            ], width=6),
        ], className="filter-row"),

        # Content Area
        html.Div(id="ai-analysis-content")

    ], className="execution-content")
])


# -----------------------------------------------------------
# Render Functions
# -----------------------------------------------------------
def render_summary_cards(metrics):
    """Render enhanced summary metric cards"""
    return dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div([
                    html.H4(f"{metrics['total_failures']}", className="summary-card-number",
                            style={"fontSize": "1.5rem", "color": "#ef4444"}),
                    html.P("Total Failures", className="summary-card-label",
                           style={"fontSize": "0.9rem", "margin": 0})
                ]),
                html.Div([
                    html.I(className="fas fa-bug", style={"fontSize": "24px", "color": "#ef4444"})
                ])
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
        ]), className="summary-card shadow-sm p-2", style={"height": "100%"}), width=2),

        dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div([
                    html.H4(f"{metrics['patterns_detected']}", className="summary-card-number",
                            style={"fontSize": "1.5rem", "color": "#8b5cf6"}),
                    html.P("Unique Patterns", className="summary-card-label",
                           style={"fontSize": "0.9rem", "margin": 0})
                ]),
                html.Div([
                    html.I(className="fas fa-project-diagram", style={"fontSize": "24px", "color": "#8b5cf6"})
                ])
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
        ]), className="summary-card shadow-sm p-2", style={"height": "100%"}), width=2),

        dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div([
                    html.H4(f"{metrics['flaky_tests']}", className="summary-card-number",
                            style={"fontSize": "1.5rem", "color": "#f59e0b"}),
                    html.P("Flaky Tests", className="summary-card-label",
                           style={"fontSize": "0.9rem", "margin": 0})
                ]),
                html.Div([
                    html.I(className="fas fa-random", style={"fontSize": "24px", "color": "#f59e0b"})
                ])
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
        ]), className="summary-card shadow-sm p-2", style={"height": "100%"}), width=2),

        dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div([
                    html.H4(f"{metrics['recent_regressions']}", className="summary-card-number",
                            style={"fontSize": "1.5rem", "color": "#ef4444"}),
                    html.P("Recent Regressions", className="summary-card-label",
                           style={"fontSize": "0.9rem", "margin": 0})
                ]),
                html.Div([
                    html.I(className="fas fa-exclamation-circle", style={"fontSize": "24px", "color": "#ef4444"})
                ])
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
        ]), className="summary-card shadow-sm p-2", style={"height": "100%"}), width=2),

        dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div([
                    html.H4(f"{metrics['critical_count']}", className="summary-card-number",
                            style={"fontSize": "1.5rem", "color": "#dc2626"}),
                    html.P("Critical Priority", className="summary-card-label",
                           style={"fontSize": "0.9rem", "margin": 0})
                ]),
                html.Div([
                    html.I(className="fas fa-fire", style={"fontSize": "24px", "color": "#dc2626"})
                ])
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
        ]), className="summary-card shadow-sm p-2", style={"height": "100%"}), width=2),

        dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div([
                    html.H4(f"{metrics['avg_confidence']}%", className="summary-card-number",
                            style={"fontSize": "1.5rem", "color": "#22c55e"}),
                    html.P("AI Confidence", className="summary-card-label",
                           style={"fontSize": "0.9rem", "margin": 0})
                ]),
                html.Div([
                    html.I(className="fas fa-brain", style={"fontSize": "24px", "color": "#22c55e"})
                ])
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
        ]), className="summary-card shadow-sm p-2", style={"height": "100%"}), width=2),
    ], className="summary-row", style={"marginBottom": "20px"})


def render_failures_table(project_id, module_name):
    """Render AI Failure Analysis table identical to module_details but dynamically fetches failed scenarios."""
    try:
        # Step 1: Get latest execution for the project
        print(f"calling with project_id: {project_id}")
        print(f"calling with module_name: {module_name}")
        executions_url = f"{API_BASE_URL}/api/executions/{project_id}/executions"
        exec_resp = httpx.get(executions_url)
        exec_resp.raise_for_status()
        executions = exec_resp.json()

        if not executions:
            return html.Div([html.P("No executions found for this project.", className="info-message")])

        # Step 2: Get the latest execution (last entry in list)
        latest_execution = executions[0]
        execution_id = latest_execution.get("id")

        # Step 3: Fetch scenarios for that execution
        scenarios_url = f"{API_BASE_URL}/api/executions/{execution_id}/scenarios"
        scen_resp = httpx.get(scenarios_url)
        scen_resp.raise_for_status()
        scenarios = scen_resp.json()

        if not scenarios:
            return html.Div([html.P("No scenarios available for the latest execution.", className="info-message")])

        # Step 4: Filter only failed scenarios
        failed_scenarios = [s for s in scenarios if
                            str(s.get("status", "")).lower() in ["❌ failed", "fail", "❌", "error"]]
        if not failed_scenarios:
            return html.Div([html.P("No failed scenarios found in the latest execution.", className="info-message")])

    except Exception as e:
        logging.error(f"Error fetching AI failure data for {project_id}/{module_name}: {e}")
        return dbc.Alert("Unable to fetch AI failure analysis data from backend.", color="danger")

    # Step 5: Build table rows and tooltips
    normalized_data = []
    tooltip_rows = []

    for i, sc in enumerate(failed_scenarios):
        s = str(sc.get("status", "")).lower()
        status_icon = "✅" if s in ["passed", "success", "green"] else "❌"

        tags = ", ".join(sc.get("tags", [])) if isinstance(sc.get("tags"), list) else sc.get("tags", "-")
        duration = sc.get("duration", "-")
        failed_step = sc.get("failed_step", "-")
        scenario_name = sc.get("scenario", "-")
        error = sc.get("error", "-")
        scenario_id = sc.get("id", "-")

        ai_insight_btn = (
            "<div style='text-align:center;'>"
            f"<button class='view-ai-insight-btn' data-failure-id='{sc.get('id', '')}' "
            "style='background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);"
            "color:white;border:none;border-radius:8px;"
            "padding:6px 14px;font-size:0.85rem;cursor:pointer;"
            "box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);"
            "transition: all 0.3s ease;font-weight:500;'>"
            "<i class='fas fa-brain'></i></button></div>"
        )

        normalized_row = {
            "scenario_id": scenario_id,
            "scenario": scenario_name,
            "tags": tags,
            "duration": duration,
            "status": status_icon,
            "failed_step": failed_step,
            "error": error,
            "ai_insight": ai_insight_btn,
            "index": i
        }

        tooltip_row = {k: {"value": str(v), "type": "markdown"} for k, v in normalized_row.items()}
        # tooltip_rows.append(tooltip_row)
        normalized_data.append(normalized_row)

    # Step 6: Return table identical in style to module_details.py
    return html.Div([
        html.H5("AI Failure Analysis", className="scenarios-title"),
        dash_table.DataTable(
            id="ai-failures-table",
            columns=[
                # {"name": "Scenario_ID", "id": "scenario_id"},
                {"name": "Scenario", "id": "scenario"},
                {"name": "Tags", "id": "tags"},
                {"name": "Duration", "id": "duration"},
                {"name": "Status", "id": "status"},
                {"name": "Failed Step", "id": "failed_step"},
                {"name": "AI Insight", "id": "ai_insight", "presentation": "markdown"},
            ],
            data=normalized_data,
            markdown_options={"html": True, "link_target": "_self"},
            tooltip_data=tooltip_rows,
            tooltip_duration=None,
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
            style_data_conditional=[
                {"if": {"filter_query": "{status} = '✅'"}, "backgroundColor": "#e6f7ec"},
                {"if": {"filter_query": "{status} = '❌'"}, "backgroundColor": "#fdecea"},
            ],
            page_size=10,
            style_table={"overflowX": "auto", "width": "100%"},
        )
    ], className="table-container")


def render_detailed_analysis_modal_content(failure):
    """Render comprehensive AI-powered analysis modal body (without footer actions)."""
    if not failure:
        return html.Div()

    # Historical Context as collapsed Accordion by default (active_item None -> collapsed)
    historical_item = dbc.AccordionItem(
        [
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Strong("Test Stability Timeline"),
                        html.Hr(className="my-2"),
                        html.Div([
                            html.I(className="fas fa-check-circle me-2", style={"color": "#22c55e"}),
                            html.Span(f"Stable for: 2 months")
                        ], className="mb-2"),
                        html.Div([
                            html.I(className="fas fa-chart-bar me-2", style={"color": "#3b82f6"}),
                            html.Span(f"Failed Step: {failure.get('failed_step', '-')}")
                        ], className="mb-2"),
                        html.Div([
                            html.I(className="fas fa-chart-bar me-2", style={"color": "#3b82f6"}),
                            html.Span(f"Failure Cause: {failure.get('error', '-')}")
                        ], className="mb-2")
                    ])
                ], md=12),
            ])
        ],
        title="Historical Context & Stability Analysis",
    )

    return html.Div([
        # Use Accordion collapsed by default
        dbc.Card([
            dbc.CardBody(
                dbc.Accordion(
                    [historical_item],
                    id="historical-accordion",
                    active_item=None,  # None -> collapsed by default
                )
            )
        ], className="mb-3 shadow-sm", style={"borderRadius": "8px"}),

        # Similar Failures
        html.Div([
            html.H6("Similar Failures Detected", className="fw-bold mb-2"),
            html.Div([
                dbc.Badge(test, color="warning", className="me-2 mb-2", pill=True)
                for test in failure.get("similar_failures", [])
            ]) if failure.get("similar_failures") else html.Span("No similar failures detected", className="text-muted")
        ], className="mb-3"),

        html.Div(
            dcc.Loading(
                id="ai-loading-spinner",
                type="default",
                color="#000000",
                children=html.Div(id="ai-fix-output", className="mt-3")
            )
        ),

        html.Hr(),

        # Note: The Generate-Fix button is intentionally moved to the Modal Footer (as requested).
    ])


# -----------------------------------------------------------
# Callbacks
# -----------------------------------------------------------
@callback(
    [Output("ai-module-dropdown", "options"),
     Output("ai-module-dropdown", "disabled"),
     Output("ai-module-dropdown", "value")],
    Input("ai-project-dropdown", "value")
)
def update_module_dropdown(selected_project):
    """Update module dropdown based on selected project"""
    if not selected_project:
        return [], True, None

    PROJECT_RELATED_MODULES = fetch_modules_for_project(selected_project)
    options = [{"label": "All Modules", "value": "all"}] + [{"label": m, "value": m} for m in PROJECT_RELATED_MODULES]
    return options, False, "all"


@callback(
    [Output("ai-analysis-content", "children"),
     Output("ai-failures-store", "data")],
    [Input("ai-project-dropdown", "value"),
     Input("ai-module-dropdown", "value")]
)
def update_analysis_content(project, module):
    if not project:
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Please select a project to begin AI failure analysis."
            ], color="info", className="text-center")
        ]), None

    if not module:
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Please select a module to view failure analysis."
            ], color="info", className="text-center")
        ]), None

    # Generate or fetch failures
    if module == "all":
        modules = fetch_modules_for_project(project)
        all_failures = []
        for mod in modules:
            all_failures.extend(generate_enhanced_failures(project, mod))
    else:
        all_failures = generate_enhanced_failures(project, module)

    filtered_failures = all_failures

    if not filtered_failures:
        return html.Div([
            dbc.Alert(
                "No failures found for analysis.",
                color="warning",
                className="text-center mt-3"
            )
        ]), []

    # Calculate metrics
    metrics = calculate_ai_metrics(filtered_failures)

    content = html.Div([
        render_summary_cards(metrics),

        html.H5([
            html.I(className="fas fa-list-alt me-2"),
            "Intelligent Failure Analysis"
        ], className="fw-bold mb-3"),

        render_failures_table(project, module),

        html.Div([
            html.Hr(),
            html.P([
                html.I(className="fas fa-sync-alt me-2"),
                f"AI Analysis updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ",
                html.I(className="fas fa-check-circle me-2 ms-3", style={"color": "#22c55e"}),
                "ML models active"
            ], className="footer-text")
        ], className="footer-container mt-4")
    ])

    return content, filtered_failures


@timed_cache(seconds=3600)
def fetch_run_scenarios(run_id):
    if not run_id:
        return []
    try:
        resp = httpx.get(f"{API_BASE_URL}/api/executions/{run_id}/scenarios")
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


@callback(
    Output("ai-analysis-content", "children", allow_duplicate=True),
    Input("ai-failures-table", "active_cell"),
    State("ai-failures-table", "data"),
    State("ai-failures-store", "data"),
    State("ai-analysis-content", "children"),
    prevent_initial_call=True
)
def show_detailed_analysis(active_cell, table_data, all_failures, current_content):
    """Show detailed AI analysis when a 'View AI Analysis' or 'View AI Insight' button is clicked."""
    if not active_cell or not all_failures:
        return current_content

    row_index = active_cell["row"]
    clicked_row = table_data[row_index]

    modal_body = render_detailed_analysis_modal_content(clicked_row)

    # Place Generate Fix button in Modal Footer (replacing Close)
    generate_btn = dbc.Button(
        [
            html.Span(id="fix-btn-content", children=[
                html.I(className="fas fa-magic me-2"),
                "Generate AI Fix"
            ])
        ],
        id="generate-fix-btn",
        color="primary",  # use primary to avoid conflicts
        size="sm",
        style={
            "background": "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
            "color": "white",
            "border": "none",
            "border-radius": "8px",
            "padding": "6px 14px",
            "font-size": "0.85rem",
            "cursor": "pointer",
            "box-shadow": "0 4px 12px rgba(0,0,0,0.3)",
            "transition": "all 0.3s ease",
            "font-weight": "500"
        }
    )

    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(f"AI Analysis: {clicked_row.get('scenario', '')}")),
            dbc.ModalBody(modal_body, style={"maxHeight": "70vh", "overflowY": "auto"}),
            dbc.ModalFooter(
                generate_btn  # Replaced the Close button with Generate AI Fix button, as requested.
            ),
        ],
        id="analysis-detail-modal",
        size="xl",
        scrollable=True,
        is_open=True,
    )

    # Append modal to current layout
    return html.Div([current_content, modal])


# ------------------------------
# Generate Fix: two-step pattern to allow immediate UI change (spinner) then server processing
# 1) Immediate callback sets generate-fix-store True and changes button content to loading spinner.
# 2) Worker callback watches store and performs API call when True, then writes ai-fix-output and resets button and store.
# ------------------------------

@callback(
    [Output("fix-btn-content", "children"),
     Output("generate-fix-store", "data")],
    Input("generate-fix-btn", "n_clicks"),
    prevent_initial_call=True
)
def start_generate_fix(n_clicks):
    """Immediately show loading state on the button and set store flag to True."""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    # Button content with spinner (immediate UI feedback)
    loading_children = [
        dbc.Spinner(
            size="sm",
            children=[],
            type="border",
            spinner_style={"marginRight": "8px"}
        ),
        html.Span("Generating...")
    ]
    return loading_children, True


@callback(
    [Output("ai-fix-output", "children"),
     Output("fix-btn-content", "children", allow_duplicate=True),
     Output("generate-fix-store", "data", allow_duplicate=True)],
    Input("generate-fix-store", "data"),
    State("ai-failures-table", "active_cell"),
    State("ai-failures-table", "data"),
    prevent_initial_call=True
)
def perform_generate_fix(store_flag, active_cell, table_data):
    """
    Perform the AI API call when store_flag becomes True.
    After completion, return the AI fix output, reset button content, and set store to False.
    """
    if not store_flag:
        raise dash.exceptions.PreventUpdate

    if not active_cell or not table_data:
        error_output = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "No scenario selected to generate fix for."
        ], color="warning")
        button_content = [
            html.I(className="fas fa-magic me-2"),
            "Generate Slingshot Fix"
        ]
        return error_output, button_content, False

    row_index = active_cell["row"]
    failure = table_data[row_index]

    try:
        # Call the AI API (this blocks until response; UI already shows spinner by previous callback)
        ai_response = asyncio.run(call_API(failure.get('error', failure.get('error_log', ''))))

        # Defensive checks on ai_response structure
        text = ""
        if ai_response and isinstance(ai_response, dict):
            # try to extract safety
            if "choices" in ai_response and ai_response["choices"]:
                # path used in earlier code
                text = ai_response["choices"][0].get("message", {}).get("content", "")
            elif "result" in ai_response and isinstance(ai_response["result"], dict):
                text = ai_response["result"].get("content", "")
        if not text:
            text = "Auth session ended! Authorize again to get the AI insights."

        # Trim finishing punctuation for better display
        trimmed_text = text
        if isinstance(trimmed_text, str) and "." in trimmed_text:
            # Keep up to last period for readability (if present)
            last_period = trimmed_text.rfind('.')
            if last_period != -1:
                trimmed_text = trimmed_text[: last_period + 1]

        # Creative AI output display
        fix_output = html.Div([
            html.Hr(style={"borderColor": "#d1fae5", "margin": "1.5rem 0"}),

            # Header with icon
            html.Div([
                html.Div([
                    html.I(className="fas fa-robot", style={
                        "fontSize": "1.5rem",
                        "color": "#10b981",
                        "marginRight": "10px"
                    }),
                    html.H6("AI-Generated Solution", className="fw-bold mb-0", style={"color": "#065f46"})
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "1rem"}),

                # Decorative line
                html.Div(style={
                    "height": "3px",
                    "background": "linear-gradient(90deg, #10b981 0%, #d1fae5 100%)",
                    "borderRadius": "2px",
                    "marginBottom": "1rem"
                })
            ]),

            # AI Response with typing effect styling
            html.Div([
                dcc.Markdown(
                    trimmed_text,
                    style={
                        "whiteSpace": "pre-wrap",
                        "fontSize": "0.95rem",
                        "color": "#064e3b",
                        "fontFamily": "'Inter', 'Segoe UI', sans-serif",
                        "lineHeight": "1.8",
                        "padding": "1.25rem",
                    },
                    dangerously_allow_html=False
                )
            ], style={
                "backgroundColor": "#f0fdf4",
                "border": "2px solid #bbf7d0",
                "borderRadius": "12px",
                "position": "relative",
                "boxShadow": "0 4px 12px rgba(16, 185, 129, 0.1)"
            }),

            # Footer badge
            html.Div([
                html.Span([
                    html.I(className="fas fa-check-circle me-2", style={"color": "#10b981"}),
                    "Analysis Complete"
                ], style={
                    "fontSize": "0.85rem",
                    "color": "#059669",
                    "fontWeight": "500"
                })
            ], style={"marginTop": "1rem", "textAlign": "right"})

        ], className="ai-output-container")

        # Reset button content to default
        button_content = [
            html.I(className="fas fa-magic me-2"),
            "Generate Slingshot Fix"
        ]

        # Return the ai output, reset button and store flag
        return fix_output, button_content, False

    except Exception as e:
        error_output = html.Div([
            html.Hr(),
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Unable to generate fix: {str(e)}"
            ], color="warning")
        ])

        button_content = [
            html.I(className="fas fa-magic me-2"),
            "Generate Slingshot Fix"
        ]

        return error_output, button_content, False
