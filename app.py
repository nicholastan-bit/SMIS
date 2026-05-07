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
def submit():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Ambil No. KP dari borang (yang telah disahkan di gateway)
        kp = request.form.get('no_kp_pelajar')
        
        # Pastikan data wujud sebelum memproses (Langkah keselamatan tambahan)
        if not kp:
            flash("Ralat: No. KP tidak ditemui.")
            return redirect(url_for('gateway'))

        # Semak jika pelajar sudah wujud dalam pangkalan data
        cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
        existing = cursor.fetchone()

        # Kumpul data dari borang. 
        # Disebabkan anda telah meletakkan 'required' pada HTML, 
        # data ini dijamin ada oleh pelayar web.
        student_data = (
            request.form['nama_pelajar'], 
            request.form['email'], 
            kp,
            request.form['jantina'], 
            request.form['bangsa'], 
            request.form['agama'],
            request.form['tarikh_lahir'], # Format YYYY-MM-DD dari input type="date"
            request.form['alamat_rumah'],
            request.form['telefonNo'], 
            1 if 'warganegara' in request.form else 0,
            request.form['sekolah_tamat'], # Tarikh tamat sekolah
            request.form['masalah_kesihatan'],
            request.form['cara_datang_sekolah'], 
            1 # status_study (Aktif)
        )

        if existing:
            # KEMASKINI rekod sedia ada
            s_id = existing[0]
            update_query = """UPDATE pelajar SET 
                nama_pelajar=%s, email=%s, no_kp_pelajar=%s, jantina=%s, bangsa=%s, agama=%s, 
                tarikh_lahir=%s, alamat_rumah=%s, telefonNo=%s, warganegara=%s, 
                sekolah_tamat=%s, masalah_kesihatan=%s, cara_datang_sekolah=%s, status_study=%s 
                WHERE no_pendaftaran_pelajar=%s"""
            cursor.execute(update_query, student_data + (s_id,))
            flash("Maklumat anda berjaya dikemaskini!")
        else:
            # MASUKKAN rekod baru
            insert_query = """INSERT INTO pelajar 
                (nama_pelajar, email, no_kp_pelajar, jantina, bangsa, agama, tarikh_lahir, alamat_rumah, 
                telefonNo, warganegara, sekolah_tamat, masalah_kesihatan, cara_datang_sekolah, status_study) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(insert_query, student_data)
            flash("Pendaftaran pelajar baru berjaya!")

        conn.commit()

    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    # Kembali ke halaman utama (index) selepas selesai
    return redirect(url_for('index'))

@app.route('/register_guardian')
def guardian_page():
    # Security check: Ensure they entered their KP at the gateway first
    if not session.get('verified_kp'):
        flash("Sila masukkan No. KP anda terlebih dahulu.")
        return redirect(url_for('gateway'))
        
    return render_template('guardian.html')

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
        return redirect(url_for('gateway'))
    return render_template('spm.html') # You will need to create this file

@app.route('/submit_spm', methods=['POST'])
def submit_spm():
    if not session.get('verified_kp'):
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get student ID from session KP
        kp = session.get('verified_kp')
        cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
        student = cursor.fetchone()
        
        if not student:
            flash("Please complete your Personal Profile first.")
            return redirect(url_for('register_page'))
            
        student_id = student[0]

        # Get the lists from the form
        subjects = request.form.getlist('subjek[]')
        other_subjects = request.form.getlist('subjek_lain[]')
        grades = request.form.getlist('gred[]')

        for i in range(len(subjects)):
            # Logic to pick the subject name
            subject_name = subjects[i]
            if subject_name == "LAIN-LAIN" and other_subjects[i]:
                subject_name = other_subjects[i].strip().upper()

            if subject_name and grades[i]:
                # The "Upsert" query
                query = """
                    INSERT INTO spm_hasil (no_pendaftaran_pelajar, subjek, gred) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE gred = VALUES(gred)
                """
                cursor.execute(query, (student_id, subject_name, grades[i]))

        conn.commit()
        flash("SPM results saved/updated successfully!")
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
    
    search_query = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    if search_query:
        query = "SELECT no_pendaftaran_pelajar, nama_pelajar, no_kp_pelajar FROM pelajar WHERE nama_pelajar LIKE %s OR no_kp_pelajar LIKE %s"
        cursor.execute(query, (f"%{search_query}%", f"%{search_query}%"))
    else:
        query = "SELECT no_pendaftaran_pelajar, nama_pelajar, no_kp_pelajar FROM pelajar"
        cursor.execute(query)
        
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