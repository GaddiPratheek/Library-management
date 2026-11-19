import os
import csv
import io
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, Response, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "library_super_secret_key_2026_xyz")

# Ensure DB is initialized
init_db()

# ----------------- Database Helpers & Context ----------------- #
def get_db_conn():
    if "db" not in g:
        g.db = get_db()
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def update_overdue_records(conn):
    """Automatically updates overdue status and fine (₹5/day) for past-due issued books."""
    today = datetime.now().date()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, due_date FROM issue_records 
        WHERE status IN ('issued', 'overdue')
    """)
    records = cursor.fetchall()
    for row in records:
        try:
            due_date = datetime.strptime(row["due_date"], "%Y-%m-%d").date()
            if today > due_date:
                overdue_days = (today - due_date).days
                fine = overdue_days * 5.0
                cursor.execute("""
                    UPDATE issue_records 
                    SET status = 'overdue', fine_amount = ? 
                    WHERE id = ?
                """, (fine, row["id"]))
            else:
                cursor.execute("""
                    UPDATE issue_records 
                    SET status = 'issued', fine_amount = 0.0 
                    WHERE id = ?
                """, (row["id"],))
        except ValueError:
            continue
    conn.commit()

# ----------------- Decorators ----------------- #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in first.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Admin access privileges required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

# Context processor for templates
@app.context_processor
def inject_globals():
    return {
        "current_user": {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "role": session.get("role"),
            "student_id": session.get("student_id")
        },
        "now": datetime.now()
    }

# ----------------- Authentication Routes ----------------- #
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role_type = request.form.get("role_type", "admin")

        if not username or not password:
            flash("Please fill in all credentials.", "danger")
            return render_template("login.html")

        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username))
        user = cursor.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["student_id"] = user["student_id"]
            flash(f"Welcome back, {user['username']}! Logged in as {user['role'].capitalize()}.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username/email or password.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session and session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        role = request.form.get("role", "student")
        student_id = request.form.get("student_id", "").strip().upper()
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "Computer Science")
        year = request.form.get("year", "1st Year")

        if not username or not email or not password:
            flash("All required fields must be filled.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html")

        conn = get_db_conn()
        cursor = conn.cursor()

        # Check existing user
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone():
            flash("Username or Email already registered.", "danger")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        if role == "student":
            if not student_id:
                student_id = f"STU{datetime.now().strftime('%M%S')}"
            
            # Check or create student record
            cursor.execute("SELECT id FROM students WHERE student_id = ?", (student_id,))
            existing_stu = cursor.fetchone()
            if not existing_stu:
                cursor.execute("""
                    INSERT INTO students (student_id, name, email, phone, department, year)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (student_id, name or username.capitalize(), email, phone or "N/A", department, year))

        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, student_id)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, password_hash, role, student_id if role == "student" else None))
        conn.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("login"))

# ----------------- Dashboard Route ----------------- #
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_conn()
    update_overdue_records(conn)
    cursor = conn.cursor()

    is_admin = session.get("role") == "admin"
    student_id = session.get("student_id")

    # 1. System-wide statistics
    cursor.execute("SELECT SUM(total_qty) AS total_books, SUM(available_qty) AS available_books FROM books")
    book_stats = cursor.fetchone()
    total_books = book_stats["total_books"] or 0
    available_books = book_stats["available_books"] or 0

    cursor.execute("SELECT COUNT(*) AS total_students FROM students")
    total_students = cursor.fetchone()["total_students"] or 0

    cursor.execute("SELECT COUNT(*) AS issued_books FROM issue_records WHERE status IN ('issued', 'overdue')")
    issued_books = cursor.fetchone()["issued_books"] or 0

    cursor.execute("SELECT COUNT(*) AS overdue_books FROM issue_records WHERE status = 'overdue'")
    overdue_books = cursor.fetchone()["overdue_books"] or 0

    cursor.execute("SELECT SUM(fine_amount) AS total_fines FROM return_records WHERE fine_paid = 1")
    fines_collected = cursor.fetchone()["total_fines"] or 0.0

    cursor.execute("SELECT SUM(fine_amount) AS pending_fines FROM issue_records WHERE status = 'overdue'")
    fines_pending = cursor.fetchone()["pending_fines"] or 0.0

    # 2. Student-specific statistics if student logged in
    student_stats = {}
    if not is_admin and student_id:
        cursor.execute("SELECT id FROM students WHERE student_id = ?", (student_id,))
        stu_row = cursor.fetchone()
        stu_db_id = stu_row["id"] if stu_row else 0

        cursor.execute("""
            SELECT COUNT(*) AS my_active FROM issue_records 
            WHERE student_id = ? AND status IN ('issued', 'overdue')
        """, (stu_db_id,))
        student_stats["active_borrowed"] = cursor.fetchone()["my_active"] or 0

        cursor.execute("""
            SELECT COUNT(*) AS my_overdue FROM issue_records 
            WHERE student_id = ? AND status = 'overdue'
        """, (stu_db_id,))
        student_stats["overdue_count"] = cursor.fetchone()["my_overdue"] or 0

        cursor.execute("""
            SELECT SUM(fine_amount) AS my_fines FROM issue_records 
            WHERE student_id = ? AND status = 'overdue'
        """, (stu_db_id,))
        student_stats["pending_fines"] = cursor.fetchone()["my_fines"] or 0.0

    # 3. Recent Transactions (last 6)
    recent_query = """
        SELECT ir.id, ir.issue_date, ir.due_date, ir.return_date, ir.status, ir.fine_amount,
               b.title AS book_title, b.isbn,
               s.name AS student_name, s.student_id
        FROM issue_records ir
        JOIN books b ON ir.book_id = b.id
        JOIN students s ON ir.student_id = s.id
    """
    if not is_admin and student_id:
        recent_query += " WHERE s.student_id = ? "
        params = (student_id,)
    else:
        params = ()

    recent_query += " ORDER BY ir.id DESC LIMIT 6"
    cursor.execute(recent_query, params)
    recent_transactions = cursor.fetchall()

    # 4. Critical Overdue Alerts
    cursor.execute("""
        SELECT ir.id, ir.due_date, ir.fine_amount,
               b.title AS book_title, s.name AS student_name, s.student_id, s.phone
        FROM issue_records ir
        JOIN books b ON ir.book_id = b.id
        JOIN students s ON ir.student_id = s.id
        WHERE ir.status = 'overdue'
        ORDER BY ir.due_date ASC LIMIT 5
    """)
    overdue_alerts = cursor.fetchall()

    # 5. Chart Data: Books by Category
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM books 
        GROUP BY category 
        ORDER BY count DESC LIMIT 6
    """)
    category_chart_data = cursor.fetchall()

    return render_template(
        "dashboard.html",
        total_books=total_books,
        available_books=available_books,
        issued_books=issued_books,
        total_students=total_students,
        overdue_books=overdue_books,
        fines_collected=fines_collected,
        fines_pending=fines_pending,
        student_stats=student_stats,
        recent_transactions=recent_transactions,
        overdue_alerts=overdue_alerts,
        category_chart_data=category_chart_data
    )

# ----------------- Book Management Routes ----------------- #
@app.route("/books")
@login_required
def books():
    conn = get_db_conn()
    cursor = conn.cursor()

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    availability = request.args.get("availability", "").strip()

    query = "SELECT * FROM books WHERE 1=1"
    params = []

    if search:
        query += " AND (title LIKE ? OR author LIKE ? OR isbn LIKE ? OR publisher LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if category:
        query += " AND category = ?"
        params.append(category)

    if availability == "available":
        query += " AND available_qty > 0"
    elif availability == "out_of_stock":
        query += " AND available_qty = 0"

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    book_list = cursor.fetchall()

    # Get distinct categories for filter
    cursor.execute("SELECT DISTINCT category FROM books ORDER BY category ASC")
    categories = [row["category"] for row in cursor.fetchall()]

    return render_template("books.html", books=book_list, categories=categories,
                           search=search, selected_category=category, availability=availability)

@app.route("/books/add", methods=["GET", "POST"])
@admin_required
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        isbn = request.form.get("isbn", "").strip()
        category = request.form.get("category", "").strip()
        publisher = request.form.get("publisher", "").strip()
        publication_year = request.form.get("publication_year", "").strip()
        total_qty = request.form.get("total_qty", "1").strip()

        if not title or not author or not isbn or not category:
            flash("Title, Author, ISBN, and Category are required.", "danger")
            return render_template("add_book.html")

        try:
            total_qty = int(total_qty)
            if total_qty < 1:
                total_qty = 1
            publication_year = int(publication_year) if publication_year else None
        except ValueError:
            flash("Invalid quantity or year value.", "danger")
            return render_template("add_book.html")

        conn = get_db_conn()
        cursor = conn.cursor()

        # Check unique ISBN
        cursor.execute("SELECT id FROM books WHERE isbn = ?", (isbn,))
        if cursor.fetchone():
            flash("A book with this ISBN already exists.", "danger")
            return render_template("add_book.html")

        cursor.execute("""
            INSERT INTO books (title, author, isbn, category, publisher, publication_year, total_qty, available_qty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, author, isbn, category, publisher, publication_year, total_qty, total_qty))
        conn.commit()

        flash(f"Book '{title}' added successfully!", "success")
        return redirect(url_for("books"))

    return render_template("add_book.html")

@app.route("/books/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_book(id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (id,))
    book = cursor.fetchone()

    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for("books"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        isbn = request.form.get("isbn", "").strip()
        category = request.form.get("category", "").strip()
        publisher = request.form.get("publisher", "").strip()
        publication_year = request.form.get("publication_year", "").strip()
        total_qty = request.form.get("total_qty", "1").strip()

        if not title or not author or not isbn or not category:
            flash("Please fill in all required fields.", "danger")
            return render_template("add_book.html", book=book, is_edit=True)

        try:
            total_qty = int(total_qty)
            publication_year = int(publication_year) if publication_year else None
        except ValueError:
            flash("Invalid number format for quantity or year.", "danger")
            return render_template("add_book.html", book=book, is_edit=True)

        # Check ISBN collision with other books
        cursor.execute("SELECT id FROM books WHERE isbn = ? AND id != ?", (isbn, id))
        if cursor.fetchone():
            flash("Another book already uses this ISBN.", "danger")
            return render_template("add_book.html", book=book, is_edit=True)

        # Current issued count
        currently_issued = book["total_qty"] - book["available_qty"]
        if total_qty < currently_issued:
            flash(f"Cannot set total quantity to {total_qty}. {currently_issued} copies are currently issued to students.", "danger")
            return render_template("add_book.html", book=book, is_edit=True)

        new_available_qty = total_qty - currently_issued

        cursor.execute("""
            UPDATE books
            SET title = ?, author = ?, isbn = ?, category = ?, publisher = ?,
                publication_year = ?, total_qty = ?, available_qty = ?
            WHERE id = ?
        """, (title, author, isbn, category, publisher, publication_year, total_qty, new_available_qty, id))
        conn.commit()

        flash(f"Book '{title}' updated successfully!", "success")
        return redirect(url_for("books"))

    return render_template("add_book.html", book=book, is_edit=True)

@app.route("/books/delete/<int:id>", methods=["POST"])
@admin_required
def delete_book(id):
    conn = get_db_conn()
    cursor = conn.cursor()

    # Verify if active issues exist
    cursor.execute("""
        SELECT COUNT(*) AS active_count FROM issue_records 
        WHERE book_id = ? AND status IN ('issued', 'overdue')
    """, (id,))
    active_count = cursor.fetchone()["active_count"]

    if active_count > 0:
        flash(f"Cannot delete book: {active_count} copy/copies are currently issued and pending return.", "danger")
        return redirect(url_for("books"))

    cursor.execute("SELECT title FROM books WHERE id = ?", (id,))
    b = cursor.fetchone()
    title = b["title"] if b else "Book"

    # Also delete past return and issue records associated with book
    cursor.execute("DELETE FROM issue_records WHERE book_id = ?", (id,))
    cursor.execute("DELETE FROM books WHERE id = ?", (id,))
    conn.commit()

    flash(f"Book '{title}' deleted successfully.", "success")
    return redirect(url_for("books"))

# ----------------- Student Management Routes ----------------- #
@app.route("/students")
@admin_required
def students():
    conn = get_db_conn()
    cursor = conn.cursor()

    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()

    query = """
        SELECT s.*, 
            (SELECT COUNT(*) FROM issue_records WHERE student_id = s.id AND status IN ('issued', 'overdue')) AS active_books,
            (SELECT COUNT(*) FROM issue_records WHERE student_id = s.id AND status = 'overdue') AS overdue_books
        FROM students s
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (s.name LIKE ? OR s.student_id LIKE ? OR s.email LIKE ? OR s.phone LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if department:
        query += " AND s.department = ?"
        params.append(department)

    query += " ORDER BY s.id DESC"
    cursor.execute(query, params)
    student_list = cursor.fetchall()

    cursor.execute("SELECT DISTINCT department FROM students ORDER BY department ASC")
    departments = [row["department"] for row in cursor.fetchall()]

    return render_template("students.html", students=student_list, departments=departments,
                           search=search, selected_department=department)

@app.route("/students/add", methods=["GET", "POST"])
@admin_required
def add_student():
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip().upper()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()

        if not student_id or not name or not email or not phone:
            flash("Student ID, Name, Email, and Phone are required.", "danger")
            return render_template("add_student.html")

        conn = get_db_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM students WHERE student_id = ? OR email = ?", (student_id, email))
        if cursor.fetchone():
            flash("Student ID or Email already exists in the system.", "danger")
            return render_template("add_student.html")

        cursor.execute("""
            INSERT INTO students (student_id, name, email, phone, department, year)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, name, email, phone, department, year))
        conn.commit()

        flash(f"Student '{name}' ({student_id}) enrolled successfully!", "success")
        return redirect(url_for("students"))

    return render_template("add_student.html")

@app.route("/students/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_student(id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()

    if not student:
        flash("Student record not found.", "danger")
        return redirect(url_for("students"))

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip().upper()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()

        if not student_id or not name or not email:
            flash("Student ID, Name, and Email are required.", "danger")
            return render_template("add_student.html", student=student, is_edit=True)

        cursor.execute("SELECT id FROM students WHERE (student_id = ? OR email = ?) AND id != ?", (student_id, email, id))
        if cursor.fetchone():
            flash("Another student already has this Student ID or Email.", "danger")
            return render_template("add_student.html", student=student, is_edit=True)

        cursor.execute("""
            UPDATE students
            SET student_id = ?, name = ?, email = ?, phone = ?, department = ?, year = ?
            WHERE id = ?
        """, (student_id, name, email, phone, department, year, id))
        conn.commit()

        flash(f"Student '{name}' details updated successfully!", "success")
        return redirect(url_for("students"))

    return render_template("add_student.html", student=student, is_edit=True)

@app.route("/students/delete/<int:id>", methods=["POST"])
@admin_required
def delete_student(id):
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS active_count FROM issue_records 
        WHERE student_id = ? AND status IN ('issued', 'overdue')
    """, (id,))
    active_count = cursor.fetchone()["active_count"]

    if active_count > 0:
        flash(f"Cannot delete student: Student currently holds {active_count} issued book(s).", "danger")
        return redirect(url_for("students"))

    cursor.execute("SELECT name FROM students WHERE id = ?", (id,))
    s = cursor.fetchone()
    name = s["name"] if s else "Student"

    cursor.execute("DELETE FROM issue_records WHERE student_id = ?", (id,))
    cursor.execute("DELETE FROM students WHERE id = ?", (id,))
    conn.commit()

    flash(f"Student record '{name}' deleted.", "success")
    return redirect(url_for("students"))

@app.route("/students/view/<int:id>")
@login_required
def view_student(id):
    conn = get_db_conn()
    update_overdue_records(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()

    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("students"))

    # If student user, ensure they can only view their own profile
    if session.get("role") != "admin" and session.get("student_id") != student["student_id"]:
        flash("You are only authorized to view your own profile.", "danger")
        return redirect(url_for("dashboard"))

    cursor.execute("""
        SELECT ir.*, b.title AS book_title, b.isbn, b.category
        FROM issue_records ir
        JOIN books b ON ir.book_id = b.id
        WHERE ir.student_id = ?
        ORDER BY ir.id DESC
    """, (id,))
    history = cursor.fetchall()

    return render_template("student_detail.html", student=student, history=history)

# ----------------- Issue Books Route ----------------- #
@app.route("/issue", methods=["GET", "POST"])
@admin_required
def issue_book():
    conn = get_db_conn()
    cursor = conn.cursor()

    if request.method == "POST":
        student_id_val = request.form.get("student_id", "").strip()
        book_id_val = request.form.get("book_id", "").strip()
        issue_date_str = request.form.get("issue_date", "").strip()
        due_date_str = request.form.get("due_date", "").strip()
        remarks = request.form.get("remarks", "").strip()

        if not student_id_val or not book_id_val:
            flash("Please select both a student and a book.", "danger")
            return redirect(url_for("issue_book"))

        try:
            student_id = int(student_id_val)
            book_id = int(book_id_val)
        except ValueError:
            flash("Invalid student or book selection.", "danger")
            return redirect(url_for("issue_book"))

        # Check dates
        if not issue_date_str:
            issue_date = datetime.now().date()
        else:
            issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d").date()

        if not due_date_str:
            due_date = issue_date + timedelta(days=14)
        else:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()

        # Check book availability
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()
        if not book:
            flash("Selected book does not exist.", "danger")
            return redirect(url_for("issue_book"))

        if book["available_qty"] <= 0:
            flash(f"Book '{book['title']}' is currently out of stock!", "danger")
            return redirect(url_for("issue_book"))

        # Check student
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            flash("Selected student not found.", "danger")
            return redirect(url_for("issue_book"))

        # Prevent duplicate active issue of the SAME book to the same student
        cursor.execute("""
            SELECT id FROM issue_records 
            WHERE student_id = ? AND book_id = ? AND status IN ('issued', 'overdue')
        """, (student_id, book_id))
        if cursor.fetchone():
            flash(f"Student {student['name']} already has an active copy of '{book['title']}'. Return it before issuing another.", "warning")
            return redirect(url_for("issue_book"))

        # Issue book transaction
        cursor.execute("""
            INSERT INTO issue_records (book_id, student_id, issue_date, due_date, status, fine_amount, remarks)
            VALUES (?, ?, ?, ?, 'issued', 0.0, ?)
        """, (book_id, student_id, str(issue_date), str(due_date), remarks))

        # Decrement available quantity
        cursor.execute("""
            UPDATE books SET available_qty = available_qty - 1 WHERE id = ?
        """, (book_id,))

        conn.commit()

        flash(f"Successfully issued '{book['title']}' to {student['name']} ({student['student_id']}). Due Date: {due_date.strftime('%d-%b-%Y')}.", "success")
        return redirect(url_for("transactions"))

    # GET: Load available books and students
    cursor.execute("SELECT id, title, author, isbn, available_qty FROM books WHERE available_qty > 0 ORDER BY title ASC")
    available_books = cursor.fetchall()

    cursor.execute("SELECT id, student_id, name, department FROM students ORDER BY name ASC")
    students_list = cursor.fetchall()

    today_str = datetime.now().strftime("%Y-%m-%d")
    default_due_str = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    # Optional pre-selected book or student from query params
    pre_book_id = request.args.get("book_id", "")
    pre_student_id = request.args.get("student_id", "")

    return render_template(
        "issue_book.html",
        books=available_books,
        students=students_list,
        today=today_str,
        default_due=default_due_str,
        pre_book_id=pre_book_id,
        pre_student_id=pre_student_id
    )

# ----------------- Return Books Route ----------------- #
@app.route("/return", methods=["GET", "POST"])
@admin_required
def return_book():
    conn = get_db_conn()
    update_overdue_records(conn)
    cursor = conn.cursor()

    if request.method == "POST":
        issue_id = request.form.get("issue_id")
        return_date_str = request.form.get("return_date", "").strip()
        fine_paid = 1 if request.form.get("fine_paid") == "1" else 0
        remarks = request.form.get("remarks", "").strip()

        if not issue_id:
            flash("Invalid issue record selected.", "danger")
            return redirect(url_for("return_book"))

        cursor.execute("""
            SELECT ir.*, b.id AS book_id, b.title AS book_title, s.name AS student_name
            FROM issue_records ir
            JOIN books b ON ir.book_id = b.id
            JOIN students s ON ir.student_id = s.id
            WHERE ir.id = ? AND ir.status IN ('issued', 'overdue')
        """, (issue_id,))
        record = cursor.fetchone()

        if not record:
            flash("No active issued record found for this request.", "danger")
            return redirect(url_for("return_book"))

        if not return_date_str:
            return_date = datetime.now().date()
        else:
            return_date = datetime.strptime(return_date_str, "%Y-%m-%d").date()

        due_date = datetime.strptime(record["due_date"], "%Y-%m-%d").date()

        # Calculate late fine: ₹5 per day
        days_delayed = max(0, (return_date - due_date).days)
        fine_amount = days_delayed * 5.0

        # Update Issue Record
        cursor.execute("""
            UPDATE issue_records
            SET return_date = ?, status = 'returned', fine_amount = ?
            WHERE id = ?
        """, (str(return_date), fine_amount, issue_id))

        # Insert Return Record
        cursor.execute("""
            INSERT INTO return_records (issue_id, return_date, days_delayed, fine_amount, fine_paid, remarks)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (issue_id, str(return_date), days_delayed, fine_amount, fine_paid, remarks))

        # Restore Book Available Quantity (cannot exceed total_qty)
        cursor.execute("""
            UPDATE books 
            SET available_qty = MIN(total_qty, available_qty + 1)
            WHERE id = ?
        """, (record["book_id"],))

        conn.commit()

        fine_msg = f" Fine of ₹{fine_amount:.2f} calculated ({days_delayed} days late)." if fine_amount > 0 else " No late fine."
        flash(f"Book '{record['book_title']}' successfully returned by {record['student_name']}!{fine_msg}", "success")
        return redirect(url_for("transactions"))

    # GET: Active issues to return
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()

    query = """
        SELECT ir.*, b.title AS book_title, b.isbn,
               s.name AS student_name, s.student_id, s.department
        FROM issue_records ir
        JOIN books b ON ir.book_id = b.id
        JOIN students s ON ir.student_id = s.id
        WHERE ir.status IN ('issued', 'overdue')
    """
    params = []

    if search:
        query += " AND (b.title LIKE ? OR b.isbn LIKE ? OR s.name LIKE ? OR s.student_id LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if status_filter:
        query += " AND ir.status = ?"
        params.append(status_filter)

    query += " ORDER BY ir.due_date ASC"
    cursor.execute(query, params)
    active_issues = cursor.fetchall()

    today_str = datetime.now().strftime("%Y-%m-%d")

    return render_template("return_book.html", active_issues=active_issues, search=search,
                           status_filter=status_filter, today=today_str)

# ----------------- Transactions Route ----------------- #
@app.route("/transactions")
@login_required
def transactions():
    conn = get_db_conn()
    update_overdue_records(conn)
    cursor = conn.cursor()

    status_filter = request.args.get("status", "").strip()
    search = request.args.get("search", "").strip()

    is_admin = session.get("role") == "admin"
    student_id = session.get("student_id")

    query = """
        SELECT ir.*, b.title AS book_title, b.isbn, b.category,
               s.name AS student_name, s.student_id, s.department,
               rr.fine_paid, rr.days_delayed
        FROM issue_records ir
        JOIN books b ON ir.book_id = b.id
        JOIN students s ON ir.student_id = s.id
        LEFT JOIN return_records rr ON rr.issue_id = ir.id
        WHERE 1=1
    """
    params = []

    if not is_admin and student_id:
        query += " AND s.student_id = ?"
        params.append(student_id)

    if status_filter:
        query += " AND ir.status = ?"
        params.append(status_filter)

    if search:
        query += " AND (b.title LIKE ? OR b.isbn LIKE ? OR s.name LIKE ? OR s.student_id LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    query += " ORDER BY ir.id DESC"
    cursor.execute(query, params)
    transaction_records = cursor.fetchall()

    return render_template("transactions.html", transactions=transaction_records,
                           status_filter=status_filter, search=search)

# ----------------- Reports Route ----------------- #
@app.route("/reports")
@admin_required
def reports():
    conn = get_db_conn()
    update_overdue_records(conn)
    cursor = conn.cursor()

    # 1. Total books & stock stats
    cursor.execute("""
        SELECT COUNT(id) AS title_count, SUM(total_qty) AS total_copies,
               SUM(available_qty) AS available_copies,
               (SUM(total_qty) - SUM(available_qty)) AS issued_copies
        FROM books
    """)
    stock_stats = cursor.fetchone()

    # 2. Most Borrowed Books (Top 6)
    cursor.execute("""
        SELECT b.id, b.title, b.author, b.category, COUNT(ir.id) AS borrow_count
        FROM books b
        LEFT JOIN issue_records ir ON b.id = ir.book_id
        GROUP BY b.id
        ORDER BY borrow_count DESC
        LIMIT 6
    """)
    most_borrowed = cursor.fetchall()

    # 3. Overdue Books and Fine Summary
    cursor.execute("""
        SELECT ir.*, b.title AS book_title, s.name AS student_name, s.student_id, s.phone, s.email
        FROM issue_records ir
        JOIN books b ON ir.book_id = b.id
        JOIN students s ON ir.student_id = s.id
        WHERE ir.status = 'overdue'
        ORDER BY ir.due_date ASC
    """)
    overdue_report = cursor.fetchall()

    # 4. Top Borrowing Students
    cursor.execute("""
        SELECT s.student_id, s.name, s.department, COUNT(ir.id) AS total_borrowed
        FROM students s
        LEFT JOIN issue_records ir ON s.id = ir.student_id
        GROUP BY s.id
        ORDER BY total_borrowed DESC
        LIMIT 6
    """)
    top_students = cursor.fetchall()

    # 5. Category Breakdown
    cursor.execute("""
        SELECT category, COUNT(id) AS titles, SUM(total_qty) AS total_qty, SUM(available_qty) AS available_qty
        FROM books
        GROUP BY category
        ORDER BY total_qty DESC
    """)
    category_summary = cursor.fetchall()

    return render_template(
        "reports.html",
        stock_stats=stock_stats,
        most_borrowed=most_borrowed,
        overdue_report=overdue_report,
        top_students=top_students,
        category_summary=category_summary
    )

# ----------------- CSV Export Route ----------------- #
@app.route("/reports/export/<string:report_type>")
@admin_required
def export_csv(report_type):
    conn = get_db_conn()
    cursor = conn.cursor()
    output = io.StringIO()
    writer = csv.writer(output)

    today_str = datetime.now().strftime("%Y%m%d")

    if report_type == "books":
        cursor.execute("SELECT id, title, author, isbn, category, publisher, publication_year, total_qty, available_qty FROM books")
        rows = cursor.fetchall()
        writer.writerow(["Book ID", "Title", "Author", "ISBN", "Category", "Publisher", "Year", "Total Qty", "Available Qty"])
        for r in rows:
            writer.writerow([r["id"], r["title"], r["author"], r["isbn"], r["category"], r["publisher"], r["publication_year"], r["total_qty"], r["available_qty"]])
        filename = f"library_books_inventory_{today_str}.csv"

    elif report_type == "overdue":
        update_overdue_records(conn)
        cursor.execute("""
            SELECT ir.id, b.title, b.isbn, s.student_id, s.name, s.phone, ir.issue_date, ir.due_date, ir.fine_amount
            FROM issue_records ir
            JOIN books b ON ir.book_id = b.id
            JOIN students s ON ir.student_id = s.id
            WHERE ir.status = 'overdue'
            ORDER BY ir.due_date ASC
        """)
        rows = cursor.fetchall()
        writer.writerow(["Issue ID", "Book Title", "ISBN", "Student ID", "Student Name", "Phone", "Issue Date", "Due Date", "Fine (INR)"])
        for r in rows:
            writer.writerow([r["id"], r["title"], r["isbn"], r["student_id"], r["name"], r["phone"], r["issue_date"], r["due_date"], f"{r['fine_amount']:.2f}"])
        filename = f"library_overdue_report_{today_str}.csv"

    elif report_type == "transactions":
        cursor.execute("""
            SELECT ir.id, b.title, s.student_id, s.name, ir.issue_date, ir.due_date, ir.return_date, ir.status, ir.fine_amount
            FROM issue_records ir
            JOIN books b ON ir.book_id = b.id
            JOIN students s ON ir.student_id = s.id
            ORDER BY ir.id DESC
        """)
        rows = cursor.fetchall()
        writer.writerow(["Transaction ID", "Book Title", "Student ID", "Student Name", "Issue Date", "Due Date", "Return Date", "Status", "Fine (INR)"])
        for r in rows:
            writer.writerow([r["id"], r["title"], r["student_id"], r["name"], r["issue_date"], r["due_date"], r["return_date"] or "N/A", r["status"].capitalize(), f"{r['fine_amount']:.2f}"])
        filename = f"library_transactions_{today_str}.csv"

    else:
        flash("Invalid report type for export.", "danger")
        return redirect(url_for("reports"))

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

# ----------------- REST APIs for AJAX & Modals ----------------- #
@app.route("/api/books")
def api_books():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, isbn, category, total_qty, available_qty FROM books ORDER BY title ASC")
    books = [dict(row) for row in cursor.fetchall()]
    return jsonify(books)

@app.route("/api/books/<int:id>")
def api_book_detail(id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (id,))
    book = cursor.fetchone()
    if book:
        return jsonify(dict(book))
    return jsonify({"error": "Book not found"}), 404

@app.route("/api/calculate-fine/<int:issue_id>")
def api_calculate_fine(issue_id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ir.*, b.title AS book_title, s.name AS student_name 
        FROM issue_records ir
        JOIN books b ON ir.book_id = b.id
        JOIN students s ON ir.student_id = s.id
        WHERE ir.id = ?
    """, (issue_id,))
    record = cursor.fetchone()

    if not record:
        return jsonify({"error": "Record not found"}), 404

    target_date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        ret_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except ValueError:
        ret_date = datetime.now().date()

    due_date = datetime.strptime(record["due_date"], "%Y-%m-%d").date()
    late_days = max(0, (ret_date - due_date).days)
    fine = late_days * 5.0

    return jsonify({
        "issue_id": issue_id,
        "book_title": record["book_title"],
        "student_name": record["student_name"],
        "due_date": record["due_date"],
        "return_date": str(ret_date),
        "days_overdue": late_days,
        "fine_amount": fine
    })

# ----------------- Error Handlers ----------------- #
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
