import dash
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash import Input, Output, State
from dash.dependencies import ALL
from insights import get_job_insights 

class App:
    def __init__(self, df):
        self.merged = df
        self.app = dash.Dash(__name__, suppress_callback_exceptions = True, external_stylesheets = [dbc.themes.BOOTSTRAP])
        server = self.app.server
        self.app.title = "Standard of Living Dashboard"
        self.define_layout()
        self.define_callbacks()

    def define_layout(self):
        # Sidebar layout
        sidebar = dbc.Col([
            html.H2("Dashboard", className="display-6 text-white mb-4"),
            html.Hr(),
            dbc.Nav([
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Compare by region", href="/page-1", active="exact"),
                dbc.NavLink("Compare by spending category", href="/page-2", active="exact"),
                dbc.NavLink("Search for jobs", href = "/page-3", active = "exact")
            ], vertical=True, pills=True, className="text-white")
        ], width=3, className="bg-dark p-4 vh-100")

        # Content area placeholder
        content = dbc.Col(
            html.Div(id="page-content", className="p-4"),
            width=9
        )

        # Main layout (URL tracker and page content placeholder)
        self.app.layout = html.Div([
            dcc.Location(id='url', refresh=False),
            dbc.Row([sidebar, content], className = "gx-0")
        ])

    # Home page layout
    def home_layout(self):
        return html.Div([
            html.H3("Welcome to the standard of living dashboard!", className = "mb-4"),
            html.P("See how purchasing power varies across geography and spending category by occupation. " \
            "This app uses occupational wage data from the U.S. Bureau of Labor Statistics and regional price parity data from the U.S. Bureau of Economic Analysis. " \
            "For a given occupation and geographical location, purchasing power is calculated by multiplying the ratio of median annual salary to regional price parity by 100."),
            dcc.Link("Compare by region", href="/page-1"),
            html.Br(),
            dcc.Link("Compare by spending category", href="/page-2"),
            html.Br(),
            dcc.Link("Search for jobs", href = "/page-3")
        ])

    # Page 1 layout
    def page1_layout(self):
        return html.Div([
            dcc.Dropdown(
                id = "occupation-dropdown1",
                options = [
                    {"label": occupation, "value": occupation} for occupation in self.merged["Occupation Title"].unique().tolist()
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

    # Page 2 layout
    def page2_layout(self):
        return html.Div([
            dcc.Dropdown(
                id = "occupation-dropdown2",
                options = [
                    {"label": occupation, "value": occupation} for occupation in self.merged["Occupation Title"].unique().tolist()
                ],
                value = "All Occupations",
                multi = False,
                style = {"width": "50%"}
            ),
            dcc.Dropdown(
                id = "location-dropdown2",
                options = [
                    {"label": location, "value": location} for location in self.merged["Area"].unique().tolist()
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
    
    # page 3 layout
    def page3_layout(self):
        return html.Div([
            dcc.Dropdown(
                id="occupation-dropdown3",
                options=[
                    {"label": occupation, "value": occupation} for occupation in self.merged["Occupation Title"].unique().tolist()
                ],
                value="All Occupations",
                multi=False,
                style={"width": "50%"}
            ),
            dcc.Input(
                id="location-input",
                type="text",
                placeholder="Enter a city or address",
                debounce=True,
                style={"width": "50%"}
            ),

            dbc.Button("Search Jobs", id="search-button", color="primary", className="my-3"),
            
            html.Div(id="output-page3", className="mb-4"),
            
            dbc.Accordion([
                dbc.AccordionItem([dcc.Graph(id="technical-skills-chart")], title="Top Technical Skills"),
                dbc.AccordionItem([dcc.Graph(id="soft-skills-chart")], title="Top Soft Skills"),
                dbc.AccordionItem([dcc.Graph(id="experience-chart")], title="Experience / Education"),
            ], start_collapsed=True)
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
            
        # Update page 1
        @self.app.callback(
            Output("location-bar-chart", "figure"),
            Input("occupation-dropdown1", "value"),
            Input("category-dropdown1", "value")
        )
            
        def update_page1(occupation_input, category_input):

            filtered_df = self.merged[(self.merged["Occupation Title"] == occupation_input) & (self.merged["Category"] == category_input)]
            filtered_df = filtered_df.sort_values(by = "Median Purchasing Power", ascending = False)

            if filtered_df.empty:
                return px.bar()

            fig1 = px.bar(
                filtered_df.head(8),
                x = "Area",
                y = "Median Purchasing Power",
                title = "Metropolitan Areas with Highest Standard of Living",
                labels = {"Median Purchasing Power" : "Median Purchasing Power", "Area": "Area"},
                height = 400
            )
            
            return fig1
        
        # Update page 2
        @self.app.callback(
            Output("rpp-bar-chart", "figure"),
            Input("occupation-dropdown2", "value"),
            Input("location-dropdown2", "value")
        )

        def update_page2(occupation_input, location_input):
            filtered_df = self.merged[(self.merged["Occupation Title"] == occupation_input) & (self.merged["Area"] == location_input)]
            
            if filtered_df.empty:
                return px.bar()

            fig2 = px.bar(
                filtered_df.head(5),
                x = "Category",
                y = "Median Purchasing Power",
                title = "Purchasing Power by Spending Category",
                labels = {"Median Purchasing Power" : "Median Purchasing Power", "Category": "Category"},
                height = 400
            )
            return fig2

        # update page 3
        @self.app.callback(
            [
                Output("technical-skills-chart", "figure"),
                Output("soft-skills-chart", "figure"),
                Output("experience-chart", "figure"),
                Output("output-page3", "children")
            ],
            Input("search-button", "n_clicks"),
            State("occupation-dropdown3", "value"),
            State("location-input", "value"),
            prevent_initial_call=True
        )
        def update_page3(n_clicks, occupation, location):
            import pandas as pd
            import plotly.express as px

            df_jobs, top_skills = get_job_insights(occupation, location)

            if df_jobs.empty or not top_skills:
                empty_fig = px.bar(title="No jobs found.")
                return empty_fig, empty_fig, empty_fig, html.Div("No job postings found.")

            def make_chart(skill_list, title):
                skill_df = pd.DataFrame(skill_list, columns=["Skill", "Appearances"])
                return px.bar(skill_df, x="Skill", y="Appearances", title=title)

            tech_fig = make_chart(top_skills["technical_skills"], "Top Technical Skills")
            soft_fig = make_chart(top_skills["soft_skills"], "Top Soft Skills")
            exp_fig = make_chart(top_skills["experience_education"], "Experience / Education")

            # Extract top entries
            top_tech = top_skills["technical_skills"][0][0] if top_skills["technical_skills"] else "N/A"
            top_soft = top_skills["soft_skills"][0][0] if top_skills["soft_skills"] else "N/A"
            top_exp = top_skills["experience_education"][0][0] if top_skills["experience_education"] else "N/A"

            summary_card = dbc.Card([
                dbc.CardBody([
                    html.H4("Job Market Insights", className="card-title"),
                    html.P(f"🔍 Found {len(df_jobs)} job postings for **{occupation}** in **{location}** in the past week."),
                    html.Hr(),
                    html.P(["📌 Most requested technical skill: ", dbc.Badge(top_tech, color="info", className="ms-1")]),
                    html.P(["🧠 Top soft skill employers seek: ", dbc.Badge(top_soft, color="success", className="ms-1")]),
                    html.P(["🎓 Common experience/education level: ", dbc.Badge(top_exp, color="warning", className="ms-1")]),
                ])
            ], className="shadow-sm")

            return tech_fig, soft_fig, exp_fig, summary_card
            
    def start(self):
        self.app.run(debug = True)