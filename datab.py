import sqlite3

def create_tables():
    conn = sqlite3.connect('oil_data.sqlite')
    c = conn.cursor()
    
    c.execute('''INSERT INTO Transactions (TransactionID, ContractDate, TransactionType, Price, PurchaseDate) VALUES (2, '2016-01-01', 'Buy', 94.69, '2015-07-09')''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()