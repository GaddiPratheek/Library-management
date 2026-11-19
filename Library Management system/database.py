import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        student_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        publisher TEXT,
        publication_year INTEGER,
        total_qty INTEGER NOT NULL DEFAULT 1,
        available_qty INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        department TEXT NOT NULL,
        year TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS issue_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        issue_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        status TEXT NOT NULL DEFAULT 'issued',
        fine_amount REAL DEFAULT 0.0,
        remarks TEXT,
        FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE RESTRICT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS return_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER NOT NULL,
        return_date TEXT NOT NULL,
        days_delayed INTEGER DEFAULT 0,
        fine_amount REAL DEFAULT 0.0,
        fine_paid INTEGER DEFAULT 1,
        remarks TEXT,
        FOREIGN KEY (issue_id) REFERENCES issue_records(id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # Seed Initial Data if Users table is empty
    cursor.execute("SELECT COUNT(*) AS count FROM users;")
    user_count = cursor.fetchone()["count"]

    if user_count == 0:
        seed_sample_data(conn)

    conn.close()

def seed_sample_data(conn):
    cursor = conn.cursor()
    today = datetime.now().date()

    # 1. Seed Users (Admin & Students)
    admin_pw = generate_password_hash("admin123")
    student_pw = generate_password_hash("student123")

    users_data = [
        ("admin", "admin@library.com", admin_pw, "admin", None),
        ("rahul", "rahul.sharma@college.edu", student_pw, "student", "STU101"),
        ("priya", "priya.patel@college.edu", student_pw, "student", "STU102"),
        ("amit", "amit.verma@college.edu", student_pw, "student", "STU103")
    ]
    cursor.executemany("""
        INSERT INTO users (username, email, password_hash, role, student_id)
        VALUES (?, ?, ?, ?, ?)
    """, users_data)

    # 2. Seed Students
    students_data = [
        ("STU101", "Rahul Sharma", "rahul.sharma@college.edu", "+91 9876543210", "Computer Science", "3rd Year"),
        ("STU102", "Priya Patel", "priya.patel@college.edu", "+91 9876543211", "Information Technology", "2nd Year"),
        ("STU103", "Amit Verma", "amit.verma@college.edu", "+91 9876543212", "Mechanical Engineering", "4th Year"),
        ("STU104", "Sneha Reddy", "sneha.reddy@college.edu", "+91 9876543213", "Electronics & Comm.", "1st Year"),
        ("STU105", "Vikram Singh", "vikram.singh@college.edu", "+91 9876543214", "Civil Engineering", "3rd Year"),
        ("STU106", "Ananya Das", "ananya.das@college.edu", "+91 9876543215", "Computer Science", "2nd Year")
    ]
    cursor.executemany("""
        INSERT INTO students (student_id, name, email, phone, department, year)
        VALUES (?, ?, ?, ?, ?, ?)
    """, students_data)

    # 3. Seed Books
    # (id, title, author, isbn, category, publisher, year, total_qty, available_qty)
    books_data = [
        ("Clean Code: Agile Software Craftsmanship", "Robert C. Martin", "978-0132350884", "Computer Science", "Prentice Hall", 2008, 5, 4),
        ("Introduction to Algorithms (CLRS)", "Thomas H. Cormen", "978-0262033848", "Computer Science", "MIT Press", 2009, 4, 3),
        ("The Pragmatic Programmer", "Andrew Hunt, David Thomas", "978-0135957059", "Software Engineering", "Addison-Wesley", 2019, 3, 2),
        ("Artificial Intelligence: A Modern Approach", "Stuart Russell, Peter Norvig", "978-0136042594", "Artificial Intelligence", "Pearson", 2020, 4, 4),
        ("Database System Concepts", "Abraham Silberschatz", "978-0078022159", "Database Systems", "McGraw-Hill", 2019, 6, 5),
        ("Python Crash Course", "Eric Matthes", "978-1593279288", "Programming", "No Starch Press", 2023, 5, 4),
        ("Design Patterns: Elements of Reusable OOD", "Erich Gamma, Richard Helm", "978-0201633610", "Software Engineering", "Addison-Wesley", 1994, 3, 3),
        ("Computer Networking: A Top-Down Approach", "James Kurose, Keith Ross", "978-0136681557", "Networking", "Pearson", 2021, 4, 4),
        ("To Kill a Mockingbird", "Harper Lee", "978-0060935467", "Literature", "Harper Perennial", 1960, 3, 2),
        ("Sapiens: A Brief History of Humankind", "Yuval Noah Harari", "978-0062316097", "History & Philosophy", "Harper", 2014, 4, 4)
    ]
    cursor.executemany("""
        INSERT INTO books (title, author, isbn, category, publisher, publication_year, total_qty, available_qty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, books_data)

    # 4. Seed Issue Records
    # Student 1 (Rahul) has Book 1 issued (Active, within due date)
    date_issue1 = today - timedelta(days=4)
    date_due1 = date_issue1 + timedelta(days=14)

    # Student 2 (Priya) has Book 2 issued (Overdue! Issued 20 days ago, due 6 days ago)
    date_issue2 = today - timedelta(days=20)
    date_due2 = date_issue2 + timedelta(days=14)
    overdue_days2 = (today - date_due2).days
    fine2 = overdue_days2 * 5.0

    # Student 3 (Amit) has Book 3 issued (Active, within due date)
    date_issue3 = today - timedelta(days=7)
    date_due3 = date_issue3 + timedelta(days=14)

    # Student 1 (Rahul) had Book 6 issued and Returned 2 days ago
    date_issue4 = today - timedelta(days=18)
    date_due4 = date_issue4 + timedelta(days=14)
    date_ret4 = today - timedelta(days=2)
    delayed_days4 = (date_ret4 - date_due4).days
    fine4 = max(0, delayed_days4 * 5.0)

    # Student 2 (Priya) had Book 9 issued (Active, within due date)
    date_issue5 = today - timedelta(days=2)
    date_due5 = date_issue5 + timedelta(days=14)

    issue_records = [
        (1, 1, str(date_issue1), str(date_due1), None, "issued", 0.0, "Regular issue for semester study"),
        (2, 2, str(date_issue2), str(date_due2), None, "overdue", fine2, "Overdue book - reminder sent"),
        (3, 3, str(date_issue3), str(date_due3), None, "issued", 0.0, "Final year project reference"),
        (6, 1, str(date_issue4), str(date_due4), str(date_ret4), "returned", fine4, "Returned with fine settled"),
        (9, 2, str(date_issue5), str(date_due5), None, "issued", 0.0, "Fiction reading")
    ]
    cursor.executemany("""
        INSERT INTO issue_records (book_id, student_id, issue_date, due_date, return_date, status, fine_amount, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, issue_records)

    # 5. Seed Return Record for the returned book (issue_id = 4)
    cursor.execute("""
        INSERT INTO return_records (issue_id, return_date, days_delayed, fine_amount, fine_paid, remarks)
        VALUES (4, ?, ?, ?, 1, 'Fine settled via UPI')
    """, (str(date_ret4), delayed_days4, fine4))

    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully with sample data!")
