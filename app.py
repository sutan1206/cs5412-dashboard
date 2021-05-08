import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
    dbc.themes.BOOTSTRAP
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "Milk Analysis"
server = app.server

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Attribute Report", href="/report")),
        dbc.NavItem(dbc.NavLink("Activity Monitor", href="/monitor")),
    ],
    brand="Milk Analytics",
    color="dark",
    dark=True,
)

header = html.Div(
    children=[
        html.P(children="🐮", className="header-emoji"),
        html.H1(
            children="Milk Analytics", className="header-title"
        ),
        html.P(
            children="Analyze the behavior of cow and its activity and fat data",
            className="header-description",
        ),
    ],
    className="header",
)

app.layout = html.Div(
    children=[
        dcc.Location(id='url', refresh=False),
        navbar,
        header,
        html.Div(id='search-bar', className="menu"),
        html.Div(id='graph', className="wrapper"),
    ]
)
