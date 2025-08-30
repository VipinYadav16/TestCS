import os
import pandas as pd
import plotly.express as px
import json
import plotly.utils as pu

def plot_anomalies(df, coin_name, anomalies_df, output_dir='public/pred'):
    """
    Creates and saves an interactive Plotly chart for price trends with anomalies.
    
    :param df: DataFrame with price and volume data
    :param coin_name: Name of the cryptocurrency
    :param anomalies_df: DataFrame of detected anomalies
    :param output_dir: Directory to save the plot image for AI analysis
    :return: A tuple containing the JSON string of the Plotly chart and the path to the saved image file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a line chart for the price data
    fig = px.line(df, x=df.index, y='value', title=f"{coin_name.capitalize()} Price with Anomalies",
                  line_shape='linear',
                  color_discrete_sequence=['#8B5CF6'])

    # Add markers for anomalies
    if not anomalies_df.empty:
        fig.add_scatter(x=anomalies_df.index, y=anomalies_df['value'], mode='markers', name='Anomalies',
                        marker=dict(color='#EF4444', size=10, symbol='circle',
                                    line=dict(width=1, color='white')),
                        hovertemplate='<b>Anomaly Date:</b> %{x|%b %d, %Y}<br><b>Price:</b> $%{y:.2f}<extra></extra>')
    
    # Configure a basic dark theme independent of the frontend
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor='rgba(255,255,255,0.1)',
        yaxis_gridcolor='rgba(255,255,255,0.1)',
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#333333",
            font_color="white",
            bordercolor="#666666",
            namelength=-1
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(0,0,0,0)',
        ),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    fig.update_xaxes(
        title_font=dict(size=12),
        tickfont=dict(size=10),
        linecolor='#666666',
        mirror=True
    )
    fig.update_yaxes(
        title_font=dict(size=12),
        tickfont=dict(size=10),
        linecolor='#666666',
        mirror=True
    )

    fig.update_traces(
        hovertemplate='<b>Date:</b> %{x|%b %d, %Y}<br><b>Price:</b> $%{y:.2f}<extra></extra>',
        selector=dict(mode='lines')
    )

    # Export a static image for Gemini analysis
    file_path = os.path.join(output_dir, f"{coin_name}_analysis.png")
    fig.write_image(file_path)

    return json.dumps(fig, cls=pu.PlotlyJSONEncoder), file_path


def plot_volume_analysis(df, coin_name, start_date_str, end_date_str):
    """
    Creates an interactive Plotly chart for trading volume analysis.
    
    :param df: DataFrame with volume data
    :param coin_name: Name of the cryptocurrency
    :param start_date_str: Start date for the plot title
    :param end_date_str: End date for the plot title
    :return: JSON string of the Plotly chart data
    """
    avg_volume = df['volume'].mean()
    peak_volume_date = df['volume'].idxmax()
    peak_volume = df['volume'].max()

    fig = px.line(df, x=df.index, y='volume', title=f"{coin_name.capitalize()} Trading Volume Analysis ({start_date_str} to {end_date_str})",
                  color_discrete_sequence=['teal'])

    # Add average volume line
    fig.add_hline(y=avg_volume, line_dash="dash", line_color="red", name="Average Volume")

    # Add marker for peak volume
    fig.add_scatter(x=[peak_volume_date], y=[peak_volume], mode='markers', name='Peak Volume Day',
                    marker=dict(color='red', size=10, symbol='circle'))

    # Format the y-axis to be more readable
    def format_volume(x, pos):
        if x > 1e9:
            return f'${x/1e9:.2f}B'
        elif x > 1e6:
            return f'${x/1e6:.2f}M'
        else:
            return f'${x:,.0f}'

    fig.update_yaxes(tickformat = ',.0f')
    fig.layout.yaxis.tickformat = '.2s'

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Date",
        yaxis_title=f"Trading Volume (in USD)",
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor='rgba(255,255,255,0.1)',
        yaxis_gridcolor='rgba(255,255,255,0.1)',
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#333333",
            font_color="white",
            bordercolor="#666666",
            namelength=-1
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(0,0,0,0)',
        ),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    fig.update_xaxes(
        title_font=dict(size=12),
        tickfont=dict(size=10),
        linecolor='#666666',
        mirror=True
    )
    fig.update_yaxes(
        title_font=dict(size=12),
        tickfont=dict(size=10),
        linecolor='#666666',
        mirror=True
    )
    
    return json.dumps(fig, cls=pu.PlotlyJSONEncoder)