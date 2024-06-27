import pyodbc
import pandas as pd
from flask import Flask, render_template, request, jsonify
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QDateEdit, QTreeView, QHBoxLayout, QToolButton, QPushButton
from PyQt6.QtCore import QDate, Qt, QEvent
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QSizePolicy
import sys

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

def color_cells(val):
    if val < 0:
        color = 'red'
    elif val > 0:
        color = 'green'
    else:
        color = 'white'
    return 'background-color: %s' % color

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Contract Settlement Prices Dashboard")
        self.setGeometry(100, 100, 1400, 800)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        

        # Define the path to your Access database
        database_path = r"C:\Users\TPI-P330\OneDrive\Documents\Oil\test.accdb"
        self.connection = connect_to_access(database_path)
        self.data = fetch_data(self.connection)

        # Convert date columns to datetime
        self.data['CurrentDate'] = pd.to_datetime(self.data['CurrentDate']).dt.date

        # Create a list of unique dates for the dropdown
        self.data['CloseDate'] = pd.to_datetime(self.data['CloseDate']).dt.date

        # Get the first and last current date from the data
        min_current_date = self.data['CurrentDate'].min()
        max_current_date = self.data['CurrentDate'].max()

        
        self.layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.treeView = QTreeView()
        self.treeView.setFixedWidth(800)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Contract Month', 'Settlement Price', 'Change', 'Percent (%)', 'Spread'])
        self.treeView.setModel(self.model)
        

        self.layout.addStretch(1)
        self.layout.addWidget(self.treeView)
        self.layout.addStretch(1)

        self.setLayout(self.layout)

        self.label = QLabel("Select a current date:")
        self.layout.addWidget(self.label)


        self.layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        dateEditLayout = QHBoxLayout()
        dateEditLayout.addStretch()
        
        self.dateEdit = CustomDateEdit()
        self.dateEdit.setDate(max_current_date)
        self.dateEdit.setFixedWidth(300)
        self.dateEdit.setDateRange(min_current_date, max_current_date)  
        self.dateEdit.dateChanged.connect(self.update_table)
        dateEditLayout.addWidget(self.dateEdit)

        dateEditLayout.addStretch()
        self.layout.addLayout(dateEditLayout)


        self.prevButton = QPushButton("<")
        self.nextButton = QPushButton(">")

        self.prevButton.clicked.connect(self.select_prev_day)
        self.nextButton.clicked.connect(self.select_next_day)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.prevButton)
        buttonsLayout.addWidget(self.nextButton)

        dateEditLayout.addLayout(buttonsLayout)

        
        self.update_table()
        self.treeView.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Ensure tree view expands to fill the window
        self.show()  # Show the window before adjusting columns to ensure correct sizing
        self.adjust_tree_columns()

    def select_prev_day(self):
        current_date = self.dateEdit.date()
        self.dateEdit.setDate(current_date.addDays(-1))

    def select_next_day(self):
        current_date = self.dateEdit.date()
        self.dateEdit.setDate(current_date.addDays(1))

    def adjust_tree_columns(self):
        total_columns = self.treeView.model().columnCount()
        tree_view_width = self.treeView.viewport().width()  # Use viewport width to account for scrollbar
        if self.treeView.verticalScrollBar().isVisible():  # Check if the vertical scrollbar is visible
            tree_view_width -= self.treeView.verticalScrollBar().width()  # Subtract scrollbar width
        if total_columns > 0:
            column_width = tree_view_width // total_columns
            for column in range(total_columns):
                self.treeView.setColumnWidth(column, column_width)

    def tree_clicked(self, index):
        print(self.model.itemFromIndex(index).text())

    def update_table(self):
        self.treeView.setModel(self.model)
        selected_current_date = self.dateEdit.date().toPyDate()

        # Filter data where CurrentDate is on or before the selected date and CloseDate is on or after the selected date
        filtered_data = self.data[(self.data['CurrentDate'] <= selected_current_date) & (self.data['CloseDate'] >= selected_current_date)]

        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Contract Month', 'Settlement Price', 'Change', 'Percent (%)', 'Spread'])

        if filtered_data.empty:
            self.tree.insert("", "end", values=["No contracts found for the selected date"])
            return

        # Sort the data
        filtered_data = filtered_data.sort_values(['CloseDate', 'CurrentDate'], ascending=[True, False])

        # Initialize 'Change' column
        filtered_data['Change'] = 0

        # Find the last settlement price before the selected date for each CloseDate
        last_prices_before_selected_date = filtered_data[filtered_data['CurrentDate'] < selected_current_date] \
            .groupby('CloseDate')['Settlement Price'].first().reset_index()


        # Merge this information back to the original dataframe
        filtered_data = filtered_data.merge(last_prices_before_selected_date, on='CloseDate', how='left', suffixes=('', '_LastBeforeSelected'))

        # Calculate 'Change' for the selected date
        filtered_data.loc[filtered_data['CurrentDate'] == selected_current_date, 'Change'] = \
            (filtered_data['Settlement Price'] - filtered_data['Settlement Price_LastBeforeSelected']).round(2)
        
        filtered_data['percent_change'] = (filtered_data['Change'] / filtered_data['Settlement Price'] * 100).round(2)

        # Remove duplicates to ensure unique CloseDate
        filtered_data = filtered_data.drop_duplicates(subset='CloseDate')

        # Sort final data by CloseDate in ascending order
        filtered_data = filtered_data.sort_values('CloseDate', ascending=True)

        filtered_data['Next Settlement Price'] = filtered_data['Settlement Price'].shift(1)
        filtered_data['Spread'] = filtered_data['Settlement Price'] - filtered_data['Next Settlement Price']
        filtered_data['Spread'] = filtered_data['Spread'].fillna(0).round(2)

        filtered_data.style.map(color_cells, subset=['Change'])
        
        # Insert filtered data into the model
        for _, row in filtered_data.iterrows():
            # Create QStandardItem for each cell
            close_date_item = QStandardItem(str(row['CloseDate']))
            settlement_price_item = QStandardItem(str(row['Settlement Price']))
            change_item = create_coloured_item(row['Change'])
            percent_item = create_coloured_item(row['percent_change'])
            spread_item = create_coloured_item(row['Spread'])

            # Add items to the model
            self.model.appendRow([close_date_item, settlement_price_item, change_item, percent_item, spread_item])
        
        self.adjust_tree_columns()

def create_coloured_item(value):
    item = QStandardItem(str(value))
    if value < 0:
        item.setBackground(Qt.GlobalColor.red)
    elif value > 0:
        item.setBackground(Qt.GlobalColor.green)
    return item
    


class CustomDateEdit(QDateEdit):
    
    def __init__(self, parent=None):
        super(CustomDateEdit, self).__init__(parent)
        self.setCalendarPopup(True)
        self.calendarWidget().installEventFilter(self)
        self.year_buttons = []

    def eventFilter(self, obj, event):
        if obj == self.calendarWidget():
            if event.type() == QEvent.Type.Show or event.type() == QEvent.Type.Resize or event.type() == QEvent.Type.Paint:
                self.customizeCalendarButtons()
        elif event.type() == QEvent.Type.KeyPress:
            key_event = QKeyEvent(event)
            if key_event.key() == Qt.Key.Key_Left:
                self.setDate(self.date().addDays(-1))
                return True
            elif key_event.key() == Qt.Key.Key_Right:
                self.setDate(self.date().addDays(1))
                return True
        return super(CustomDateEdit, self).eventFilter(obj, event)
    
    def customizeCalendarButtons(self):
        calendarWidget = self.calendarWidget()
        toolButtons = calendarWidget.findChildren(QToolButton)
        spinButtons = calendarWidget.findChildren(QToolButton, "qt_calendar_spinbox")

        for btns in spinButtons:
            btns.setMinimumSize(80, 30)
        for btn in toolButtons:
            if not btn.text().isnumeric() and btn.text() != "" :  # Month buttons contain spaces
                btn.setFont(QFont("default", 16))  # Larger font for month buttons
                btn.setFixedSize(120, 30)  # Larger size for month selection buttons
            elif btn.text().isnumeric():  # Year buttons are numeric
                btn.setFont(QFont("default", 14))  # Slightly smaller font for year buttons
                btn.setFixedSize(80, 30)  # Different size for year selection buttons
               

            else:  # Arrow buttons
                btn.setFixedSize(20, 20)  # Smaller size for arrow buttons

    def keepButtonSize(self, btn):
        btn.setFixedSize(80, 30)  # Reapply the fixed size when the button is pressed

if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open('style.qss', "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

