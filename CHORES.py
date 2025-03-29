import tkinter as tk
from tkinter import messagebox
import sqlite3

# Database setup
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT,
        price REAL
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS balance (
        id INTEGER PRIMARY KEY,
        amount REAL
    )
""")
conn.commit()

# Check if balance exists, otherwise set default
cursor.execute("SELECT amount FROM balance WHERE id = 1")
result = cursor.fetchone()
initial_balance = result[0] if result else 1000  # Default 1000 if not set

if not result:
    cursor.execute("INSERT INTO balance (id, amount) VALUES (1, ?)", (initial_balance,))
    conn.commit()


def update_balance():
    """Update balance on UI and database"""
    cursor.execute("SELECT SUM(price) FROM purchases")
    total_spent = cursor.fetchone()[0] or 0
    remaining_balance = initial_balance - total_spent
    balance_label.config(text=f"Remaining Balance: {remaining_balance:.2f} VND")

    cursor.execute("UPDATE balance SET amount = ? WHERE id = 1", (remaining_balance,))
    conn.commit()


def add_purchase():
    """Add new purchase to database"""
    item = item_entry.get()
    try:
        price = float(price_entry.get())
    except ValueError:
        messagebox.showerror("Input Error", "Price must be a number")
        return

    if item and price > 0:
        cursor.execute("INSERT INTO purchases (item, price) VALUES (?, ?)", (item, price))
        conn.commit()
        item_entry.delete(0, tk.END)
        price_entry.delete(0, tk.END)
        update_list()
        update_balance()
    else:
        messagebox.showerror("Input Error", "Enter valid item and price!")


def update_list():
    """Update purchase history"""
    listbox.delete(0, tk.END)
    cursor.execute("SELECT item, price FROM purchases")
    for row in cursor.fetchall():
        listbox.insert(tk.END, f"{row[0]} - {row[1]:.2f} VND")


# UI setup
root = tk.Tk()
root.title("Daily Expense Tracker")

# Initial Balance Label
balance_label = tk.Label(root, text=f"Remaining Balance: {initial_balance:.2f} VND", font=("Arial", 12, "bold"))
balance_label.pack(pady=5)

# Input Fields
frame = tk.Frame(root)
frame.pack(pady=5)

tk.Label(frame, text="Item:").grid(row=0, column=0)
item_entry = tk.Entry(frame)
item_entry.grid(row=0, column=1)

tk.Label(frame, text="Price (VND):").grid(row=1, column=0)
price_entry = tk.Entry(frame)
price_entry.grid(row=1, column=1)

# Buttons
add_button = tk.Button(root, text="Add Purchase", command=add_purchase)
add_button.pack(pady=5)

# Purchase List
listbox = tk.Listbox(root, width=40)
listbox.pack(pady=5)

update_list()
update_balance()

root.mainloop()
