from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = 'placement_secret_key_2024'
DB_PATH = 'placement.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
        phone TEXT, department TEXT, year TEXT, cgpa REAL, skills TEXT,
        resume_link TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS job_drives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL, role TEXT NOT NULL, description TEXT,
        eligibility TEXT, package TEXT, location TEXT, drive_date TEXT, last_date TEXT,
        posted_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (posted_by) REFERENCES admins(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER, drive_id INTEGER,
        status TEXT DEFAULT 'Applied',
        interview_date TEXT DEFAULT NULL,
        result TEXT DEFAULT 'Pending',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (drive_id) REFERENCES job_drives(id),
        UNIQUE(student_id, drive_id))''')
    # Migrate existing DB
    for col in ["interview_date TEXT DEFAULT NULL",
                "result TEXT DEFAULT 'Pending'",
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"]:
        try: c.execute(f"ALTER TABLE applications ADD COLUMN {col}")
        except: pass
    conn.commit()
    conn.close()

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# Pages
@app.route('/')
def index(): return render_template('index.html')
@app.route('/student/register')
def student_register(): return render_template('student_register.html')
@app.route('/student/login')
def student_login(): return render_template('student_login.html')
@app.route('/student/home')
def student_home():
    if 'student_id' not in session: return redirect('/student/login')
    return render_template('student_home.html')
@app.route('/student/profile')
def student_profile():
    if 'student_id' not in session: return redirect('/student/login')
    return render_template('student_profile.html')
@app.route('/admin/register')
def admin_register(): return render_template('admin_register.html')
@app.route('/admin/login')
def admin_login(): return render_template('admin_login.html')
@app.route('/admin/home')
def admin_home():
    if 'admin_id' not in session: return redirect('/admin/login')
    return render_template('admin_home.html')

# Auth
@app.route('/api/student/register', methods=['POST'])
def api_student_register():
    data = request.json
    conn = get_db()
    try:
        conn.execute('INSERT INTO students (name,email,password,phone,department,year,cgpa,skills) VALUES (?,?,?,?,?,?,?,?)',
                     (data['name'],data['email'],hash_password(data['password']),data.get('phone',''),
                      data.get('department',''),data.get('year',''),data.get('cgpa',0),data.get('skills','')))
        conn.commit()
        return jsonify({'success':True,'message':'Account created successfully!'})
    except sqlite3.IntegrityError:
        return jsonify({'success':False,'message':'Email already registered!'})
    finally: conn.close()

@app.route('/api/student/login', methods=['POST'])
def api_student_login():
    data = request.json
    conn = get_db()
    s = conn.execute('SELECT * FROM students WHERE email=? AND password=?',(data['email'],hash_password(data['password']))).fetchone()
    conn.close()
    if s:
        session['student_id']=s['id']; session['student_name']=s['name']
        return jsonify({'success':True})
    return jsonify({'success':False,'message':'Invalid credentials!'})

@app.route('/api/admin/register', methods=['POST'])
def api_admin_register():
    data = request.json
    conn = get_db()
    try:
        conn.execute('INSERT INTO admins (name,email,password) VALUES (?,?,?)',(data['name'],data['email'],hash_password(data['password'])))
        conn.commit()
        return jsonify({'success':True,'message':'Admin account created!'})
    except sqlite3.IntegrityError:
        return jsonify({'success':False,'message':'Email already registered!'})
    finally: conn.close()

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    data = request.json
    conn = get_db()
    a = conn.execute('SELECT * FROM admins WHERE email=? AND password=?',(data['email'],hash_password(data['password']))).fetchone()
    conn.close()
    if a:
        session['admin_id']=a['id']; session['admin_name']=a['name']
        return jsonify({'success':True})
    return jsonify({'success':False,'message':'Invalid credentials!'})

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({'success':True})

@app.route('/api/session/student')
def check_student_session():
    if 'student_id' in session: return jsonify({'logged_in':True,'name':session['student_name']})
    return jsonify({'logged_in':False})

@app.route('/api/session/admin')
def check_admin_session():
    if 'admin_id' in session: return jsonify({'logged_in':True,'name':session['admin_name']})
    return jsonify({'logged_in':False})

# Student APIs
@app.route('/api/student/profile', methods=['GET'])
def get_student_profile():
    if 'student_id' not in session: return jsonify({'success':False}),401
    conn = get_db()
    s = conn.execute('SELECT * FROM students WHERE id=?',(session['student_id'],)).fetchone()
    conn.close()
    return jsonify({'success':True,'data':dict(s)})

@app.route('/api/student/profile', methods=['PUT'])
def update_student_profile():
    if 'student_id' not in session: return jsonify({'success':False}),401
    data = request.json
    conn = get_db()
    conn.execute('UPDATE students SET name=?,phone=?,department=?,year=?,cgpa=?,skills=?,resume_link=? WHERE id=?',
                 (data['name'],data['phone'],data['department'],data['year'],data['cgpa'],data['skills'],data.get('resume_link',''),session['student_id']))
    conn.commit(); conn.close()
    return jsonify({'success':True,'message':'Profile updated!'})

@app.route('/api/student/drives', methods=['GET'])
def get_drives_student():
    if 'student_id' not in session: return jsonify({'success':False}),401
    conn = get_db()
    drives = conn.execute('''SELECT jd.*, CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END as applied
        FROM job_drives jd LEFT JOIN applications a ON jd.id=a.drive_id AND a.student_id=?
        ORDER BY jd.created_at DESC''',(session['student_id'],)).fetchall()
    conn.close()
    return jsonify({'success':True,'data':[dict(d) for d in drives]})

@app.route('/api/student/apply/<int:drive_id>', methods=['POST'])
def apply_drive(drive_id):
    if 'student_id' not in session: return jsonify({'success':False}),401
    conn = get_db()
    try:
        conn.execute('INSERT INTO applications (student_id,drive_id) VALUES (?,?)',(session['student_id'],drive_id))
        conn.commit()
        return jsonify({'success':True,'message':'Applied successfully!'})
    except sqlite3.IntegrityError:
        return jsonify({'success':False,'message':'Already applied!'})
    finally: conn.close()

@app.route('/api/student/applications', methods=['GET'])
def get_student_applications():
    if 'student_id' not in session: return jsonify({'success':False}),401
    conn = get_db()
    apps = conn.execute('''SELECT jd.company_name,jd.role,jd.package,jd.drive_date,jd.location,
                           a.status,a.interview_date,a.result,a.applied_at
                           FROM applications a JOIN job_drives jd ON a.drive_id=jd.id
                           WHERE a.student_id=? ORDER BY a.applied_at DESC''',(session['student_id'],)).fetchall()
    conn.close()
    return jsonify({'success':True,'data':[dict(a) for a in apps]})

@app.route('/api/student/report', methods=['GET'])
def get_student_report():
    if 'student_id' not in session: return jsonify({'success':False}),401
    conn = get_db()
    sid = session['student_id']
    selected = conn.execute('''SELECT jd.company_name,jd.role,jd.package,jd.location,
                               a.interview_date,a.result,a.applied_at FROM applications a
                               JOIN job_drives jd ON a.drive_id=jd.id
                               WHERE a.student_id=? AND a.result='Selected' ORDER BY a.updated_at DESC''',(sid,)).fetchall()
    rejected = conn.execute('''SELECT jd.company_name,jd.role,jd.package,jd.location,
                               a.result,a.applied_at FROM applications a
                               JOIN job_drives jd ON a.drive_id=jd.id
                               WHERE a.student_id=? AND a.result='Rejected' ORDER BY a.updated_at DESC''',(sid,)).fetchall()
    pending = conn.execute('''SELECT jd.company_name,jd.role,jd.package,jd.location,
                              a.status,a.interview_date,a.result,a.applied_at FROM applications a
                              JOIN job_drives jd ON a.drive_id=jd.id
                              WHERE a.student_id=? AND a.result='Pending' ORDER BY a.applied_at DESC''',(sid,)).fetchall()
    interviews = conn.execute('''SELECT jd.company_name,jd.role,a.interview_date,a.result
                                 FROM applications a JOIN job_drives jd ON a.drive_id=jd.id
                                 WHERE a.student_id=? AND a.interview_date IS NOT NULL AND a.interview_date!=''
                                 ORDER BY a.interview_date ASC''',(sid,)).fetchall()
    conn.close()
    return jsonify({'success':True,
        'selected':[dict(r) for r in selected],
        'rejected':[dict(r) for r in rejected],
        'pending':[dict(r) for r in pending],
        'interviews':[dict(r) for r in interviews]})

# Admin APIs
@app.route('/api/admin/drives', methods=['GET'])
def get_drives_admin():
    if 'admin_id' not in session: return jsonify({'success':False}),401
    conn = get_db()
    drives = conn.execute('''SELECT jd.*, COUNT(a.id) as applicant_count,
        SUM(CASE WHEN a.result='Selected' THEN 1 ELSE 0 END) as selected_count,
        SUM(CASE WHEN a.result='Rejected' THEN 1 ELSE 0 END) as rejected_count
        FROM job_drives jd LEFT JOIN applications a ON jd.id=a.drive_id
        GROUP BY jd.id ORDER BY jd.created_at DESC''').fetchall()
    conn.close()
    return jsonify({'success':True,'data':[dict(d) for d in drives]})

@app.route('/api/admin/drives', methods=['POST'])
def post_drive():
    if 'admin_id' not in session: return jsonify({'success':False}),401
    data = request.json
    conn = get_db()
    conn.execute('INSERT INTO job_drives (company_name,role,description,eligibility,package,location,drive_date,last_date,posted_by) VALUES (?,?,?,?,?,?,?,?,?)',
                 (data['company_name'],data['role'],data['description'],data['eligibility'],
                  data['package'],data['location'],data['drive_date'],data['last_date'],session['admin_id']))
    conn.commit(); conn.close()
    return jsonify({'success':True,'message':'Drive posted successfully!'})

@app.route('/api/admin/students', methods=['GET'])
def get_all_students():
    if 'admin_id' not in session: return jsonify({'success':False}),401
    conn = get_db()
    students = conn.execute('SELECT id,name,email,phone,department,year,cgpa,skills,created_at FROM students').fetchall()
    conn.close()
    return jsonify({'success':True,'data':[dict(s) for s in students]})

@app.route('/api/admin/drives/<int:drive_id>/applicants', methods=['GET'])
def get_applicants(drive_id):
    if 'admin_id' not in session: return jsonify({'success':False}),401
    conn = get_db()
    applicants = conn.execute('''SELECT a.id as app_id, s.id as student_id,
        s.name,s.email,s.phone,s.department,s.year,s.cgpa,
        a.status,a.interview_date,a.result,a.applied_at
        FROM applications a JOIN students s ON a.student_id=s.id
        WHERE a.drive_id=? ORDER BY a.applied_at''',(drive_id,)).fetchall()
    conn.close()
    return jsonify({'success':True,'data':[dict(a) for a in applicants]})

@app.route('/api/admin/applications/<int:app_id>/result', methods=['PUT'])
def update_result(app_id):
    if 'admin_id' not in session: return jsonify({'success':False}),401
    data = request.json
    result = data.get('result')
    if result not in ('Selected','Rejected','Pending'):
        return jsonify({'success':False,'message':'Invalid result'})
    conn = get_db()
    conn.execute('UPDATE applications SET result=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',
                 (result, result if result!='Pending' else 'Applied', app_id))
    conn.commit(); conn.close()
    return jsonify({'success':True,'message':f'Marked as {result}'})

@app.route('/api/admin/applications/<int:app_id>/interview', methods=['PUT'])
def set_interview_date(app_id):
    if 'admin_id' not in session: return jsonify({'success':False}),401
    data = request.json
    conn = get_db()
    conn.execute('UPDATE applications SET interview_date=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',
                 (data.get('interview_date',''), app_id))
    conn.commit(); conn.close()
    return jsonify({'success':True,'message':'Interview date set!'})

@app.route('/api/admin/drives/<int:drive_id>/selected', methods=['GET'])
def get_selected(drive_id):
    if 'admin_id' not in session: return jsonify({'success':False}),401
    conn = get_db()
    rows = conn.execute('''SELECT s.name,s.email,s.phone,s.department,s.year,s.cgpa,
        a.interview_date,a.result,a.applied_at FROM applications a
        JOIN students s ON a.student_id=s.id
        WHERE a.drive_id=? AND a.result='Selected' ORDER BY s.name''',(drive_id,)).fetchall()
    conn.close()
    return jsonify({'success':True,'data':[dict(r) for r in rows]})

@app.route('/api/admin/drives/<int:drive_id>/rejected', methods=['GET'])
def get_rejected(drive_id):
    if 'admin_id' not in session: return jsonify({'success':False}),401
    conn = get_db()
    rows = conn.execute('''SELECT s.name,s.email,s.phone,s.department,s.year,s.cgpa,
        a.result,a.applied_at FROM applications a
        JOIN students s ON a.student_id=s.id
        WHERE a.drive_id=? AND a.result='Rejected' ORDER BY s.name''',(drive_id,)).fetchall()
    conn.close()
    return jsonify({'success':True,'data':[dict(r) for r in rows]})

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    if 'admin_id' not in session: return jsonify({'success':False}),401
    conn = get_db()
    def q(sql): return conn.execute(sql).fetchone()['c']
    data = {
        'total_students':     q('SELECT COUNT(*) as c FROM students'),
        'total_drives':       q('SELECT COUNT(*) as c FROM job_drives'),
        'total_applications': q('SELECT COUNT(*) as c FROM applications'),
        'total_selected':     q("SELECT COUNT(*) as c FROM applications WHERE result='Selected'"),
        'total_rejected':     q("SELECT COUNT(*) as c FROM applications WHERE result='Rejected'"),
    }
    conn.close()
    return jsonify({'success':True,'data':data})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)