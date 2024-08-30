import sqlite3
import csv

def create_tables():
    conn = sqlite3.connect('oil_data.sqlite')
    c = conn.cursor()
    
    c.execute('''DROP TABLE IF EXISTS mstrOil''')
    #c.execute('''CREATE TABLE mstrOil (CurrentDate TEXT, CloseDate TEXT, 'Settlement Price' REAL)''')
    
    conn.commit()
    conn.close()
    
    #c.execute('''CREATE TABLE IF NOT EXISTS SavedGames (Trans_id INTEGER PRIMARY KEY, trans_date TEXT, contract_date TEXT, qty INTEGER, limit_price REAL, status TEXT, purchase_date TEXT, type TEXT, purchase_price REAL, trans_price REAL, close_qty INTEGER, close_limit REAL, game INTEGER)''')
    #c.execute('''ALTER TABLE wallet ADD COLUMN excess INTEGER;''')
    
def insert_data(csv_file):

    conn = sqlite3.connect('oil_data.sqlite')
    c = conn.cursor()
    
    with open(csv_file, 'r') as f:
        dr = csv.DictReader(f)
        for row in dr:
            c.execute('''INSERT INTO mstrOil (CurrentDate, CloseDate, 'Settlement Price') VALUES (?, ?, ?)''',
                        (row['CurrentDate'], row['CloseDate'], row['Settlement Price']))
    
    conn.commit()
    conn.close()


if __name__ == '__main__':
    #create_tables()
    #insert_data('merged_sorted_final.csv')
    conn = sqlite3.connect('oil_data.sqlite')
    c = conn.cursor()

    c.execute('DELETE FROM games')
    c.execute('''DELETE FROM sqlite_sequence WHERE name = 'games';''')

   
    
    conn.commit()
    conn.close()