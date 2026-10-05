import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime


class ExpenseTracker:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Personal Expense Tracker")
        self.window.geometry("700x550")
        self.window.configure(bg="#f0f2f5")

        # Database Setup
        # This creates a file called expenses.db in the same folder as the script
        self.conn = sqlite3.connect("expenses.db")
        self.create_table()

        # UI Styling
        self.style = ttk.Style()
        self.style.configure("Treeview", font=("Arial", 11), rowheight=25)
        self.style.configure("Treeview.Heading", font=("Arial", 12, "bold"))

        self.setup_ui()
        self.load_data()

    def create_table(self):
        """Creates the SQLite table if it doesn't already exist."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL,
                category TEXT,
                description TEXT,
                date TEXT
            )
        ''')
        self.conn.commit()

    def setup_ui(self):
        """Sets up the Graphical User Interface."""
        # --- Input Frame (The top section where you enter data) ---
        input_frame = tk.Frame(self.window, bg="#ffffff", padx=20, pady=20, relief="groove", borderwidth=2)
        input_frame.pack(pady=20, padx=20, fill="x")

        # Amount Field
        tk.Label(input_frame, text="Amount:", bg="#ffffff", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5,
                                                                                     sticky="e")
        self.amount_entry = ttk.Entry(input_frame)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        # Category Dropdown
        tk.Label(input_frame, text="Category:", bg="#ffffff", font=("Arial", 10)).grid(row=0, column=2, padx=5, pady=5,
                                                                                       sticky="e")
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(input_frame, textvariable=self.category_var, state="readonly")
        self.category_dropdown['values'] = ("Food", "Transport", "Rent", "Entertainment", "Health", "Shopping", "Other")
        self.category_dropdown.grid(row=0, column=3, padx=5, pady=5)
        self.category_dropdown.current(0)

        # Description Field
        tk.Label(input_frame, text="Description:", bg="#ffffff", font=("Arial", 10)).grid(row=1, column=0, padx=5,
                                                                                          pady=5,
                                                                                          sticky="e")
        self.desc_entry = ttk.Entry(input_frame, width=40)
        self.desc_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        # Add Button
        self.add_btn = tk.Button(input_frame, text="Add Expense", bg="#2ecc71", fg="white",
                                 font=("Arial", 10, "bold"), command=self.add_expense, width=15, cursor="hand2")
        self.add_btn.grid(row=1, column=4, padx=10, pady=5)

        # --- Table Frame (The middle section showing the list) ---
        table_frame = tk.Frame(self.window, bg="#f0f2f5")
        table_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Treeview Table
        columns = ("ID", "Amount", "Category", "Description", "Date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        # Define headings and column widths
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)

        # Vertical Scrollbar for the table
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # --- Bottom Frame (Totals and Actions) ---
        bottom_frame = tk.Frame(self.window, bg="#f0f2f5")
        bottom_frame.pack(pady=20, fill="x", padx=20)

        # Total Display
        self.total_label = tk.Label(bottom_frame, text="Total Spent: $0.00",
                                    font=("Arial", 16, "bold"), bg="#f0f2f5", fg="#c0392b")
        self.total_label.pack(side="left")

        # Delete Button
        self.del_btn = tk.Button(bottom_frame, text="Delete Selected", bg="#e74c3c", fg="white",
                                 font=("Arial", 10), command=self.delete_expense, cursor="hand2")
        self.del_btn.pack(side="right")

    def add_expense(self):
        """Handles adding a new expense to the database."""
        amount = self.amount_entry.get()
        category = self.category_var.get()
        desc = self.desc_entry.get()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        if not amount:
            messagebox.showwarning("Input Error", "Please enter an amount.")
            return

        try:
            # Convert amount to float to ensure it's a number
            amount_float = float(amount)
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
                           (amount_float, category, desc, date))
            self.conn.commit()

            # Clear the input fields for the next entry
            self.amount_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)

            self.load_data()  # Refresh the table
        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a valid number (e.g. 12.50).")

    def load_data(self):
        """Loads data from the database into the Treeview table."""
        # Clear the table first so we don't get duplicates
        for item in self.tree.get_children():
            self.tree.delete(item)

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
        rows = cursor.fetchall()

        total = 0
        for row in rows:
            self.tree.insert("", tk.END, values=row)
            total += row[1]  # Add the amount (index 1 in the row)

        self.total_label.config(text=f"Total Spent: ${total:.2f}")

    def delete_expense(self):
        """Handles deleting the selected item from the table and database."""
        # 1. Identify which row is selected
        selected_item = self.tree.selection()

        # 2. Check if a selection actually exists
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select an expense from the list first.")
            return

        try:
            # 3. Get the data from the selected row
            item_data = self.tree.item(selected_item)
            values = item_data.get('values', [])

            if not values:
                return

            expense_id = values[0]  # The ID is the first column

            # 4. Ask for confirmation before deleting
            if messagebox.askyesno("Confirm", "Are you sure you want to delete this expense?"):
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
                self.conn.commit()
                self.load_data()  # Refresh the table
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def run(self):
        """Starts the application loop."""
        self.window.mainloop()


if __name__ == "__main__":
    app = ExpenseTracker()
    app.run()