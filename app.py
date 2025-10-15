import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
conn = sqlite3.connect("habit_mood.db")
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    habit TEXT,
    mood TEXT
)
''')
conn.commit()

# --- FUNCTIONS ---
def add_entry():
    date = date_entry.get()
    habit = habit_entry.get()
    mood = mood_combobox.get()
    
    if not date or not habit or not mood:
        messagebox.showwarning("Input Error", "Please fill all fields.")
        return
    
    c.execute("INSERT INTO tracker (date, habit, mood) VALUES (?, ?, ?)", (date, habit, mood))
    conn.commit()
    messagebox.showinfo("Success", "Entry added successfully!")
    load_entries()
    clear_fields()

def load_entries():
    for row in tree.get_children():
        tree.delete(row)
    
    c.execute("SELECT * FROM tracker ORDER BY date DESC")
    for row in c.fetchall():
        tree.insert("", tk.END, values=row)

def clear_fields():
    date_entry.delete(0, tk.END)
    date_entry.insert(0, datetime.today().strftime('%Y-%m-%d'))
    habit_entry.delete(0, tk.END)
    mood_combobox.set("Neutral")  
def delete_entry():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select an entry to delete.")
        return
    for item in selected:
        entry_id = tree.item(item)['values'][0]
        c.execute("DELETE FROM tracker WHERE id=?", (entry_id,))
        conn.commit()
        tree.delete(item)
    
    messagebox.showinfo("Deleted", "Selected entry deleted successfully!")
root = tk.Tk()
root.title("Habit & Mood Tracker")
root.geometry("600x450")
frame = tk.Frame(root)
frame.pack(pady=10)
tk.Label(frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5)
date_entry = tk.Entry(frame)
date_entry.grid(row=0, column=1, padx=5, pady=5)
date_entry.insert(0, datetime.today().strftime('%Y-%m-%d'))
tk.Label(frame, text="Habit:").grid(row=1, column=0, padx=5, pady=5)
habit_entry = tk.Entry(frame)
habit_entry.grid(row=1, column=1, padx=5, pady=5)
tk.Label(frame, text="Mood:").grid(row=2, column=0, padx=5, pady=5)
mood_combobox = ttk.Combobox(frame, values=["Happy", "Sad", "Neutral", "Excited", "Angry"])
mood_combobox.grid(row=2, column=1, padx=5, pady=5)
mood_combobox.set("Neutral") 
tk.Button(frame, text="Add Entry", command=add_entry).grid(row=3, column=0, columnspan=2, pady=5)
tk.Button(frame, text="Delete Selected", command=delete_entry).grid(row=4, column=0, columnspan=2, pady=5)
columns = ("ID", "Date", "Habit", "Mood")
tree = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
tree.pack(pady=20, fill=tk.BOTH, expand=True)
load_entries()
root.mainloop()