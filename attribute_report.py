from app import app

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go

from dash.dependencies import Output, Input
from plotly.subplots import make_subplots
from azure.cosmos import CosmosClient

url = 'https://cs5412finalprocosmos.documents.azure.com:443/'
key = 'lKQOG519VP60ez0hT5aah945IV0eyRIuYN3cu2caZulDUJHYhOdQOCnbWd7s8lXOTlufv7yaJBjPI3GnnTqASQ=='
dbClient = CosmosClient(url, credential=key)
db = dbClient.get_database_client(database='OutputDB')
container = db.get_container_client('test')
attribute_choice = ["Dim", "Lactation_Num", "Yield", "ProdRate", "Fat", "Avg_Fat", "Protein", "Avg_Protein",
                    "Lactose", "Avg_Lactose", "Conductivity", "Avg_Conductivity", "Milking_Time", 
                    "Avg_Milking_Time", "Activity", "Activity_Deviation"]
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

reportSearchBar = [
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
            html.Div(children="Group", className="menu-title"),
            dcc.Dropdown(
                id="group-filter",
                options=[{"label": row['Group_ID'], "value": row['Group_ID']} for row in groupIDs],
                clearable=True,
                searchable=True,
                multi=True,
                className="dropdown",
            ),
        ],
        style={"width": "30%"},
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
                children="Date Range", className="menu-title"
            ),
            dcc.DatePickerRange(
                id="date-range",
                min_date_allowed=minDate,
                max_date_allowed=maxDate,
                start_date=minDate,
                end_date=maxDate,
            ),
        ]
    ),
    html.Div(className='submit', children=[
      html.Button('Submit', id='submit_button', n_clicks=0)
    ]),
]

reportGraph = [
    html.Div(
        children=dcc.Graph(
            id="attribute-chart2",
            config={"displayModeBar": False},
            figure={},
        ),
        className="card",
    ),
]

@app.callback(
    Output("attribute-chart2", "figure"),
    [   
        Input("animal-filter", "value"),
        Input("group-filter", "value"),
        Input("attribute1-filter", "value"),
        Input("attribute2-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(animal_id, group_id, attribute1, attribute2, start_date, end_date):
    if attribute1 == attribute2:
      attribute2 = None

    data = list(container.query_items(
        query = f"""
          SELECT c.Timestamp, c.Animal_ID, c.Group_ID
                 {f', c.{attribute1}' if attribute1 else ''}
                 {f', c.{attribute2}' if attribute2 else ''}
          FROM container c
          WHERE {'false' if animal_id is None else 'c.Animal_ID = @aID'} AND 
                {'true' if not group_id else 'ARRAY_CONTAINS(@gIDs, c.Group_ID)'} AND
                (c.Timestamp BETWEEN @sDate AND @eDate)
          ORDER BY c.Timestamp
        """,
        parameters=[
            dict(name='@aID', value=animal_id),
            dict(name='@gIDs', value=group_id),
            dict(name='@sDate', value=start_date),
            dict(name='@eDate', value=end_date),
        ],
        enable_cross_partition_query=True
    ))

    print(data)
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    if attribute1:
      fig.add_trace(
          go.Scatter(x=[row['Timestamp'] for row in data], y=[row[attribute1] for row in data], name=attribute1),
          secondary_y=False,
      )

    if attribute2:
      fig.add_trace(
          go.Scatter(x=[row['Timestamp'] for row in data], y=[row[attribute2] for row in data], name=attribute2),
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
      fig.update_yaxes(title_text="<b>%s</b>" % attribute1, secondary_y=False)

    if attribute2:
      fig.update_yaxes(title_text="<b>%s</b>" % attribute2, secondary_y=True)

    return fig
