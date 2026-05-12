from flask import Flask, render_template, request, redirect, url_for, session, flash
from db.db_config import db_config
import mysql.connector

app = Flask(__name__)
app.secret_key = 'smis_admin_secret_key'

def get_db_connection():
    return mysql.connector.connect(**db_config)

# --- GATEWAY / ACCESS CONTROL ---

@app.route('/access', methods=['GET', 'POST'])
def gateway():
    """The entry point for students. Verifies KP before allowing registration."""
    if request.method == 'POST':
        kp_input = request.form.get('no_kp')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Check if student already exists
        cursor.execute("SELECT * FROM pelajar WHERE no_kp_pelajar = %s", (kp_input,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()

        # Save KP to session to "unlock" the register page
        session['verified_kp'] = kp_input
        
        if student:
            flash(f"Rekod dijumpai untuk {student['nama_pelajar']}. Anda boleh mengemaskini maklumat.")
            session['existing_data'] = student # Store data to pre-fill form
        else:
            flash("No. KP baru dikesan. Sila lengkapkan pendaftaran.")
            session['existing_data'] = None
            
        return redirect(url_for('index'))
        
    return render_template('gateway.html')

# --- ADMIN AUTHENTICATION ---

@app.route('/adminlogin', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == '12345':
            session['admin_logged'] = True
            session['role'] = 'admin'
            flash("Log masuk admin berjaya!")
            return redirect(url_for('index')) 
        else:
            flash("Username atau Password salah!")
            # This sends them back to the login page to try again
            return redirect(url_for('login')) 
            
    # This handles the 'GET' request (when you click a link to go to the page)
    return render_template('adminlogin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Anda telah log keluar.")
    return redirect(url_for('gateway'))

# --- CORE ROUTES ---

@app.route('/')
def index():
    status = {
        'profil': False,
        'penjaga': False,
        'spm': False
    }
    
    kp = session.get('verified_kp')
    
    if kp:
        conn = get_db_connection()
        # Add buffered=True here to prevent "Unread result found"
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        try:
            # 1. Check Profile (pelajar table)
            cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
            student = cursor.fetchone()
            
            if student:
                status['profil'] = True
                student_id = student['no_pendaftaran_pelajar']
                
                # 2. Check Guardian (penjaga table)
                cursor.execute("SELECT no_kp_penjaga FROM penjaga WHERE no_pendaftaran_pelajar = %s", (student_id,))
                if cursor.fetchone():
                    status['penjaga'] = True
                
                # 3. Check SPM Results
                cursor.execute("SELECT id_spm FROM spm_hasil WHERE no_pendaftaran_pelajar = %s", (student_id,))
                if cursor.fetchone():
                    status['spm'] = True
        finally:
            cursor.close()
            conn.close()

    return render_template('index.html', completion_status=status)

@app.route('/register')
def register_page():
    # SECURITY: If not admin and haven't verified KP, boot to gateway
    if not session.get('admin_logged') and not session.get('verified_kp'):
        flash("Sila masukkan No. KP anda terlebih dahulu.")
        return redirect(url_for('gateway'))
        
    # Pass existing data (if any) to the template for auto-filling
    data = session.get('existing_data')
    return render_template('register.html', student=data, verified_kp=session.get('verified_kp'))

@app.route('/submit', methods=['POST'])
def submit_registration():
    if not session.get('verified_kp'):
        return redirect(url_for('gateway'))

    # Retrieve form data
    data = (
        request.form.get('nama_pelajar'),
        request.form.get('email'),
        request.form.get('no_kp_pelajar'),
        request.form.get('jantina'),
        request.form.get('bangsa'),
        request.form.get('agama'), 
        request.form.get('tarikh_lahir'),
        request.form.get('alamat_rumah'),
        request.form.get('telefonNo'),
        request.form.get('warganegara'),
        request.form.get('sekolah_tamat'),
        request.form.get('masalah_kesihatan'),
        request.form.get('cara_datang_sekolah')
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check for update vs new insert
        cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (data[2],))
        existing = cursor.fetchone()

        if existing:
            query = """UPDATE pelajar SET nama_pelajar=%s, email=%s, jantina=%s, bangsa=%s, agama=%s, 
                       tarikh_lahir=%s, alamat_rumah=%s, telefonNo=%s, warganegara=%s, sekolah_tamat=%s, 
                       masalah_kesihatan=%s, cara_datang_sekolah=%s WHERE no_kp_pelajar=%s"""
            # Reorder params for UPDATE: name, email, jantina, bangsa, agama, dob, addr, tel, citizen, school, health, transport, KP
            params = (data[0], data[1], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11], data[12], data[2])
            cursor.execute(query, params)
        else:
            query = """INSERT INTO pelajar (nama_pelajar, email, no_kp_pelajar, jantina, bangsa, agama, 
                       tarikh_lahir, alamat_rumah, telefonNo, warganegara, sekolah_tamat, masalah_kesihatan, 
                       cara_datang_sekolah, status_study) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)"""
            cursor.execute(query, data)

        conn.commit()
        flash("Registration saved successfully!")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
        flash("An error occurred while saving.")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('view_own_profile'))

@app.route('/register_guardian')
def guardian_page():
    if not session.get('verified_kp'):
        flash("Sila masukkan No. KP anda terlebih dahulu.")
        return redirect(url_for('gateway'))
        
    kp = session.get('verified_kp')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch existing guardians
    cursor.execute("""
        SELECT g.* FROM penjaga g 
        JOIN pelajar p ON g.no_pendaftaran_pelajar = p.no_pendaftaran_pelajar 
        WHERE p.no_kp_pelajar = %s""", (kp,))
    existing_guardians = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Pass guardians to the template
    return render_template('guardian.html', existing_guardians=existing_guardians)

@app.route('/submit_guardians', methods=['POST'])
def submit_guardians():
    if not session.get('verified_kp'):
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Get the student ID using the verified KP
        kp = session.get('verified_kp')
        cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
        student = cursor.fetchone()
        
        if not student:
            flash("Sila lengkapkan pendaftaran pelajar terlebih dahulu.")
            return redirect(url_for('register_page'))
            
        student_id = student[0]

        cursor.execute("DELETE FROM penjaga WHERE no_pendaftaran_pelajar = %s", (student_id,))
        
        # 2. Extract lists from the form
        names = request.form.getlist('g_nama_penjaga[]')
        kps = request.form.getlist('g_no_kp_penjaga[]')
        relationships = request.form.getlist('g_hubungan[]')
        jobs = request.form.getlist('g_pekerjaan[]')
        incomes = request.form.getlist('g_pendapatan[]')
        addresses = request.form.getlist('g_alamat_kerja[]')

        # 3. Insert each guardian
        for i in range(len(names)):
            if names[i]: # Only insert if name is filled
                query = """INSERT INTO penjaga 
                    (no_pendaftaran_pelajar, nama_penjaga, no_kp_penjaga, penjaga, pekerjaan, pendapatan, alamat_tempat_kerja) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(query, (student_id, names[i], kps[i], relationships[i], jobs[i], incomes[i], addresses[i]))

        conn.commit()
        flash("Maklumat penjaga berjaya disimpan!")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

@app.route('/register_spm')
def spm_page():
    if not session.get('verified_kp'):
        flash("Sila masukkan No. KP anda terlebih dahulu.")
        return redirect(url_for('gateway'))
        
    kp = session.get('verified_kp')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch existing SPM results
    cursor.execute("""
        SELECT s.* FROM spm_hasil s 
        JOIN pelajar p ON s.no_pendaftaran_pelajar = p.no_pendaftaran_pelajar 
        WHERE p.no_kp_pelajar = %s""", (kp,))
    existing_spm = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('spm.html', existing_spm=existing_spm)

@app.route('/submit_spm', methods=['POST'])
def submit_spm():
    if not session.get('verified_kp'):
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Get student ID
        kp = session.get('verified_kp')
        cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
        student = cursor.fetchone()
        
        if not student:
            flash("Please complete your Personal Profile first.")
            return redirect(url_for('register_page'))
            
        student_id = student[0]

        # --- THE FIX STARTS HERE ---
        # 2. Delete ALL existing SPM records for this student first
        # This ensures that if a row was removed from the HTML, it's also gone from the DB.
        cursor.execute("DELETE FROM spm_hasil WHERE no_pendaftaran_pelajar = %s", (student_id,))
        # --- THE FIX ENDS HERE ---

        # 3. Get the lists from the form
        subjects = request.form.getlist('subjek[]')
        other_subjects = request.form.getlist('subjek_lain[]')
        grades = request.form.getlist('gred[]')

        for i in range(len(subjects)):
            subject_name = subjects[i]
            # Use the "Other" text if LAIN-LAIN is selected
            if subject_name == "LAIN-LAIN" and i < len(other_subjects) and other_subjects[i]:
                subject_name = other_subjects[i].strip().upper()

            if subject_name and grades[i]:
                # We can use a simple INSERT now since we cleared the old data
                query = """
                    INSERT INTO spm_hasil (no_pendaftaran_pelajar, subjek, gred) 
                    VALUES (%s, %s, %s)
                """
                cursor.execute(query, (student_id, subject_name, grades[i]))

        conn.commit()
        flash("Keputusan SPM berjaya dikemaskini!")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

@app.route('/profile')
def view_own_profile():
    if not session.get('verified_kp'):
        flash("Sila masukkan No. KP anda terlebih dahulu.")
        return redirect(url_for('gateway'))

    kp = session.get('verified_kp')
    conn = get_db_connection()
    # Using buffered cursor to handle multiple consecutive queries
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    try:
        # 1. Fetch Student Info
        cursor.execute("SELECT * FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
        student = cursor.fetchone()
        
        if not student:
            flash("Profil tidak ditemui. Sila lengkapkan pendaftaran.")
            return redirect(url_for('register_page'))

        s_id = student['no_pendaftaran_pelajar']

        # 2. Fetch All Guardians
        cursor.execute("SELECT * FROM penjaga WHERE no_pendaftaran_pelajar = %s", (s_id,))
        guardians = cursor.fetchall()

        # 3. Fetch SPM Results
        cursor.execute("SELECT * FROM spm_hasil WHERE no_pendaftaran_pelajar = %s", (s_id,))
        spm_results = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template('profile.html', student=student, guardians=guardians, spm=spm_results)

@app.route('/students_list')
def view_students():
    if not session.get('admin_logged'):
        flash("Admin access only.")
        return redirect(url_for('login'))
    
    # Get all filter arguments
    search_query = request.args.get('search', '')
    gender = request.args.get('gender', '')
    race = request.args.get('race', '')
    religion = request.args.get('religion', '')
    transport = request.args.get('transport', '')
    citizen = request.args.get('citizen', '')
    min_income = request.args.get('min_income', '')
    max_income = request.args.get('max_income', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    # Base query with subqueries for calculated fields
    query = """
        SELECT p.*,
               (SELECT SUM(pendapatan) FROM penjaga WHERE no_pendaftaran_pelajar = p.no_pendaftaran_pelajar) as total_income,
               (SELECT COUNT(*) FROM spm_hasil WHERE no_pendaftaran_pelajar = p.no_pendaftaran_pelajar 
                AND gred IN ('A+', 'A', 'A-')) as total_as
        FROM pelajar p
        WHERE 1=1
    """
    params = []

    # Apply filters to the core 'pelajar' table
    if search_query:
        query += " AND (p.nama_pelajar LIKE %s OR p.no_kp_pelajar LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    
    if gender:
        query += " AND p.jantina = %s"
        params.append(gender)

    if race:
        query += " AND p.bangsa = %s"
        params.append(race)

    if religion:
        query += " AND p.agama = %s"
        params.append(religion)

    if transport:
        query += " AND p.cara_datang_sekolah = %s"
        params.append(transport)

    if citizen != '' and citizen is not None:
        query += " AND p.warganegara = %s"
        params.append(int(citizen))

    # Wrap in outer query to filter by calculated total_income
    full_query = f"SELECT * FROM ({query}) AS student_records WHERE 1=1"
    
    filter_params = []
    if min_income:
        full_query += " AND total_income >= %s"
        filter_params.append(float(min_income))
    if max_income:
        full_query += " AND total_income <= %s"
        filter_params.append(float(max_income))

    cursor.execute(full_query, tuple(params + filter_params))
    students = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('students_list.html', students=students)

@app.route('/admin/view_student/<int:student_id>')
def admin_view_profile(student_id):
    if not session.get('admin_logged'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    try:
        # Fetch Student
        cursor.execute("SELECT * FROM pelajar WHERE no_pendaftaran_pelajar = %s", (student_id,))
        student = cursor.fetchone()
        
        # Fetch Guardians
        cursor.execute("SELECT * FROM penjaga WHERE no_pendaftaran_pelajar = %s", (student_id,))
        guardians = cursor.fetchall()

        # Fetch SPM
        cursor.execute("SELECT * FROM spm_hasil WHERE no_pendaftaran_pelajar = %s", (student_id,))
        spm_results = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    # Reuse the profile.html template!
    return render_template('profile.html', student=student, guardians=guardians, spm=spm_results, is_admin=True)

# Tambahkan route ini di dalam app.py

@app.route('/admin/update_status/<int:student_id>', methods=['POST'])
def update_status(student_id):
    # Security: Verify admin session
    if not session.get('admin_logged'):
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    new_status = request.form.get('new_status')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update the status_study column in the database
        query = "UPDATE pelajar SET status_study = %s WHERE no_pendaftaran_pelajar = %s"
        cursor.execute(query, (new_status, student_id))
        conn.commit()
        flash("Student status updated successfully!")
    except Exception as e:
        conn.rollback()
        flash(f"Error updating status: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    # Redirect back to the profile view
    return redirect(url_for('admin_view_profile', student_id=student_id))

@app.route('/student/<int:student_id>')
def view_profile(student_id):
    if not session.get('admin_logged'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT p.*, g.* FROM pelajar p LEFT JOIN penjaga g ON p.no_pendaftaran_pelajar = g.no_pendaftaran_pelajar WHERE p.no_pendaftaran_pelajar = %s"
    cursor.execute(query, (student_id,))
    student_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if student_data:
        return render_template('profile.html', student=student_data)
    flash("Pelajar tidak dijumpai.")
    return redirect(url_for('view_students'))

if __name__ == '__main__':
    app.run(debug=True)