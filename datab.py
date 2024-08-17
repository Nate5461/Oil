import sqlite3

def create_tables():
    conn = sqlite3.connect('oil_data.sqlite')
    c = conn.cursor()
    
    #c.execute('''CREATE TABLE IF NOT EXISTS spreadTransactions (transaction_id INTEGER PRIMARY KEY, transaction_date TEXT, qty INTEGER, frontMonth TEXT, backMonth TEXT, type TEXT, limit_price REAL, status TEXT, purchase_date TEXT)''')
    #c.execute('''ALTER TABLE wallet ADD COLUMN excess INTEGER;''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()