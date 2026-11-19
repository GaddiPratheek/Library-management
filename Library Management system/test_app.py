import unittest
from datetime import datetime, timedelta
from app import app
from database import get_db, init_db
from werkzeug.security import check_password_hash

class LibrarySystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        init_db()

    def test_database_initialization(self):
        conn = get_db()
        cursor = conn.cursor()
        for table in ["users", "books", "students", "issue_records", "return_records"]:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()["count"]
            self.assertGreaterEqual(count, 0, f"Table {table} should exist")
        conn.close()

    def test_admin_and_student_logins(self):
        # Admin login
        response = self.client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back, admin!", response.data)

        # Logout
        self.client.get("/logout", follow_redirects=True)

        # Student login
        response = self.client.post("/login", data={
            "username": "rahul",
            "password": "student123"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"rahul", response.data)

        # Logout
        self.client.get("/logout", follow_redirects=True)

        # Invalid login
        response = self.client.post("/login", data={
            "username": "admin",
            "password": "wrongpassword"
        }, follow_redirects=True)
        self.assertIn(b"Invalid username", response.data)

    def test_book_crud_lifecycle(self):
        # Login as Admin first
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "admin"

        # 1. Add Book
        unique_isbn = f"978-TEST-{datetime.now().strftime('%f')}"
        response = self.client.post("/books/add", data={
            "title": "Automated Testing in Python",
            "author": "Guido Test",
            "isbn": unique_isbn,
            "category": "Computer Science",
            "publisher": "Tech Press",
            "publication_year": "2024",
            "total_qty": "3"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Automated Testing in Python", response.data)

        # Verify in DB
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE isbn = ?", (unique_isbn,))
        book = cursor.fetchone()
        self.assertIsNotNone(book)
        book_id = book["id"]
        self.assertEqual(book["available_qty"], 3)

        # 2. Edit Book
        response = self.client.post(f"/books/edit/{book_id}", data={
            "title": "Automated Testing in Python (Updated)",
            "author": "Guido Test",
            "isbn": unique_isbn,
            "category": "Software Engineering",
            "publisher": "Tech Press",
            "publication_year": "2025",
            "total_qty": "5"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        updated = cursor.fetchone()
        self.assertEqual(updated["title"], "Automated Testing in Python (Updated)")
        self.assertEqual(updated["total_qty"], 5)
        self.assertEqual(updated["available_qty"], 5)

        # 3. Delete Book
        response = self.client.post(f"/books/delete/{book_id}", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        self.assertIsNone(cursor.fetchone())
        conn.close()

    def test_student_crud_lifecycle(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "admin"

        stu_id = f"TEST{datetime.now().strftime('%f')[:4]}"
        email = f"test_{stu_id}@college.edu"

        # 1. Add Student
        response = self.client.post("/students/add", data={
            "student_id": stu_id,
            "name": "Test Student Runner",
            "email": email,
            "phone": "+91 9999988888",
            "department": "Information Technology",
            "year": "2nd Year"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Student Runner", response.data)

        # Verify DB
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (stu_id,))
        stu = cursor.fetchone()
        self.assertIsNotNone(stu)
        db_id = stu["id"]

        # 2. Edit Student
        response = self.client.post(f"/students/edit/{db_id}", data={
            "student_id": stu_id,
            "name": "Test Student Runner (Updated)",
            "email": email,
            "phone": "+91 9999977777",
            "department": "Computer Science",
            "year": "3rd Year"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        cursor.execute("SELECT * FROM students WHERE id = ?", (db_id,))
        updated_stu = cursor.fetchone()
        self.assertEqual(updated_stu["name"], "Test Student Runner (Updated)")

        # 3. Delete Student
        response = self.client.post(f"/students/delete/{db_id}", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        cursor.execute("SELECT * FROM students WHERE id = ?", (db_id,))
        self.assertIsNone(cursor.fetchone())
        conn.close()

    def test_issue_return_and_fine_calculation(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "admin"

        conn = get_db()
        cursor = conn.cursor()

        # Get an available book and a student
        cursor.execute("SELECT id, available_qty FROM books WHERE available_qty > 0 LIMIT 1")
        book = cursor.fetchone()
        book_id = book["id"]
        initial_qty = book["available_qty"]

        cursor.execute("SELECT id FROM students LIMIT 1")
        student_id = cursor.fetchone()["id"]

        # Issue book with overdue issue date to test late fine calculation (e.g. issued 20 days ago)
        issue_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
        due_date = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")

        response = self.client.post("/issue", data={
            "student_id": student_id,
            "book_id": book_id,
            "issue_date": issue_date,
            "due_date": due_date,
            "remarks": "Automated Test Loan"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check stock decremented
        cursor.execute("SELECT available_qty FROM books WHERE id = ?", (book_id,))
        new_qty = cursor.fetchone()["available_qty"]
        self.assertEqual(new_qty, initial_qty - 1)

        # Get the new issue record
        cursor.execute("SELECT id FROM issue_records WHERE student_id = ? AND book_id = ? AND status IN ('issued', 'overdue') ORDER BY id DESC LIMIT 1", (student_id, book_id))
        issue_record = cursor.fetchone()
        self.assertIsNotNone(issue_record)
        issue_id = issue_record["id"]

        # Test API fine calculation: 6 days overdue * ₹5 = ₹30
        today_str = datetime.now().strftime("%Y-%m-%d")
        api_resp = self.client.get(f"/api/calculate-fine/{issue_id}?date={today_str}")
        self.assertEqual(api_resp.status_code, 200)
        fine_data = api_resp.get_json()
        self.assertGreaterEqual(fine_data["days_overdue"], 5)
        self.assertGreaterEqual(fine_data["fine_amount"], 25.0)

        # Return the book
        ret_response = self.client.post("/return", data={
            "issue_id": issue_id,
            "return_date": today_str,
            "fine_paid": "1",
            "remarks": "Returned via automated test"
        }, follow_redirects=True)
        self.assertEqual(ret_response.status_code, 200)

        # Verify stock restored
        cursor.execute("SELECT available_qty FROM books WHERE id = ?", (book_id,))
        restored_qty = cursor.fetchone()["available_qty"]
        self.assertEqual(restored_qty, initial_qty)

        # Verify status is returned
        cursor.execute("SELECT status, fine_amount FROM issue_records WHERE id = ?", (issue_id,))
        returned_issue = cursor.fetchone()
        self.assertEqual(returned_issue["status"], "returned")
        self.assertGreater(returned_issue["fine_amount"], 0)

        conn.close()

    def test_reports_and_csv_export(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "admin"

        # Reports page load
        rep_resp = self.client.get("/reports")
        self.assertEqual(rep_resp.status_code, 200)
        self.assertIn(b"Reports & Library Analytics", rep_resp.data)

        # Export CSVs
        for rtype in ["books", "overdue", "transactions"]:
            csv_resp = self.client.get(f"/reports/export/{rtype}")
            self.assertEqual(csv_resp.status_code, 200)
            self.assertEqual(csv_resp.mimetype, "text/csv")
            self.assertIn("attachment;filename=", csv_resp.headers["Content-Disposition"])

if __name__ == "__main__":
    unittest.main()
