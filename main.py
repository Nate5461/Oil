import pandas as pd
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_caching import Cache
from flaskwebgui import FlaskUI
from waitress import serve
from threading import Thread
import os
import numpy as np

app = Flask(__name__)

app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'oil_data.sqlite')
template_dir = os.path.join(script_dir, 'templates')

app.template_folder = template_dir

@cache.cached(timeout=50)
def fetch_oil():
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM mstrOil"  
    data = pd.read_sql(query, conn)
    conn.close()
    return data

@app.context_processor
def inject_wallet_number():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT amount FROM wallet")

    wallet = cursor.fetchone()[0]
    conn.close()
    return dict(wallet_number=wallet)

@app.context_processor
def inject_unrealized():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT unrealized FROM wallet")
    unrealized = cursor.fetchone()[0]
    conn.close()
    return dict(unrealized=unrealized)

@app.context_processor
def inject_netLiquid():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT netLiquid FROM wallet")
    netLiquid = cursor.fetchone()[0]
    conn.close()
    return dict(netLiquid=netLiquid)


@app.route('/getWallet', methods=['GET'])
def get_wallet_number():
    wallet_info = inject_wallet_number()
    unrealized = inject_unrealized()
    netLiquid = inject_netLiquid()

    response = {
        'wallet_info': wallet_info,
        'unrealized_info': unrealized,
        'netLiquid_info': netLiquid
    }

    return jsonify(response)


def fetch_bought():
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM transactions"  
    data = pd.read_sql(query, conn)
    conn.close()
    return data

def fetch_limits():
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM limit_orders"  
    data = pd.read_sql(query, conn)
    conn.close()
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/withdraw', methods=['POST'])
def withdraw():
    try:
        data = request.json
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE wallet SET amount = amount - ?", (data['amount'],))
        conn.commit()
        return jsonify({"message": "Withdrawal successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/deposit', methods=['POST'])
def deposit():
    try:
        data = request.json
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE wallet SET amount = amount + ?", (data['amount'],))
        conn.commit()
        return jsonify({"message": "Deposit successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/restart', methods=['POST'])
def restart():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE wallet SET amount = 0.0")
        cursor.execute("DELETE FROM transactions")
        conn.commit()
        return jsonify({"message": "Restart successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data', methods=['POST'])
def get_data():
    selected_date = request.json['date']
    data = fetch_oil()
    
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

    filtered_data['CloseDate'] = filtered_data['CloseDate'].astype(str)
    # Prepare response
    response_data = filtered_data[['CloseDate', 'Settlement Price', 'Change', 'percent_change', 'Spread']].to_dict(orient='records')

    return jsonify(response_data)

@app.route('/bought', methods=['GET'])
def bought():
    return render_template('bought.html')



@app.route('/buyContract', methods=['POST'])
def buy_contract():
    print("buyContract")
    try:
        data = request.json
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        mstrOil = fetch_oil()

        # Assuming data and mstrOil are defined somewhere above this code
        data['contractDate'] = pd.to_datetime(data['contractDate']).date()
        data['transactionDate'] = pd.to_datetime(data['transactionDate']).date()
        
        # Ensure the mstrOil DataFrame columns are in the correct format
        mstrOil['CurrentDate'] = pd.to_datetime(mstrOil['CurrentDate']).dt.date
        mstrOil['CloseDate'] = pd.to_datetime(mstrOil['CloseDate']).dt.date

        price = mstrOil[(mstrOil['CurrentDate'] == data['transactionDate']) & (mstrOil['CloseDate'] == data['contractDate'])]['Settlement Price'].values[0]


        #THis will never happen for spreads currently
        if float(data['limitPrice']) == float(price):
            purchase_date = data['transactionDate']
            status = 'Purchased'
            purchase_price = price
        else:
            purchase_date = None
            status = 'Pending'
            purchase_price = None

        

        cursor.execute("INSERT INTO transactions (trans_date, contract_date, qty, limit_price, status, purchase_date, type, purchase_price, trans_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                       (data['transactionDate'], data['contractDate'], data['qty'], data['limitPrice'], status, purchase_date, data['type'], purchase_price, data['trans_price']))
        conn.commit()  

        return jsonify({"message": "Transaction sent"}), 200 
    except Exception as e:
        return jsonify({"message": str(e)}), 500  
    

@app.route('/buySpread', methods=['POST'])
def buy_spread():
    try:
        data = request.json
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO spreadTransactions (transaction_date, qty, frontMonth, backMonth, type, limit_price, status, purchase_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                       (data['currentDate'], data['qty'], data['frontMonth'], data['backMonth'], data['type'], data['price'], data['status'], data['purchaseDate']))
        conn.commit()  
        return jsonify({"message": "Purchase successful"}), 200 
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/boughtData', methods=['POST'])
def bought_data():
    selected_date = request.json['date']
    data = fetch_bought()
    mstrOil = fetch_oil()
    
    # Convert date columns to datetime
    data['contract_date'] = pd.to_datetime(data['contract_date']).dt.date
    data['purchase_date'] = pd.to_datetime(data['purchase_date']).dt.date.astype(str)
    data['contract_date'] = pd.to_datetime(data['contract_date']).dt.date
    data['trans_date'] = pd.to_datetime(data['trans_date']).dt.date
    selected_current_date = pd.to_datetime(selected_date).date()


    mstrOil['CurrentDate'] = pd.to_datetime(mstrOil['CurrentDate']).dt.date
    mstrOil['CloseDate'] = pd.to_datetime(mstrOil['CloseDate']).dt.date

    for index, row in data.iterrows():
        # Debugging prints
        row['contract_date'] = pd.to_datetime(row['contract_date']).date()

        filtered_mstrOil = mstrOil[(mstrOil['CurrentDate'] == selected_current_date)  & (mstrOil['CloseDate'] == row['contract_date'])]
        
        if not filtered_mstrOil.empty:
            data.at[index, 'settle_price'] = filtered_mstrOil['Settlement Price'].values[0]
        else:
            data.at[index, 'settle_price'] = 0

    
    
    data['change'] = (data['settle_price'] - data['limit_price']).round(2)
    data['percent_change'] = (data['change'] / data['limit_price'] * 100).round(2)

    # Filter data
    filtered_data = data[(data['trans_date'] <= selected_current_date) & (data['contract_date'] >= selected_current_date)]
    filtered_data['contract_date'] = filtered_data['contract_date'].astype(str)

    # Prepare response
    response_data = filtered_data[['contract_date', 'settle_price', 'type', 'limit_price', 'purchase_date', 'status', 'change', 'percent_change']].to_dict(orient='records')

    print(response_data)
    return jsonify(response_data)



def run_server():
    serve(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    app.run()
    #FlaskUI(app=app, server="flask").run()

