import pandas as pd
import dash
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash import Input, Output

# reads in a file, converts it to a dataframe, & cleans it
def process(file_path):
    df = pd.read_csv(file_path)

    if df.isnull().values.any():
        df.fillna(0, inplace = True)

    for column in df.columns:
        if pd.api.types.is_string_dtype(df[column]):
            df[column] = df[column].str.strip()
    
    return df

def run():
    # process wage & rpp data
    wage_data = process("data/regional_salaries.csv")
    rpp_data = process("data/regional_prices.csv")
    # merge datasets on GeoFIPS
    merged = pd.merge(wage_data, rpp_data, on = "GeoFIPS")
    merged = merged.drop(columns = ["GeoFIPS", "Occupation Code", "GeoName_y"])
    # calculate median purchasing power
    merged["Median Purchasing Power"] = (merged["Annual Salary Median"].astype(float) / merged["RPP 2023"].astype(float) / 100).round(2)
    # rename & get relevant columns
    merged = merged.rename(columns = {"GeoName_x" : "Area", "Description" : "Category"})
    merged = merged[["Area", "Occupation Title", "Annual Salary Median", "Category", "RPP 2023", "Median Purchasing Power"]]
    return merged

merged = run()

app = dash.Dash(__name__, suppress_callback_exceptions = True, external_stylesheets = [dbc.themes.BOOTSTRAP])
server = app.server
app.title = "Standard of Living Dashboard"

# Sidebar layout
sidebar = dbc.Col([
    html.H2("Dashboard", className="display-6 text-white mb-4"),
    html.Hr(),
    dbc.Nav([
        dbc.NavLink("Home", href="/", active="exact"),
        dbc.NavLink("Compare by region", href="/page-1", active="exact"),
        dbc.NavLink("Compare by spending category", href="/page-2", active="exact"),
    ], vertical=True, pills=True, className="text-white")
], width=3, className="bg-dark p-4 vh-100")

# Content area placeholder
content = dbc.Col(
    html.Div(id="page-content", className="p-4"),
    width=9
)

# Main layout (URL tracker and page content placeholder)
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.Row([sidebar, content], className = "gx-0")
])

# Home page layout
def home_layout():
    return html.Div([
        html.H3("Welcome to the standard of living dashboard!", className = "mb-4"),
        html.P("See how purchasing power varies across geography and spending category by occupation. " \
        "This app uses occupational wage data from the U.S. Bureau of Labor Statistics and regional price parity data from the U.S. Bureau of Economic Analysis. " \
        "For a given occupation and geographical location, purchasing power is calculated by multiplying the ratio of median annual salary to regional price parity by 100."),
        dcc.Link("Compare by region", href="/page-1"),
        html.Br(),
        dcc.Link("Compare by spending category", href="/page-2")
    ])

# Page 1 layout
def page1_layout():
    return html.Div([
        dcc.Dropdown(
            id = "occupation-dropdown1",
            options = [
                {"label": occupation, "value": occupation} for occupation in merged["Occupation Title"].unique().tolist()
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
def page2_layout():
    return html.Div([
        dcc.Dropdown(
            id = "occupation-dropdown2",
            options = [
                {"label": occupation, "value": occupation} for occupation in merged["Occupation Title"].unique().tolist()
            ],
            value = "All Occupations",
            multi = False,
            style = {"width": "50%"}
        ),
        dcc.Dropdown(
            id = "location-dropdown2",
            options = [
                {"label": location, "value": location} for location in merged["Area"].unique().tolist()
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

# Page routing callback: Updates page content based on URL
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))

def display_page(pathname):
    if pathname == '/page-1':
        return page1_layout()
    elif pathname == '/page-2':
        return page2_layout()
    else:
        return home_layout()

# Update page 1
@app.callback(
    Output("location-bar-chart", "figure"),
    Input("occupation-dropdown1", "value"),
    Input("category-dropdown1", "value")
)

def update_page1(occupation_input, category_input):
    filtered_df = merged[(merged["Occupation Title"] == occupation_input) & (merged["Category"] == category_input)]
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
@app.callback(
    Output("rpp-bar-chart", "figure"),
    Input("occupation-dropdown2", "value"),
    Input("location-dropdown2", "value")
)

def update_page2(occupation_input, location_input):
    filtered_df = merged[(merged["Occupation Title"] == occupation_input) & (merged["Area"] == location_input)]
    
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

if __name__ == '__main__':
    app.run(debug = True)