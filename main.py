import pandas as pd
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_caching import Cache
from flaskwebgui import FlaskUI
from waitress import serve
from threading import Thread
from datetime import datetime
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

@app.route('/stats', methods=['GET'])
def stats():
    return render_template('stats.html')

def fetch_settlePrice(date, contract_date):
    mstrOil = fetch_oil()
    mstrOil['CurrentDate'] = pd.to_datetime(mstrOil['CurrentDate'], format='%Y-%m-%d').dt.date
    mstrOil['CloseDate'] = pd.to_datetime(mstrOil['CloseDate'], format='%Y-%m-%d').dt.date

    contract_date = pd.to_datetime(contract_date).date()

    # Filter for the exact match
    filtered_mstrOil = mstrOil[(mstrOil['CurrentDate'] == date) & (mstrOil['CloseDate'] == contract_date)]
    
    if not filtered_mstrOil.empty:
        settlePrice = filtered_mstrOil['Settlement Price'].values[0]
    else:
        # Find the closest previous date's settlement price
        previous_dates = mstrOil[(mstrOil['CurrentDate'] < date) & (mstrOil['CloseDate'] == contract_date)]
        if not previous_dates.empty:
            closest_date = previous_dates['CurrentDate'].max()
            closest_record = previous_dates[previous_dates['CurrentDate'] == closest_date]
            settlePrice = closest_record['Settlement Price'].values[0]
        else:
            settlePrice = None  # Handle the case where no previous date is found

    return settlePrice

@app.route('/check_pending', methods=['POST'])
def check_pending():
    data = request.json
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Set row factory to sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE status = 'Pending'")

    current_date = pd.to_datetime(data['date']).date()
    next_date = pd.to_datetime(data['next_date']).date()


    pending_data = cursor.fetchall()
    

    for transaction in pending_data:

        transaction_date = pd.to_datetime(transaction['trans_date']).date()
        contract_date = pd.to_datetime(transaction['contract_date']).date()


        if transaction_date <= current_date and contract_date >= next_date:
            
            current_settle = fetch_settlePrice(current_date, transaction['contract_date'])
            next_settle = fetch_settlePrice(next_date, transaction['contract_date'])


            if (transaction['limit_price'] >= current_settle and transaction['limit_price'] <= next_settle) or (transaction['limit_price'] <= current_settle and transaction['limit_price'] >= next_settle):
                update_query = "UPDATE transactions SET status = 'Purchased', purchase_date = ?, purchase_price = ? WHERE Trans_ID = ?"
                
                cursor.execute(update_query, (next_date, next_settle, transaction['Trans_ID']))
                conn.commit()
              
    conn.close()
    return jsonify("Pending transactions checked")


@app.route('/buyContract', methods=['POST'])
def buy_contract():
    print("buyContract")
    try:
        data = request.json
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        mstrOil = fetch_oil()

        
        data['contractDate'] = pd.to_datetime(data['contractDate']).date()
        data['transactionDate'] = pd.to_datetime(data['transactionDate']).date()
        
        mstrOil['CurrentDate'] = pd.to_datetime(mstrOil['CurrentDate'], format='%Y-%m-%d').dt.date
        mstrOil['CloseDate'] = pd.to_datetime(mstrOil['CloseDate'], format='%Y-%m-%d').dt.date

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
    
    

def convert_to_standard_types(data):
    if isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, dict):
        return {k: convert_to_standard_types(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_standard_types(i) for i in data]
    else:
        return data
    

def calculate_margin_contract(qty, risk, maitenaince):
    pass

def calculate_margin_spread():
    pass


@app.route('/boughtData', methods=['POST'])
def bought_data():
    selected_date = request.json['date']
    data = fetch_bought()
    mstrOil = fetch_oil()
    
    # Convert date columns to datetime
    data['contract_date'] = pd.to_datetime(data['contract_date']).dt.date
    data['purchase_date'] = pd.to_datetime(data['purchase_date']).dt.date.astype(str)
    data['trans_date'] = pd.to_datetime(data['trans_date']).dt.date
    selected_current_date = pd.to_datetime(selected_date).date()


    mstrOil['CurrentDate'] = pd.to_datetime(mstrOil['CurrentDate']).dt.date
    mstrOil['CloseDate'] = pd.to_datetime(mstrOil['CloseDate']).dt.date

    for index, row in data.iterrows():
        
        row['contract_date'] = pd.to_datetime(row['contract_date']).date()

        filtered_mstrOil = mstrOil[(mstrOil['CurrentDate'] == selected_current_date)  & (mstrOil['CloseDate'] == row['contract_date'])]
        
        if not filtered_mstrOil.empty:
            data.at[index, 'settle_price'] = filtered_mstrOil['Settlement Price'].values[0]
        else:
            # Find the closest previous date's settlement price
            previous_dates = mstrOil[(mstrOil['CurrentDate'] <= selected_current_date) & (mstrOil['CloseDate'] == row['contract_date'])]
            if not previous_dates.empty:
                closest_date = previous_dates['CurrentDate'].max()
                closest_record = previous_dates[previous_dates['CurrentDate'] == closest_date]
                data.at[index, 'settle_price'] = closest_record['Settlement Price'].values[0]
            else:
                data.at[index, 'settle_price'] = 0

    
    
    data['change'] = (data['settle_price'] - data['purchase_price']).round(2)
    data['percent_change'] = (data['change'] / data['settle_price'] * 100).round(2)

    # Replace NaN values with 0
    data['change'] = data['change'].fillna(0)
    data['percent_change'] = data['percent_change'].fillna(0)
    data['purchase_date'] = data['purchase_date'].fillna('').astype(str)
    data['purchase_price'] = data['purchase_price'].fillna('')

    # Filter data
    filtered_data = data[(data['trans_date'] <= selected_current_date) & (data['contract_date'] >= selected_current_date)]
    filtered_data['contract_date'] = filtered_data['contract_date'].astype(str)

    # Group spreads
    spread_data = []
    grouped = filtered_data.groupby(['type', 'contract_date'])

    # Create a dictionary to hold buy and sell groups by contract date
    buy_groups = {}
    sell_groups = {}

    for (type_, contract_date), group in grouped:
        if type_ == 'buy':
            buy_groups[contract_date] = group
        elif type_ == 'sell':
            sell_groups[contract_date] = group

    for buy_contract_date, buy_group in buy_groups.items():
        buy_date = datetime.strptime(buy_contract_date, '%Y-%m-%d')
        for sell_contract_date, sell_group in sell_groups.items():
            sell_date = datetime.strptime(sell_contract_date, '%Y-%m-%d')
            print("buy ", buy_date, "sell ", sell_date)

            # Check if the months are exactly one month apart
            if (buy_date.year == sell_date.year and buy_date.month == sell_date.month + 1) or \
            (buy_date.year == sell_date.year + 1 and buy_date.month == 1 and sell_date.month == 12) or \
            (sell_date.year == buy_date.year and sell_date.month == buy_date.month + 1) or \
            (sell_date.year == buy_date.year + 1 and sell_date.month == 1 and buy_date.month == 12):
                
                # Match contracts in pairs
                min_length = min(len(buy_group), len(sell_group))
                for i in range(min_length):
                    buy_row = buy_group.iloc[i]
                    sell_row = sell_group.iloc[i]
                    spread = {
                        'contract_date': f"{buy_row['contract_date']}/{sell_row['contract_date']}",
                        'settle_price': round(buy_row['settle_price'] - sell_row['settle_price'], 2),
                        'type': 'spread',
                        'limit_price': buy_row['limit_price'],
                        'purchase_date': buy_row['purchase_date'],
                        'status': buy_row['status'],
                        'change': round((buy_row['settle_price'] - sell_row['settle_price']) - buy_row['limit_price'], 2),
                        'percent_change': round((buy_row['settle_price'] - sell_row['settle_price'] - buy_row['limit_price']) / buy_row['limit_price'] * 100, 2),
                        'qty': 1  # Each spread represents one pair
                    }
                    spread_data.append(spread)

                # Handle remaining buy contracts
                remaining_buy_quantity = len(buy_group) - min_length
                if remaining_buy_quantity > 0:
                    lone_contract = {
                        'contract_date': buy_group.iloc[min_length]['contract_date'],
                        'settle_price': buy_group.iloc[min_length]['settle_price'],
                        'type': 'lone_buy',
                        'limit_price': buy_group.iloc[min_length]['limit_price'],
                        'purchase_date': buy_group.iloc[min_length]['purchase_date'],
                        'status': buy_group.iloc[min_length]['status'],
                        'change': buy_group.iloc[min_length]['change'],
                        'percent_change': buy_group.iloc[min_length]['percent_change'],
                        'qty': remaining_buy_quantity  # Quantity of remaining buy contracts
                    }
                    spread_data.append(lone_contract)

                # Handle remaining sell contracts
                remaining_sell_quantity = len(sell_group) - min_length
                if remaining_sell_quantity > 0:
                    lone_contract = {
                        'contract_date': sell_group.iloc[min_length]['contract_date'],
                        'settle_price': sell_group.iloc[min_length]['settle_price'],
                        'type': 'lone_sell',
                        'limit_price': sell_group.iloc[min_length]['limit_price'],
                        'purchase_date': sell_group.iloc[min_length]['purchase_date'],
                        'status': sell_group.iloc[min_length]['status'],
                        'change': sell_group.iloc[min_length]['change'],
                        'percent_change': sell_group.iloc[min_length]['percent_change'],
                        'qty': remaining_sell_quantity  # Quantity of remaining sell contracts
                    }
                    spread_data.append(lone_contract)


    # Prepare response
    response_data = filtered_data[['contract_date', 'settle_price', 'type', 'limit_price', 'purchase_date', 'status', 'change', 'percent_change', 'qty', 'purchase_price']].to_dict(orient='records')
    response_data.extend(spread_data)
    
    # Convert to standard types
    response_data = convert_to_standard_types(response_data)
    return jsonify(response_data)



def run_server():
    serve(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    app.run()
    #FlaskUI(app=app, server="flask").run()

