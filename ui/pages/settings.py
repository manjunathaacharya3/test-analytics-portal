import os
from urllib.parse import parse_qs, urlparse

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback

dash.register_page(__name__, path="/settings", name="Settings")

API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ---------------- Layout ---------------- #
layout = dbc.Container([
    dcc.Location(id="settings-url", refresh=False),
    html.Div(id="settings-content")
], fluid=True)


# ---------------- Render Function ---------------- #
# ---------------- Render Function ---------------- #
def render_project_form(project=None):
    """
    Returns dbc.Card containing form for Add or Modify project.
    If project is provided, fields are pre-filled.
    """
    action_text = "Save Project" if project else "Create Project"
    page_title = "Modify Project" if project else "Add New Project"
    page_subtitle = "Edit the details below for the selected project." if project else \
        "Fill in the details below to add a new project to TAP."

    return html.Div([
        # Header Row: Title on left, Back button on right
        # Header Row: Title on left, Back button on right
        dbc.Row(
            [
                dbc.Col(html.H2(page_title, className="mb-0")),
                dbc.Col(
                    dbc.Button("← Back to Projects", href="/projects", color="secondary", size="sm"),
                    width="auto",
                    className="d-flex justify-content-end align-items-start"
                ),
            ],
            className="align-items-center mb-2"
        ),

        # Subtitle
        html.P(page_subtitle, className="text-muted mb-4"),

        # Project Form
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Project Name", className="form-label"),
                        dbc.Input(
                            id="project-name",
                            placeholder="Enter project name",
                            type="text",
                            value=project.get("name", "") if project else ""
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Owner", className="form-label"),
                        dbc.Input(
                            id="project-owner",
                            placeholder="Project owner",
                            type="text",
                            value=project.get("owner", "") if project else ""
                        )
                    ], md=6)
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Description", className="form-label"),
                        dbc.Textarea(
                            id="project-description",
                            placeholder="Brief project description",
                            className="form-control mb-3",
                            style={"width": "100%"},
                            value=project.get("description", "") if project else ""
                        )
                    ], md=12)
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Repository URL", className="form-label"),
                        dbc.Input(
                            id="project-repo",
                            placeholder="https://github.com/your-repo",
                            type="url",
                            value=project.get("repository_url", "") if project else ""
                        )
                    ], md=12)
                ], className="mb-3"),

                dbc.Button(action_text, id="save-project", color="success", className="w-100"),
                html.Div(id="project-action-msg", className="mt-3")
            ])
        ], className="shadow-sm p-4")
    ])


# ---------------- Page Callback ---------------- #
@callback(
    Output("settings-content", "children"),
    Input("settings-url", "href")
)
def render_settings_page(href):
    """
    If URL has ?project=<id>, render modify form with pre-filled values.
    Otherwise, render add new project form.
    """
    query = parse_qs(urlparse(href).query) if href else {}
    project_id = query.get("project", [None])[0]

    # Simulate fetching project for modification (no actual API call)
    project = {"id": project_id, "name": "Sample Project", "owner": "John Doe",
               "description": "This is a sample project", "repository_url": "https://github.com/sample"} \
        if project_id else None

    return render_project_form(project)


import requests


@callback(
    Output("project-action-msg", "children"),
    Input("save-project", "n_clicks"),
    State("project-name", "value"),
    State("project-owner", "value"),
    State("project-description", "value"),
    State("project-repo", "value"),
    prevent_initial_call=True
)
def handle_save_project(n_clicks, name, owner, description, repo_url):
    if not n_clicks:
        return ""

    if not name or not owner:
        return dbc.Alert("Project Name and Owner are required.", color="warning", dismissable=True)

    # --- Call backend API to create project ---
    try:
        payload = {
            "name": name,
            "owner": owner,
            "description": description,
            "repository_url": repo_url
        }
        response = requests.post(API_BASE_URL + "/projects/create_project", json=payload)
        response.raise_for_status()
        data = response.json()
        # You can optionally return the created project info from data
        return dbc.Alert(
            [html.I(className="fas fa-check-circle me-2"), f"Project '{name}' created successfully!"],
            color="success",
            dismissable=True
        )
    except requests.HTTPError as e:
        return dbc.Alert(f"Failed to create project: {e}", color="danger", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Error: {e}", color="danger", dismissable=True)
