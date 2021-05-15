from app import app
from attribute_report import reportSearchBar, reportGraph
from daily_monitor import monitorSearchBar, monitorGraph
from yield_prediction import predictSearchBar, predictGraph
from dash.dependencies import Output, Input

@app.callback(
    [Output('search-bar', 'children'), Output('graph', 'children')],
    [Input('url', 'pathname')]
)
def display_page(pathname):
  if pathname in ('/report', '/'):
    return reportSearchBar, reportGraph
  elif pathname == '/monitor':
    return monitorSearchBar, monitorGraph
  elif pathname == '/prediction':
    return predictSearchBar, predictGraph
  else:
    return None, None

if __name__ == '__main__':
    app.run_server(debug=True)
