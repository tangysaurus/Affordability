import dash
import plotly.express as px
import dash_bootstrap_components as dbc
import json
import pandas as pd
import asyncio
import os
from dash import html, dcc
from dash import Input, Output, State
from dash.dependencies import ALL
from src.fetch_data import main, extract_job_info
from src.job_match import extract_resume_text_from_base64, get_matches
from src.llm_prompt import get_feedback, get_insights
from dash.exceptions import PreventUpdate
from src.purchasing_power import run

class App:
    def __init__(self, occupation_data):
        self.occupation_data = occupation_data
        self.app = dash.Dash(__name__, suppress_callback_exceptions = True, external_stylesheets = [dbc.themes.BOOTSTRAP])
        server = self.app.server
        self.app.title = "Standard of Living Dashboard"
        self.define_layout()
        self.define_callbacks()

    def define_layout(self):
        # Top Navbar layout
        navbar = dbc.Navbar(
            dbc.Container([
                dbc.Row([
                    dbc.Col(
                        html.H2(
                            [
                                html.Img(
                                    src = "/assets/career_icon.png",
                                    style={"height": "40px", "transform": "scale(1.4)", "marginRight": "10px", "position": "relative", "top": "4px" }
                                ),
                                # html.I(className="fas fa-chalkboard-teacher", style={"marginRight": "10px"}),
                                "Career Match",
                            ],
                            className="display-6 text-white mb-3",
                            style={"display": "flex", "alignItems": "center", "fontWeight": "600"}
                        ),
                        width="auto"),  # Title
                    dbc.Col(
                        dbc.Nav([
                            dbc.NavLink("Home", href="/", active="exact", className="text-white"),
                            dbc.NavLink("Search for jobs", href="/page-1", active="exact", className="text-white"),
                            dbc.NavLink("SOL by region", href="/page-2", active="exact", className="text-white"),
                            dbc.NavLink("SOL by spending category", href="/page-3", active="exact", className="text-white")
                        ], navbar=True, pills = True), 
                        className="d-flex align-items-center"                   )
                ], align = "center", className = "w-100")
            ], fluid=True),
            color="dark", dark=True, className="mb-4"
        )

        # Content area placeholder
        content = dbc.Col(
            html.Div(id="page-content", className="p-4"),
            width=12
        )

        # Main layout (URL tracker and page content placeholder)
        self.app.layout = html.Div([
            dcc.Location(id='url', refresh=False),
            dcc.Store(id = "resume-text-store"),
            navbar,
            content
        ])

    def home_layout(self):
        return html.Div(
            children=[
                html.Div(
                    children=[
                        html.H3("Welcome to Career Match!", className="mb-4", style={'text-align': 'center', 'font-size': '2.5em'}),
                        html.P(
                            "If you're looking to advance your career, this is the place to be! \n"
                            "Match with jobs based on your resume, generate concise job breakdowns, and get personalized feedback to help you craft the most competitive job application.",
                            style={'text-align': 'center', 'font-size': '1.1em', 'margin-top': '20px', 'line-height': '1.6em'}
                        ),
                        html.Div(
                            children=[
                                dcc.Link("Search for jobs", href="/page-3", style={'display': 'block', 'margin-top': '10px', 'font-size': '1.2em', 'text-align': 'center'})
                            ],
                            style={'text-align': 'center', 'margin-top': '30px'}
                        ),
                        html.P(
                            "Also, don't forget to use the standard of living (SOL) dashboard to see how your purchasing power varies by geography and spending category. \n"
                            "We've compiled occupational wages and regional price levels to help you make the most informed decisions. \n",
                            style={'text-align': 'center', 'font-size': '1.1em', 'margin-top': '20px', 'line-height': '1.6em'}
                        ),
                        html.Div(
                            children=[
                                dcc.Link("SOL by region", href="/page-1", style={'display': 'block', 'margin-top': '20px', 'font-size': '1.2em', 'text-align': 'center'}),
                                dcc.Link("SOL by spending category", href="/page-2", style={'display': 'block', 'margin-top': '10px', 'font-size': '1.2em', 'text-align': 'center'})
                            ],
                            style={'text-align': 'center', 'margin-top': '30px'}
                        )
                    ],
                    style={
                        'maxWidth': '800px',
                        'width': '100%',
                        'textAlign': 'center',  # Aligns all inner text
                        'padding': '20px'
                    }
                )
            ],
            style={
                'display': 'flex',
                'justifyContent': 'center',
                'padding': '40px',
            }
        )
    
    # page 1 layout
    def page1_layout(self):
        return html.Div([
            html.Div([
                dbc.Row([
                    # Occupation dropdown
                    dbc.Col(
                        dcc.Dropdown(
                            id="occupation-dropdown3",
                            options=[
                                {"label": occupation, "value": occupation}
                                for occupation in self.occupation_data["Occupation Title"].unique().tolist()
                            ],
                            value="All Occupations",
                            multi=False,
                            placeholder="What job are you looking for?",
                        ),
                        width=5
                    ),

                    # Location input with location icon
                    dbc.Col(
                        dbc.InputGroup([
                            dbc.InputGroupText("📍"),
                            dbc.Input(
                                id="location-input",
                                type="text",
                                placeholder="Enter a city or address",
                                debounce=True,
                            )
                        ]),
                        width=4
                    ),

                    # Search button
                    dbc.Col(
                        dbc.Button("Search Jobs", id="search-button", color="primary", className="w-100"),
                        width=3
                    ),
                ], justify="center", className="my-4 g-2"),
                # Resume upload section
                dbc.Row([
                    dbc.Col([
                        html.Label("📄 Upload Your Resume (PDF)", className="form-label"),
                        dcc.Upload(
                            id="resume-upload",
                            children=html.Div(id = "upload-box-content", children = [
                                "Drag and drop or ",
                                html.A("select a PDF file")
                            ]),
                            style={
                                "width": "100%",
                                "height": "40px",
                                "lineHeight": "40px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "10px",
                                "textAlign": "center",
                                "marginTop": "10px",
                            },
                            multiple=False,
                            accept=".pdf"
                        ),
                    ], width=12)
                ], className="my-2"),
            ], style={"maxWidth": "900px", "margin": "0 auto"}),
            html.Div(id = "output-page3", className = "mb-4")
        ])

    # Page 2 layout
    def page2_layout(self):
        return html.Div([
            dcc.Dropdown(
                id = "occupation-dropdown1",
                options = [
                    {"label": occupation, "value": occupation} for occupation in self.occupation_data["Occupation Title"].unique().tolist()
                ],
                value = "All Occupations",
                multi = False,
                style = {"width": "50%"}
            ),
            dcc.Dropdown(
                id = "category-dropdown1",
                options = [
                    {"label": "All items", "value": "RPPs: All items"},
                    {"label": "Goods", "value": "RPPs: Goods"},
                    {"label": "Housing", "value": "RPPs: Services: Housing"},
                    {"label": "Utilities", "value": "RPPs: Services: Utilities"},
                    {"label": "Other Services", "value": "RPPs: Services: Other"}
                ],
                value = "RPPs: All items",
                multi = False,
                style = {"width": "50%"}
            ),
            dbc.Card([
                dbc.CardBody([
                    html.Div(id="output-page1"),
                    dcc.Graph(id = "location-bar-chart")
                ])
            ])
        ])

    # Page 3 layout
    def page3_layout(self):
        return html.Div([
            dcc.Dropdown(
                id = "occupation-dropdown2",
                options = [
                    {"label": occupation, "value": occupation} for occupation in self.occupation_data["Occupation Title"].unique().tolist()
                ],
                value = "All Occupations",
                multi = False,
                style = {"width": "50%"}
            ),
            dcc.Dropdown(
                id = "location-dropdown2",
                options = [
                    {"label": location, "value": location} for location in self.occupation_data["Area"].unique().tolist()
                ],
                value = "Abilene, TX",
                multi = False,
                style = {"width": "50%"}
            ),
            dbc.Card([
                dbc.CardBody([
                    html.Div(id="output-page2"),
                    dcc.Graph(id = "rpp-bar-chart")
                ])
            ])
        ])

    def define_callbacks(self):

        # Page routing callback: Updates page content based on URL
        @self.app.callback(
            Output('page-content', 'children'),
            Input('url', 'pathname')
        )

        def display_page(pathname):
            if pathname == '/page-1':
                return self.page1_layout()
            elif pathname == '/page-2':
                return self.page2_layout()
            elif pathname == "/page-3":
                return self.page3_layout()
            else:
                return self.home_layout()
            
        # store resume text
        @self.app.callback(
            Output("upload-box-content", "children"),
            Output('resume-text-store', 'data'),
            Input('resume-upload', 'contents'),
            prevent_initial_call=True
        )

        def cache_resume_text(resume_contents):
            if not resume_contents:
                return dash.no_update
            return (
                html.Span("✅ Resume uploaded and read"), 
                extract_resume_text_from_base64(resume_contents)
            )

        # Callback to generate job cards and layout
        @self.app.callback(
            Output("output-page3", "children"),
            Input("search-button", "n_clicks"),
            State("occupation-dropdown3", "value"),
            State("location-input", "value"),
            State("resume-text-store", "data"),
            prevent_initial_call=True
        )

        # update page 1
        def update_page1(n_clicks, occupation, location, resume_text):
            if not resume_text:
                return "Please upload a resume."
            
            # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            job_data = extract_job_info(asyncio.run(main(occupation, location)))
            matches = get_matches(resume_text, job_data)

            if not matches:
                return html.Div([
                    html.H5("No job matches found.", style={"color": "red"})
                ])

            top_matches = list(matches.items())[:8]

            # Job Cards
            job_cards = [
                html.Div([
                    html.H5(job_data.loc[job_id, 'title'], style={"marginBottom": "5px"}),
                    html.P(job_data.loc[job_id, 'employer']),
                    html.P(f"{round(match_rating * 100)}% match"),
                    html.A("View Job Posting", href=job_data.loc[job_id, 'apply_link'], target="_blank", style={"color": "#007BFF"})
                ],
                id={'type': 'job-card', 'index': job_id},
                n_clicks=0,
                style={
                    "border": "1px solid #ccc",
                    "borderRadius": "10px",
                    "padding": "15px",
                    "marginBottom": "15px",
                    "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
                    "backgroundColor": "#fafafa",
                    "cursor": "pointer"
                })
                for job_id, match_rating in top_matches
            ]

            return dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.H5(f"🔍 Found {len(job_data)} jobs in the past week!", className="mb-3"),
                        html.H5("🎯 Your top 8 matches:", className="mb-4"),
                        html.Div(job_cards),
                        dcc.Store(id='job-data-store', data=job_data.to_dict()),
                        dcc.Store(id='match-data-store', data=dict(top_matches)),
                        dcc.Store(id = "chat-store", data = [])
                    ], width=5),
                    # Loading spinner + output display
                    dbc.Col([
                        dbc.RadioItems(
                            id="insight-toggle",
                            options=[
                                {"label": "🧠 Job Breakdown", "value": "breakdown"},
                                {"label": "💬 Resume Advisor", "value": "advisor"},
                            ],
                            value="breakdown",
                            inline=True,
                            className="mb-2"
                        ),
                        dcc.Loading(
                            id="loading-spinner",
                            type="circle",
                            children = html.Div(id = "insight-display")
                        )
                    ], width = 5)
                ], justify = "center", className="mt-4")
            ], fluid=True)

        # Callback to display insights
        @self.app.callback(
            Output("insight-display", "children"),
            Input({'type': 'job-card', 'index': ALL}, 'n_clicks'),
            Input("insight-toggle", "value"),
            State("resume-text-store", "data"),
            State("job-data-store", "data"),
            State("match-data-store", "data"),
            prevent_initial_call=True
        )

        def display_insight(n_clicks_list, toggle_value, resume_text, job_data_dict, match_data_dict):
            if not any(n_clicks_list):
                raise PreventUpdate
            
            def render_list(items):
                if isinstance(items, list):
                    return html.Ul([html.Li(item) for item in items])
                else:
                    return html.P(items or "N/A")

            clicked_index = next(i for i, n in enumerate(n_clicks_list) if n)
            job_data = pd.DataFrame.from_dict(job_data_dict)
            top_matches = list(match_data_dict.items())
            job_id = top_matches[clicked_index][0]

            # Get feedback
            if toggle_value == "advisor":
                raw_advice = get_feedback(resume_text, job_data.loc[job_id, "title"], job_data.loc[job_id, "description"])
                try:
                    advice = json.loads(raw_advice)
                except json.JSONDecodeError:
                    return html.Div("Sorry, couldn't parse insights.")
                
                # Then update your Card layout
                return dbc.Card([
                    dbc.CardBody([
                        html.H6("General Fit"),
                        render_list(advice.get("How well does this resume match the job description?")),

                        html.H6("Strengths"),
                        render_list(advice.get("Highlight key skills, experiences, or qualifications in the resume that make me a good fit for this job.")),

                        html.H6("Weaknesses"),
                        render_list(advice.get("Point out any potential gaps or areas where I might need to improve to increase my chances for this role.")),

                        html.H6("Should you apply"),
                        render_list(advice.get("Overall, would you recommend I apply for this job? Why or why not?"))
                    ])
                ], className="shadow-sm mt-3", style={"borderRadius": "12px"})
            
            # Get insights for that job
            raw_insights = get_insights(job_data.loc[job_id, "title"], job_data.loc[job_id, "description"])
            try:
                insights = json.loads(raw_insights)
            except json.JSONDecodeError:
                return html.Div("Sorry, couldn't parse insights.")
            
            # Then update your Card layout
            return dbc.Card([
                dbc.CardBody([
                    html.H6("Main Responsibilities"),
                    render_list(insights.get("main_responsibilities")),

                    html.H6("Preferred Qualifications"),
                    render_list(insights.get("preferred_qualifications")),

                    html.H6("Key Skills"),
                    render_list(insights.get("key_skills")),

                    html.H6("Time Commitment & Deadlines"),
                    render_list(insights.get("time_commitment_deadlines")),

                    html.H6("Salary & Benefits"),
                    render_list(insights.get("salary_benefits", "N/A")),

                    html.H6("Risk of Automation"),
                    html.P(insights.get("automation_risk", "N/A"))
                ])
            ], className="shadow-sm mt-3", style={"borderRadius": "12px"})
            
        # Update page 2
        @self.app.callback(
            Output("location-bar-chart", "figure"),
            Input("occupation-dropdown1", "value"),
            Input("category-dropdown1", "value")
        )
            
        def update_page1(occupation_input, category_input):

            filtered_occupation_data = self.occupation_data[(self.occupation_data["Occupation Title"] == occupation_input) & (self.occupation_data["Category"] == category_input)]
            filtered_occupation_data = filtered_occupation_data.sort_values(by = "Median Purchasing Power", ascending = False)

            if filtered_occupation_data.empty:
                return px.bar()

            fig1 = px.bar(
                filtered_occupation_data.head(8),
                x = "Area",
                y = "Median Purchasing Power",
                title = "Metropolitan Areas with Highest Standard of Living",
                labels = {"Median Purchasing Power" : "Median Purchasing Power", "Area": "Area"},
                height = 400
            )
            
            return fig1
        
        # Update page 3
        @self.app.callback(
            Output("rpp-bar-chart", "figure"),
            Input("occupation-dropdown2", "value"),
            Input("location-dropdown2", "value")
        )

        def update_page2(occupation_input, location_input):
            filtered_occupation_data = self.occupation_data[(self.occupation_data["Occupation Title"] == occupation_input) & (self.occupation_data["Area"] == location_input)]
            
            if filtered_occupation_data.empty:
                return px.bar()

            fig2 = px.bar(
                filtered_occupation_data.head(5),
                x = "Category",
                y = "Median Purchasing Power",
                title = "Purchasing Power by Spending Category",
                labels = {"Median Purchasing Power" : "Median Purchasing Power", "Category": "Category"},
                height = 400
            )
            return fig2

    def start(self):
        port = int(os.environ.get("PORT", 8050)) 
        self.app.run(debug = True, host="0.0.0.0", port=port)

occupation_data = run()
dashboard = App(occupation_data)
server = dashboard.app.server