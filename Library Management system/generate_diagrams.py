import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Ensure diagrams directory exists
os.makedirs("doc_assets", exist_ok=True)

def generate_sru_logo():
    fig, ax = plt.subplots(figsize=(3, 2), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # Draw "sru" stylized logo
    ax.text(5, 3, "sru", fontsize=58, fontweight='heavy', color='#104c97',
            ha='center', va='center', fontfamily='sans-serif')
    
    plt.tight_layout()
    fig.savefig("doc_assets/sru_logo.png", bbox_inches='tight', transparent=True)
    plt.close()

def generate_architecture_diagram():
    fig, ax = plt.subplots(figsize=(9, 6), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Colors
    c_client = "#e0f2fe"
    c_app = "#ede9fe"
    c_db = "#fef3c7"
    border_c = "#334155"

    # Title
    ax.text(5, 9.6, "Three-Tier System Architecture", fontsize=15, fontweight='bold', ha='center', color='#1e293b')

    # Tier 1: Presentation Layer
    p1 = patches.FancyBboxPatch((0.5, 6.8), 9, 2.2, boxstyle="round,pad=0.2", facecolor=c_client, edgecolor='#0284c7', linewidth=1.5)
    ax.add_patch(p1)
    ax.text(0.8, 8.6, "1. Presentation Layer (Client Tier)", fontsize=11, fontweight='bold', color='#0369a1')
    
    # Components in Tier 1
    boxes_t1 = [
        ("Responsive Web Browser\n(Desktop / Tablet / Mobile)", 1.0, 7.1, 2.4),
        ("Bootstrap 5.3 UI & CSS3\nModern Library Layout", 3.8, 7.1, 2.6),
        ("Client JS & Chart.js\nReal-time Fine Calc & Charts", 6.8, 7.1, 2.4)
    ]
    for text, x, y, w in boxes_t1:
        ax.add_patch(patches.FancyBboxPatch((x, y), w, 1.2, boxstyle="round,pad=0.1", facecolor='#ffffff', edgecolor='#38bdf8', linewidth=1))
        ax.text(x + w/2, y + 0.6, text, fontsize=8.5, ha='center', va='center', color='#0f172a')

    # Arrow 1 <-> 2
    ax.annotate('', xy=(5, 5.8), xytext=(5, 6.7),
                arrowprops=dict(arrowstyle="<|-|>", color="#475569", lw=2))
    ax.text(5.2, 6.2, "HTTP / HTTPS (RESTful Requests & HTML Responses)", fontsize=8, color="#475569", va='center')

    # Tier 2: Application / Business Logic Layer
    p2 = patches.FancyBboxPatch((0.5, 3.4), 9, 2.3, boxstyle="round,pad=0.2", facecolor=c_app, edgecolor='#7c3aed', linewidth=1.5)
    ax.add_patch(p2)
    ax.text(0.8, 5.3, "2. Application & Logic Layer (Flask Web Server)", fontsize=11, fontweight='bold', color='#6d28d9')

    boxes_t2 = [
        ("Authentication & RBAC\n(Werkzeug Password Hash)", 0.8, 3.7, 2.0),
        ("Circulation Controller\n(14-day Due Date Engine)", 3.0, 3.7, 2.0),
        ("Late Fine Engine\n(₹5/day Overdue Rules)", 5.2, 3.7, 1.9),
        ("Reporting & CSV API\n(Stock Audit & Analytics)", 7.3, 3.7, 1.9)
    ]
    for text, x, y, w in boxes_t2:
        ax.add_patch(patches.FancyBboxPatch((x, y), w, 1.3, boxstyle="round,pad=0.1", facecolor='#ffffff', edgecolor='#a78bfa', linewidth=1))
        ax.text(x + w/2, y + 0.65, text, fontsize=8, ha='center', va='center', color='#0f172a')

    # Arrow 2 <-> 3
    ax.annotate('', xy=(5, 2.4), xytext=(5, 3.3),
                arrowprops=dict(arrowstyle="<|-|>", color="#475569", lw=2))
    ax.text(5.2, 2.8, "SQLite Connection & Parametrized SQL Queries", fontsize=8, color="#475569", va='center')

    # Tier 3: Database Layer
    p3 = patches.FancyBboxPatch((0.5, 0.4), 9, 1.9, boxstyle="round,pad=0.2", facecolor=c_db, edgecolor='#d97706', linewidth=1.5)
    ax.add_patch(p3)
    ax.text(0.8, 1.9, "3. Relational Database Layer (SQLite3 - library.db)", fontsize=11, fontweight='bold', color='#b45309')

    tables = ["users", "books", "students", "issue_records", "return_records"]
    for i, t in enumerate(tables):
        tx = 0.8 + i * 1.7
        ax.add_patch(patches.FancyBboxPatch((tx, 0.65), 1.5, 0.9, boxstyle="round,pad=0.1", facecolor='#ffffff', edgecolor='#f59e0b', linewidth=1))
        ax.text(tx + 0.75, 1.1, f"Table: {t}\n[FK Constraints]", fontsize=7.5, ha='center', va='center', color='#78350f', fontweight='semibold')

    plt.tight_layout()
    fig.savefig("doc_assets/system_architecture.png", bbox_inches='tight', dpi=200)
    plt.close()

def generate_use_case_diagram():
    fig, ax = plt.subplots(figsize=(9, 6.5), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Title
    ax.text(5, 9.6, "Use Case Diagram: Library Management System", fontsize=14, fontweight='bold', ha='center', color='#1e293b')

    # System boundary
    rect = patches.Rectangle((2.3, 0.5), 5.4, 8.7, fill=False, edgecolor="#64748b", linestyle="--", linewidth=1.5)
    ax.add_patch(rect)
    ax.text(2.5, 8.9, "Library Management System", fontsize=10, fontweight='bold', color='#475569')

    # Actors: Admin (Left), Student (Right)
    # Admin icon / text
    ax.plot(1.0, 7.0, 'o', markersize=14, color='#1e293b')
    ax.plot([1.0, 1.0], [5.8, 6.7], color='#1e293b', lw=2.5) # body
    ax.plot([0.5, 1.5], [6.3, 6.3], color='#1e293b', lw=2.5) # arms
    ax.plot([1.0, 0.6], [5.8, 5.0], color='#1e293b', lw=2.5) # leg 1
    ax.plot([1.0, 1.4], [5.8, 5.0], color='#1e293b', lw=2.5) # leg 2
    ax.text(1.0, 4.6, "Administrator\n(Librarian)", fontsize=10, fontweight='bold', ha='center', color='#1e293b')

    # Student icon / text
    ax.plot(9.0, 5.5, 'o', markersize=14, color='#0369a1')
    ax.plot([9.0, 9.0], [4.3, 5.2], color='#0369a1', lw=2.5) # body
    ax.plot([8.5, 9.5], [4.8, 4.8], color='#0369a1', lw=2.5) # arms
    ax.plot([9.0, 8.6], [4.3, 3.5], color='#0369a1', lw=2.5) # leg 1
    ax.plot([9.0, 9.4], [4.3, 3.5], color='#0369a1', lw=2.5) # leg 2
    ax.text(9.0, 3.1, "Student\n(Borrower)", fontsize=10, fontweight='bold', ha='center', color='#0369a1')

    # Use cases inside system boundary
    use_cases = [
        ("Login & Authentication", 5.0, 8.2),
        ("Manage Books (CRUD)", 5.0, 7.2),
        ("Manage Students (CRUD)", 5.0, 6.2),
        ("Issue Book (14 Days)", 5.0, 5.2),
        ("Return Book & Fine Calc", 5.0, 4.2),
        ("View Own Loan Records", 5.0, 3.2),
        ("Browse Book Inventory", 5.0, 2.2),
        ("Generate Reports & CSV", 5.0, 1.2),
    ]

    for uc, x, y in use_cases:
        ellipse = patches.Ellipse((x, y), 3.4, 0.65, facecolor="#eff6ff", edgecolor="#3b82f6", linewidth=1.2)
        ax.add_patch(ellipse)
        ax.text(x, y, uc, fontsize=8.5, ha='center', va='center', color='#1e293b', fontweight='medium')

    # Lines from Admin to Use Cases
    admin_targets = [8.2, 7.2, 6.2, 5.2, 4.2, 2.2, 1.2]
    for ty in admin_targets:
        ax.plot([1.4, 3.3], [6.2, ty], color='#64748b', lw=1.2)

    # Lines from Student to Use Cases
    student_targets = [8.2, 3.2, 2.2]
    for ty in student_targets:
        ax.plot([8.6, 6.7], [4.7, ty], color='#0284c7', lw=1.2)

    plt.tight_layout()
    fig.savefig("doc_assets/use_case_diagram.png", bbox_inches='tight', dpi=200)
    plt.close()

def generate_class_diagram():
    fig, ax = plt.subplots(figsize=(9.5, 7), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Title
    ax.text(5, 9.6, "UML Class Diagram: Entity Relationships & Methods", fontsize=13, fontweight='bold', ha='center', color='#1e293b')

    def draw_class(x, y, w, title, attrs, methods, header_bg='#e0e7ff', border_c='#4f46e5'):
        total_h = 0.5 + len(attrs)*0.22 + 0.1 + len(methods)*0.22
        # Outer box
        ax.add_patch(patches.Rectangle((x, y - total_h), w, total_h, facecolor='#ffffff', edgecolor=border_c, linewidth=1.5))
        # Header
        ax.add_patch(patches.Rectangle((x, y - 0.5), w, 0.5, facecolor=header_bg, edgecolor=border_c, linewidth=1.5))
        ax.text(x + w/2, y - 0.28, title, fontsize=9.5, fontweight='bold', ha='center', va='center', color='#1e1b4b')
        
        # Attributes
        curr_y = y - 0.7
        for a in attrs:
            ax.text(x + 0.1, curr_y, a, fontsize=7.5, va='center', color='#334155', fontfamily='monospace')
            curr_y -= 0.22
            
        # Divider line
        ax.plot([x, x + w], [curr_y + 0.08, curr_y + 0.08], color=border_c, lw=1)
        curr_y -= 0.12
        
        # Methods
        for m in methods:
            ax.text(x + 0.1, curr_y, m, fontsize=7.5, va='center', color='#1e293b', fontfamily='monospace')
            curr_y -= 0.22

    # 1. User Class
    draw_class(0.4, 9.0, 2.7, "User", 
               ["- id: int", "- username: str", "- email: str", "- password_hash: str", "- role: str", "- student_id: str"],
               ["+ verify_password()", "+ is_admin(): bool"])

    # 2. Student Class
    draw_class(0.4, 5.0, 2.7, "Student",
               ["- id: int", "- student_id: str", "- name: str", "- email: str", "- phone: str", "- department: str", "- year: str"],
               ["+ get_active_loans()", "+ get_overdue_fines()"])

    # 3. Book Class
    draw_class(6.8, 9.0, 2.8, "Book",
               ["- id: int", "- title: str", "- author: str", "- isbn: str", "- category: str", "- total_qty: int", "- available_qty: int"],
               ["+ is_available(): bool", "+ decrement_qty()", "+ restore_qty()"])

    # 4. IssueRecord Class
    draw_class(3.6, 7.3, 2.8, "IssueRecord",
               ["- id: int", "- book_id: int", "- student_id: int", "- issue_date: Date", "- due_date: Date", "- status: str", "- fine_amount: float"],
               ["+ calculate_due_date()", "+ mark_returned()", "+ check_overdue()"])

    # 5. ReturnRecord Class
    draw_class(3.6, 3.4, 2.8, "ReturnRecord",
               ["- id: int", "- issue_id: int", "- return_date: Date", "- days_delayed: int", "- fine_amount: float", "- fine_paid: int"],
               ["+ calculate_fine(rate=5)", "+ process_settlement()"])

    # Relationship connectors
    # Student -> IssueRecord (1 to 0..*)
    ax.annotate('', xy=(3.6, 6.0), xytext=(3.1, 4.2),
                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.5))
    ax.text(3.3, 5.2, "1..*", fontsize=8, color="#475569")

    # Book -> IssueRecord (1 to 0..*)
    ax.annotate('', xy=(6.4, 6.5), xytext=(6.8, 7.5),
                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.5))
    ax.text(6.4, 7.2, "1..*", fontsize=8, color="#475569")

    # IssueRecord -> ReturnRecord (1 to 0..1)
    ax.annotate('', xy=(5.0, 3.4), xytext=(5.0, 4.4),
                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.5))
    ax.text(5.1, 3.9, "1 to 0..1", fontsize=8, color="#475569")

    # User -> Student (optional link)
    ax.annotate('', xy=(1.7, 5.0), xytext=(1.7, 6.4),
                arrowprops=dict(arrowstyle="--", color="#94a3b8", lw=1.2))

    plt.tight_layout()
    fig.savefig("doc_assets/class_diagram.png", bbox_inches='tight', dpi=200)
    plt.close()

def generate_sequence_diagram():
    fig, ax = plt.subplots(figsize=(9.5, 6.5), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    ax.text(5, 9.6, "Sequence Diagram: Book Checkout and Return Workflow", fontsize=13, fontweight='bold', ha='center', color='#1e293b')

    # Lifelines
    actors = [
        ("Librarian / UI", 1.2),
        ("Flask Controller", 3.8),
        ("Circulation / Fine Engine", 6.5),
        ("SQLite Database", 9.0)
    ]

    for label, x in actors:
        # Box
        ax.add_patch(patches.FancyBboxPatch((x - 0.9, 8.8), 1.8, 0.5, boxstyle="round,pad=0.05", facecolor="#f1f5f9", edgecolor="#475569"))
        ax.text(x, 9.05, label, fontsize=8, fontweight='bold', ha='center', va='center')
        # Dashed line
        ax.plot([x, x], [0.8, 8.8], linestyle="--", color="#94a3b8", lw=1)

    # Sequence Messages
    steps = [
        (8.2, 1.2, 3.8, "POST /issue (student_id, book_id, date)", "->"),
        (7.6, 3.8, 9.0, "SELECT available_qty, active_loans", "->"),
        (7.0, 9.0, 3.8, "Return Available Stock & Eligibility", "<--"),
        (6.4, 3.8, 6.5, "Calculate Due Date (Date + 14 Days)", "->"),
        (5.8, 3.8, 9.0, "INSERT issue_records, UPDATE books qty - 1", "->"),
        (5.2, 3.8, 1.2, "Flash Success 'Book Issued (Due: +14d)'", "<--"),
        
        # Return Sequence
        (4.4, 1.2, 3.8, "POST /return (issue_id, return_date)", "->"),
        (3.8, 3.8, 6.5, "calculate_late_fine(return_date, due_date)", "->"),
        (3.2, 6.5, 3.8, "Return Late Days * ₹5.00", "<--"),
        (2.6, 3.8, 9.0, "UPDATE issue_records, UPDATE books qty + 1", "->"),
        (2.0, 9.0, 3.8, "INSERT return_records (fine_paid)", "->"),
        (1.4, 3.8, 1.2, "Display Return Confirmation & Receipt", "<--")
    ]

    for y, x1, x2, msg, direction in steps:
        if direction == "->":
            ax.annotate('', xy=(x2, y), xytext=(x1, y),
                        arrowprops=dict(arrowstyle="->", color="#2563eb", lw=1.3))
        else:
            ax.annotate('', xy=(x2, y), xytext=(x1, y),
                        arrowprops=dict(arrowstyle="->", linestyle="--", color="#059669", lw=1.3))
        mid_x = (x1 + x2) / 2
        ax.text(mid_x, y + 0.15, msg, fontsize=7.2, ha='center', color='#1e293b')

    plt.tight_layout()
    fig.savefig("doc_assets/sequence_diagram.png", bbox_inches='tight', dpi=200)
    plt.close()

def generate_activity_diagram():
    fig, ax = plt.subplots(figsize=(8.5, 7), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    ax.text(5, 9.7, "Activity Diagram: Library Circulation Life-Cycle", fontsize=13, fontweight='bold', ha='center', color='#1e293b')

    def draw_node(x, y, w, h, text, bg='#eff6ff', edge='#3b82f6'):
        ax.add_patch(patches.FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.1", facecolor=bg, edgecolor=edge, lw=1.2))
        ax.text(x, y, text, fontsize=7.5, ha='center', va='center', color='#0f172a', fontweight='medium')

    def draw_decision(x, y, text):
        diamond = patches.RegularPolygon((x, y), numVertices=4, radius=0.55, orientation=0, facecolor='#fef3c7', edgecolor='#d97706', lw=1.2)
        ax.add_patch(diamond)
        ax.text(x, y, text, fontsize=6.8, ha='center', va='center', color='#78350f', fontweight='bold')

    # Initial Node
    ax.plot(5, 9.1, 'o', markersize=12, color='#1e293b')

    # Steps
    ax.annotate('', xy=(5, 8.4), xytext=(5, 9.0), arrowprops=dict(arrowstyle="->", lw=1.2))
    draw_node(5, 8.1, 4.0, 0.6, "Select Student & Book in Checkout Form")

    ax.annotate('', xy=(5, 7.3), xytext=(5, 7.8), arrowprops=dict(arrowstyle="->", lw=1.2))
    draw_decision(5, 6.9, "Available?\n(Qty > 0)")

    # Decision No
    ax.annotate('', xy=(2.4, 6.9), xytext=(4.4, 6.9), arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.text(3.4, 7.1, "[No]", fontsize=7.5, color='#b91c1c', fontweight='bold')
    draw_node(1.5, 6.9, 1.8, 0.6, "Show Out of Stock\nAlert", bg='#fee2e2', edge='#ef4444')

    # Decision Yes
    ax.annotate('', xy=(5, 5.8), xytext=(5, 6.4), arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.text(5.3, 6.1, "[Yes]", fontsize=7.5, color='#15803d', fontweight='bold')
    draw_node(5, 5.5, 4.2, 0.6, "Issue Book, Set Due Date (+14d), Qty - 1")

    # Loan Period Waiting
    ax.annotate('', xy=(5, 4.5), xytext=(5, 5.2), arrowprops=dict(arrowstyle="->", lw=1.2))
    draw_node(5, 4.2, 3.8, 0.6, "Active Loan Period (Books with Student)")

    # Return Initiation
    ax.annotate('', xy=(5, 3.2), xytext=(5, 3.9), arrowprops=dict(arrowstyle="->", lw=1.2))
    draw_decision(5, 2.8, "Returned\nPast Due?")

    # No Overdue
    ax.annotate('', xy=(2.5, 2.8), xytext=(4.4, 2.8), arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.text(3.4, 3.0, "[No]", fontsize=7.5, color='#15803d', fontweight='bold')
    draw_node(1.5, 2.8, 1.8, 0.6, "Fine = ₹0.00\nOn-time return", bg='#dcfce7', edge='#10b981')

    # Yes Overdue
    ax.annotate('', xy=(7.5, 2.8), xytext=(5.6, 2.8), arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.text(6.5, 3.0, "[Yes]", fontsize=7.5, color='#b91c1c', fontweight='bold')
    draw_node(8.5, 2.8, 1.8, 0.6, "Calculate Fine\n(Days * ₹5.00)", bg='#fee2e2', edge='#ef4444')

    # Both lead to Final Stock Restoration
    draw_node(5, 1.4, 4.2, 0.6, "Update Status to 'Returned', Restore Qty + 1")
    ax.annotate('', xy=(5, 1.7), xytext=(1.5, 2.5), arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.annotate('', xy=(5, 1.7), xytext=(8.5, 2.5), arrowprops=dict(arrowstyle="->", lw=1.2))

    # Final Node
    ax.annotate('', xy=(5, 0.5), xytext=(5, 1.1), arrowprops=dict(arrowstyle="->", lw=1.2))
    circle_outer = plt.Circle((5, 0.35), 0.22, fill=False, color='#1e293b', lw=1.5)
    circle_inner = plt.Circle((5, 0.35), 0.14, facecolor='#1e293b')
    ax.add_patch(circle_outer)
    ax.add_patch(circle_inner)

    plt.tight_layout()
    fig.savefig("doc_assets/activity_diagram.png", bbox_inches='tight', dpi=200)
    plt.close()

if __name__ == "__main__":
    generate_sru_logo()
    generate_architecture_diagram()
    generate_use_case_diagram()
    generate_class_diagram()
    generate_sequence_diagram()
    generate_activity_diagram()
    print("All diagrams generated successfully!")
