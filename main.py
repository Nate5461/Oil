import pandas as pd
import sqlite3
from flask import Flask, render_template, request, jsonify, make_response
from flask_caching import Cache
from flaskwebgui import FlaskUI
from waitress import serve
from threading import Thread
from datetime import datetime, timedelta
import os
import numpy as np

app = Flask(__name__)

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'oil_data.sqlite')
template_dir = os.path.join(script_dir, 'templates')

app.template_folder = template_dir

def no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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
def inject_margin():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT margin FROM wallet")
    margin = cursor.fetchone()[0]
    print("margin", margin)
    conn.close()
    return dict(margin=margin)


@app.route('/getWallet', methods=['GET'])
def get_wallet_number():
    wallet_info = inject_wallet_number()
    unrealized = inject_unrealized()
    margin = inject_margin()

    response = {
        'wallet_info': wallet_info,
        'unrealized_info': unrealized,
        'margin_info': margin
    }

    return no_cache(jsonify(response))

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
        cursor.execute("UPDATE wallet SET amount = 0.0, unrealized = 0.0, margin = 0.0")
        cursor.execute("DELETE FROM transactions")
        conn.commit()
        return jsonify({"message": "Restart successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data', methods=['POST'])
def get_data():
    try:
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
        safe_data = replace_nan(response_data)
        
        return jsonify(safe_data)
    
    except Exception as e:
        response_data = {"error": str(e)}
        print(response_data)
        return jsonify(response_data)
    
def replace_nan(obj):
        if isinstance(obj, float) and obj != obj:  # NaN check
            return None
        if isinstance(obj, dict):
            return {k: replace_nan(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [replace_nan(i) for i in obj]
        return obj

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

@app.route('/getSingleProfit', methods=['POST'])
def get_single_profit():
    data = request.json

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    current_date = pd.to_datetime(data['date']).date()
    contract_date = pd.to_datetime(data['contract_date']).date()
    cursor.execute("SELECT * FROM transactions WHERE status = 'Purchased' AND contract_date = ? AND ", (current_date, contract_date))
    pending_data = cursor.fetchall()

    df = pd.DataFrame(pending_data, columns=[col[0] for col in cursor.description])

    limit = data['limit_price']
    qty = data['qty']

    profit = limit - df['purchase_price'].values[0]


@app.route('/check_pending', methods=['POST'])
def check_pending():
    data = request.json
    current_date = pd.to_datetime(data['date']).date()
    next_date = pd.to_datetime(data['next_date']).date()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    next3days = next_date + timedelta(days=3)

    #fetch relevent data
    cursor.execute("SELECT * FROM transactions WHERE trans_date <= ? AND contract_date >= ?", (current_date, current_date))
    pending_data = cursor.fetchall()

    df = pd.DataFrame(pending_data, columns=[col[0] for col in cursor.description])
    

    grouped = df.groupby(['type', 'contract_date'])

    buy_groups = {}
    sell_groups = {}

    for (type_, contract_date), group in grouped:
        if type_ == 'buy':
            buy_groups[contract_date] = group
        elif type_ == 'sell':
            sell_groups[contract_date] = group

    processed_contract_dates = set()

    for buy_contract_date, buy_group in buy_groups.items():
        buy_date = datetime.strptime(buy_contract_date, '%Y-%m-%d')
        for sell_contract_date, sell_group in sell_groups.items():
            sell_date = datetime.strptime(sell_contract_date, '%Y-%m-%d')


            #BUY SPREAD
            if (buy_date.year == sell_date.year and buy_date.month == sell_date.month + 1) or \
               (buy_date.year == sell_date.year + 1 and buy_date.month == 1 and sell_date.month == 12):
               

                min_length = min(len(buy_group), len(sell_group))
                for i in range(min_length):
                    buy_row = buy_group.iloc[i]
                    sell_row = sell_group.iloc[i]

                    if buy_row['trans_date'] == sell_row['trans_date']:
                        
                        curr_buy_price = fetch_settlePrice(current_date, buy_row['contract_date'])
                        curr_sell_price = fetch_settlePrice(current_date, sell_row['contract_date'])
                        next_buy_price = fetch_settlePrice(next_date, buy_row['contract_date'])
                        next_sell_price = fetch_settlePrice(next_date, sell_row['contract_date'])
                        current_settle = round(curr_buy_price - curr_sell_price, 4)
                        next_settle = round(next_buy_price - next_sell_price, 4)

                        if buy_row['status'] == 'Pending' or sell_row['status'] == 'Pending':
                        
                            if (buy_row['limit_price'] >= current_settle and buy_row['limit_price'] <= next_settle) or (buy_row['limit_price'] <= current_settle and buy_row['limit_price'] >= next_settle):
                                update_query = "UPDATE transactions SET status = 'Purchased', purchase_date = ?, purchase_price = ? WHERE Trans_ID = ?"
                                try:
                                    
                                    cursor.execute(update_query, (next_date, float(next_sell_price + buy_row['limit_price']), int(buy_row['Trans_ID'])))
                                    cursor.execute(update_query, (next_date, float(next_sell_price), int(sell_row['Trans_ID'])))
                                    conn.commit()
                                except Exception as e:
                                    print("Error:", e)

                            processed_contract_dates.add(buy_row['Trans_ID'])
                            processed_contract_dates.add(sell_row['Trans_ID'])

                        elif buy_row['close_qty'] != None:
                            # Lookijng for close outs

                            print("buy_row['close_limit']", buy_row['close_limit'], "current_settle", current_settle, "next_settle", next_settle)
                            if (buy_row['close_limit'] >= current_settle and buy_row['close_limit'] <= next_settle) or (buy_row['close_limit'] <= current_settle and buy_row['close_limit'] >= next_settle):
                                print("I run1")
                                curs = cursor.execute("SELECT amount FROM wallet")
                                curr = float(curs.fetchone()[0])
                                newcurr = curr + (float(buy_row['close_limit']) - (float(buy_row['purchase_price']) - float(sell_row['purchase_price']))) * int(buy_row['close_qty']) * 1000
                                cursor.execute("UPDATE wallet SET amount = ?", (newcurr,))

                                
                                try:
                                    if int(buy_row['close_qty']) == int(buy_row['qty']):
                                       
                                        print("deleting, close_qty", buy_row['close_qty'], "available",  buy_row['qty'])
                                        cursor.execute("DELETE FROM transactions WHERE Trans_ID = ?", (int(buy_row['Trans_ID']),)) 
                                        cursor.execute("DELETE FROM transactions WHERE Trans_ID = ?", (int(sell_row['Trans_ID']),))
                                        
                                        conn.commit()
                                        conn.close()
                                    else:

                                        print("updating, close_qty", buy_row['close_qty'], "available",  buy_row['qty'])
                                        cursor.execute("UPDATE transactions SET qty = ?, close_limit = null, close_qty = null WHERE Trans_ID = ?", (int(buy_row['qty']) - int(buy_row['close_qty']), int(buy_row['Trans_ID'])))
                                        cursor.execute("UPDATE transactions SET qty = ?, close_limit = null, close_qty = null WHERE Trans_ID = ?", (int(sell_row['qty']) - int(buy_row['close_qty']), int(sell_row['Trans_ID'])))
                                        conn.commit()
                                        
                                        conn.close()
                                except Exception as e:
                                    print("Error:", e)
            #SELL SPREAD
            elif (sell_date.year == buy_date.year and sell_date.month == buy_date.month + 1) or \
                 (sell_date.year == buy_date.year + 1 and sell_date.month == 1 and buy_date.month == 12):
                
                min_length = min(len(buy_group), len(sell_group))
                for i in range(min_length):
                    buy_row = buy_group.iloc[i]
                    sell_row = sell_group.iloc[i]

                    
                    if buy_row['trans_date'] == sell_row['trans_date']:

                        
                        if buy_row['status'] == 'Pending' and sell_row['status'] == 'Pending':
                            curr_buy_price = fetch_settlePrice(current_date, buy_row['contract_date'])
                            curr_sell_price = fetch_settlePrice(current_date, sell_row['contract_date'])
                            next_buy_price = fetch_settlePrice(next_date, buy_row['contract_date'])
                            next_sell_price = fetch_settlePrice(next_date, sell_row['contract_date'])
                            current_settle = round(curr_sell_price - curr_buy_price, 4)
                            next_settle = round(next_sell_price - next_buy_price, 4)

                            
                            if (buy_row['limit_price'] >= current_settle and buy_row['limit_price'] <= next_settle) or (buy_row['limit_price'] <= current_settle and buy_row['limit_price'] >= next_settle):
                                update_query = "UPDATE transactions SET status = 'Purchased', purchase_date = ?, purchase_price = ? WHERE Trans_ID = ?"
                                try:
                                    
                                    cursor.execute(update_query, (next_date, float(next_buy_price), int(buy_row['Trans_ID'])))
                                    cursor.execute(update_query, (next_date, float(next_buy_price + buy_row['limit_price']), int(sell_row['Trans_ID'])))
                                    conn.commit()
                                except Exception as e:
                                    print("Error:", e)

                            processed_contract_dates.add(buy_row['Trans_ID'])
                            processed_contract_dates.add(sell_row['Trans_ID'])
                    
                        elif buy_row['close_qty'] != None and sell_row['close_qty'] != None:
                            # Looking for close outs
                            if (buy_row['close_limit'] >= current_settle and buy_row['close_limit'] <= next_settle) or (buy_row['close_limit'] <= current_settle and buy_row['close_limit'] >= next_settle):
                                    
                                    curs = cursor.execute("SELECT amount FROM wallet")
                                    curr = float(curs.fetchone()[0])
                                    newcurr = curr + (float(buy_row['close_limit']) - (float(buy_row['purchase_price']) - float(sell_row['purchase_price']))) * int(buy_row['close_qty']) * 1000
                                    
                                    cursor.execute("UPDATE wallet SET amount = ?", (newcurr,))
                                    if buy_row['close_qty'] == buy_row['qty']:
                                        cursor.execute("DELETE FROM transactions WHERE Trans_ID = ?", (int(buy_row['Trans_ID']),)) 
                                        cursor.execute("DELETE FROM transactions WHERE Trans_ID = ?", (int(sell_row['Trans_ID']),))
                                    else:
                                        print("I run2", buy_row['qty'] - buy_row['close_qty'], buy_row['Trans_ID'])
                                        cursor.execute("UPDATE transactions SET qty = ?, close_limit = null, close_qty = null WHERE Trans_ID = ?", (int(buy_row['qty']) - int(buy_row['close_qty'])), int(buy_row['Trans_ID']))
                                        cursor.execute("UPDATE transactions SET qty = ?, close_limit = null, close_qty = null WHERE Trans_ID = ?", (int(sell_row['qty']) - int(buy_row['close_qty'])), int(sell_row['Trans_ID']))

                                    conn.commit()

                                    # Check if the transactions were actually deleted or updated
                                    cursor.execute("SELECT * FROM transactions WHERE Trans_ID = ?", (buy_row['Trans_ID'],))
                                    buy_row_check = cursor.fetchone()
                                    print(f"After operation, buy_row with Trans_ID {buy_row['Trans_ID']}: {buy_row_check}")

                                    cursor.execute("SELECT * FROM transactions WHERE Trans_ID = ?", (sell_row['Trans_ID'],))
                                    sell_row_check = cursor.fetchone()
                                    print(f"After operation, sell_row with Trans_ID {sell_row['Trans_ID']}: {sell_row_check}")


    #Buying

    print(processed_contract_dates)
    for contract_date, group in buy_groups.items():
        for _, row in group.iterrows():
            if row['Trans_ID'] not in processed_contract_dates:
                if row['status'] == 'Pending':
                    curr_price = fetch_settlePrice(current_date, row['contract_date'])
                    next_price = fetch_settlePrice(next_date, row['contract_date'])
                    if row['limit_price'] <= curr_price and row['limit_price'] >= next_price or row['limit_price'] >= curr_price and row['limit_price'] <= next_price:
                        update_query = "UPDATE transactions SET status = 'Purchased', purchase_date = ?, purchase_price = ? WHERE Trans_ID = ?"
                        cursor.execute(update_query, (next_date, row['limit_price'], row['Trans_ID']))
                        conn.commit()
                elif row['close_qty'] != None:
                    # Look for close outs

                    
                    curr_price = float(fetch_settlePrice(current_date, row['contract_date']))
                    next_price = float(fetch_settlePrice(next_date, row['contract_date']))
                    print("curr_price", curr_price, "next_price", next_price)
                    print("row['close_limit']", row['close_limit'], "row['purchase_price']", row['purchase_price'], "row['close_qty']", row['close_qty'])

                    if row['close_limit'] <= curr_price and row['close_limit'] >= next_price or row['close_limit'] >= curr_price and row['close_limit'] <= next_price:
                        
                        print('ran the buy section')
                        curs = cursor.execute("SELECT amount FROM wallet")
                        curr = float(curs.fetchone()[0])
                        newcurr = curr + (float(row['close_limit']) - float(row['purchase_price'])) * int(row['close_qty']) * 1000
                        cursor.execute("UPDATE wallet SET amount = ?", (newcurr,))
                        if row['close_qty'] == row['qty']:
                            cursor.execute("DELETE FROM transactions WHERE Trans_ID = ?", (int(row['Trans_ID']),))
                        else:
                            cursor.execute("UPDATE transactions SET qty = ?, close_limit = null, close_qty = null WHERE Trans_ID = ?", (int(row['qty']) - int(row['close_qty']), int(row['Trans_ID'])))
                        conn.commit()

    #Selling                      
    for contract_date, group in sell_groups.items():
        for _, row in group.iterrows():
            if row['Trans_ID'] not in processed_contract_dates:

                if row['status'] == 'Pending':
                    curr_price = fetch_settlePrice(current_date, row['contract_date'])
                    next_price = fetch_settlePrice(next_date, row['contract_date'])
                    if row['limit_price'] <= curr_price and row['limit_price'] >= next_price or row['limit_price'] >= curr_price and row['limit_price'] <= next_price:
                        update_query = "UPDATE transactions SET status = 'Purchased', purchase_date = ?, purchase_price = ? WHERE Trans_ID = ?"
                        cursor.execute(update_query, (next_date, row['limit_price'], row['Trans_ID']))
                        conn.commit()
                elif row['close_qty'] != None:
                    # Look for close outs
                    print('Ran hereeee')
                    curr_price = fetch_settlePrice(current_date, row['contract_date'])
                    next_price = fetch_settlePrice(next_date, row['contract_date'])
                    if row['close_limit'] <= curr_price and row['close_limit'] >= next_price or row['close_limit'] >= curr_price and row['close_limit'] <= next_price:
                        
                        print('got hereeee')
                        curs = cursor.execute("SELECT amount FROM wallet")
                        curr = float(curs.fetchone()[0])
                        newcurr = curr - (float(row['close_limit']) - float(row['purchase_price'])) * int(row['close_qty']) * 1000

                        cursor.execute("UPDATE wallet SET amount = ?", (newcurr,))
                        if row['close_qty'] == row['qty']:
                            cursor.execute("DELETE FROM transactions WHERE Trans_ID = ?", (int(row['Trans_ID']),))
                        else:
                            cursor.execute("UPDATE transactions SET qty = ?, close_limit = null, close_qty = null WHERE Trans_ID = ?", (int(row['qty']) - int(row['close_qty']), int(row['Trans_ID'])))
                        conn.commit()
    conn.close()
    return jsonify("Pending transactions checked")


spreadMargin = 0
contractMargin = 0

@app.route("/giveConfig", methods = ['POST'])
def getSpreadMargin():
    global spreadMargin, contractMargin
    data = request.get_json()
    spreadMargin = data['spreadMargin']
    contractMargin = data['contractMargin']

    return jsonify({'status': 'success'})

@app.route('/getWalletValues', methods=['POST'])
def update_wallet():
    #print("update_wallet_values please")
    data = request.json
    print(data)
    print(data['date'])
    current_date = pd.to_datetime(data['date']).date()
    
    # Open database connection once
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch wallet and transactions in one go
    cursor.execute("SELECT * FROM wallet")
    wallet = cursor.fetchall()
    
    cursor.execute("SELECT * FROM transactions WHERE status = 'Purchased' AND purchase_date <= ? AND contract_date >= ?", (current_date, current_date))
    transactions = cursor.fetchall()

    print("transactions", transactions)
    if not transactions:
        cursor.execute("UPDATE wallet SET unrealized = 0.0, margin = 0.0")
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    
    
    # Fetch oil data
    oil_data = fetch_oil()
    oil_data['CurrentDate'] = pd.to_datetime(oil_data['CurrentDate'], format='%Y-%m-%d').dt.date
    oil_data['CloseDate'] = pd.to_datetime(oil_data['CloseDate'], format='%Y-%m-%d').dt.date
    
    # Margin update
    margin = 0
    buy_groups = {}
    sell_groups = {}
    
    for transaction in transactions:
        type_ = transaction[7]
        contract_date = transaction[2]
        
        if type_ == 'buy':
            buy_groups.setdefault(contract_date, []).append(transaction)
        elif type_ == 'sell':
            sell_groups.setdefault(contract_date, []).append(transaction)
    
    processed_contract_dates = set()
    
    for buy_contract_date, buy_group in buy_groups.items():
        buy_date = datetime.strptime(buy_contract_date, '%Y-%m-%d')
        for sell_contract_date, sell_group in sell_groups.items():
            sell_date = datetime.strptime(sell_contract_date, '%Y-%m-%d')
            
            if (buy_date.year == sell_date.year and buy_date.month == sell_date.month + 1) or \
               (buy_date.year == sell_date.year + 1 and buy_date.month == 1 and sell_date.month == 12) or \
               (sell_date.year == buy_date.year and sell_date.month == buy_date.month + 1) or \
               (sell_date.year == buy_date.year + 1 and sell_date.month == 1 and buy_date.month == 12):
                
                min_length = min(len(buy_group), len(sell_group))
                for i in range(min_length):
                    buy_row = buy_group[i]
                    sell_row = sell_group[i]
                    
                    if buy_row[1] == sell_row[1]:
                        margin += spreadMargin * buy_row[3]
                        processed_contract_dates.update([buy_row[0], sell_row[0]])
    
    for group in buy_groups.values():
        for row in group:
            if row[0] not in processed_contract_dates:
                margin += contractMargin * row[3]
    
    for group in sell_groups.values():
        for row in group:
            if row[0] not in processed_contract_dates:
                margin += contractMargin * row[3]
    
    cursor.execute("UPDATE wallet SET margin = ?", (margin,))
    conn.commit()
    
    temp = 0

    for transaction in transactions:
        contract_date = pd.to_datetime(transaction[2]).date()
        
        filtered_data = oil_data[oil_data['CloseDate'] == contract_date]
        
        filtered_data = filtered_data[filtered_data['CurrentDate'] == current_date]

        #Get the closest date if the current date is not found
        if filtered_data.empty:
            filtered_data = oil_data[(oil_data['CurrentDate'] <= current_date) & (oil_data['CloseDate'] == contract_date)]
            if not filtered_data.empty:
                closest_date = filtered_data['CurrentDate'].max()
                filtered_data = filtered_data[filtered_data['CurrentDate'] == closest_date]
        
        
        if not filtered_data.empty:
            settle_price = filtered_data['Settlement Price'].values[0]

            if transaction[7] == 'buy':
                
                temp += (settle_price - transaction[8]) * transaction[3] * 1000
            else:
                
                temp -= (settle_price - transaction[8]) * transaction[3] * 1000
    
    
    cursor.execute("UPDATE wallet SET unrealized = ?", (temp,))
    conn.commit()
    
    wallet_amount = wallet[0][0]
    wallet_margin = wallet[0][1]
    
    if wallet_amount <= abs(temp - wallet_margin):
        cost = round(wallet_amount + (temp - wallet_margin), 2)
        return jsonify({'message': 'margin call', 'margin_info': cost}), 200
    
    conn.close()
    return jsonify({'message': 'success'})

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
        if data['immediate']:
            purchase_date = data['transactionDate']
            status = 'Purchased'
            purchase_price = data['trans_price']
        else:
            purchase_date = None
            status = 'Pending'
            purchase_price = None


        cursor.execute("INSERT INTO transactions (trans_date, contract_date, qty, limit_price, status, purchase_date, type, purchase_price, trans_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                       (data['transactionDate'], data['contractDate'], data['qty'], data['limitPrice'], status, purchase_date, data['type'], purchase_price, data['trans_price']))
        conn.commit()  
        conn.close()

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
    

@app.route('/boughtData', methods=['POST'])
def bought_data():
    selected_date = request.json['date']
    data = fetch_bought()
    mstrOil = fetch_oil()
    
    if data.empty:
        return jsonify([])
    
    # Convert date columns to datetime
    data['contract_date'] = pd.to_datetime(data['contract_date']).dt.date
    data['purchase_date'] = pd.to_datetime(data['purchase_date']).dt.date.astype(str)
    data['trans_date'] = pd.to_datetime(data['trans_date']).dt.date
    selected_current_date = pd.to_datetime(selected_date).date()

    mstrOil['CurrentDate'] = pd.to_datetime(mstrOil['CurrentDate']).dt.date
    mstrOil['CloseDate'] = pd.to_datetime(mstrOil['CloseDate']).dt.date

    # Getting settle prices
    for index, row in data.iterrows():
        row['contract_date'] = pd.to_datetime(row['contract_date']).date()
        filtered_mstrOil = mstrOil[(mstrOil['CurrentDate'] == selected_current_date) & (mstrOil['CloseDate'] == row['contract_date'])]
        
        if not filtered_mstrOil.empty:
            data.at[index, 'settle_price'] = filtered_mstrOil['Settlement Price'].values[0]
        else:
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

    # Set to keep track of processed contract dates
    processed_contract_dates = set()

    for buy_contract_date, buy_group in buy_groups.items():
        buy_date = datetime.strptime(buy_contract_date, '%Y-%m-%d')
        for sell_contract_date, sell_group in sell_groups.items():
            sell_date = datetime.strptime(sell_contract_date, '%Y-%m-%d')

            # Check if the months are exactly one month apart

            # buying the close month selling the next month (less common) SELL SPREAD
            if (buy_date.year == sell_date.year and buy_date.month == sell_date.month + 1) or \
            (buy_date.year == sell_date.year + 1 and buy_date.month == 1 and sell_date.month == 12):
              
                # Match contracts in pairs
                min_length = min(len(buy_group), len(sell_group))
                for i in range(min_length):
                    buy_row = buy_group.iloc[i]
                    sell_row = sell_group.iloc[i]
                    
                    # Check if trans_dates are equal
                    if buy_row['trans_date'] == sell_row['trans_date']:
                        # Convert purchase_price to float, handle empty strings
                        buy_purchase_price = float(buy_row['purchase_price']) if buy_row['purchase_price'] else 0
                        sell_purchase_price = float(sell_row['purchase_price']) if sell_row['purchase_price'] else 0

                        if buy_purchase_price == 0 or sell_purchase_price == 0:
                            change = 0
                            percent_change = 0
                            purchase_price = ''
                        else:
                            purchase_price = round(buy_purchase_price - sell_purchase_price, 2)
                            change = round((buy_row['settle_price'] - sell_row['settle_price']) - (buy_purchase_price - sell_purchase_price), 2)
                            percent_change = round(((buy_row['settle_price'] - sell_row['settle_price']) - (buy_purchase_price - sell_purchase_price)) / ((buy_purchase_price - sell_purchase_price)) * 100, 2)

                        spread = {
                            'contract_date': f"{sell_row['contract_date']}/{buy_row['contract_date']}",
                            'settle_price': round(buy_row['settle_price'] - sell_row['settle_price'], 2),
                            'type': 'buy',
                            'limit_price': buy_row['limit_price'],
                            'purchase_date': buy_row['purchase_date'],
                            'status': buy_row['status'],
                            'purchase_price': purchase_price,
                            'change': change,
                            'percent_change': percent_change,
                            'qty': buy_row['qty'],
                            'Trans_ID': f"{buy_row['Trans_ID']}, {sell_row['Trans_ID']}"
                        }
                        spread_data.append(spread)
                        # Mark these contract dates as processed
                        processed_contract_dates.add(buy_row['Trans_ID'])
                        processed_contract_dates.add(sell_row['Trans_ID'])

            #buying the next month selling the close month
            elif (sell_date.year == buy_date.year and sell_date.month == buy_date.month + 1) or \
            (sell_date.year == buy_date.year + 1 and sell_date.month == 1 and buy_date.month == 12):
                
                # Match contracts in pairs
                min_length = min(len(buy_group), len(sell_group))
                for i in range(min_length):
                    buy_row = buy_group.iloc[i]
                    sell_row = sell_group.iloc[i]
                    
                    # Check if trans_dates are equal
                    if buy_row['trans_date'] == sell_row['trans_date']:
                        # Convert purchase_price to float, handle empty strings
                        buy_purchase_price = float(buy_row['purchase_price']) if buy_row['purchase_price'] else 0
                        sell_purchase_price = float(sell_row['purchase_price']) if sell_row['purchase_price'] else 0

                        if buy_purchase_price == 0 or sell_purchase_price == 0:
                            change = 0
                            percent_change = 0
                            purchase_price = ''
                        else:
                            purchase_price = round(sell_purchase_price - buy_purchase_price, 2)
                            change = round((buy_purchase_price - sell_purchase_price) - (buy_row['settle_price'] - sell_row['settle_price']), 2)
                            percent_change = round(((buy_purchase_price - sell_purchase_price) - (buy_row['settle_price'] - sell_row['settle_price'])) / (buy_row['settle_price'] - sell_row['settle_price']) * 100, 2)

                        spread = {
                            'contract_date': f"{buy_row['contract_date']}/{sell_row['contract_date']}",
                            'settle_price': round(sell_row['settle_price'] - buy_row['settle_price'], 2),
                            'type': 'sell',
                            'limit_price': buy_row['limit_price'],
                            'purchase_date': buy_row['purchase_date'],
                            'status': buy_row['status'],
                            'purchase_price': purchase_price,
                            'change': change,
                            'percent_change': percent_change,
                            'qty': buy_row['qty'],
                            'Trans_ID': f"{buy_row['Trans_ID']}, {sell_row['Trans_ID']}"
                        }
                        spread_data.append(spread)
                        # Mark these contract dates as processed
                        processed_contract_dates.add(buy_row['Trans_ID'])
                        processed_contract_dates.add(sell_row['Trans_ID'])


    # Handle remaining lone contracts
    lone_data = []
    print(processed_contract_dates)

    # Buying
    for contract_date, group in buy_groups.items():
        for _, row in group.iterrows():
            if row['Trans_ID'] not in processed_contract_dates:
                # Convert purchase_price to float, handle empty strings
                purchase_price = float(row['purchase_price']) if row['purchase_price'] else 0
                
                if purchase_price == 0:
                    buy_change = 0
                    buy_percent = 0
                else:
                    buy_change = round(row['settle_price'] - purchase_price, 2)
                    buy_percent = round((row['settle_price'] - purchase_price) / purchase_price * 100, 2)
                
                lone_contract = {
                    'contract_date': row['contract_date'],
                    'settle_price': row['settle_price'],
                    'type': 'buy',
                    'limit_price': row['limit_price'],
                    'purchase_date': row['purchase_date'],
                    'status': row['status'],
                    'purchase_price': row['purchase_price'],
                    'change': buy_change,
                    'percent_change': buy_percent,
                    'qty': row['qty'],
                    'Trans_ID': row['Trans_ID']
                }
                lone_data.append(lone_contract)

    # Selling
    for contract_date, group in sell_groups.items():
        for _, row in group.iterrows():
            if row['Trans_ID'] not in processed_contract_dates:
                # Convert purchase_price to float, handle empty strings
                purchase_price = float(row['purchase_price']) if row['purchase_price'] else 0

                if purchase_price == 0:
                    sell_change = 0
                    sell_percent = 0
                else:
                    sell_change = round(purchase_price - row['settle_price'], 2)
                    sell_percent = round((purchase_price - row['settle_price']) / purchase_price * 100, 2)
                

                lone_contract = {
                    'contract_date': row['contract_date'],
                    'settle_price': row['settle_price'],
                    'type': 'sell',
                    'limit_price': row['limit_price'],
                    'purchase_date': row['purchase_date'],
                    'status': row['status'],
                    'purchase_price': row['purchase_price'],
                    'change': sell_change,
                    'percent_change': sell_percent,
                    'qty': row['qty'],
                    'Trans_ID': row['Trans_ID']
                }
                lone_data.append(lone_contract)

    # Prepare response
    response_data = spread_data + lone_data

    status_order = {'Purchased': 0, 'Pending': 1}

    # Convert to standard types
    response_data = convert_to_standard_types(response_data)

    # Sort by status, contract_date, and purchase_date (handling NaT)
    response_data = sorted(response_data, key=lambda x: (
        status_order[x['status']],
        x['contract_date'],
        x['purchase_date'] if x['purchase_date'] is not pd.NaT else pd.Timestamp.max
    ))

    return no_cache(jsonify(response_data))

@app.route('/cancelTransaction', methods=['POST'])
def cancel_transaction():
    data = request.json
    id = data['transID']
    

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if id.find(',') != -1:
        ids = id.split(',')
        id1 = ids[0]
        id2 = ids[1]
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM transactions WHERE Trans_ID = ?", (id1,))
        cursor.execute("DELETE FROM transactions WHERE Trans_ID = ?", (id2,))
        conn.commit()
        conn.close()
    else:
        cursor.execute("DELETE FROM transactions WHERE Trans_ID = ?", (id,))
        conn.commit()
        conn.close()

    return jsonify({"message": "Transaction cancelled"}), 200

@app.route('/closeContract', methods=['POST'])     
def close_contract():
    print("closeContract")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    data = request.json
    id1 = int(data['transID1'])
    id2 = data['transID2']
    qty = int(data['qty'])
    limitQty = int(data['limitQty'])

    print(data)
    if limitQty == qty:

        if id2 == 'none':
            cursor.execute("Delete FROM transactions where Trans_ID = ?", (id1,))
            cursor.execute("Select amount FROM wallet")
            wallet = cursor.fetchone()[0]
            wallet += float(data['profit'])
            cursor.execute("UPDATE wallet SET amount = ?", (wallet,))
            conn.commit()
            conn.close()
        else:
            id2 = int(id2)
            cursor.execute("Delete from transactions where Trans_ID = ?", (id1,))
            cursor.execute("Delete from transactions where Trans_ID = ?", (id2,))
            cursor.execute("Select amount FROM wallet")
            wallet = cursor.fetchone()[0]
            wallet += float(data['profit'])
            cursor.execute("UPDATE wallet SET amount = ?", (wallet,))
            conn.commit()
            conn.close()
        return jsonify({"message": "Contract closed"}), 200
    
    elif limitQty < qty:

        if id2 == 'none':
            print("this should be running")
            cursor.execute("Select amount FROM wallet")
            wallet = cursor.fetchone()[0]
            wallet += float(data['profit'])
            cursor.execute("UPDATE wallet SET amount = ?", (wallet,))
            cursor.execute("UPDATE transactions SET qty = ? WHERE Trans_ID = ?", (qty - limitQty, id1))
            conn.commit()
            conn.close()
        else:
            cursor.execute("Select amount FROM wallet")
            wallet = cursor.fetchone()[0]
            wallet += float(data['profit'])
            cursor.execute("UPDATE wallet SET amount = ?", (wallet,))
            cursor.execute("UPDATE transactions SET qty = ? WHERE Trans_ID = ?", (qty - limitQty, id1))
            cursor.execute("UPDATE transactions SET qty = ? WHERE Trans_ID = ?", (qty - limitQty, id2))   
            conn.commit()
        return jsonify({"message": "Contract closed"}), 200
    else:
        return jsonify({"message": "Error: Quantity too large or not entered"}), 500
    
    
                       
@app.route('/limitClose', methods=['POST'])
def limit_close():
    data = request.json
    id1 = data['transID1']
    id2 = data['transID2']
    
    
    if id2 == 'none':
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE transactions SET close_qty = ?, close_limit = ? WHERE Trans_ID = ?", (int(data['limitQty']), float(data['limitPrice']), int(id1)))
        print("UPDATE transactions SET close_qty = ?, close_limit = ? WHERE Trans_ID = ?", (int(data['limitQty']), float(data['limitPrice']), int(id1)))
        conn.commit()
        conn.close()   
    else:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE transactions SET close_qty = ?, close_limit = ? WHERE Trans_ID = ?", (int(data['limitQty']), float(data['limitPrice']), int(id1)))
        cursor.execute("UPDATE transactions SET close_qty = ?, close_limit = ? WHERE Trans_ID = ?", (int(data['limitQty']), float(data['limitPrice']), int(id2)))
        conn.commit()
        conn.close()
    return jsonify({"message": "Limit close set"}), 200


def run_server():
    serve(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    #app.run()
    FlaskUI(app=app, server="flask").run()

