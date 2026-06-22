#Importing Libraries
import dash_core_components as dcc
import dash_html_components as html
from dash import Dash
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
from jitcache import Cache
import numpy as np
import os
import pickle
import time
from astropy.io import fits
import subprocess
from astropy.visualization import ZScaleInterval
interval = ZScaleInterval()
import plotly.graph_objects as go

#Tempelate for app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
     
#Configuring dash app
app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

#CACHE MANAGEMENT
#CACHE MANAGEMENT
cache = Cache()

app.layout = html.Div(children = [

                html.Label('Forced Photometry Pipeline'),
                html.Br(),
                html.Label('Enter RA and DEC: '),
                html.Br(),
                dcc.Input(id='input1', type='number', placeholder='RA'),
                dcc.Input(id='input2', type='number', placeholder='DEC'),
                html.Br(),
                html.Br(),
                html.Button('Submit', id='btn-submit'),
                html.Hr(),
                
                html.Div([
                #Reference and difference images
                html.Div(dcc.Graph(id='sci',className="six columns",
                    style={'display': 'inline-block',"width" : "50%"})),    
                html.Div(dcc.Graph(id='d',className="six columns",
                    style={'display': 'inline-block',"width" : "50%"}))],className="row"),
                
                #Light Curve
                dcc.Graph(id='Mygraph',animate=True),
                
                #hidden signal value
                html.Div(id='signal', style={'display': 'none'}),
                html.Label('Click on a data point to see the difference image'),

            ],style={'text-align': 'center'})
            
# perform expensive computations in this "global store"
# these computations are cached in a globally available
# redis memory store which is available across processes
# and for all time.
@cache.memoize
def global_store(signal):
    
    if signal is not None:
        
       
        #saving input for psf script
        np.save('nparray/input.npy',signal)
        os.system('sh comp.sh')
        #loading up different arrays
        mag = pickle.load(open("nparray/mag.txt","rb"))
        sigp = pickle.load(open("nparray/sigp.txt","rb"))
        sign = pickle.load(open("nparray/sign.txt","rb"))
        date = pickle.load(open("nparray/date.txt","rb"))
        fid = pickle.load(open("nparray/fid.txt","rb"))
        no = pickle.load(open("nparray/no.txt","rb"))
        mlim = pickle.load(open("nparray/mlim.txt","rb"))
        mag = pd.Series(mag)
        sigp = pd.Series(sigp)
        sign = pd.Series(sign)
        date = pd.Series(date)
        fid = pd.Series(fid)
        no = pd.Series(no)
        mlim = pd.Series(mlim)
        data = {'Mag':mag, 'MJD': date, 'Er+': sigp,'Er-':sign, 'Band': fid, 'Image':no,'Mlim':mlim}
        df = pd.DataFrame(data)
        df['Mag'] = df['Mag'].round(2)
        df['Er+'] = df['Er+'].round(2)
        df['Er-'] = df['Er-'].round(2)
        #df.to_csv('ZTF18abjqmrh.csv', sep='\t')
        return df

#generating figure
def generate_figure(signal):
    
    if signal is not None:
        
        df = global_store(signal)
        fig = px.scatter(df, x='MJD', y='Mag', error_y='Er+',error_y_minus="Er-", 
                         color='Band',
                         color_discrete_map={'g': 'green', 'r': 'red','i':'blue'},
                         custom_data=['Image'],width=1400, height=600)
        color = df['Band'].to_numpy()
        color = np.where(color=='g', 'green', color)
        color = np.where(color=='r', 'red', color)
        color = np.where(color=='i', 'blue', color)
        fig.update_layout(title_text='Light Curve', title_x=0.5)
        fig.add_trace(go.Scatter(x=df['MJD'],y=df['Mlim'],mode='markers',name='upperlim',marker_symbol = 'triangle-down',marker=dict(color=color)))
        fig['layout']['uirevision'] = 10
        fig.update_layout(xaxis_title="MJD")
        fig.update_layout(yaxis_title="magnitude")
        fig.update_layout(xaxis = dict(tickformat = "000"))
        return fig

###############################################################################
#Callcacks
@app.callback(Output('signal','children'),
                [Input('btn-submit', 'n_clicks')],
                [State('input1','value'),State('input2','value')])


def compute_value(n_clicks,input1,input2):

    if n_clicks:
        
        signal = [input1,input2]
        global_store(signal)
        return signal

#updating graph
@app.callback([Output('Mygraph','figure'),Output('sci','figure')]
              ,[Input('signal','children')])

def update_graph(signal):
    
    if signal is not None:
    
        fig = generate_figure(signal)
        fig['layout']['yaxis']['autorange'] = "reversed"
        img = os.listdir('dat/psf/')
        hdulist = fits.open('dat/psf/'+img[0])
        data = hdulist[0].data
        lim = interval.get_limits(data)
        figg = px.imshow(data,color_continuous_scale='Greys',zmin=lim[0], zmax=lim[1])
        figg['layout']['yaxis']['visible'] = False
       
        figg['layout']['yaxis']['autorange'] = "reversed"
        figg.update_layout(title_text='Reference Image', title_x=0.5)
        return [fig,figg]



@app.callback([Output('d', 'figure')], [Input('Mygraph', 'clickData')])
def updateDimg(clickData):
    
    if clickData:
        
        imgd = clickData['points'][0]['customdata'][0]
        img = os.listdir('dat/dif/') 
        hdulist = fits.open('dat/dif/'+img[imgd])
        data = hdulist[1].data
        lim = interval.get_limits(data)
        figg = px.imshow(data,color_continuous_scale='Greys',zmin=lim[0], zmax=lim[1])
        figg['layout']['yaxis']['visible'] = False
        figg['layout']['yaxis']['autorange'] = "reversed"
        figg.update_layout(title_text='Difference Image', title_x=0.5)
        return [figg]

if __name__ == "__main__":

    app.run_server(port=8000)
