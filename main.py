import pyodbc
import pandas as pd
from flask import Flask, render_template, request, jsonify
from flaskwebgui import FlaskUI
from waitress import serve
from threading import Thread

app = Flask(__name__)

database_path = r"C:\Users\TPI-P330\OneDrive\Documents\Oil\test.accdb"

def connect_to_access(database_path):
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        r'DBQ=' + database_path + ';'
    )
    conn = pyodbc.connect(conn_str)
    return conn

def fetch_data(conn):
    query = "SELECT * FROM mstrOil"  
    data = pd.read_sql(query, conn)
    return data

@app.route('/')

def index():
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def get_data():
    selected_date = request.json['date']
    connection = connect_to_access(database_path)
    data = fetch_data(connection)
    
    # Convert date columns to datetime
    data['CurrentDate'] = pd.to_datetime(data['CurrentDate']).dt.date
    data['CloseDate'] = pd.to_datetime(data['CloseDate']).dt.date
    
    selected_current_date = pd.to_datetime(selected_date).date()

    # Filter data
    filtered_data = data[(data['CurrentDate'] <= selected_current_date) & (data['CloseDate'] >= selected_current_date)]

    # Process data
    filtered_data = filtered_data.sort_values(['CloseDate', 'CurrentDate'], ascending=[True, False])
    filtered_data['Change'] = 0.0
    last_prices = filtered_data[filtered_data['CurrentDate'] < selected_current_date].groupby('CloseDate')['Settlement Price'].first().reset_index()
    filtered_data = filtered_data.merge(last_prices, on='CloseDate', how='left', suffixes=('', '_LastBeforeSelected'))
    filtered_data.loc[filtered_data['CurrentDate'] == selected_current_date, 'Change'] = (filtered_data['Settlement Price'] - filtered_data['Settlement Price_LastBeforeSelected']).round(2)
    filtered_data['percent_change'] = (filtered_data['Change'] / filtered_data['Settlement Price'] * 100).round(2)
    filtered_data = filtered_data.drop_duplicates(subset='CloseDate')
    filtered_data = filtered_data.sort_values('CloseDate', ascending=True)
    filtered_data['Next Settlement Price'] = filtered_data['Settlement Price'].shift(1)
    filtered_data['Spread'] = (filtered_data['Settlement Price'] - filtered_data['Next Settlement Price']).fillna(0).round(2)

    # Prepare response
    response_data = filtered_data[['CloseDate', 'Settlement Price', 'Change', 'percent_change', 'Spread']].to_dict(orient='records')

    return jsonify(response_data)

def run_server():
    serve(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    FlaskUI(app=app, server="flask").run()

