import pandas as pd
from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

df = pd.read_csv('hot100.csv', sep=',')

df['Weeks in Charts'] = df['Weeks in Charts'].replace('-', 0)
df['Weeks in Charts'] = df['Weeks in Charts'].astype(int)

df['Last Week'] = df['Last Week'].replace('-', 0)
df['Last Week'] = df['Last Week'].astype(int)

df['Date'] = pd.to_datetime(df['Date'])

top_songs = df.groupby(['Artist', 'Song']).agg({
  'Peak Position' : 'min',
  'Weeks in Charts': 'max',
}).reset_index()

top_songs.sort_values('Peak Position', inplace=True)

app = Dash(__name__)

songs_summary = df.groupby(['Artist','Song'], as_index=False).agg({
    'Peak Position':'min',
    'Weeks in Charts':'max',
    'Date':'min'
}).rename(columns={'Date':'First Date'})

songs_summary['Month'] = songs_summary['First Date'].dt.month_name()
seasonal_counts = songs_summary['Month'].value_counts().reindex(
    ['January','February','March','April','May','June',
     'July','August','September','October','November','December']
).fillna(0).reset_index()
seasonal_counts.columns = ['Month','Count']

seasonal_fig = px.bar(seasonal_counts, x='Month', y='Count', title='Songs entering Hot 100 by Month',color='Count', color_continuous_scale=px.colors.sequential.Viridis)
seasonal_fig.update_layout(height=600)

artist_ranking = songs_summary.groupby('Artist', as_index=False)['Weeks in Charts'].sum()
artist_ranking = artist_ranking.sort_values('Weeks in Charts', ascending=False).head(50)
ranking_fig = px.bar(artist_ranking, x='Weeks in Charts', y='Artist', orientation='h', color='Weeks in Charts',
                     title='Top Artists by Total Weeks on Hot 100', color_continuous_scale=px.colors.sequential.Viridis)

ranking_fig.update_layout(height=600)

artist_counts = songs_summary.groupby('Artist')['Song'].nunique().reset_index()
artist_counts['Category'] = artist_counts['Song'].apply(lambda x: 'One-hit' if x==1 else 'Multi-hit')
onehit_fig = px.pie(artist_counts, names='Category', title='One-hit vs Multi-hit Artists')
onehit_fig.update_layout(height=600)

artists = df['Artist'].dropna().unique().tolist()
default_artist = [artists[0]] if artists else []

def make_artist_fig(selected_artists):
    if not selected_artists:
        return px.bar(title='Select one or more artists to see comparison')
    filt = df[df['Artist'].isin(selected_artists)]
    agg = filt.groupby(['Artist', 'Song']).agg({
        'Weeks in Charts': 'max',
        'Peak Position': 'min'
    }).reset_index()
    agg = agg.sort_values('Weeks in Charts', ascending=False).head(30)
    fig = px.bar(agg, x='Song', y='Weeks in Charts', color='Artist',
                 hover_data=['Peak Position'], title='Weeks in Charts')
    fig.update_layout(xaxis={'categoryorder':'total descending'}, height=600)
    return fig

artist_fig_default = make_artist_fig(default_artist)


app.layout = html.Div([
    html.Div([
        html.H1('Billboard Hits Dashboard', 
                style={'color': 'Black', 'textAlign': 'center', 'fontFamily': 'Arial'})
    ], style={
        'padding': '20px',
        'borderRadius': '10px',
        'margin': '10px',
        
    }),

    html.Div([
        html.Div([
            html.Div([
                html.H3('Artist Comparison', style={'color': 'Black', 'textAlign':'center', 'fontFamily': 'Arial'}),
                dcc.Dropdown(
                    id='artist-dropdown',
                    options=[{'label': artist, 'value': artist} for artist in df['Artist'].unique()],
                    value=[],
                    multi=True,
                    style={'marginBottom': '10px', 'width':'60%', 'margin':'auto'}
                ),
                html.Div([
                    dcc.Graph(id='artist-chart', figure=artist_fig_default)
                ], style={'width':'80%','margin':'auto'})
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px'}),


            html.Div([
                html.Div([
                    dcc.Graph(id='seasonal-chart', figure=seasonal_fig)
                ], style={'width':'80%','margin':'auto'})
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px'})
            
            ,

            html.Div([
                html.Div([
                    dcc.Graph(figure=ranking_fig)
                ], style={'width':'80%','margin':'auto','marginBottom':'30px'})
            ])
            
            ,

            html.Div([
                html.Div([
                    dcc.Graph(figure=onehit_fig)
                ], style={'width':'80%','margin':'auto','marginBottom':'30px'})
            ]),

            html.Div([
            html.Label('Select Time Period:'),
            dcc.RangeSlider(
            id='year-slider',
            min=df['Date'].dt.year.min(),
            max=df['Date'].dt.year.max(),
            value=[1990, df['Date'].dt.year.max()],
            marks={i: str(i) for i in range(df['Date'].dt.year.min(),
                                            df['Date'].dt.year.max()+1, 10)},
            step=1
            ), dcc.Graph(id='num1-chart') 
            ], style={'padding': '20px'})
            
        ])
    ], style={'padding': '20px'})
])

@app.callback(
    Output('artist-chart', 'figure'),
    Input('artist-dropdown', 'value'),
)
def update_artist_chart(selected_artists):
    if isinstance(selected_artists, str):
        selected_artists = [selected_artists]
    return make_artist_fig(selected_artists or [])

@app.callback(
    Output('num1-chart', 'figure'),
    Input('year-slider', 'value')
)
def update_num1_chart(year_range):
    start_year, end_year = year_range

    filtered = df[(df['Date'].dt.year >= start_year) & (df['Date'].dt.year <= end_year)]
    num1 = (
        filtered[filtered['Peak Position'] == 1]
        .groupby(filtered['Date'].dt.year)['Song']
        .nunique()
        .reset_index()
    )
    num1.columns = ['Year', 'Number of #1 Songs']

    fig = px.line(num1, x='Year', y='Number of #1 Songs',
                  markers=True, title='Number of #1 Songs Per Year')
    return fig


if __name__ == '__main__':
  app.run(debug=True)