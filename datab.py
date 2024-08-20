import sqlite3

def create_tables():
    conn = sqlite3.connect('oil_data.sqlite')
    c = conn.cursor()
    
    c.execute('''DROP TABLE IF EXISTS spreadTransactions''')
    c.execute('''CREATE TABLE IF NOT EXISTS SavedGames (Trans_id INTEGER PRIMARY KEY, trans_date TEXT, contract_date TEXT, qty INTEGER, limit_price REAL, status TEXT, purchase_date TEXT, type TEXT, purchase_price REAL, trans_price REAL, close_qty INTEGER, close_limit REAL, game INTEGER)''')
    #c.execute('''ALTER TABLE wallet ADD COLUMN excess INTEGER;''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()