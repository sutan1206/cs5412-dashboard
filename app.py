import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import numpy as np
from dash.dependencies import Output, Input
from azure.cosmos import CosmosClient

url = 'https://cs5412finalprocosmos.documents.azure.com:443/'
key = 'lKQOG519VP60ez0hT5aah945IV0eyRIuYN3cu2caZulDUJHYhOdQOCnbWd7s8lXOTlufv7yaJBjPI3GnnTqASQ=='
dbClient = CosmosClient(url, credential=key)
db = dbClient.get_database_client(database='OutputDB')
container = db.get_container_client('milk')
attribute_choice = ["Dim", "Lactation_Num", "Yield", "ProdRate", "Fat", "Avg_Fat", "Protein", "Avg_Protein",
"Lactose", "Avg_Lactose", "Conductivity", "Avg_Conductivity", "Milking_Time", "Avg_Milking_Time", "Activity", "Activity",
"Activity_Deviation", "Weight", "Temperature", "Stomach_Activity"]
PAGE_SIZE = 5

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "Milk Analysis"

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

print(minDate, maxDate)

app.layout = html.Div(
    children=[
        html.Div(
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
        ),
        html.Div(
            children=[
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
                    style={"width": "50%"},
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
            ],
            className="menu",
        ),
         html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="activity-chart",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="fat-chart",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dash_table.DataTable(
                        id='activity-table',
                        columns=[{"name": i, "id": i} for i in ['Animal_ID', 'Group_ID', 'ActivityDeviation(%)']],
                        page_current=0,
                        page_action='custom',
                        page_size=PAGE_SIZE,
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)

@app.callback(
    [Output("activity-chart", "figure"), Output("fat-chart", "figure"), Output('activity-table', 'data'),],
    [   
        Input("animal-filter", "value"),
        Input("group-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input('activity-table', "page_current"),
        Input('activity-table', "page_size"),
    ],
)
def update_charts(animal_id, group_id, start_date, end_date, page_current, page_size):
    data = list(container.query_items(
        query = f"""
          SELECT c.Timestamp, c.Animal_ID, c.Group_ID, c['Activity_Deviation'], c['Fat'] FROM container c
          WHERE {'false' if animal_id is None else 'c.Animal_ID = @aID'} AND 
                {'true' if not group_id else 'ARRAY_CONTAINS(@gIDs, c.Group_ID)'} AND
                (c.Timestamp BETWEEN @sDate AND @eDate)
          ORDER BY c.Timestamp
        """,
        parameters=[
            dict(name='@aID', value=animal_id),
            dict(name='@gIDs', value=group_id),
            dict(name='@sDate', value=start_date),
            dict(name='@eDate', value=end_date)
        ],
        enable_cross_partition_query=True
    ))

    activity_chart_figure = {
        "data": [
            {
                "x": [row['Timestamp'] for row in data],
                "y": [row["Activity_Deviation"] for row in data],
                "type": "lines",
                "hovertemplate": "%{y:.2f}%<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Acrivity Deviation %",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"ticksuffix": "%", "fixedrange": True},
            "colorway": ["#17B897"],
        },
    }

    fat_chart_figure = {
        "data": [
            {
                "x": [row["Timestamp"] for row in data],
                "y": [row["Fat"] for row in data],
                "type": "lines",
            },
        ],
        "layout": {
            "title": {"text": "Fat(%)", "x": 0.05, "xanchor": "left"},
            "xaxis": {"fixedrange": True},
            "yaxis": {"ticksuffix": "%", "fixedrange": True},
            "colorway": ["#E12D39"],
        },
    }

    table_data = data
    print(data)

    return activity_chart_figure, fat_chart_figure, table_data


if __name__ == "__main__":
    app.run_server(debug=True)

