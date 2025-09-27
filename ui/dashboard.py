"""
Dashboard Application for Test Analytics Portal

This module initializes the Dash application and sets up the sidebar navigation
for the Test Analytics Portal. It defines the layout structure including sidebar
and main content area.
"""

import dash
import dash_bootstrap_components as dbc
from dash import html

# Initialize the Dash application with required stylesheets
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",  # icons
        "/assets/sidebar.css", "/assets/projects.css", "/assets/execution_summary.css",
        "/assets/module_details.css", "/assets/settings.css", "/assets/trends.css"
        # Reference to our separate CSS file
    ],
    suppress_callback_exceptions=True
)

# Sidebar menu items configuration
menu_items = [
    {"name": "Projects", "href": "/projects", "icon": "fas fa-project-diagram"},
    {"name": "Execution Summary", "href": "/execution-summary", "icon": "fas fa-chart-line"},
    {"name": "Module Details", "href": "/module-details", "icon": "fas fa-cogs"},
    {"name": "Trends", "href": "/trends", "icon": "fas fa-chart-bar"},
    {"name": "Settings", "href": "/settings", "icon": "fas fa-gear"},
]

# Professional sidebar component
sidebar = html.Div(
    [
        # Header/Brand Section
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(className="fas fa-flask")
                            ],
                            className="brand-icon-wrapper"
                        ),
                        html.Div(
                            [
                                html.H4("T A P", className="brand-title"),
                                html.Small("Test Analytics Portal", className="brand-subtitle"),
                            ],
                            className="brand-text"
                        )
                    ],
                    className="brand-container"
                )
            ],
            className="sidebar-header"
        ),

        # Navigation Section
        html.Div(
            [
                html.Div("NAVIGATION", className="nav-section-title"),
                dbc.Nav(
                    [
                        dbc.NavLink(
                            [
                                html.Div(
                                    html.I(className=item["icon"]),
                                    className="nav-icon-wrapper"
                                ),
                                html.Span(item["name"], className="nav-text")
                            ],
                            href=item["href"],
                            active="exact",
                            className="nav-link-modern"
                        )
                        for item in menu_items
                    ],
                    vertical=True,
                    className="nav-modern"
                ),
            ],
            className="nav-section"
        ),

        # Footer Section
        html.Div(
            [
                html.Div(
                    [
                        html.I(className="fas fa-user-circle user-icon"),
                        html.Div("Admin User", className="user-name"),
                        html.Small("System Administrator", className="user-role")
                    ],
                    className="user-info"
                )
            ],
            className="sidebar-footer"
        )
    ],
    className="sidebar-professional"
)

# App layout
app.layout = html.Div([
    sidebar,
    html.Div(dash.page_container, className="page-content")
])

if __name__ == "__main__":
    app.run(debug=True, port=8050)
