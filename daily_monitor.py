from app import app

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go

from dash.dependencies import Output, Input
from plotly.subplots import make_subplots
from azure.cosmos import CosmosClient

url = 'https://cs5412finalprocosmos.documents.azure.com:443/'
key = 'lKQOG519VP60ez0hT5aah945IV0eyRIuYN3cu2caZulDUJHYhOdQOCnbWd7s8lXOTlufv7yaJBjPI3GnnTqASQ=='

db = CosmosClient(url, credential=key).get_database_client(database='OutputDB')
container = db.get_container_client('test')

attribute_choice = ["Temperature", "Stomach_Activity"]
PAGE_SIZE = 5

animalIDs = container.query_items(
    query="SELECT DISTINCT c.Animal_ID FROM container c ORDER BY c.Animal_ID",
    enable_cross_partition_query=True
)

groupIDs = container.query_items(
    query="""
      SELECT DISTINCT c.Group_ID FROM container c ORDER BY c.Group_ID
    """,
    enable_cross_partition_query=True
)

minDate = list(container.query_items(
    query="SELECT VALUE MIN(c.Timestamp) FROM container c",
    enable_cross_partition_query=True
))[0]

maxDate = list(container.query_items(
    query="SELECT VALUE MAX(c.Timestamp) FROM container c",
    enable_cross_partition_query=True
))[0]

monitorSearchBar = [
    html.Div(
        children=[
            html.Div(children="Animal ID", className="menu-title"),
            dcc.Dropdown(
                id="animal-filter",
                options=[{"label": row['Animal_ID'], "value": row['Animal_ID']}for row in animalIDs],
                clearable=True,
                className="dropdown",
            ),
        ],
        style={"width": "10%"},
    ),
    html.Div(
        children=[
            html.Div(children="Attribute 1", className="menu-title"),
            dcc.Dropdown(
                id="attribute1-filter",
                options=[{"label": attribute, "value": attribute} for attribute in attribute_choice],
                clearable=True,
                searchable=True,
                className="dropdown",
            ),
        ],
        style={"width": "10%"},
    ),
    html.Div(
        children=[
            html.Div(children="Attribute 2", className="menu-title"),
            dcc.Dropdown(
                id="attribute2-filter",
                options=[{"label": attribute, "value": attribute} for attribute in attribute_choice],
                clearable=True,
                searchable=True,
                className="dropdown",
            ),
        ],
        style={"width": "10%"},
    ),
    html.Div(
        children=[
            html.Div(
                children="Date", className="menu-title"
            ),
            dcc.DatePickerSingle(
                id="date-picker",
                clearable=True,
                min_date_allowed=minDate,
                max_date_allowed=maxDate,
            ),
        ]
    ),
    html.Div(className='submit', children=[
      html.Button('Submit', id='submit_button', n_clicks=0)
    ]),
    dcc.Interval(
            id='interval-component',
            interval=10*1000, # in milliseconds
            n_intervals=0
    )
]

monitorGraph = [
    html.Div(
        children=dcc.Graph(
            id="attribute-chart",
            config={"displayModeBar": False},
            figure={},
        ),
        className="card",
    ),
    
]



@app.callback(
    Output("attribute-chart", "figure"),
    [
        Input("animal-filter", "value"),
        Input("attribute1-filter", "value"),
        Input("attribute2-filter", "value"),
        Input("date-picker", "date"),
        Input('interval-component', 'n_intervals'),
        
    ],
)
def update_charts(animal_id, attribute1, attribute2, date, n):
    if attribute1 == attribute2:
      attribute2 = None

    data = list(container.query_items(
        query = f"""
          SELECT c.Timestamp, c.Animal_ID
                 {f', c.{attribute1}' if attribute1 else ''}
                 {f', c.{attribute2}' if attribute2 else ''}
          FROM container c
          WHERE {'false' if animal_id is None else 'c.Animal_ID = @aID'} AND
                {'false' if date is None else 'c.Timestamp = @date'}
          ORDER BY c.Timestamp
        """,
        parameters=[
            dict(name='@aID', value=animal_id),
            dict(name='@date', value=date),
        ],
        enable_cross_partition_query=True
    ))
    print(data)
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    if data and attribute1:
      data[0][attribute1].sort()
      fig.add_trace(
          go.Scatter(x=[p[0] for p in data[0][attribute1]], y=[p[1] for p in data[0][attribute1]], name=attribute1),
          secondary_y=False,
      )
      

    if data and attribute2:
      data[0][attribute2].sort()
      fig.add_trace(
          go.Scatter(x=[p[0] for p in data[0][attribute2]], y=[p[1] for p in data[0][attribute2]], name=attribute2),
          secondary_y=True,
      )
      

    # Add figure title
    fig.update_layout(
        title_text="Attribute plot"
    )

    # Set x-axis title
    fig.update_xaxes(title_text="timestamp ")

    # Set y-axes titles
    if attribute1:
      fig.update_yaxes(title_text="<b>%s</b>" %attribute1, secondary_y=False)

    if attribute2:
      fig.update_yaxes(title_text="<b>%s</b>" %attribute2, secondary_y=True)
   
    return fig
