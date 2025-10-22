import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime

# --- Database Setup ---
conn = sqlite3.connect("habit_mood.db")
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS habits (
    habit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    habit_name TEXT,
    start_date TEXT,
    frequency INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS habit_tracker (
    tracker_id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER,
    date TEXT,
    status INTEGER,
    FOREIGN KEY(habit_id) REFERENCES habits(habit_id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS mood (
    mood_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    mood TEXT,
    notes TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
''')
conn.commit()

current_user = None

# --- User Authentication ---
def register_user():
    global current_user
    username = reg_username.get().strip()
    password = reg_password.get().strip()
    if not username or not password:
        messagebox.showwarning("Input Error", "Please fill all fields!")
        return
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        c.execute("SELECT user_id FROM users WHERE username=?", (username,))
        current_user = c.fetchone()[0]
        messagebox.showinfo("Success", f"Registration successful! Welcome {username}!")
        reg_username.delete(0, tk.END)
        reg_password.delete(0, tk.END)
        login_frame.pack_forget()
        main_frame.pack(fill=tk.BOTH, expand=True)
        load_habits()
        load_moods()
        update_dashboard()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists!")

def login_user():
    global current_user
    username = login_username.get().strip()
    password = login_password.get().strip()
    c.execute("SELECT user_id FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    if result:
        current_user = result[0]
        messagebox.showinfo("Success", f"Welcome {username}!")
        login_frame.pack_forget()
        main_frame.pack(fill=tk.BOTH, expand=True)
        load_habits()
        load_moods()
        update_dashboard()
    else:
        messagebox.showerror("Error", "Invalid username or password!")

def logout_user():
    global current_user
    current_user = None
    main_frame.pack_forget()
    login_frame.pack(pady=10)
    login_username.delete(0, tk.END)
    login_password.delete(0, tk.END)

# --- Habit Management ---
def add_habit():
    name = habit_name.get().strip()
    freq = habit_freq.get().strip()
    if not name or not freq.isdigit():
        messagebox.showwarning("Input Error", "Enter valid habit name and frequency!")
        return
    c.execute("INSERT INTO habits (user_id, habit_name, start_date, frequency) VALUES (?, ?, ?, ?)",
              (current_user, name, datetime.today().strftime('%Y-%m-%d'), int(freq)))
    conn.commit()
    habit_name.delete(0, tk.END)
    habit_freq.delete(0, tk.END)
    load_habits()
    update_dashboard()

def load_habits():
    for row in habit_tree.get_children():
        habit_tree.delete(row)
    c.execute("SELECT habit_id, habit_name, frequency FROM habits WHERE user_id=?", (current_user,))
    today = datetime.today().strftime('%Y-%m-%d')
    for habit_id, name, freq in c.fetchall():
        # Check status for today
        c.execute("SELECT status FROM habit_tracker WHERE habit_id=? AND date=?", (habit_id, today))
        status = c.fetchone()
        status_text = "Done" if status and status[0] == 1 else "Not Done"
        habit_tree.insert("", tk.END, values=(habit_id, name, freq, status_text))

def mark_done():
    selected = habit_tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Select a habit first!")
        return
    habit_id = habit_tree.item(selected[0])['values'][0]
    today = datetime.today().strftime('%Y-%m-%d')
    
    # Toggle status
    c.execute("SELECT status FROM habit_tracker WHERE habit_id=? AND date=?", (habit_id, today))
    result = c.fetchone()
    if result:
        new_status = 0 if result[0] == 1 else 1
        c.execute("UPDATE habit_tracker SET status=? WHERE habit_id=? AND date=?", (new_status, habit_id, today))
    else:
        c.execute("INSERT INTO habit_tracker (habit_id, date, status) VALUES (?, ?, 1)", (habit_id, today))
    
    conn.commit()
    load_habits()
    update_dashboard()

def edit_habit():
    selected = habit_tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Select a habit to edit!")
        return
    habit_id, name, freq, _ = habit_tree.item(selected[0])['values']
    
    habit_name.delete(0, tk.END)
    habit_name.insert(0, name)
    habit_freq.delete(0, tk.END)
    habit_freq.insert(0, freq)
    
    def save_changes():
        new_name = habit_name.get().strip()
        new_freq = habit_freq.get().strip()
        if not new_name or not new_freq.isdigit():
            messagebox.showwarning("Input Error", "Enter valid habit name and frequency!")
            return
        c.execute("UPDATE habits SET habit_name=?, frequency=? WHERE habit_id=?",
                  (new_name, int(new_freq), habit_id))
        conn.commit()
        habit_name.delete(0, tk.END)
        habit_freq.delete(0, tk.END)
        load_habits()
        update_dashboard()
        edit_habit_btn.config(text="Edit Habit", command=edit_habit)
    
    edit_habit_btn.config(text="Save Changes", command=save_changes)

def delete_habit():
    selected = habit_tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Select a habit to delete!")
        return
    habit_id = habit_tree.item(selected[0])['values'][0]
    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this habit?"):
        c.execute("DELETE FROM habits WHERE habit_id=?", (habit_id,))
        c.execute("DELETE FROM habit_tracker WHERE habit_id=?", (habit_id,))
        conn.commit()
        load_habits()
        update_dashboard()

# --- Mood Management ---
def add_mood():
    mood = mood_combobox.get()
    notes = mood_notes.get().strip()
    if not mood:
        messagebox.showwarning("Input Error", "Select a mood!")
        return
    today = datetime.today().strftime('%Y-%m-%d')
    c.execute("INSERT OR REPLACE INTO mood (user_id, date, mood, notes) VALUES (?, ?, ?, ?)",
              (current_user, today, mood, notes))
    conn.commit()
    mood_notes.delete(0, tk.END)
    load_moods()
    update_dashboard()

def load_moods():
    for row in mood_tree.get_children():
        mood_tree.delete(row)
    c.execute("SELECT date, mood, notes FROM mood WHERE user_id=? ORDER BY date DESC", (current_user,))
    for row in c.fetchall():
        mood_tree.insert("", tk.END, values=row)

def edit_mood():
    selected = mood_tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Select a mood to edit!")
        return
    date, mood, notes = mood_tree.item(selected[0])['values']
    
    mood_combobox.set(mood)
    mood_notes.delete(0, tk.END)
    mood_notes.insert(0, notes)
    
    def save_changes():
        new_mood = mood_combobox.get()
        new_notes = mood_notes.get().strip()
        if not new_mood:
            messagebox.showwarning("Input Error", "Select a mood!")
            return
        c.execute("UPDATE mood SET mood=?, notes=? WHERE user_id=? AND date=?",
                  (new_mood, new_notes, current_user, date))
        conn.commit()
        mood_notes.delete(0, tk.END)
        load_moods()
        update_dashboard()
        edit_mood_btn.config(text="Edit Mood", command=edit_mood)
    
    edit_mood_btn.config(text="Save Changes", command=save_changes)

def delete_mood():
    selected = mood_tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Select a mood to delete!")
        return
    date = mood_tree.item(selected[0])['values'][0]
    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this mood entry?"):
        c.execute("DELETE FROM mood WHERE user_id=? AND date=?", (current_user, date))
        conn.commit()
        load_moods()
        update_dashboard()

# --- Dashboard ---
def update_dashboard():
    c.execute("SELECT COUNT(*) FROM habits WHERE user_id=?", (current_user,))
    total_habits = c.fetchone()[0]
    today = datetime.today().strftime('%Y-%m-%d')
    c.execute("""SELECT COUNT(*) FROM habit_tracker ht
                 JOIN habits h ON ht.habit_id = h.habit_id
                 WHERE h.user_id=? AND ht.date=? AND ht.status=1""", (current_user, today))
    done_today = c.fetchone()[0]
    dashboard_label.config(text=f"Total Habits: {total_habits} | Completed Today: {done_today}")

# --- GUI ---
root = tk.Tk()
root.title("Habit & Mood Tracker")
root.geometry("900x600")

# Login Frame
login_frame = tk.Frame(root)
login_frame.pack(pady=10)

tk.Label(login_frame, text="Username:").grid(row=0, column=0)
login_username = tk.Entry(login_frame)
login_username.grid(row=0, column=1)

tk.Label(login_frame, text="Password:").grid(row=1, column=0)
login_password = tk.Entry(login_frame, show="*")
login_password.grid(row=1, column=1)

tk.Button(login_frame, text="Login", command=login_user).grid(row=2, column=0, columnspan=2, pady=5)
tk.Label(login_frame, text="Don't have an account? Register below:").grid(row=3, column=0, columnspan=2, pady=5)

tk.Label(login_frame, text="Username:").grid(row=4, column=0)
reg_username = tk.Entry(login_frame)
reg_username.grid(row=4, column=1)

tk.Label(login_frame, text="Password:").grid(row=5, column=0)
reg_password = tk.Entry(login_frame, show="*")
reg_password.grid(row=5, column=1)

tk.Button(login_frame, text="Register", command=register_user).grid(row=6, column=0, columnspan=2, pady=5)

# Main Frame
main_frame = tk.Frame(root)
tk.Button(main_frame, text="Logout", command=logout_user).pack(pady=5)

# Habit Frame
habit_frame = tk.LabelFrame(main_frame, text="Habits")
habit_frame.pack(fill=tk.X, padx=10, pady=5)

tk.Label(habit_frame, text="Habit Name:").grid(row=0, column=0)
habit_name = tk.Entry(habit_frame)
habit_name.grid(row=0, column=1)

tk.Label(habit_frame, text="Frequency per week:").grid(row=0, column=2)
habit_freq = tk.Entry(habit_frame)
habit_freq.grid(row=0, column=3)

tk.Button(habit_frame, text="Add Habit", command=add_habit).grid(row=0, column=4, padx=5)
tk.Button(habit_frame, text="Mark Done/Undone Today", command=mark_done).grid(row=0, column=5, padx=5)

edit_habit_btn = tk.Button(habit_frame, text="Edit Habit", command=edit_habit)
edit_habit_btn.grid(row=0, column=6, padx=5)

tk.Button(habit_frame, text="Delete Habit", command=delete_habit).grid(row=0, column=7, padx=5)

habit_tree = ttk.Treeview(main_frame, columns=("ID","Habit","Freq","Status"), show="headings")
for col in ("ID","Habit","Freq","Status"):
    habit_tree.heading(col, text=col)
habit_tree.pack(fill=tk.X, padx=10, pady=5)

# Mood Frame
mood_frame = tk.LabelFrame(main_frame, text="Mood")
mood_frame.pack(fill=tk.X, padx=10, pady=5)

mood_combobox = ttk.Combobox(mood_frame, values=["Happy","Sad","Neutral","Excited","Angry"])
mood_combobox.grid(row=0, column=0, padx=5)
mood_notes = tk.Entry(mood_frame)
mood_notes.grid(row=0, column=1, padx=5)

tk.Button(mood_frame, text="Add Mood", command=add_mood).grid(row=0, column=2, padx=5)

edit_mood_btn = tk.Button(mood_frame, text="Edit Mood", command=edit_mood)
edit_mood_btn.grid(row=0, column=3, padx=5)

tk.Button(mood_frame, text="Delete Mood", command=delete_mood).grid(row=0, column=4, padx=5)

mood_tree = ttk.Treeview(main_frame, columns=("Date","Mood","Notes"), show="headings")
for col in ("Date","Mood","Notes"):
    mood_tree.heading(col, text=col)
mood_tree.pack(fill=tk.X, padx=10, pady=5)

dashboard_label = tk.Label(main_frame, text="Dashboard")
dashboard_label.pack(pady=10)

root.mainloop()
