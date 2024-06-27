import pyodbc
import csv

# Define the path to your Access database
database_path = r"C:\Users\TPI-P330\OneDrive\Documents\Oil\test.accdb"

# Establish connection to the Access database
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    r'DBQ=' + database_path + ';'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# List of table names to merge
table_names = ['Query2', 'Query3', 'Query4', 'Query5', 'Query6', 
               'Query7', 'Oil10-15']

# Open the output CSV file
with open('merged_table.csv', mode='w', newline='') as file:
    csv_writer = csv.writer(file)

    # Loop through each table
    for table in table_names:
        # Fetch data from the table
        cursor.execute(f'SELECT * FROM [{table}]')
        rows = cursor.fetchall()
        
        # Get column names from the first table only (header row)
        if cursor.description:
            headers = [column[0] for column in cursor.description]
            csv_writer.writerow(headers)
            break

    # Write rows from all tables
    for table in table_names:
        cursor.execute(f'SELECT * FROM [{table}]')
        rows = cursor.fetchall()
        for row in rows:
            csv_writer.writerow(row)

print("Tables have been successfully merged into 'merged_table.csv'")

# Close the database connection
conn.close()