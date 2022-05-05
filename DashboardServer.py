from dash import dcc,html
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
import flask

server = flask.Flask(__name__)

app = DashProxy(server=server,prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()])
app.layout = html.Div([
    # dcc.Graph(figure=fig, id="country"),
    # dcc.Slider(min=1979, max=2020, step=1,
    #            value=1979,
    #            id='my-slider',
    #            marks={i: i for i in range(1979, 2020, 1)}
    #            ),
    # dcc.Graph(figure=m, id = "country" ),
    # dcc.Store(id = "year",storage_type='local',data = 1979),
    # dcc.Store(id = "country_value",storage_type='local',data = "Albania"),


])

if __name__ == '__main__':
    app.run_server(host="172.28.1.5", debug=True, port=8050)