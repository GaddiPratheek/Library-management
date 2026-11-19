/**
 * Library Management System - Frontend JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Sidebar Toggle for Mobile / Tablets
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.querySelector(".sidebar");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", function () {
      sidebar.classList.toggle("show");
    });

    // Close sidebar on click outside on small screens
    document.addEventListener("click", function (event) {
      if (
        window.innerWidth < 992 &&
        sidebar.classList.contains("show") &&
        !sidebar.contains(event.target) &&
        !sidebarToggle.contains(event.target)
      ) {
        sidebar.classList.remove("show");
      }
    });
  }

  // 2. Issue Date to Due Date Auto-Calculation (14 Days)
  const issueDateInput = document.getElementById("issue_date");
  const dueDateInput = document.getElementById("due_date");
  if (issueDateInput && dueDateInput) {
    issueDateInput.addEventListener("change", function () {
      if (this.value) {
        const parts = this.value.split("-");
        const issueDate = new Date(parts[0], parts[1] - 1, parts[2]);
        issueDate.setDate(issueDate.getDate() + 14);

        const year = issueDate.getFullYear();
        const month = String(issueDate.getMonth() + 1).padStart(2, "0");
        const day = String(issueDate.getDate()).padStart(2, "0");
        dueDateInput.value = `${year}-${month}-${day}`;
      }
    });
  }

  // 3. Client-side Table Filter for instant search
  const tableSearchInput = document.getElementById("tableSearchInput");
  if (tableSearchInput) {
    tableSearchInput.addEventListener("keyup", function () {
      const filter = this.value.toLowerCase();
      const targetTable = document.querySelector(".filterable-table tbody");
      if (!targetTable) return;

      const rows = targetTable.getElementsByTagName("tr");
      for (let i = 0; i < rows.length; i++) {
        const text = rows[i].textContent || rows[i].innerText;
        if (text.toLowerCase().indexOf(filter) > -1) {
          rows[i].style.display = "";
        } else {
          rows[i].style.display = "none";
        }
      }
    });
  }

  // 4. Return Book Fine Modal Setup
  const returnModal = document.getElementById("returnModal");
  if (returnModal) {
    returnModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      if (!button) return;

      const issueId = button.getAttribute("data-issue-id");
      const bookTitle = button.getAttribute("data-book-title");
      const studentName = button.getAttribute("data-student-name");
      const dueDate = button.getAttribute("data-due-date");

      document.getElementById("modal_issue_id").value = issueId;
      document.getElementById("modal_book_title").textContent = bookTitle;
      document.getElementById("modal_student_name").textContent = studentName;
      document.getElementById("modal_due_date").textContent = dueDate;

      // Calculate Fine for today
      calculateReturnFine(dueDate);
    });

    const returnDateInput = document.getElementById("modal_return_date");
    if (returnDateInput) {
      returnDateInput.addEventListener("change", function () {
        const dueDate = document.getElementById("modal_due_date").textContent;
        calculateReturnFine(dueDate, this.value);
      });
    }
  }

  function calculateReturnFine(dueDateStr, returnDateStr) {
    if (!dueDateStr) return;

    const dueParts = dueDateStr.split("-");
    const dueDate = new Date(dueParts[0], dueParts[1] - 1, dueParts[2]);

    let retDate;
    if (returnDateStr) {
      const retParts = returnDateStr.split("-");
      retDate = new Date(retParts[0], retParts[1] - 1, retParts[2]);
    } else {
      retDate = new Date();
    }
    retDate.setHours(0, 0, 0, 0);
    dueDate.setHours(0, 0, 0, 0);

    const diffTime = retDate - dueDate;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    const lateDays = diffDays > 0 ? diffDays : 0;
    const fineAmount = lateDays * 5.0; // ₹5 per day

    const daysElem = document.getElementById("modal_late_days");
    const fineElem = document.getElementById("modal_fine_amount");
    const fineBadge = document.getElementById("modal_fine_badge");

    if (daysElem) daysElem.textContent = lateDays;
    if (fineElem) fineElem.textContent = `₹${fineAmount.toFixed(2)}`;

    if (fineBadge) {
      if (lateDays > 0) {
        fineBadge.className = "alert alert-danger py-2 mb-3";
        fineBadge.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-2"></i><strong>Overdue by ${lateDays} days!</strong> Fine calculated at ₹5/day: <strong>₹${fineAmount.toFixed(2)}</strong>`;
      } else {
        fineBadge.className = "alert alert-success py-2 mb-3";
        fineBadge.innerHTML = `<i class="bi bi-check-circle-fill me-2"></i>Returned on time. No late fine applied.`;
      }
    }
  }

  // 5. Auto dismiss flash alerts after 5 seconds
  setTimeout(function () {
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);
});

// Helper for Book Quick View Modal
function viewBookDetails(bookId) {
  fetch(`/api/books/${bookId}`)
    .then((response) => response.json())
    .then((book) => {
      if (book.error) return alert("Book details not found.");
      document.getElementById("view_book_title").textContent = book.title;
      document.getElementById("view_book_author").textContent = book.author;
      document.getElementById("view_book_isbn").textContent = book.isbn;
      document.getElementById("view_book_category").textContent = book.category;
      document.getElementById("view_book_publisher").textContent = book.publisher || "N/A";
      document.getElementById("view_book_year").textContent = book.publication_year || "N/A";
      document.getElementById("view_book_total").textContent = book.total_qty;
      document.getElementById("view_book_avail").textContent = book.available_qty;

      const modal = new bootstrap.Modal(document.getElementById("bookDetailModal"));
      modal.show();
    })
    .catch((err) => console.error(err));
}
