# PlacementHub — College Placement Portal

## 🚀 Setup & Run

### 1. Install Dependencies
```bash
pip install flask
```

### 2. Run the Application
```bash
cd placement_app
python app.py
```

### 3. Open in Browser
Visit: **http://localhost:5000**

---

## 📁 Project Structure

```
placement_app/
├── app.py                     # Flask backend + SQLite DB
├── requirements.txt
├── placement.db               # Auto-created on first run
├── templates/
│   ├── index.html             # Landing page — portal selector
│   ├── student_register.html  # Student account creation
│   ├── student_login.html     # Student login
│   ├── student_home.html      # Student dashboard
│   ├── student_profile.html   # Student profile editor
│   ├── admin_register.html    # Admin account creation
│   ├── admin_login.html       # Admin login
│   └── admin_home.html        # Admin dashboard
└── static/
    └── css/
        └── style.css          # Shared dark-theme styles
```

---

## 🌐 All 8 Pages & Their Features

### 1. `index.html` — Landing Page (`/`)
- Homepage with two portal cards: Student and Admin
- Each card has direct links to Register and Login

### 2. `student_register.html` — Student Registration (`/student/register`)
- Fields: Full Name, Phone, Email, Department (dropdown), Year (dropdown), CGPA, Skills (comma-separated), Password
- On success: toast notification + auto-redirect to Student Login

### 3. `student_login.html` — Student Login (`/student/login`)
- Fields: Email, Password (Enter key supported)
- Session-based auth; redirects to Student Dashboard on success
- Link back to Register and Home

### 4. `student_home.html` — Student Dashboard (`/student/home`)
- **Dashboard tab** — Stats cards: Available Drives, Applied count, Pending Results; Recent 3 drives preview
- **Job Drives tab** — Full grid of all posted drives; live search by company/role; click any card to open detail modal with package, location, dates, eligibility, description; Apply button (disabled if already applied)
- **My Applications tab** — Table showing: Company, Role, Package, Drive Date, Status, Applied Date
- Sidebar navigation + topbar with username and avatar initial

### 5. `student_profile.html` — Student Profile (`/student/profile`)
- Profile header: Avatar with initial, Name, Email, Department badge, Year badge, CGPA badge
- Editable fields: Full Name, Phone, Department, Year, CGPA, Resume Link (URL), Skills
- Skills section: renders each comma-separated skill as a visual tag/badge
- Save Changes updates the profile instantly via API

### 6. `admin_register.html` — Admin Registration (`/admin/register`)
- Fields: Full Name, Email, Password
- On success: toast notification + auto-redirect to Admin Login

### 7. `admin_login.html` — Admin Login (`/admin/login`)
- Fields: Email, Password
- Session-based auth; redirects to Admin Dashboard on success
- Link back to Register and Home

### 8. `admin_home.html` — Admin Dashboard (`/admin/home`)
- **Dashboard tab** — Stats cards: Total Students, Active Drives, Total Applications; Recent drives summary table
- **Post Job Drive tab** — Form fields: Company Name, Role, Package (CTC), Location, Drive Date, Last Date to Apply, Eligibility Criteria, Description; posts drive to DB on submit
- **All Drives tab** — Cards for every posted drive with all details and applicant count badge; "View Applicants" opens a modal listing everyone who applied (Name, Email, Dept, Year, CGPA, Status)
- **All Students tab** — Searchable table of all registered students: Name, Email, Phone, Department, Year, CGPA (green if ≥8.0, amber otherwise), Skills, Joined Date

---

## 🗄️ Database Tables
- `students` — student accounts and full profile data
- `admins` — admin accounts
- `job_drives` — placement drives posted by admins
- `applications` — student-to-drive applications (many-to-many, unique per student+drive pair)

## 🔐 Security
- Passwords stored as SHA-256 hashes (never plaintext)
- All dashboard routes protected by server-side session checks
- Unauthenticated access auto-redirects to the appropriate login page
