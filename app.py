import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import numpy as np
from dash.dependencies import Output, Input

data = pd.read_csv("Milk_Daily_Data.csv")
data["Date"] = pd.to_datetime(data["datesql"], format="%Y-%m-%d")
data.sort_values("Date", inplace=True)
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
                        html.Div(children="Animal_ID", className="menu-title"),
                        dcc.Dropdown(
                            id="animal-filter",
                            options=[
                                {"label": animal, "value": animal}
                                for animal in np.sort(data.Animal_ID.unique())
                            ],
                            value=1,
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Group", className="menu-title"),
                        dcc.Dropdown(
                            id="group-filter",
                            options=[
                                {"label": group, "value": group}
                                for group in np.sort(data.Group_ID.unique())
                            ],
                            value=5,
                            clearable=True,
                            searchable=False,
                            className="dropdown",
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Date Range", className="menu-title"
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=data.Date.min().date(),
                            max_date_allowed=data.Date.max().date(),
                            start_date=data.Date.min().date(),
                            end_date=data.Date.max().date(),
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
                        columns=[{"name": i, "id": i} for i in data[['Animal_ID', 'Group_ID', 'ActivityDeviation(%)']].columns
                        ],
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
        Input('activity-table', "page_current"),
        Input('activity-table', "page_size"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(animal_id, group_id, page_current, page_size, start_date, end_date):
    
    mask = (
        (data.Animal_ID == animal_id)
        & (not group_id or (data.Group_ID == group_id))
        & (data.Date >= start_date)
        & (data.Date <= end_date)
    )
    filtered_data = data.loc[mask, :]
    activity_chart_figure = {
        "data": [
            {
                "x": filtered_data["Date"],
                "y": filtered_data["ActivityDeviation(%)"],
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
                "x": filtered_data["Date"],
                "y": filtered_data["Fat(%)"],
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
    table_data = filtered_data[['Animal_ID', 'Group_ID', 'ActivityDeviation(%)']].iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')
    return activity_chart_figure, fat_chart_figure, table_data


if __name__ == "__main__":
    app.run_server(debug=True)

