import sqlite3

def create_tables():
    conn = sqlite3.connect('oil_data.sqlite')
    c = conn.cursor()
    
    c.execute('''''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()