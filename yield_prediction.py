from app import app

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go

from dash.dependencies import Output, Input
from plotly.subplots import make_subplots
from azure.cosmos import CosmosClient

import json
import os
import ssl
import urllib.request
from datetime import datetime, timedelta
from collections import deque

url = 'https://cs5412finalprocosmos.documents.azure.com:443/'
key = 'lKQOG519VP60ez0hT5aah945IV0eyRIuYN3cu2caZulDUJHYhOdQOCnbWd7s8lXOTlufv7yaJBjPI3GnnTqASQ=='

db = CosmosClient(url, credential=key).get_database_client(database='OutputDB')
container = db.get_container_client('test')

attribute_choice = ["Temperature", "Stomach_Activity"]

animalIDs = container.query_items(
    query="SELECT DISTINCT c.Animal_ID FROM container c ORDER BY c.Animal_ID",
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

predictSearchBar = [
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
            html.Div(
                children="Start Date", className="menu-title"
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

predictGraph = [
    html.Div(
        children=dcc.Graph(
            id="attribute-chart3",
            config={"displayModeBar": False},
            figure={},
        ),
        className="card",
    ),
    
]

def allowSelfSignedHttps(allowed):
    # bypass the server certificate verification on client side
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

allowSelfSignedHttps(True)

def predict(lastFive):
  data = {'data': [{f'last{5 - i}':lastFive[i] for i in range(5)}]}
  body = str.encode(json.dumps(data))
  modelUrl = 'http://e72a2dfd-de80-4dd7-a5c9-1c71b7c5b0ba.eastus.azurecontainer.io/score'
  headers = {'Content-Type':'application/json', 'Authorization':('Bearer ')}

  req = urllib.request.Request(modelUrl, body, headers)
  response = urllib.request.urlopen(req)

  result = json.loads(json.loads(response.read().decode()))
  return result['result']

@app.callback(
    Output("attribute-chart3", "figure"),
    [
        Input("animal-filter", "value"),
        Input("date-picker", "date"),
        Input('interval-component', 'n_intervals'),
        
    ],
)
def update_charts(animal_id, date, n):
    data = list(container.query_items(
        query = f"""
          SELECT c.Timestamp, c.Yield
          FROM container c
          WHERE {'false' if animal_id is None else 'c.Animal_ID = @aID'} AND
                {'false' if date is None else 'c.Timestamp >= @date'}
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
    if data:
      fig.add_trace(
          go.Scatter(x=[row['Timestamp'] for row in data], y=[row['Yield'] for row in data], name='Historial Yield'),
          secondary_y=False,
      )

      lastDate = datetime.strptime(data[-1]['Timestamp'], '%Y-%m-%d')
      predictions = [data[-1]['Yield']]
      lastFive = deque([row['Yield'] for row in data[max(0, len(data) - 5):]])

      for _ in range(7):
        predictions.append(predict(lastFive))
        lastFive.popleft()
        lastFive.append(predictions[-1])

      fig.add_trace(
          go.Scatter(x=[lastDate + timedelta(days=i) for i in range(8)], y=predictions, name='Predicted Yield'),
          secondary_y=False,
      ) 

    # Add figure title
    fig.update_layout(
        title_text="Yield prediction plot"
    )

    # Set x-axis title
    fig.update_xaxes(title_text="timestamp ")

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>Yield (kg)</b>", secondary_y=False)

    return fig
