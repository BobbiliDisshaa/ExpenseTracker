import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")

        # Connect to SQLite database
        self.conn = sqlite3.connect("expense_tracker.db")
        self.cursor = self.conn.cursor()

        # Create tables if not exist
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS roommates (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                roommate_id INTEGER,
                amount REAL,
                FOREIGN KEY (roommate_id) REFERENCES roommates(id)
            )
        """)
        self.conn.commit()

        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        self.setup_roommates_tab()
        self.setup_expenses_tab()

    def setup_roommates_tab(self):
        expenses_tab = ttk.Frame(self.notebook)
        self.notebook.add(expenses_tab, text='Roommates')

        self.label_roommate = tk.Label(expenses_tab, text="Roommate:")
        self.label_roommate.grid(row=0, column=0, padx=10, pady=10)

        self.entry_roommate = tk.Entry(expenses_tab)
        self.entry_roommate.grid(row=0, column=1, padx=10, pady=10)

        self.add_roommate_button = tk.Button(expenses_tab, text="Add Roommate", command=self.add_roommate)
        self.add_roommate_button.grid(row=0, column=2, padx=10, pady=10)

        self.setup_roommates_list(expenses_tab)

    def setup_expenses_tab(self):
        roommates_tab = ttk.Frame(self.notebook)
        self.notebook.add(roommates_tab, text='Expenses')

        self.setup_expenses_table(roommates_tab)

        self.label_amount = tk.Label(roommates_tab, text="Bill Amount:")
        self.label_amount.pack(side="left", padx=10, pady=10)

        self.entry_amount = tk.Entry(roommates_tab)
        self.entry_amount.pack(side="left", padx=10, pady=10)

        self.label_payer = tk.Label(roommates_tab, text="Payer:")
        self.label_payer.pack(side="left", padx=10, pady=10)

        self.payer_var = tk.StringVar(roommates_tab)
        self.payer_dropdown = ttk.Combobox(roommates_tab, textvariable=self.payer_var, state="readonly")
        self.payer_dropdown.pack(side="left", padx=10, pady=10)

        self.add_expense_button = tk.Button(roommates_tab, text="Add Expense", command=self.add_expense)
        self.add_expense_button.pack(side="left", padx=10, pady=10)
        self.update_expenses_table()

        # Update payer dropdown with roommate names
        self.update_payer_dropdown()

    def setup_roommates_list(self, expenses_tab):
        self.roommates_frame = tk.Frame(expenses_tab)
        self.roommates_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

        self.roommates_label = tk.Label(self.roommates_frame, text="Roommates:", font=("Helvetica", 14))
        self.roommates_label.pack()

        self.roommates_listbox = tk.Listbox(self.roommates_frame, width=30, height=10, font=("Helvetica", 12))
        self.roommates_listbox.pack()

        # Fetch roommates from database and populate listbox
        self.cursor.execute("SELECT name FROM roommates")
        roommates = self.cursor.fetchall()
        for roommate in roommates:
            self.roommates_listbox.insert(tk.END, roommate[0])

    def setup_expenses_table(self, roommates_tab):
        self.expenses_frame = ttk.Frame(roommates_tab)
        self.expenses_frame.pack(padx=10, pady=10)

        self.expenses_label = tk.Label(self.expenses_frame, text="Expenses:", font=("Helvetica", 14))
        self.expenses_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        self.expenses_table = ttk.Treeview(self.expenses_frame, columns=("Roommate", "Expense"), show="headings")
        self.expenses_table.heading("Roommate", text="Roommate")
        self.expenses_table.heading("Expense", text="Expense")
        self.expenses_table.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

    def add_roommate(self):
        roommate_name = self.entry_roommate.get().strip()
        if not roommate_name:
            messagebox.showwarning("Error", "Please enter a roommate name.")
            return

        try:
            self.cursor.execute("INSERT INTO roommates (name) VALUES (?)", (roommate_name,))
            self.conn.commit()
            self.roommates_listbox.insert(tk.END, roommate_name)
            self.update_payer_dropdown()
            messagebox.showinfo("Success", f"Roommate {roommate_name} added successfully.")
            self.entry_roommate.delete(0, tk.END)
        except sqlite3.IntegrityError:
            messagebox.showwarning("Error", "Roommate already added.")

    def add_expense(self):
        amount = self.entry_amount.get()
        payer = self.payer_var.get()

        if not amount or not payer:
            messagebox.showwarning("Error", "Please enter both bill amount and select payer.")
            return

        try:
            amount = float(amount)
        except ValueError:
            messagebox.showwarning("Error", "Invalid amount. Please enter a number.")
            return

        self.cursor.execute("SELECT id FROM roommates WHERE name=?", (payer,))
        payer_id = self.cursor.fetchone()[0]

        self.cursor.execute("INSERT INTO expenses (roommate_id, amount) VALUES (?, ?)", (payer_id, amount))
        self.conn.commit()

        self.update_expenses_table()
        messagebox.showinfo("Success", f"Expense of ₹{amount} paid by {payer} added successfully.")
        self.entry_amount.delete(0, tk.END)

    def update_expenses_table(self):
        self.expenses_table.delete(*self.expenses_table.get_children())

        self.cursor.execute("SELECT COUNT(id) FROM roommates")
        num_roommates = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT r.name, COALESCE(SUM(e.amount), 0)
            FROM roommates r
            LEFT JOIN expenses e ON r.id = e.roommate_id
            GROUP BY r.name
        """)
        expenses = self.cursor.fetchall()

        total_expense = sum(expense[1] for expense in expenses)

        for roommate, paid_amount in expenses:
            roommate_share = total_expense / num_roommates
            amount_owed = roommate_share - paid_amount
            self.expenses_table.insert("", "end", values=(roommate, f"₹{amount_owed:.2f}"))

    def update_payer_dropdown(self):
        self.cursor.execute("SELECT name FROM roommates")
        roommates = self.cursor.fetchall()
        self.payer_dropdown["values"] = [roommate[0] for roommate in roommates]

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()
