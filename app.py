import os
import requests
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from sklearn.ensemble import IsolationForest
from dotenv import load_dotenv
import google.generativeai as genai
import textwrap
from plot_generator import plot_anomalies, plot_volume_analysis
import time

# Load environment variables from .env file
load_dotenv()

# Configure Flask app and CORS
app = Flask(__name__)
CORS(app)

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GEMINI API KEY"))

# --- Model Check ---
try:
    print("Checking for available Gemini models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Found model: {m.name}")
    print("Model check complete.")
except Exception as e:
    print(f"Failed to list models. This may be due to an incorrect API key or network issues: {e}")
# --------------------

# List of cryptocurrencies
TOP_5_COINS = ['bitcoin', 'ethereum', 'ripple', 'cardano', 'solana']

# Function to fetch historical data for price
def fetch_historical_price_data(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    
    if coin_id not in TOP_5_COINS:
        raise ValueError(f"Invalid coin_id: {coin_id}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        timestamps = [item[0] for item in data['prices']]
        prices = [item[1] for item in data['prices']]
        volumes = [item[1] for item in data['total_volumes']]

        df = pd.DataFrame({
            'date': pd.to_datetime(timestamps, unit='ms'),
            'value': prices,
            'volume': volumes
        })
        
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()
    except KeyError:
        print(f"API response for {coin_id} is missing expected keys.")
        return pd.DataFrame()

# Function to fetch historical data for volume (new logic)
def fetch_historical_volume_data(coin_id, start_date_str, end_date_str):
    try:
        start_timestamp = int(time.mktime(pd.to_datetime(start_date_str).timetuple()))
        end_timestamp = int(time.mktime(pd.to_datetime(end_date_str).timetuple()))
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
        
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range?"
        f"vs_currency=usd&from={start_timestamp}&to={end_timestamp}"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        volumes_data = data.get('total_volumes', [])

        if not volumes_data:
            return pd.DataFrame()

        df = pd.DataFrame(volumes_data, columns=['timestamp', 'volume'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('date', inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        raise Exception(f"An error occurred during the API request: {e}")
        

# Function to run anomaly detection
def run_anomaly_detection(df):
    if df.empty:
        return df, pd.DataFrame()
        
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    df.ffill(inplace=True)

    model = IsolationForest(contamination=0.05, random_state=42)
    df['anomaly_score'] = model.fit_predict(df[['value', 'volume']])
    df['anomaly'] = df['anomaly_score'].apply(lambda x: x == -1)
    
    anomalies = df[df['anomaly'] == True]
    
    return df, anomalies

# Function to get Gemini analysis from an image
def get_gemini_analysis(stock_code, anomalies_df, image_path):
    # Use a model that supports multimodal input
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Read the image file
    with open(image_path, 'rb') as f:
        image_data = f.read()

    # Create a Generative Language API Part from the image data
    image_part = {
        "inline_data": {
            "mime_type": "image/png",
            "data": image_data
        }
    }
    
    # Create the text part of the prompt
    anomalies_text = ""
    if not anomalies_df.empty:
        anomaly_dates = anomalies_df.index.strftime('%Y-%m-%d').tolist()
        anomalies_text = "The following dates show anomalies: " + ", ".join(anomaly_dates) + ". Use these dates to reference the anomalies in your analysis."
    
    text_part = textwrap.dedent(f"""
    I want you to act as a crypto market analyzer and analyze the graph I show you(in the attached image
".
    
    i have built a Crypto market manipulation detection tool- Crypto Sentinel.
it is a deep learning model that uses a feedforward autoencoder to perform anomaly detection on crypto currency prices
    
    {anomalies_text}
Here is the pipeline for my project-
Detailed Pipeline
1. Data Acquisition and Initial Processing
Technology: yfinance, pandas, numpy
Description:
Historical stock/crypto price data downloaded via yfinance API using the user-provided ticker.
Only the closing price ('Close') is considered.
Data timestamps are standardized to Asia/Kolkata timezone for consistency.
Data smoothing:
A 4-day rolling sum smooths short-term fluctuations, reducing noise.
Visualization:
Full lifetime rolling-close price plotted for initial exploratory analysis using matplotlib.
2. Data Preparation
Windowing:
Time series is segmented into overlapping fixed-length windows of size 30 days, moving with a step of 5 days.
Normalization:
Within each window, values are scaled to via MinMaxScaler.
Training/testing split:
Training data covers 2000 to 2021 and test data from 2022 onwards based on timestamps.
Outputs:
X_train and X_test are 3D arrays (num_windows x window_size x 1) flattened to 2D arrays (num_windows x window_size) for model input.
3. Model Architecture: Feedforward Autoencoder
Technology: TensorFlow 2.x, Keras API
Components:
PartDescription
Encoder
Sequential feedforward network with two Dense layers (16 units → 8 units), ReLU activation.
Decoder
Sequential feedforward network with two Dense layers (16 units → 30 units), ReLU and sigmoid activation on output layer.
Input/Output
Input is a vector of 30 normalized prices per window; output is reconstructed 30-output vector.
Objective:
The autoencoder learns an internal "compressed" representation of the typical 30-day price sequence and reconstructs it.
Trained with Mean Absolute Error (MAE) loss to minimize reconstruction differences.
4. Model Training
Hyperparameters:
Epochs: up to 40
Batch size: 16
Training details:
Trains in an unsupervised fashion using X_train both as input and target output.
Employs early stopping callback monitoring validation loss with patience 2 to prevent overfitting.
Output:
Trained model saved in "saved_models/anomaly_autoencoder.h5".
5. Anomaly Detection Logic
Reconstruction and error calculation:
Applies autoencoder to training and test data windows.
Computes MAE reconstruction loss per window.
Threshold setting:
Threshold computed from training reconstruction errors using 95th percentile to robustly separate normal windows from anomalies.
Flagging:
Test windows with reconstruction error above threshold are flagged as anomalies.
6. Visualization and User Input
User Interaction:
User inputs custom date ranges (start and end) from 2022 onwards.
Only detected anomaly windows fully within that date range are visualized, allowing focused analysis.
Plotting:
For each anomaly window, plots include:
Actual normalized rolling-close prices (blue line) for the 30-day window.
Autoencoder reconstruction (red line).
Shaded reconstruction error (red transparent fill).
Fallback:
If no anomalies detected within date range, the output is a text saying "No anomalies detected"
7. Resource Management
Clears TensorFlow backend session and runs Python garbage collector after plotting to minimize memory usage.

the output of this project is in a graphical format, with the x axis being the dates and the y axis is the normalized prices.
Legend of the graph-
Actual normalized rolling-close prices (blue line) for the 30-day window.
Autoencoder reconstruction (red line).
Shaded reconstruction error (red transparent fill).

More context-
There are different kind of market manipulations(pump-and-dump schemes, spoofing (placing and canceling orders to create a false sense of supply or demand), wash trading (simultaneous buy and sell orders of the same asset), cornering the market (controlling the supply of an asset to influence its price), and front-running (trading on advance knowledge of a large pending order))

What YOU HAVE TO DO as a crypto market analyzer-
For experience traders, the graph itself is enough to make inferences about the state of the market/currency and whether there is a potential for market manipulation.
But i have to take into account rookie traders that cannot make sense of the graph. Thats where you come in.
I want you to analyze the graphical output attached with the prompt and analyze it. and give me an output.
the output should contain-
-A detailed explanation of the graph(what the user is seeing, what the elements of the graph represents)
-An inference, that is based on your knowledge of the crypto market, of the graph, and what the graphical data is suggesting.
-Whether there is a potential for market manipulation in the given timeframe(the x axis)


Final Output format and structure-
###Key Trends and Observations
###Anomaly(If any) Breakdown
###Recommended Actions(generalized NON FINANCIAL advice)
###A Strict disclaimer-
    """)
    
    # Create the prompt with both text and image parts
    prompt_parts = [text_part, image_part]
    
    response = model.generate_content(prompt_parts)
    return response.text

# API endpoint for price and anomaly analysis
@app.route('/api/analyze-crypto')
def analyze_crypto():
    stock_code = request.args.get('stock_code', 'bitcoin')
    
    try:
        data_df, anomalies_df = run_anomaly_detection(fetch_historical_price_data(stock_code, days=30))
        
        # The plot_anomalies function now saves a PNG and returns its path
        plotly_json, plot_path = plot_anomalies(data_df, stock_code, anomalies_df)
        
        # The Gemini analysis is performed using the saved image
        gemini_analysis = get_gemini_analysis(stock_code, anomalies_df, plot_path)
        
        return jsonify({
            'plotly_data': plotly_json,
            'gemini_analysis': gemini_analysis
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# NEW API endpoint for volume analysis
@app.route('/api/analyze-crypto-volume')
def analyze_crypto_volume():
    coin_id = request.args.get('coin_id', 'bitcoin')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not all([coin_id, start_date, end_date]):
        return jsonify({'error': 'Missing coin_id, start_date, or end_date parameter'}), 400

    try:
        volume_df = fetch_historical_volume_data(coin_id, start_date, end_date)
        if volume_df.empty:
            return jsonify({'error': 'No volume data found for the specified period.'}), 404

        plotly_json = plot_volume_analysis(volume_df, coin_id, start_date, end_date)

        return jsonify({
            'plotly_data': plotly_json
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)
