'''Updates ig 09/05
I think I fixed the budget/balance thing. It should be working perfectly fine after removing the dummy data
Figured out a way to translate the ui but wont do it rn. If anyone wants to work on it here is a link
https://stackoverflow.com/questions/77905757/how-to-change-the-language-of-the-whole-interface-by-command-from-the-user'''

import sys
import cv2
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QFont, QPainter, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QHeaderView, QHBoxLayout, QTabWidget, QGroupBox, QLabel,
                               QLineEdit, QMainWindow, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget, QDialog, QFormLayout, QMessageBox, QDialogButtonBox, QMenu, QFileDialog)
from PySide6.QtCharts import QChartView, QPieSeries, QChart

import receiptReader

# Asks for monthly income and user name
class UserInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Information")
        self.setWindowModality(Qt.ApplicationModal)

        self.name_label = QLabel("Name:")
        self.budget_label = QLabel("Monthly Budget:")
        self.name_edit = QLineEdit()
        self.budget_edit = QLineEdit()

        layout = QFormLayout()
        layout.addRow(self.name_label, self.name_edit)
        layout.addRow(self.budget_label, self.budget_edit)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.check_user_info)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

        self.ok_button.setEnabled(False)

        self.name_edit.textChanged.connect(self.check_input_fields)
        self.budget_edit.textChanged.connect(self.check_input_fields)
    
    def check_input_fields(self):
        name = self.name_edit.text().strip()
        budget_text = self.budget_edit.text().strip()
        self.ok_button.setEnabled(bool(name) and bool(budget_text))

    def check_user_info(self):
        name = self.name_edit.text().strip()
        if not name.isalpha():
            self.show_error_message("Invalid Input", "Please enter a valid name containing only letters.")
            return None, None

        budget_text = self.budget_edit.text().strip()
        if not budget_text:
            budget = 0
        else:
            try:
                budget = float(budget_text)
                if budget <= 0:
                    self.show_error_message("Invalid Input", "Negative monthly budget?")
                    return None, None
            except ValueError:
                self.show_error_message("Invalid Input", "Please enter a valid number for the monthly budget.")
                return None, None

        self.accept()
        return name, budget

    def show_error_message(self, title, message):
        error_message = QMessageBox(self)
        error_message.setIcon(QMessageBox.Critical)
        error_message.setWindowTitle(title)
        error_message.setText(message)
        error_message.setStandardButtons(QMessageBox.Ok)
        error_message.exec()

# On settings to change budget(like monthly income)
class BudgetAdjustmentDialog(QDialog):
    def __init__(self, budget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adjust Monthly Budget")

        self.budget = budget

        self.balance_label = QLabel(f"Current Monthly Budget: ${self.budget:.2f}")
        self.new_balance_label = QLabel("New Monthly Budget:")
        self.new_balance_edit = QLineEdit()

        layout = QVBoxLayout()
        layout.addWidget(self.balance_label)
        layout.addWidget(self.new_balance_label)
        layout.addWidget(self.new_balance_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_new_balance(self):
        new_balance_text = self.new_balance_edit.text()
        if not new_balance_text:
            return None
        try:
            new_balance = float(new_balance_text)
            return new_balance
        except ValueError:
            return None

# On main page changes Balance
class BalanceAdjustmentDialog(QDialog):
    def __init__(self, balance, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adjust Balance")

        self.balance = balance

        self.current_balance_label = QLabel(f"Current Balance: ${self.balance:.2f}")
        self.new_balance_label = QLabel("New Balance:")
        self.new_balance_edit = QLineEdit()

        layout = QVBoxLayout()
        layout.addWidget(self.current_balance_label)
        layout.addWidget(self.new_balance_label)
        layout.addWidget(self.new_balance_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_new_balance(self):
        new_balance_text = self.new_balance_edit.text()
        if not new_balance_text:
            return None
        try:
            new_balance = float(new_balance_text)
            return new_balance
        except ValueError:
            return None

# Main page window Left side
class Widget(QWidget):
    balance_updated = Signal(float)

    def __init__(self, budget = 0, parent=None):
        super().__init__(parent)
        self.items = 0
        self._data = {"Water": 24, "Rent": 1000, "Coffee": 30, "Grocery": 300, "Phone": 45, "Internet": 70}
        self.balance = budget
		
        # Emit initial balance
        self.balance_updated.emit(self.balance)
  
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Description", "Price"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        self.description = QLineEdit()
        self.price = QLineEdit()
        self.add = QPushButton("Log Expense")
        self.add_balance = QPushButton("Adjust Balance")
        self.clear = QPushButton("Clear")
        self.undo = QPushButton("Undo")
        self.plot = QPushButton("Update The Pie Chart")

        self.add.setEnabled(False)

        self.right = QVBoxLayout()
        self.right.addWidget(QLabel("Description"))
        self.right.addWidget(self.description)
        self.right.addWidget(QLabel("Price"))
        self.right.addWidget(self.price)
        self.right.addWidget(self.add_balance)
        self.right.addWidget(self.add)
        self.right.addWidget(self.plot)
        self.right.addWidget(self.chart_view)
        self.right.addWidget(self.clear)
        self.right.addWidget(self.undo)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.table)
        self.layout.addLayout(self.right)
        self.setLayout(self.layout)

        self.add.clicked.connect(self.add_element)
        self.add_balance.clicked.connect(self.add_balance_clicked)
        self.plot.clicked.connect(self.plot_data)
        self.clear.clicked.connect(self.clear_table)
        self.undo.clicked.connect(self.undo_clear)
        self.description.textChanged[str].connect(self.check_disable)
        self.price.textChanged[str].connect(self.check_disable)

        self.fill_table()

        self.prev_state = []
    
    @Slot()
    def add_element(self):
        des = self.description.text()
        price = self.price.text()

        try:
            price_value = float(price)
            if price_value < 0:
                price_value = abs(price_value)
        except ValueError:
            self.show_error_message("Invalid Input", "Please enter a valid number for the price.")
            return

        if price_value > self.balance:
            self.show_error_message("Insufficient Balance", "Your balance is not in the mood right now!")
            return

        price_item = QTableWidgetItem(f"{price_value:.2f}")
        price_item.setTextAlignment(Qt.AlignRight)

        self.table.insertRow(self.items)
        description_item = QTableWidgetItem(des)

        self.table.setItem(self.items, 0, description_item)
        self.table.setItem(self.items, 1, price_item)

        self.balance -= price_value
        self.balance_updated.emit(self.balance)

        self.description.setText("")
        self.price.setText("")

        self.items += 1

    @Slot()
    def add_balance_clicked(self):
        dialog = BalanceAdjustmentDialog(self.balance)
        if dialog.exec() == QDialog.Accepted:
            new_balance = dialog.get_new_balance()
            if new_balance is not None:
                self.balance = new_balance
                self.balance_updated.emit(self.balance)

    @Slot()
    def check_disable(self, x):
        if not self.description.text() or not self.price.text():
            self.add.setEnabled(False)
        else:
            self.add.setEnabled(True)

    @Slot()
    def plot_data(self):
        series = QPieSeries()
        category_expenses = {}

        total_expenses = 0
        for i in range(self.table.rowCount()):
            category = self.table.item(i, 0).text().lower()
            expense = float(self.table.item(i, 1).text())
            if category in category_expenses:
                category_expenses[category] += expense
            else:
                category_expenses[category] = expense
            total_expenses += expense

        for category, expense in category_expenses.items():
            percentage = (expense / total_expenses) * 100 if total_expenses != 0 else 0
            series.append(f"{category.capitalize()} ({percentage:.2f}%)", expense)
        chart = QChart()
        chart.addSeries(series)
        chart.legend().setAlignment(Qt.AlignLeft)
        self.chart_view.setChart(chart)

    @Slot()
    def clear_table(self):

        self.prev_state.clear()
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item_text = self.table.item(row, col).text()
                row_data.append(item_text)
            self.prev_state.extend(row_data)

        self.table.clear()
        self.table.setRowCount(0)
        self.items = 0
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Description", "Price"])

    @Slot()
    def undo_clear(self):
        # Restore previous table state
        row_count = len(self.prev_state) // self.table.columnCount()
        self.table.setRowCount(row_count)
        for row in range(row_count):
            for col in range(self.table.columnCount()):
                item_text = self.prev_state[row * self.table.columnCount() + col]
                if item_text:
                    self.table.setItem(row, col, QTableWidgetItem(item_text))

    def fill_table(self, data=None):
        data = self._data if not data else data
        for desc, price in data.items():
            description_item = QTableWidgetItem(desc)
            price_item = QTableWidgetItem(f"{price:.2f}")
            price_item.setTextAlignment(Qt.AlignRight)
            self.table.insertRow(self.items)
            self.table.setItem(self.items, 0, description_item)
            self.table.setItem(self.items, 1, price_item)
            self.items += 1

    def show_error_message(self, title, message):
        error_message = QMessageBox(self)
        error_message.setIcon(QMessageBox.Critical)
        error_message.setWindowTitle(title)
        error_message.setText(message)
        error_message.setStandardButtons(QMessageBox.Ok)
        error_message.exec()
    
    def add_from_reader(self, category, max_amount, balance):
        des = category
        price = max_amount
           
        try:
            price_value = float(price)
            if price_value < 0:
                price_value = abs(price_value)
        except ValueError:
            self.show_error_message("Invalid Input", "Please enter a valid number for the price.")
            return

        if price_value > balance:
            self.show_error_message("Insufficient Balance", "Your balance is not in the mood right now!")
            return

        price_item = QTableWidgetItem(f"{price_value:.2f}")
        price_item.setTextAlignment(Qt.AlignRight)

        self.table.insertRow(self.items)
        description_item = QTableWidgetItem(des)

        self.table.setItem(self.items, 0, description_item)
        self.table.setItem(self.items, 1, price_item)

        balance -= price_value
        self.balance_updated.emit(balance)

        self.description.setText("")
        self.price.setText("")

        self.items += 1

# Settings
class Settings(QWidget):
        # Inside the Settings class __init__ method
    def __init__(self):
        QWidget.__init__(self)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        self.group_box = QGroupBox("Settings")
        self.group_box_layout = QVBoxLayout()

        # Add image to Receipt reader
        self.change_language_button = QPushButton("Change Language 💬")
        self.adjust_budget_button = QPushButton("Adjust Monthly Budget 💲")
        self.enter_name_button = QPushButton("Change Username 🤵")

         # Create QLabel to display the uploaded image
        self.image_label = QLabel()
        self.image_label.setScaledContents(True)
        
        # Connect the slot to the button
        self.change_language_button.clicked.connect(self.show_language_menu)
        
        self.group_box_layout.addWidget(self.change_language_button)
        self.group_box_layout.addWidget(self.adjust_budget_button)
        self.group_box_layout.addWidget(self.enter_name_button)

        self.group_box.setLayout(self.group_box_layout)

        self.layout.addWidget(self.group_box)
        self.setLayout(self.layout)

    # New method to show the language menu
    def show_language_menu(self):
        # Create a QMenu instance
        language_menu = QMenu()

        # Add actions to the menu for each language
        english_action = language_menu.addAction("English")
        greek_action = language_menu.addAction("Greek")

        # Get the global position of the button
        button_pos = self.change_language_button.mapToGlobal(self.change_language_button.rect().bottomLeft())

        # Show the menu at the calculated position
        chosen_action = language_menu.exec_(button_pos)
        
        # Handle the selected action
        if chosen_action == english_action:
            # Implement action for English
            print("English selected")
        elif chosen_action == greek_action:
            # Implement action for Greek
            print("Greek selected")

# Futs
class Reader(QWidget):
    def __init__(self, widget, parent=None):
        QWidget.__init__(self, parent)
        self.widget = widget
        self.initUI()
        self.max_amount = None
        self.category = None

    def initUI(self):
        layout = QVBoxLayout()

        # Layout for the "Add Image" button
        self.add_image_button = QPushButton("Add Image of Receipt 📷")
        self.add_image_button.clicked.connect(self.upload_image)
        layout.addWidget(self.add_image_button)

        # Bottom layout for the uploaded image and text
        bottom_layout = QHBoxLayout()

        # Left layout for the uploaded image
        left_layout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setScaledContents(True)
        left_layout.addWidget(self.image_label)
        bottom_layout.addLayout(left_layout)

        # Right layout for the text
        right_layout = QVBoxLayout()
        self.text_label = QLabel()
        self.text_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.text_label)
        bottom_layout.addLayout(right_layout)
        
        # Add a sub-layout for the buttons
        self.button_layout = QHBoxLayout()
        right_layout.addLayout(self.button_layout)
        bottom_layout.addLayout(right_layout)

        # Add bottom layout to the main layout
        layout.addLayout(bottom_layout)

        self.setLayout(layout)
        
    @Slot()
    def upload_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg)")
        file_dialog.setViewMode(QFileDialog.List)
        if file_dialog.exec_():
            filenames = file_dialog.selectedFiles()
            if filenames:
                image_path = filenames[0]
                pixmap = QPixmap(image_path)
                self.image_label.setPixmap(pixmap)
                
                # Process the image using receiptReader modile
                image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                self.max_amount = receiptReader.process_image(image)                
                if self.max_amount is not None:
                    self.text_label.setText(f"Your Total expenses : {self.max_amount:.2f}\nIs this the correct amount?")
                    
                    # Add "Yes" and "No" buttons
                    yes_button = QPushButton("Yes")
                    no_button = QPushButton("No")

                    # Connect button clicks to signals
                    yes_button.clicked.connect(lambda: self.on_button_clicked(1))
                    no_button.clicked.connect(lambda: self.on_button_clicked(0))

                    # Add buttons to button layout
                    self.button_layout.addWidget(yes_button)
                    self.button_layout.addWidget(no_button)
                else:
                    self.text_label.setText("No amount found")
                    
    def on_button_clicked(self, value):
        W = Widget()
        print("User clicked:", value)
        if value == 0:
            # Remove buttons from layout
            for i in reversed(range(self.button_layout.count())):
                widget = self.button_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            # Change text and add QLineEdit and QPushButton
            self.text_label.setText("What is the correct Total?")
            self.text_edit = QLineEdit()  # Create a QLineEdit for user input
            self.button_confirm = QPushButton("Confirm")  # Create a button for confirmation
            self.button_confirm.clicked.connect(self.on_confirm_clicked)  # Connect button click to slot
            self.button_layout.addWidget(self.text_edit)  # Add text_edit to button layout
            self.button_layout.addWidget(self.button_confirm)  # Add button_confirm to button layout
        elif value == 1:
            # Remove buttons from layout
            for i in reversed(range(self.button_layout.count())):
                widget = self.button_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            # Change text and add QLineEdit and QPushButton
            self.text_label.setText("What Category should it be added on?")
            self.text_edit = QLineEdit()  # Create a QLineEdit for user input
            self.button_confirm = QPushButton("Confirm")  # Create a button for confirmation
            self.button_confirm.clicked.connect(self.on_confirm_clicked)
            self.button_layout.addWidget(self.text_edit)
            self.button_layout.addWidget(self.button_confirm)
        elif value == 2:
            # Remove buttons from layout
            for i in reversed(range(self.button_layout.count())):
                widget = self.button_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            # Check if both category and max_amount are set
            if self.category is not None and self.max_amount is not None:
                self.text_label.setText(f"Category: {self.category}, Price: {self.max_amount:.2f}\n")
                balance = W.balance
                print(balance)
                W.add_from_reader(self.category, self.max_amount, balance)
            else:
                self.text_label.setText("Category and/or Price not set.")
                    
            
    
    def on_confirm_clicked(self):
        # Handle confirm button click
        if self.text_label.text() == "What is the correct Total?":
            user_input = self.text_edit.text()  # Get user input
            if self.validate_input(user_input):
                # Remove buttons from layout
                for i in reversed(range(self.button_layout.count())):
                    widget = self.button_layout.itemAt(i).widget()
                    if widget:
                        widget.deleteLater()
                        
                # If input is valid, save it
                self.text_label.setText(f"Is {user_input} your correct expenses?")  # Update text label
                self.max_amount = float(user_input)  # Store user input
                
                # Add "Yes" and "No" buttons
                yes_button = QPushButton("Yes")
                no_button = QPushButton("No")

                # Connect button clicks to signals
                yes_button.clicked.connect(lambda: self.on_button_clicked(1))
                no_button.clicked.connect(lambda: self.on_button_clicked(0))

                # Add buttons to button layout
                self.button_layout.addWidget(yes_button)
                self.button_layout.addWidget(no_button)
            else:
                # If input is invalid, show error message
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid integer or float.")
        elif self.text_label.text() == "What Category should it be added on?":
            category_input = self.text_edit.text()  # Get category input
            if category_input:  # Check if category input is not empty
                # Remove buttons from layout
                for i in reversed(range(self.button_layout.count())):
                    widget = self.button_layout.itemAt(i).widget()
                    if widget:
                        widget.deleteLater()
                        
                # If category input is not empty, proceed
                self.text_label.setText(f"Is {category_input} the correct Category?")  # Update text label
                self.category = category_input
                
                # Add "Yes" and "No" buttons
                yes_button = QPushButton("Yes")
                no_button = QPushButton("No")

                # Connect button clicks to signals
                yes_button.clicked.connect(lambda: self.on_button_clicked(2))
                no_button.clicked.connect(lambda: self.on_button_clicked(1))

                # Add buttons to button layout
                self.button_layout.addWidget(yes_button)
                self.button_layout.addWidget(no_button)
            else:
                # If category input is empty, show error message
                QMessageBox.warning(self, "Invalid Input", "Please enter a category.")
            
    def validate_input(self, input_text):
        try:
            input_text = int(input_text)
            input_text = float(input_text)
            # Check if the float can be converted back to the original input (to ensure it's valid)
            return True
        except ValueError:
            return False
# Futs

class MainWindow(QMainWindow):
    def __init__(self, widget, name, budget):
        QMainWindow.__init__(self)
        self.setWindowTitle("Financial Tracker")

        self.budget = budget
        self.balance = budget
		# self.balance = budget - total_items_price
        
        self.balance_label = QLabel(f"💰 Current Balance: {self.budget:.2f}€ ")
        self.balance_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        font = QFont("Arial", 12)
        self.balance_label.setFont(font)

        self.budget_label = QLabel(f"💼 Monthly Budget: {self.budget:.2f}€ ")
        self.budget_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.budget_label.setFont(font)

        self.statusBar().addWidget(self.balance_label)
        self.statusBar().addPermanentWidget(self.budget_label)

        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu(f"Hello, {name}!😊")

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.tab_widget.addTab(widget, "Home 🏠")
        self.settings_widget = Settings()
        self.tab_widget.addTab(self.settings_widget, "Settings ⚙️")
        self.reader_widget = Reader(widget)
        self.tab_widget.addTab(self.reader_widget, "Reader 📖")

        self.settings_widget.adjust_budget_button.clicked.connect(self.adjust_budget)

        widget.balance_updated.connect(self.update_balance)

    def get_balance(self):
        return self.balance
    @Slot(float)
    def update_balance(self, new_balance):
        self.balance_label.setText(f"💰 Current Balance: {new_balance:.2f}€ ")

    @Slot()
    def adjust_budget(self):
        dialog = BudgetAdjustmentDialog(self.budget)
        if dialog.exec() == QDialog.Accepted:
            new_budget = dialog.get_new_balance()
            if new_budget is not None:
                self.budget = new_budget
                self.budget_label.setText(f"💼 Monthly Budget: ${self.budget:.2f} ")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    name, budget = None, None
    while name is None or budget is None:
        dialog = UserInfoDialog()
        if dialog.exec() == QDialog.Accepted:
            name, budget = dialog.check_user_info()
        else:
            sys.exit()

    widget = Widget(budget)
    window = MainWindow(widget, name, budget)
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())