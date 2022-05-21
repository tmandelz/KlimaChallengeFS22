from flask import Flask
from dash import html
from dash import dcc
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform, State


# app = Flask(__name__)
server = Flask(__name__)
app = DashProxy(server=server,prevent_initial_callbacks=True,suppress_callback_exceptions=True,
                transforms=[MultiplexerTransform()], title='Klimadaten Challenge')

# page_BackgroundInfo_layout = html.Div([
#     html.H1('Hello Dash'),
#     html.Div([
#         html.P('Dash converts Python classes into HTML'),
#         html.P("This conversion happens behind the scenes by Dash's JavaScript front-end")
#     ])
# ])

header = html.Nav(className = "navbar navbar-expand-lg navbar-light bg-light", children=[
    html.Div(children=[
        dcc.Link('DashBoard', href='/DashBoard',className="nav-item nav-link btn"),
        dcc.Link('Datastory', href='/Datastory',className="nav-item nav-link btn"),
        dcc.Link('BackgroundInformation', href='/BackgroundInformation',className="nav-item nav-link btn"),
        ])])
    

page_BackgroundInfo_layout = html.Div([header,html.Div([
    html.Div(id='Datastory-content'),
    html.H5(children='Was ist eine Background?'),
])])


@app.route("/")
def hello():
    return page_BackgroundInfo_layout

app.run()