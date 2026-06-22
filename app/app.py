from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import numpy as np
import os
import pickle
from astropy.io import fits
from astropy.visualization import ZScaleInterval
import download
#import psf
import plotly.graph_objects as go

interval = ZScaleInterval()

#Tempelate for app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
     
     
#Configuring dash app
app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


app.layout = html.Div(children = [

                html.Label('Bramhaand.com'),
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


def global_store(signal):
        
    '''
    try:
        dir = './app/dat/dif'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))
        dir = './app/dat/psf'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))
        dir = './app/nparray'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))
        dir = './app/dat/ref'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))
        os.remove('./app/dat/delme.dat')
        os.remove('./app/dat/dummy.pkl')
    except:
        pass
    download.download(signal[0],signal[1])
    '''
       
    mag = pickle.load(open("./app/nparray/mag.txt","rb"))
    sigp = pickle.load(open("./app/nparray/sigp.txt","rb"))
    sign = pickle.load(open("./app/nparray/sign.txt","rb"))
    date = pickle.load(open("./app/nparray/date.txt","rb"))
    fid = pickle.load(open("./app/nparray/fid.txt","rb"))
    no = pickle.load(open("./app/nparray/no.txt","rb"))
    mlim = pickle.load(open("./app/nparray/mlim.txt","rb"))
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
    df.to_pickle("./app/dat/dummy.pkl")  
    print(df)


#generating figure
def generate_figure(signal):
    
    if signal is not None:

        df = pd.read_pickle("./app/dat/dummy.pkl")
        fig = px.scatter(df, x='MJD', y='Mag', error_y='Er+',error_y_minus="Er-", 
                         color='Band',
                         color_discrete_map={'g': 'green', 'r': 'red','i':'blue'},
                         custom_data=['Image'],width=1400, height=600)
        color = df['Band'].to_numpy()
        color = np.where(color=='g', 'green', color)
        color = np.where(color=='r', 'red', color)
        color = np.where(color=='i', 'blue', color)
        fig.update_layout(title_text='Light Curve', title_x=0.5)
        fig.add_trace(go.Scatter(x=df['MJD'],y=df['Mlim'],mode='markers',name='lim',marker_symbol = 'triangle-down',marker=dict(color=color)))
        fig['layout']['uirevision'] = 10
        fig.update_layout(xaxis_title="MJD")
        fig.update_layout(yaxis_title="magnitude")
        fig.update_layout(xaxis = dict(tickformat = "000"))
        return fig


###############################################################################
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
        img = os.listdir('./app/dat/ref/')
        hdulist = fits.open('./app/dat/ref/'+img[0],ignore_missing_simple=True)
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
        print(imgd)
        img = os.listdir('./app/dat/dif/') 
        hdulist = fits.open('./app/dat/dif/'+img[imgd])
        data = hdulist[1].data
        lim = interval.get_limits(data)
        figg = px.imshow(data,color_continuous_scale='Greys',zmin=lim[0], zmax=lim[1])
        figg['layout']['yaxis']['visible'] = False
        figg['layout']['yaxis']['autorange'] = "reversed"
        figg.update_layout(title_text='Difference Image', title_x=0.5)
        return [figg]

if __name__ == "__main__":

    app.run_server(host='0.0.0.0', port=9999)

