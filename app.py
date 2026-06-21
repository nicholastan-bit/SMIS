from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from db.db_config import db_config
import mysql.connector
import os
import json
import csv
import io
import re
from werkzeug.utils import secure_filename
from datetime import date

LIMITS_FILE = 'limits.json'

PACKAGE_LIMITS = {
    'BK': 60, 'BK1': 15, 'BK2': 15, 'BK3': 15, 'BK4': 15,
    'FK': 60, 'FK1': 20, 'FK2': 20, 'FK3': 20,
    'CK': 20, 'CK1': 20,
    'CV': 30, 'CV1': 30,
    'AP': 120
    
}
DEFAULT_LIMIT = 40

def get_limits():
    # If the file doesn't exist, create it with your default dictionary
    if not os.path.exists(LIMITS_FILE):
        default_limits = PACKAGE_LIMITS
        with open(LIMITS_FILE, 'w') as f:
            json.dump(default_limits, f)
        return default_limits
    
    with open(LIMITS_FILE, 'r') as f:
        return json.load(f)

def save_limits(limits_dict):
    with open(LIMITS_FILE, 'w') as f:
        json.dump(limits_dict, f, indent=4)

def check_activity_limit(unit_id, unit_name, unit_type):
    # Determine the prefix based on type
    prefix = ""
    if unit_type == 'Kelab': prefix = "KK_"
    elif unit_type == 'Badan Beruniform': prefix = "UB_"
    elif unit_type == 'Sukan dan Permainan': prefix = "SK_"
    
    full_key = f"{prefix}{unit_name}" # This now matches your generated key
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as count FROM KokurikulumPelajar WHERE unit_id = %s", (unit_id,))
    current_count = cursor.fetchone()['count']
    cursor.close()
    conn.close()
    
    limits = get_limits()
    # Use the full_key to look up the limit
    limit = limits.get(full_key, 60) 
    
    return current_count < limit

app = Flask(__name__)
app.secret_key = 'smis_admin_secret_key'

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Tambah laluan folder baru untuk dokumen tambahan di bawah konfigurasi sedia ada
UPLOAD_FOLDER_SPM = os.path.join(app.root_path, 'static', 'uploads', 'spm_slips')
UPLOAD_FOLDER_DOCS = os.path.join(app.root_path, 'static', 'uploads', 'student_docs')

# Add this line to your existing configuration block
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_SPM  # <--- ADD THIS LINE
app.config['UPLOAD_FOLDER_SPM'] = UPLOAD_FOLDER_SPM
app.config['UPLOAD_FOLDER_DOCS'] = UPLOAD_FOLDER_DOCS
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# Pastikan kedua-dua folder wujud di dalam direktori
os.makedirs(UPLOAD_FOLDER_SPM, exist_ok=True)   
os.makedirs(UPLOAD_FOLDER_DOCS, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'png', 'jpg', 'jpeg'}

def is_form_enabled(form_id):
    conn = get_db_connection() # Use your defined helper
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("SELECT is_enabled FROM form_settings WHERE form_id = %s", (form_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    # Returns True if enabled, False otherwise
    return bool(result['is_enabled']) if result else False

@app.route('/access', methods=['GET', 'POST'])
def gateway():
    """The entry point for students. Verifies KP before allowing registration."""
    if request.method == 'POST':
        kp_input = request.form.get('no_kp')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        # Check if student already exists
        cursor.execute("SELECT * FROM pelajar WHERE no_kp_pelajar = %s", (kp_input,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()

        # Save KP to session to "unlock" the register page
        session['verified_kp'] = kp_input
        
        if student:
            flash(f"Rekod dijumpai untuk {student['nama_pelajar']}. Hubungi guru bertugas untuk mengemaskini maklumat.")
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
        
        if username == "admin" and password == "2pi8sndlo47HIjwne726p": # (or whatever your admin check is)
            session['role'] = 'admin'
            session['verified_kp'] = 'ADMIN' # Standardizes administrative privilege sessions
            flash("Selamat Datang Pentadbir Sistem!", "success")
    
            # Redirects safely to your main index dashboard page (index.html)
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
    if session.get('role') == 'admin':
        return render_template('admin_dashboard.html')
        
    kp = session.get('verified_kp')
    
    completion_status = {
        'profil': False,
        'spm': False,
        'tambahan': False,
        'pakej': False,
        'penjaga': False, # Added key
        'koku': False,
    }
    package_class = None
    className = None
    
    if kp:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Fetch student details (includes joining for ID lookup efficiency)
        cursor.execute("""
            SELECT bil_kemasukan, nama_pelajar, surat_tawaran_path, ic_photo_path, id_pakej, kelas 
            FROM pelajar WHERE no_kp_pelajar = %s
        """, (kp,))
        student = cursor.fetchone()
        
        if student:
            student_id = student['bil_kemasukan']
            completion_status['profil'] = True
            
            # 1. Check SPM
            cursor.execute("SELECT COUNT(*) as total FROM spm_hasil WHERE bil_kemasukan = %s", (student_id,))
            spm_count = cursor.fetchone()
            if spm_count and spm_count['total'] > 0:
                completion_status['spm'] = True
                
            # 2. Check Penjaga (New Logic)
            cursor.execute("SELECT COUNT(*) as total FROM penjaga WHERE bil_kemasukan = %s", (student_id,))
            penjaga_count = cursor.fetchone()
            if penjaga_count and penjaga_count['total'] > 0:
                completion_status['penjaga'] = True
            
            # 3. Step 3 (Tambahan)
            if student['surat_tawaran_path'] and student['ic_photo_path']:
                completion_status['tambahan'] = True
                
            bil_kemasukan = student['bil_kemasukan']

            # 2. PREVENTION CHECK: Has the student already registered?
            cursor.execute("SELECT COUNT(*) as registered_count FROM KokurikulumPelajar WHERE bil_kemasukan = %s", (bil_kemasukan,))
            if cursor.fetchone()['registered_count'] > 0:
                completion_status['koku'] = True
            
            if student['id_pakej'] is not None and student['id_pakej'] != 0:
                completion_status['pakej'] = True

            if student['kelas'] is not None:
                className = student['kelas']

            cursor.execute("SELECT kod_pakej as name FROM pakej WHERE id_pakej = %s", (student['id_pakej'],))
            pakej_name = cursor.fetchone()
            package_class = pakej_name
            
        cursor.close()
        conn.close()
        
    return render_template('index.html', completion_status=completion_status, pkg_cls=package_class, clsName=className)

@app.route('/register')
def register_page():
    if not is_form_enabled('profil_form'):
        flash("Borang ini sedang ditutup oleh pentadbir.", "danger")
        return redirect(url_for('index'))
    
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))
        
    # Check if student profile already exists in the 'pelajar' table
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True) # Changed to dictionary=True, buffered=True
    cursor.execute("SELECT * FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()

    # Your original return remains unchanged
    return render_template('register.html', verified_kp=kp, student=None)

@app.route('/submit', methods=['POST'])
def submit_registration():
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # The True UPSERT Query
    query = """
        INSERT INTO pelajar (
            nama_pelajar, email, no_kp_pelajar, jantina, bangsa, agama, 
            tarikh_lahir, alamat_rumah, telefonNo, sekolah_tamat, masalah_kesihatan, 
            cara_datang_sekolah, tempat_lahir, no_surat_beranak, masalah_penglihatan, 
            aliran_ditawar, status_oku, kelas, status_study, tarikh_pendaftaran
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
        ON DUPLICATE KEY UPDATE 
            nama_pelajar=VALUES(nama_pelajar), email=VALUES(email), jantina=VALUES(jantina),
            bangsa=VALUES(bangsa), agama=VALUES(agama), tarikh_lahir=VALUES(tarikh_lahir),
            alamat_rumah=VALUES(alamat_rumah), telefonNo=VALUES(telefonNo), 
            sekolah_tamat=VALUES(sekolah_tamat), masalah_kesihatan=VALUES(masalah_kesihatan),
            cara_datang_sekolah=VALUES(cara_datang_sekolah), tempat_lahir=VALUES(tempat_lahir),
            no_surat_beranak=VALUES(no_surat_beranak), masalah_penglihatan=VALUES(masalah_penglihatan),
            aliran_ditawar=VALUES(aliran_ditawar), status_oku=VALUES(status_oku), kelas=VALUES(kelas)
    """

    today = date.today().strftime('%Y-%m-%d')

    raw_nama = request.form.get('nama_pelajar', '')
    nama_pelajar_upper = raw_nama.upper().strip() # .strip() removes accidental leading/trailing spaces

    sekolah_tamat = request.form.get('sekolah_tamat')
    if not sekolah_tamat:
        sekolah_tamat = None

    data = (
        nama_pelajar_upper, request.form.get('email'), kp,
        request.form.get('jantina'), request.form.get('bangsa'), request.form.get('agama'),
        request.form.get('tarikh_lahir'), request.form.get('alamat_rumah'), request.form.get('telefonNo'),
        sekolah_tamat, request.form.get('masalah_kesihatan'),
        request.form.get('cara_datang_sekolah'), request.form.get('tempat_lahir'),
        request.form.get('no_surat_beranak'), request.form.get('masalah_penglihatan'),
        request.form.get('aliran_ditawar'), request.form.get('status_oku'), request.form.get('kelas'),
        today 
    )

    try:
        cursor.execute(query, data)
        conn.commit()
        flash("Maklumat profil berjaya disimpan.", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f"Ralat pangkalan data: {err}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

# --- MAKLUMAT TAMBAHAN ROUTES ---

@app.route('/additional', methods=['GET'])
def additional_page():
    if not is_form_enabled('tambahan_form'):
        flash("Borang ini sedang ditutup oleh pentadbir.", "danger")
        return redirect(url_for('index'))
    
    """Renders the additional details form ONLY if it hasn't been completed yet,
    explicitly passing down the verified identity card number to prevent empty form fields.
    """
    kp = session.get('verified_kp')
    if not kp:
        flash("Sila masukkan No. KP anda terlebih dahulu.", "danger")
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    # Check if student exists and see if fields are already filled
    cursor.execute("""
        SELECT bil_kemasukan, tempat_lahir, no_surat_beranak, masalah_penglihatan 
        FROM pelajar WHERE no_kp_pelajar = %s
    """, (kp,))
    student = cursor.fetchone()
    
    cursor.close()
    conn.close()

    # FIX: Explicitly send both student record AND verified_kp down to the HTML template
    return render_template('additional.html', student=student, verified_kp=kp)


@app.route('/submit_additional', methods=['POST'])
def submit_additional():
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    # 1. Fetch current record
    cursor.execute("SELECT bil_kemasukan FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        flash("Sila lengkapkan Profil Pendaftaran utama terlebih dahulu.", "danger")
        return redirect(url_for('index'))

    student_id = student['bil_kemasukan']

    # 2. Handle File Uploads
    file_ic = request.files.get('ic_photo')
    file_offer = request.files.get('surat_tawaran')
    
    # We only update the DB if a file was actually provided
    try:
        update_query = "UPDATE pelajar SET "
        updates = []
        params = []

        if file_ic and file_ic.filename != '':
            if allowed_file(file_ic.filename):
                ext = file_ic.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"IC_{student_id}.{ext}")
                file_ic.save(os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename))
                updates.append("ic_photo_path = %s")
                params.append(filename)

        if file_offer and file_offer.filename != '':
            if allowed_file(file_offer.filename):
                ext = file_offer.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"OFFER_{student_id}.{ext}")
                file_offer.save(os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename))
                updates.append("surat_tawaran_path = %s")
                params.append(filename)

        if updates:
            update_query += ", ".join(updates) + " WHERE no_kp_pelajar = %s"
            params.append(kp)
            cursor.execute(update_query, tuple(params))
            conn.commit()
            flash("Dokumen sokongan anda berjaya dikemaskini!", "success")
        else:
            flash("Tiada perubahan dokumen dikesan.", "info")

    except mysql.connector.Error as err:
        conn.rollback()
        flash(f"Ralat Sistem: {err}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

@app.route('/register_guardian')
def guardian_page():
    if not is_form_enabled('penjaga_form'):
        flash("Borang ini sedang ditutup oleh pentadbir.", "danger")
        return redirect(url_for('index'))
    
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 1. Fetch student base details
    cursor.execute("""
        SELECT bil_kemasukan, nama_pelajar, no_surat_beranak, masalah_penglihatan, id_pakej 
        FROM pelajar WHERE no_kp_pelajar = %s
    """, (kp,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        flash("Sila lengkapkan Profil Pendaftaran utama terlebih dahulu.", "danger")
        return redirect(url_for('index'))
    
    if not student.get('nama_pelajar') or not student.get('no_surat_beranak') or not student.get('masalah_penglihatan'):
        cursor.close()
        conn.close()
        flash("Akses Disekat: Sila lengkapkan Profil dan Borang Dokumen Pelajar.", "danger")
        return redirect(url_for('additional_page'))

    cursor.close()
    conn.close()
        
    # Your original return remains unchanged
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
        cursor.execute("SELECT bil_kemasukan FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
        student = cursor.fetchone()
        
        if not student:
            flash("Sila lengkapkan pendaftaran pelajar terlebih dahulu.")
            return redirect(url_for('register_page'))
            
        student_id = student[0]

        cursor.execute("DELETE FROM penjaga WHERE bil_kemasukan = %s", (student_id,))
        
        # 2. Extract lists from the form (Termasuk g_no_telefon[])
        names = request.form.getlist('g_nama_penjaga[]')
        kps = request.form.getlist('g_no_kp_penjaga[]')
        relationships = request.form.getlist('g_hubungan[]')
        telephones = request.form.getlist('g_no_telefon[]')  # <--- BAHARU
        jobs = request.form.getlist('g_pekerjaan[]')
        incomes = request.form.getlist('g_pendapatan[]')
        addresses = request.form.getlist('g_alamat_kerja[]')

        # 3. Insert each guardian
        for i in range(len(names)):
            if names[i]: # Only insert if name is filled
                # PENTING: Lajur no_telefon dan satu lagi penanda %s ditambah di sini
                query = """INSERT INTO penjaga 
                    (bil_kemasukan, nama_penjaga, no_kp_penjaga, hubungan, no_telefon, pekerjaan, pendapatan, alamat_tempat_kerja) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(query, (student_id, names[i], kps[i], relationships[i], telephones[i], jobs[i], incomes[i], addresses[i]))

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
    if not is_form_enabled('spm_form'):
        flash("Borang ini sedang ditutup oleh pentadbir.", "danger")
        return redirect(url_for('index'))

    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 1. Fetch student base details
    cursor.execute("""
        SELECT bil_kemasukan, tempat_lahir, no_surat_beranak, masalah_penglihatan, id_pakej 
        FROM pelajar WHERE no_kp_pelajar = %s
    """, (kp,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        flash("Sila lengkapkan Profil Pendaftaran utama terlebih dahulu.", "danger")
        return redirect(url_for('index'))
    
    cursor.close()
    conn.close()
        
    return render_template('spm.html')

@app.route('/submit_spm', methods=['POST'])
def submit_spm():
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve internal index identifier
    cursor.execute("SELECT bil_kemasukan FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    student_record = cursor.fetchone()

    if not student_record:
        cursor.close()
        conn.close()
        flash("Sila lengkapkan Profil Pelajar terlebih dahulu.", "danger")
        return redirect(url_for('index'))

    student_id = student_record[0]

    # --- FILE UPLOAD PROCESSING ---
    secure_new_name = None
    if 'spm_slip' in request.files:
        file = request.files['spm_slip']
        if file and file.filename != '' and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            
            # Format filename bound to student KP
            secure_new_name = f"{kp}_slip.{file_ext}"
            # Use UPLOAD_FOLDER_SPM specifically
            save_path = os.path.join(app.config['UPLOAD_FOLDER_SPM'], secure_new_name)
            file.save(save_path)

            # Update the pelajar table with the filename
            update_query = """
                UPDATE pelajar 
                SET spm_slip_filename = %s 
                WHERE bil_kemasukan = %s
            """
            cursor.execute(update_query, (secure_new_name, student_id))

    # --- ACADEMIC DATA PROCESSING ---
    subjek_list = request.form.getlist('subjek[]')
    gred_list = request.form.getlist('gred[]')

    try:
        # Purge existing stale academic rows
        cursor.execute("DELETE FROM spm_hasil WHERE bil_kemasukan = %s", (student_id,))

        # Batch insert operation
        for subjek, gred in zip(subjek_list, gred_list):
            if subjek.strip() != "" and gred.strip() != "":
                cursor.execute(
                    "INSERT INTO spm_hasil (bil_kemasukan, subjek, gred) VALUES (%s, %s, %s)",
                    (student_id, subjek.upper(), gred.upper())
                )

        conn.commit()
        flash("Keputusan SPM anda berjaya disimpan!", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Ralat Operasi Akademik: {err}")
        flash("Gagal mengemaskini maklumat akademik.", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

# --- PILIHAN PAKEJ ROUTES ---

@app.route('/package', methods=['GET'])
def package_page():
    if not is_form_enabled('pakej_form'):
        flash("Borang ini sedang ditutup oleh pentadbir.", "danger")
        return redirect(url_for('index'))

    kp = session.get('verified_kp')
    if not kp:
        flash("Sila masukkan No. KP anda terlebih dahulu.", "danger")
        return redirect(url_for('gateway'))

    # 1. Define Capacity Limits
    DECOY_IDS = [1, 6, 8, 12, 14, 16, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Fetch student details
    cursor.execute("""
        SELECT bil_kemasukan, tempat_lahir, no_surat_beranak, masalah_penglihatan, id_pakej, aliran_ditawar 
        FROM pelajar WHERE no_kp_pelajar = %s
    """, (kp,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        flash("Rekod pelajar tidak dijumpai.", "danger")
        return redirect(url_for('index'))

    cursor.execute("SELECT COUNT(*) as count FROM spm_hasil WHERE bil_kemasukan = %s", (student['bil_kemasukan'],))
    spm_check = cursor.fetchone()
    
    if spm_check['count'] == 0:
        cursor.close()
        conn.close()
        flash("Akses Disekat: Sila lengkapkan keputusan SPM anda terlebih dahulu.", "danger")
        return redirect(url_for('index'))

    # Fetch current enrollment counts for all packages to enforce limits
    cursor.execute("SELECT id_pakej, COUNT(*) as current_count FROM pelajar WHERE id_pakej IS NOT NULL GROUP BY id_pakej")
    enrollment_data = {row['id_pakej']: row['current_count'] for row in cursor.fetchall()}

    # Check for student existence and required docs
    if not student.get('tempat_lahir') or not student.get('no_surat_beranak') or not student.get('masalah_penglihatan'):
        cursor.close()
        conn.close()
        flash("Akses Disekat: Sila lengkapkan Profil dan Borang Dokumen Pelajar.", "danger")
        return redirect(url_for('additional_page'))
    
    if student.get('id_pakej') is not None and student.get('id_pakej') != 0:
        cursor.close()
        conn.close()
        flash("Anda telah membuat pemilihan pakej. Sila hubungi pentadbir untuk sebarang perubahan.", "info")
        return redirect(url_for('index'))

    # Fetch specialized eligibility
    cursor.execute("SELECT subjek_khas FROM pelajar_eligibility WHERE no_kp_pelajar = %s", (kp,))
    eligible_subjects = [r['subjek_khas'] for r in cursor.fetchall()]
    is_eligible_syariah = 'SYARIAH' in eligible_subjects
    is_eligible_sukan = 'SAINS SUKAN' in eligible_subjects

    # 2. Fetch SPM grades
    cursor.execute("SELECT subjek, gred FROM spm_hasil WHERE bil_kemasukan = %s", (student['bil_kemasukan'],))
    spm_results = cursor.fetchall()
    grades = {str(row['subjek']).strip().upper(): str(row['gred']).strip().upper() for row in spm_results}

    def pass_c(subject_name):
        return grades.get(subject_name) in ['A+', 'A', 'A-', 'B+', 'B', 'C+', 'C']

    has_math_c = pass_c('MATEMATIK')
    has_science_c = pass_c('SAINS')
    eyes_good = (str(student['masalah_penglihatan']).strip().upper() == 'TIDAK')

    # 3. Stream Filtering
    if student['aliran_ditawar'] == 'SAINS':
        allowed_prefixes = ['BK', 'CK', 'FK']
    else:
        allowed_prefixes = ['AH', 'AP', 'BP', 'BS', 'BY', 'GB', 'GP', 'HT', 'HP', 'HY', 'CV', 'VB', 'VS']
        if not (has_math_c and has_science_c):
            allowed_prefixes = [p for p in allowed_prefixes if p not in ['BK', 'CK', 'FK', 'CV']]
        if not eyes_good:
            allowed_prefixes = [p for p in allowed_prefixes if p not in ['CV', 'VB', 'VS']]
        if not is_eligible_syariah:
            allowed_prefixes = [p for p in allowed_prefixes if p not in ['BY', 'HY']]
        if not is_eligible_sukan:
            allowed_prefixes = [p for p in allowed_prefixes if p not in ['BS', 'VS']]

    # Fetch packages
    format_strings = ','.join(['%s'] * len(DECOY_IDS))
    cursor.execute("""
    SELECT p.id_pakej, p.kod_pakej, p.aliran, p.semester, s.nama_subjek 
    FROM pakej p
    LEFT JOIN pakej_subjek ps ON p.id_pakej = ps.id_pakej
    LEFT JOIN subjek_stpm s ON ps.id_subjek = s.id_subjek
    WHERE p.status_aktif = 1
    """)
    all_rows = cursor.fetchall()

    # ... inside your package_page function, after cursor.fetchall() ...
    current_limits = get_limits()
    cursor.execute("SELECT id_pakej, kod_pakej FROM pakej")
    pakej_mapping = {row['id_pakej']: row['kod_pakej'] for row in cursor.fetchall()}

    group_counts = {}
    for pid, count in enrollment_data.items():
        kod = pakej_mapping.get(pid, '')
        prefix = ''.join([i for i in kod if not i.isdigit()])
        group_counts[prefix] = group_counts.get(prefix, 0) + count

    # Build response map
    packages_map = {}
    for row in all_rows:
        if '/' in row['kod_pakej']: continue

        kod = row['kod_pakej']
        prefix = ''.join([i for i in kod if not i.isdigit()])

        # Get Limits
        limit_class = current_limits.get(kod, DEFAULT_LIMIT)
        limit_group = current_limits.get(prefix, 120) 

        # Get Counts
        count_class = enrollment_data.get(row['id_pakej'], 0)
        count_group = group_counts.get(prefix, 0)

        # Eligibility & Capacity logic
        is_allowed = any(kod.startswith(p) for p in allowed_prefixes)
    
        # Check if either individual class OR group total is full
        if is_allowed and count_class < limit_class and count_group < limit_group:
            if kod not in packages_map:
                packages_map[kod] = {
                    'id_pakej': row['id_pakej'], 
                    'kod_pakej': kod, 
                    'aliran': row['aliran'], 
                    'subjek': [], 
                    'kekosongan': min(limit_class - count_class, limit_group - count_group),
                    'had_maksimum': limit_class
                }
            if row['nama_subjek']:
                packages_map[kod]['subjek'].append(row['nama_subjek'])
    
    cursor.close()
    conn.close()

    return render_template('package.html', 
                           packages=list(packages_map.values()), 
                           current_package_id=student['id_pakej'],
                           math_pass=has_math_c,
                           science_pass=has_science_c,
                           eyes_good=eyes_good)

@app.route('/submit_package', methods=['POST'])
def submit_package():
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))

    selected_package_id = request.form.get('pilihan_pakej')
    if not selected_package_id:
        flash("Sila pilih pakej aliran.", "danger")
        return redirect(url_for('package_page'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 1. Fetch package details
    cursor.execute("SELECT kod_pakej FROM pakej WHERE id_pakej = %s", (selected_package_id,))
    pkg = cursor.fetchone()
    
    if not pkg:
        cursor.close()
        conn.close()
        flash("Pakej tidak sah.", "danger")
        return redirect(url_for('package_page'))

    kod_pakej = pkg['kod_pakej']
    current_limits = get_limits() 
    
    
    # 2. Identify the Group Prefix (e.g., BK from BK1)
    prefix = ''.join([i for i in kod_pakej if not i.isdigit()])
    
    # Define limits
    limit_class = current_limits.get(kod_pakej, DEFAULT_LIMIT)
    limit_group = current_limits.get(prefix, 120)

    # 3. Check current counts
    # Count for the specific class
    cursor.execute("SELECT COUNT(*) as count FROM pelajar WHERE id_pakej = %s", (selected_package_id,))
    count_class = cursor.fetchone()['count']
    
    # Count for the whole group (e.g., all BK classes)
    cursor.execute("""
        SELECT COUNT(*) as count FROM pelajar p
        JOIN pakej pk ON p.id_pakej = pk.id_pakej
        WHERE pk.kod_pakej LIKE %s
    """, (f"{prefix}%",))
    count_group = cursor.fetchone()['count']

    # 4. Enforce Limits
    if count_class >= limit_class:
        flash(f"Maaf, kelas {kod_pakej} telah penuh ({count_class}/{limit_class}).", "danger")
        cursor.close(); conn.close()
        return redirect(url_for('package_page'))

    if count_group >= limit_group:
        flash(f"Maaf, kuota keseluruhan bagi kumpulan {prefix} telah penuh ({count_group}/{limit_group}).", "danger")
        cursor.close(); conn.close()
        return redirect(url_for('package_page'))
    
    # 5. Perform Update
    try:
        cursor.execute("UPDATE pelajar SET id_pakej = %s WHERE no_kp_pelajar = %s", (selected_package_id, kp))
        conn.commit()
        flash("Pilihan pakej berjaya didaftarkan!", "success")
    except Exception as err:
        conn.rollback()
        flash(f"Ralat Sistem: {err}", "danger")
    finally:
        cursor.close(); conn.close()

    return redirect(url_for('index'))

@app.route('/kokurikulum', methods=['GET'])
def kokurikulum_page():
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))

    # Get filter from URL (Default to 'Kelab')
    category = request.args.get('type', 'Kelab')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 1. Get student ID
    cursor.execute("SELECT bil_kemasukan FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    student = cursor.fetchone()
    bil_kemasukan = student['bil_kemasukan']

    # 2. PREVENTION CHECK: Has the student already registered?
    cursor.execute("SELECT COUNT(*) as registered_count FROM KokurikulumPelajar WHERE bil_kemasukan = %s", (bil_kemasukan,))
    if cursor.fetchone()['registered_count'] > 0:
        cursor.close()
        conn.close()
        flash("Anda telah mendaftar kokurikulum. Hubungi pentadbir jika perlu membuat perubahan.", "info")
        return redirect(url_for('index'))

    # 1. Get student gender and current units for restriction checks
    cursor.execute("SELECT bil_kemasukan, jantina FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    student = cursor.fetchone()
    
    # 2. Fetch all units for this category
    cursor.execute("SELECT unit_id, activity_name, unit_type FROM UnitKokurikulum WHERE unit_type = %s", (category,))
    units = cursor.fetchall()

    # 3. Get current counts for all units to check capacity
    cursor.execute("SELECT unit_id, COUNT(*) as enrolled FROM KokurikulumPelajar GROUP BY unit_id")
    enrollment_counts = {row['unit_id']: row['enrolled'] for row in cursor.fetchall()}
    
    # Load limits from your JSON
    limits = get_limits()

    # 4. Filter units based on capacity and gender (Logic in template or here)
    # Mapping for gender-restricted items (You can store this in a dictionary)
    gender_restrictions = {
        'PANDU PUTERI MALAYSIA': 'PEREMPUAN',
        'PERGERAKAN PUTERI ISLAM MALAYSIA': 'PEREMPUAN',
        'BOLA JARING': 'PEREMPUAN',
        'FUTSAL': 'LELAKI'
    }

    processed_units = []
    for u in units:
        count = enrollment_counts.get(u['unit_id'], 0)
        
        prefix = ""
        if u['unit_type'] == 'Kelab': prefix = "KK_"
        elif u['unit_type'] == 'Badan Beruniform': prefix = "UB_"
        elif u['unit_type'] == 'Sukan dan Permainan': prefix = "SK_"

        json_key = f"{prefix}{u['activity_name']}"
        limit = limits.get(json_key, 60)
        
        # 2. Add 'enrolled' and 'limit' to the dictionary
        is_full = count >= limit
        
        # Restriction Checks
        gender_match = True
        if u['activity_name'] in gender_restrictions:
            gender_match = (student['jantina'] == gender_restrictions[u['activity_name']])
            
        processed_units.append({
            **u, 
            'is_full': is_full, 
            'allowed': gender_match and not is_full,
            'enrolled': count,
            'limit': limit
        })

    cursor.execute("""
        SELECT uk.unit_id, uk.activity_name, uk.unit_type 
        FROM KokurikulumPelajar kp
        JOIN UnitKokurikulum uk ON kp.unit_id = uk.unit_id
        WHERE kp.bil_kemasukan = %s
    """, (student['bil_kemasukan'],))
    my_units = cursor.fetchall()
    
    # Check if all 3 categories are filled
    categories_filled = {u['unit_type'] for u in my_units}
    can_finish = len(categories_filled) == 3

    cursor.close()
    conn.close()

    return render_template('kokurikulum.html', 
                           units=processed_units, 
                           my_units=my_units, 
                           can_finish=can_finish,
                           selected_type=category)

@app.route('/temp_add_koku', methods=['POST'])
def temp_add_koku():
    if 'temp_units' not in session:
        session['temp_units'] = []
    
    unit_id = int(request.form.get('unit_id'))
    unit_name = request.form.get('unit_name')
    unit_type = request.form.get('unit_type')
    
    # 1. Overwrite Logic:
    # Filter the list to keep everything EXCEPT the category we are currently adding.
    # This automatically removes the 'old' selection for this category.
    session['temp_units'] = [u for u in session['temp_units'] if u['unit_type'] != unit_type]
    
    # 2. Add the new selection:
    # Now that we've cleared any existing unit of this type, we can safely add the new one.
    session['temp_units'].append({
        'unit_id': unit_id, 
        'name': unit_name, 
        'unit_type': unit_type
    })
    
    session.modified = True
    flash(f"Pilihan untuk {unit_type} telah dikemaskini kepada {unit_name}.", "success")
        
    return redirect(url_for('kokurikulum_page'))

@app.route('/final_submit_koku', methods=['POST'])
def final_submit_koku():
    kp = session.get('verified_kp')

    # 2. Execute and safely fetch
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Using dictionary=True makes access easier
    cursor.execute("SELECT bil_kemasukan FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    result = cursor.fetchone()
    
    if result:
        bil_kemasukan = result['bil_kemasukan']
    else:
        # Handle error: Student not found
        flash("Sesi tamat atau pelajar tidak dijumpai.", "danger")
        return redirect(url_for('gateway'))
    
    # Get current limits and enrollment counts
    limits = get_limits() # Assuming this loads your JSON
    cursor.execute("SELECT unit_id, COUNT(*) as enrolled FROM KokurikulumPelajar GROUP BY unit_id")
    enrollment_data = {row['unit_id']: row['enrolled'] for row in cursor.fetchall()}

    # 1. FINAL SAFETY CHECK: Loop through to verify if any unit became full
    for unit in session.get('temp_units', []):
        unit_id = unit['unit_id']
        cursor.execute("SELECT activity_name FROM UnitKokurikulum WHERE unit_id = %s", (unit_id,))
        unit_name = cursor.fetchone()['activity_name']
        
        current_enrollment = enrollment_data.get(unit_id, 0)
        max_limit = limits.get(unit_name, 60)
        
        if current_enrollment >= max_limit:
            flash(f"Maaf, {unit_name} sudah penuh. Sila pilih unit lain.", "danger")
            conn.close()
            return redirect(url_for('kokurikulum_page'))

    # 2. If all pass, proceed to Insert
    for unit in session.get('temp_units', []):
        cursor.execute("INSERT INTO KokurikulumPelajar (bil_kemasukan, unit_id) VALUES (%s, %s)", 
                       (bil_kemasukan, unit['unit_id']))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Clear the session after saving
    session.pop('temp_units', None)
    flash("Pendaftaran berjaya disimpan!", "success")
    return redirect(url_for('index'))

@app.route('/submit_koku', methods=['POST'])
def submit_koku():
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))

    unit_id = request.form.get('unit_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Get student's bil_kemasukan
    cursor.execute("SELECT bil_kemasukan FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    pelajar = cursor.fetchone()
    bil_kemasukan = pelajar['bil_kemasukan']
    
    # 2. Check: Does student already have 3 units?
    cursor.execute("SELECT COUNT(*) as count FROM KokurikulumPelajar WHERE bil_kemasukan = %s", (bil_kemasukan,))
    current_count = cursor.fetchone()['count']
    
    if current_count >= 3:
        flash("Anda sudah mendaftar 3 unit. Sila batalkan satu jika ingin menukar.", "danger")
        return redirect(url_for('kokurikulum_page'))
    
    cursor.execute("SELECT unit_type FROM UnitKokurikulum WHERE unit_id = %s", (unit_id,))
    new_unit_type = cursor.fetchone()['unit_type']

    # 2. Check if the student already has a unit in that specific category
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM KokurikulumPelajar kp
        JOIN UnitKokurikulum uk ON kp.unit_id = uk.unit_id
        WHERE kp.bil_kemasukan = %s AND uk.unit_type = %s
    """, (bil_kemasukan, new_unit_type))

    already_has_category = cursor.fetchone()['count'] > 0

    if already_has_category:
        flash(f"Anda sudah mendaftar satu unit dalam kategori {new_unit_type}. Sila batalkan unit tersebut jika mahu menukar.", "danger")
        return redirect(url_for('kokurikulum_page'))
    
    # 3. Final safety check: Is the unit already full or already taken?
    try:
        cursor.execute("""
            INSERT INTO KokurikulumPelajar (bil_kemasukan, unit_id) 
            VALUES (%s, %s)
        """, (bil_kemasukan, unit_id))
        conn.commit()
        flash("Berjaya mendaftar aktiviti!", "success")
    except mysql.connector.Error as err:
        flash("Gagal mendaftar. Mungkin anda sudah mendaftar unit ini.", "danger")
        
    cursor.close()
    conn.close()
    return redirect(url_for('kokurikulum_page'))

# =====================================================================
# --- ADMINISTRATIVE CONTROL PANEL MODULES ---
# =====================================================================

@app.route('/admin/students-list')
def admin_view_students_list():
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    sort_filter = request.args.get('sort', '')
    class_filter = request.args.get('class_filter', '')
    pakej_filter = request.args.get('pakej_filter', '')
    status_filter = request.args.get('status_filter', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Fetch choices for dropdowns
    cursor.execute("SELECT id_pakej, kod_pakej FROM pakej ORDER BY kod_pakej")
    all_packages = cursor.fetchall()
    
    cursor.execute("SELECT DISTINCT kelas FROM pelajar WHERE kelas IS NOT NULL ORDER BY kelas")
    all_classes = [r['kelas'] for r in cursor.fetchall()]

    # Base Query
    where_clause = "WHERE 1=1"
    params = []
    
    if search:
        where_clause += " AND (nama_pelajar LIKE %s OR no_kp_pelajar LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    # Updated sort_filter logic (Keep your original logic)
    if sort_filter == 'unassigned':
        where_clause += " AND (p.id_pakej IS NULL OR pk.kod_pakej REGEXP '^[^0-9]+$')"
    elif sort_filter == 'assigned':
        where_clause += " AND pk.kod_pakej IS NOT NULL AND pk.kod_pakej REGEXP '[0-9]'"
    
    # Specific Package Filter
    if pakej_filter:
        where_clause += " AND p.id_pakej = %s"
        params.append(pakej_filter)
        
    if class_filter:
        where_clause += " AND kelas = %s"
        params.append(class_filter.strip())

    if status_filter != '':
        where_clause += " AND status_study = %s"
        params.append(status_filter)

    # 3. Get total count for pagination
    count_query = f"SELECT COUNT(*) as total FROM pelajar p LEFT JOIN pakej pk ON p.id_pakej = pk.id_pakej {where_clause}"
    cursor.execute(count_query, params)
    total_students = cursor.fetchone()['total']
    total_pages = (total_students + per_page - 1) // per_page

    print(f"DEBUG: WHERE clause is: {where_clause}")
    print(f"DEBUG: Params are: {params}")

    # 4. Fetch Paginated Data
    query = f"""
        SELECT p.*, pk.kod_pakej, 
               (SELECT SUM(penjaga.pendapatan) FROM penjaga WHERE penjaga.bil_kemasukan = p.bil_kemasukan) as total_income
        FROM pelajar p 
        LEFT JOIN pakej pk ON p.id_pakej = pk.id_pakej 
        {where_clause}
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, params + [per_page, offset])
    students = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('students_list.html', 
                           students=students, 
                           page=page, 
                           total_pages=total_pages,
                           total_students=total_students,
                           search=search, 
                           sort=sort_filter, 
                           class_filter=class_filter,
                           pakej_filter=pakej_filter,
                           all_packages=all_packages,
                           all_classes=all_classes, 
                           status_filter=status_filter)

@app.route('/admin/export-students')
def admin_export_students():
    # Reuse your existing filter logic
    search = request.args.get('search', '')
    sort_filter = request.args.get('sort', '')
    class_filter = request.args.get('class_filter', '')
    pakej_filter = request.args.get('pakej_filter', '')
    status_filter = request.args.get('status_filter', '')

    conn = None
    cursor = None
    # Base Query
    where_clause = "WHERE 1=1"
    params = []
    
    if search:
        where_clause += " AND (nama_pelajar LIKE %s OR no_kp_pelajar LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    # Updated sort_filter logic (Keep your original logic)
    if sort_filter == 'unassigned':
        where_clause += " AND (p.id_pakej IS NULL OR pk.kod_pakej REGEXP '^[^0-9]+$')"
    elif sort_filter == 'assigned':
        where_clause += " AND pk.kod_pakej IS NOT NULL AND pk.kod_pakej REGEXP '[0-9]'"
    
    # Specific Package Filter
    if pakej_filter:
        where_clause += " AND p.id_pakej = %s"
        params.append(pakej_filter)
        
    if class_filter:
        where_clause += " AND kelas = %s"
        params.append(class_filter.strip())

    if status_filter != '':
        where_clause += " AND status_study = %s"
        params.append(status_filter)

    # Query without LIMIT and OFFSET
    query = f"""
        SELECT p.*, pk.kod_pakej, 
               (SELECT SUM(penjaga.pendapatan) FROM penjaga WHERE penjaga.bil_kemasukan = p.bil_kemasukan) as total_income
        FROM pelajar p 
        LEFT JOIN pakej pk ON p.id_pakej = pk.id_pakej 
        {where_clause}
    """
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    # Generate CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Bil Kemasukan', 'Nama Pelajar', 'No KP', 'Status', 'Kelas', 'Pakej', 'Pendapatan'])
    
    for s in students:
        no_kp = f"'{s['no_kp_pelajar']}" if s['no_kp_pelajar'] else ""
        
        pendapatan = s['total_income'] if s['total_income'] is not None else 0
        
        cw.writerow([
            s['bil_kemasukan'], 
            s['nama_pelajar'], 
            no_kp, # The KP with forced string formatting
            'Aktif' if s['status_study'] else 'Tidak Aktif', 
            s['kelas'] or 'TIADA', 
            s['kod_pakej'] or 'TIADA', 
            pendapatan # The numeric income
        ])
    
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=senarai_pelajar.csv"}
    )

@app.route('/admin/update-student-package', methods=['POST'])
def admin_update_student_package():
    student_id = request.form.get('student_id')
    new_package_id = request.form.get('package_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Update the student's package (set to NULL if empty string is passed)
    if new_package_id == "":
        cursor.execute("UPDATE pelajar SET id_pakej = NULL WHERE bil_kemasukan = %s", (student_id,))
    else:
        cursor.execute("UPDATE pelajar SET id_pakej = %s WHERE bil_kemasukan = %s", (new_package_id, student_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Pakej pelajar telah dikemaskini.", "success")
    # Redirect back to the same page with current filters
    return redirect(request.referrer or url_for('admin_view_students_list'))

@app.route('/admin/student-profile/<int:student_id>', methods=['GET'])
def admin_view_profile(student_id):
    """
    Fetches every data point submitted by a specific student, 
    including profile information, guardians, and academic results.
    """
    if session.get('role') != 'admin':
        flash("Akses Ditolak: Hak pentadbir sistem diperlukan.", "danger")
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    cursor.execute("""
        SELECT bil_kemasukan, tempat_lahir, no_surat_beranak, masalah_penglihatan, id_pakej, aliran_ditawar 
        FROM pelajar WHERE no_kp_pelajar = %s
    """, (student_id,))
    
    # Use fetchone() to get a single dictionary
    student = cursor.fetchone() 

    try:
        # Fetch complete profile data from the pelajar table joined with the chosen package
        student_query = """
            SELECT p.*, k.kod_pakej, k.aliran 
            FROM pelajar p
            LEFT JOIN pakej k ON p.id_pakej = k.id_pakej
            WHERE p.bil_kemasukan = %s
        """
        cursor.execute(student_query, (student_id,))
        student_data = cursor.fetchone()

        if not student_data:
            flash("Rekod pelajar tidak ditemui dalam sistem.", "danger")
            return redirect(url_for('admin_view_students_list'))

        # Fetch all registered parents/guardians for this student
        cursor.execute("""
            SELECT * FROM penjaga 
            WHERE bil_kemasukan = %s 
            ORDER BY no_penjaga ASC
        """, (student_id,))
        guardians_data = cursor.fetchall()

        # Fetch academic summary list from spm_hasil
        cursor.execute("""
            SELECT subjek, gred FROM spm_hasil 
            WHERE bil_kemasukan = %s 
            ORDER BY id_spm ASC
        """, (student_id,))
        spm_data = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Administrative Profile Fetch Failure: {err}")
        flash("Ralat pangkalan data berlaku ketika memuatkan profil.", "danger")
        return redirect(url_for('admin_view_students_list'))
    finally:
        cursor.close()
        conn.close()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("SELECT * FROM pakej")
    all_packages = cursor.fetchall()
    
    return render_template('profile.html', student=student_data, 
                           guardians=guardians_data, spm=spm_data, 
                           all_packages=all_packages)

#------------------------
@app.route('/admin/update-field', methods=['POST'])
def update_field():
    data = request.json
    field = data.get('field')
    try:
        student_id = int(data.get('id'))
    except (TypeError, ValueError):
        return jsonify(success=False, message="ID Pelajar tidak sah"), 400
        
    value = data.get('value')

    allowed_fields = [
        'nama_pelajar','email', 'jantina', 'bangsa', 'agama', 'telefonNo', 
        'alamat_rumah', 'cara_datang_sekolah', 'masalah_penglihatan', 
        'masalah_kesihatan', 'status_oku', 'aliran_ditawar', 'kelas',
        'tarikh_lahir', 'tempat_lahir', 'no_surat_beranak', 'id_pakej', 'status_study'
    ]

    if field not in allowed_fields:
        return jsonify(success=False, message="Medan tidak sah"), 400
    
    if value == "":
        value = None
    
    # Convert status_study to integer
    if field == 'status_study':
        value = 1 if str(value).lower() in ['1', 'true', 'aktif'] else 0
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = f"UPDATE pelajar SET {field} = %s WHERE bil_kemasukan = %s"
        cursor.execute(query, (value, student_id))
        conn.commit()
        
        return jsonify(success=True)
    except Exception as e:
        print(f"Database Error: {e}") 
        return jsonify(success=False, message=str(e)), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
@app.route('/admin/delete-student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Perform deletion
        query = "DELETE FROM pelajar WHERE bil_kemasukan = %s"
        cursor.execute(query, (student_id,))
        conn.commit()
        
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

#------------------------

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    # 1. Access Control
    if session.get('role') != 'admin':
        flash("Akses Ditolak.", "danger")
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 2. Handle POST requests
    if request.method == 'POST':
        # Action A: Toggle form settings
        if 'enabled_forms' in request.form:
            cursor.execute("UPDATE form_settings SET is_enabled = FALSE")
            for form_id in request.form.getlist('enabled_forms'):
                cursor.execute("UPDATE form_settings SET is_enabled = TRUE WHERE form_id = %s", (form_id,))
            conn.commit()
            flash("Tetapan borang dikemaskini.", "success")
            session['last_tab'] = 'forms'
        
        # Action B: Update Package Limit
        elif 'update_limit' in request.form:
            package_id = request.form.get('package_select')
            new_limit = request.form.get('limit_number')
            cursor.execute("SELECT kod_pakej FROM pakej WHERE id_pakej = %s", (package_id,))
            pkg = cursor.fetchone()
            if pkg and new_limit:
                limits = get_limits()
                limits[pkg['kod_pakej']] = int(new_limit)
                save_limits(limits)
                flash(f"Had {pkg['kod_pakej']} dikemaskini.", "success")
                session['last_tab'] = 'package'
        
        # Action C: Update Kokurikulum Unit Limit
        elif 'update_koku_limit' in request.form:
            unit_id = request.form.get('koku_select')
            new_limit = request.form.get('koku_limit_number')

            # 1. Fetch both activity_name AND unit_type to determine the prefix
            cursor.execute("SELECT activity_name, unit_type FROM UnitKokurikulum WHERE unit_id = %s", (unit_id,))
            unit = cursor.fetchone()

            if unit and new_limit:
                # 2.     Reconstruct the prefix logic
                prefix = ""
                if unit['unit_type'] == 'Kelab': prefix = "KK_"
                elif unit['unit_type'] == 'Badan Beruniform': prefix = "UB_"
                elif unit['unit_type'] == 'Sukan dan Permainan': prefix = "SK_"

                # 3. Create the exact same key used by the rest of your app
                full_key = f"{prefix}{unit['activity_name']}"

                limits = get_limits()

                # 4. Remove the old, incorrect key if it exists (Optional cleanup)
                if unit['activity_name'] in limits:
                    del limits[unit['activity_name']]

                # 5. Save using the standardized key
                limits[full_key] = int(new_limit)
                save_limits(limits)

                flash(f"Had {full_key} dikemaskini.", "success")
                session['last_tab'] = 'koku'
        

        conn.commit()
        cursor.close(); conn.close()
        return redirect(url_for('admin_settings'))

    # 3. Fetch Data for Display
    cursor.execute("SELECT * FROM form_settings")
    settings = cursor.fetchall()

    # Ensure this query is in your admin_settings route
    cursor.execute("""
        SELECT p.id_pakej, p.kod_pakej, 
                (SELECT COUNT(*) FROM pelajar WHERE pelajar.id_pakej = p.id_pakej) as total_students
        FROM pakej p
        WHERE p.status_aktif = 1
        ORDER BY p.kod_pakej
    """)
    package_summary = cursor.fetchall()
    
    cursor.execute("SELECT id_pakej, kod_pakej FROM pakej ORDER BY kod_pakej")
    all_packages = cursor.fetchall()

    cursor.execute("""
        SELECT unit_id, COUNT(*) as enrolled_count 
        FROM KokurikulumPelajar 
        GROUP BY unit_id
    """)
    enrollment_data = {row['unit_id']: row['enrolled_count'] for row in cursor.fetchall()}

    cursor.execute("SELECT unit_id, activity_name, unit_type FROM UnitKokurikulum ORDER BY activity_name")
    all_units = cursor.fetchall()

    cursor.close(); conn.close()

    form_labels = {
        'profil_form': 'Borang Maklumat Pelajar',
        'tambahan_form': 'Borang Dokumen Pelajar',
        'penjaga_form': 'Borang Maklumat Penjaga',
        'spm_form': 'Borang Keputusan SPM',
        'pakej_form': 'Borang Pemilihan Pakej',
        'kokurikulum_form': 'Borang Pemilihan Unit Kokurikulum'
    }

    # Retrieve last active tab to persist view after POST
    active_tab = session.pop('last_tab', 'forms')

    return render_template('admin_settings.html', 
                           settings=settings, 
                           form_labels=form_labels,
                           enrollment_data=enrollment_data,
                           package_summary=package_summary,
                           all_packages=all_packages,
                           all_units=all_units,
                           package_limits=get_limits(),
                           active_tab=active_tab,
                           default_limit=DEFAULT_LIMIT)

def get_statistics_data(mode, category, filter_stream, filter_sem, status_study):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 1. Reuse existing logic to define items and group_col
    def is_sains(kod):
        return any(prefix in kod for prefix in ['BK', 'CK', 'FK'])

    if mode == 'kelas':
        cursor.execute("SELECT DISTINCT COALESCE(kelas, 'TIADA') as id, COALESCE(kelas, 'TIADA') as label FROM pelajar ORDER BY id")
        items = cursor.fetchall()
        group_col = "kelas"
    else:
        cursor.execute("SELECT id_pakej as id, kod_pakej as label, semester FROM pakej")
        all_packages = cursor.fetchall()
        items = [p for p in all_packages if str(p['semester']) == str(filter_sem)] if filter_sem != 'semua' else all_packages
        
        def is_tiada(p):
            label = p.get('label', '') or ''
            return not any(char.isdigit() for char in label)
        
        regular_packages = [p for p in items if not is_tiada(p)]
        if filter_stream == 'sains': items = [p for p in regular_packages if is_sains(p['label'])]
        elif filter_stream == 'sosial': items = [p for p in regular_packages if not is_sains(p['label'])]
        else: items = regular_packages
        items.append({'id': 'TIADA', 'label': 'TIADA'})
        group_col = "p.id_pakej"

    # 2. Get distinct categories and counts
    cursor.execute(f"SELECT DISTINCT {category} as cat FROM pelajar WHERE {category} IS NOT NULL")
    categories = [row['cat'] for row in cursor.fetchall()]
    genders = ['LELAKI', 'PEREMPUAN']

    sem_filter_sql = "" if filter_sem == 'semua' else f" AND pk.semester = {filter_sem}"
    status_filter_sql = " AND p.status_study = 1" if status_study == 'active' else ""
    group_id_sql = "COALESCE(p.kelas, 'TIADA')" if mode == 'kelas' else "CASE WHEN p.id_pakej IS NULL THEN 'TIADA' WHEN pk.kod_pakej NOT REGEXP '[0-9]' THEN 'TIADA' ELSE p.id_pakej END"

    cursor.execute(f"SELECT {group_id_sql} as group_id, p.{category} as cat, p.jantina, COUNT(*) as total FROM pelajar p LEFT JOIN pakej pk ON p.id_pakej = pk.id_pakej WHERE 1=1 {sem_filter_sql} {status_filter_sql} GROUP BY group_id, {category}, jantina")
    results = cursor.fetchall()

    # 3. Process calculations
    counts = {str(item['id']): {cat: {g: 0 for g in genders} for cat in categories} for item in items}
    for row in results:
        gid = str(row['group_id'])
        if gid in counts and row['cat'] in counts[gid]:
            counts[gid][row['cat']][row['jantina']] = row['total']

    col_totals = {cat: {'LELAKI': sum(counts[str(i['id'])][cat]['LELAKI'] for i in items), 'PEREMPUAN': sum(counts[str(i['id'])][cat]['PEREMPUAN'] for i in items)} for cat in categories}
    row_totals = {str(item['id']): sum(sum(counts[str(item['id'])][cat].values()) for cat in categories) for item in items}
    grand_total = sum(row_totals.values())
    
    # FIX: Use local variables (counts, items, categories) instead of 'data'
    row_gender_totals = {}
    for item in items:
        iid = str(item['id'])
        row_gender_totals[iid] = {
            'L': sum(counts[iid][cat]['LELAKI'] for cat in categories),
            'P': sum(counts[iid][cat]['PEREMPUAN'] for cat in categories)
        }
    
    grand_total_l = sum(row['L'] for row in row_gender_totals.values())
    grand_total_p = sum(row['P'] for row in row_gender_totals.values())  

    cursor.close(); conn.close()

    # FIX: Include the new totals in the returned dictionary
    return {
        'items': items, 'categories': categories, 'counts': counts,
        'col_totals': col_totals, 'row_totals': row_totals, 'grand_total': grand_total,
        'group_col': group_col,
        'row_gender_totals': row_gender_totals,
        'grand_total_l': grand_total_l,
        'grand_total_p': grand_total_p
    }

@app.route('/statistics')
def statistics():
    # 1. Capture Args
    mode = request.args.get('mode', 'pakej')
    category = request.args.get('type', 'bangsa')
    filter_stream = request.args.get('filter_stream', 'semua')
    filter_sem = request.args.get('filter_sem', 'semua')
    status_study = request.args.get('status_study', 'all')
    
    # 2. Get data from helper
    data = get_statistics_data(mode, category, filter_stream, filter_sem, status_study)

    # 4. Render template
    # We use **data to pass all helper variables, plus our new local variables
    return render_template('statistics.html', 
                           **data,
                           current_type=category,
                           current_mode=mode,
                           status_study=status_study,
                           filter_stream=filter_stream,
                           filter_sem=filter_sem)

@app.route('/admin/export-statistics')
def admin_export_statistics():
    # 1. Capture filters (same as in statistics route)
    mode = request.args.get('mode', 'pakej')
    category = request.args.get('type', 'bangsa')
    filter_stream = request.args.get('filter_stream', 'semua')
    filter_sem = request.args.get('filter_sem', 'semua')
    status_study = request.args.get('status_study', 'all')

    # 2. Get the pre-calculated data using the helper
    data = get_statistics_data(mode, category, filter_stream, filter_sem, status_study)
    
    # 3. Generate CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Create Header
    # Format: Group, Category/Gender (L/P), Total
    header = [mode.capitalize(), 'Kategori', 'Lelaki', 'Perempuan', 'Jumlah']
    cw.writerow(header)
    
    # Data rows
    for item in data['items']:
        iid = str(item['id'])
        label = item['label']
        for cat in data['categories']:
            l = data['counts'][iid][cat]['LELAKI']
            p = data['counts'][iid][cat]['PEREMPUAN']
            cw.writerow([label, cat, l, p, l + p])
    
    # Add Totals row at the bottom
    cw.writerow(['JUMLAH KESELURUHAN', '', data['grand_total_l'], data['grand_total_p'], data['grand_total']])
    
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=statistik_{mode}.csv"}
    )

@app.route('/admin/toggle_status/<int:student_id>', methods=['POST'])
def toggle_status(student_id):
    if session.get('role') != 'admin':
        return {"error": "Unauthorized"}, 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Toggle logic: 1 becomes 0, 0 becomes 1
    cursor.execute("UPDATE pelajar SET status_study = NOT status_study WHERE bil_kemasukan = %s", (student_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"success": True}

def get_subject_statistics_data(filter_sem):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    def is_regular_package(kod):
        return bool(re.search(r'\d', kod))

    # Fetch Packages
    sem_filter_sql = f"WHERE semester = {filter_sem}" if filter_sem != 'all' else ""
    cursor.execute(f"SELECT id_pakej, kod_pakej FROM pakej {sem_filter_sql} ORDER BY kod_pakej")
    packages = [p for p in cursor.fetchall() if is_regular_package(p['kod_pakej'])]
    package_ids = [p['id_pakej'] for p in packages]
    
    # Fetch all subjects
    cursor.execute("SELECT id_subjek, kod_pakej_subjek, nama_subjek FROM subjek_stpm")
    subjects = cursor.fetchall()
    
    # Fetch Counts
    counts = {s['id_subjek']: {p['id_pakej']: 0 for p in packages} for s in subjects}
    if package_ids:
        placeholders = ','.join(['%s'] * len(package_ids))
        query = f"SELECT ps.id_pakej, ps.id_subjek, COUNT(p.bil_kemasukan) as total FROM pakej_subjek ps JOIN pelajar p ON ps.id_pakej = p.id_pakej WHERE p.status_study = 1 AND ps.id_pakej IN ({placeholders}) GROUP BY ps.id_pakej, ps.id_subjek"
        cursor.execute(query, package_ids)
        for row in cursor.fetchall():
            if row['id_subjek'] in counts and row['id_pakej'] in counts[row['id_subjek']]:
                counts[row['id_subjek']][row['id_pakej']] = row['total']
                
    cursor.close(); conn.close()
    return {'packages': packages, 'subjects': subjects, 'counts': counts}

@app.route('/subjects-statistics')
def subjects_statistics():
    filter_sem = request.args.get('filter_sem', 'all')
    data = get_subject_statistics_data(filter_sem)
    return render_template('subjects_statistics.html', **data, filter_sem=filter_sem)

@app.route('/admin/export-subjects-statistics')
def admin_export_subjects_statistics():
    filter_sem = request.args.get('filter_sem', 'all')
    data = get_subject_statistics_data(filter_sem)
    
    si = io.StringIO()
    cw = csv.writer(si)
    
    # 1. Header
    header = ['Nama Subjek'] + [p['kod_pakej'] for p in data['packages']] + ['Jumlah']
    cw.writerow(header)
    
    # 2. Track column totals (one for each package)
    col_totals = [0] * len(data['packages'])
    grand_total_all = 0
    
    # 3. Data Rows
    for sub in data['subjects']:
        row = [sub['nama_subjek']]
        subject_row_total = 0
        
        for i, pkg in enumerate(data['packages']):
            count = data['counts'][sub['id_subjek']][pkg['id_pakej']]
            row.append(count)
            subject_row_total += count
            col_totals[i] += count # Add to column total tracker
            
        row.append(subject_row_total)
        grand_total_all += subject_row_total
        cw.writerow(row)
    
    # 4. Final Row: "JUMLAH KESELURUHAN"
    footer_row = ['JUMLAH KESELURUHAN'] + col_totals + [grand_total_all]
    cw.writerow(footer_row)
    
    return Response(si.getvalue(), mimetype="text/csv", 
                    headers={"Content-Disposition": "attachment;filename=statistik_subjek.csv"})

@app.route('/admin/eligible-subjects', methods=['GET'])
def eligible_subject_page():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    # Removed page and offset variables
    search = request.args.get('search', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    # Removed LIMIT 10 OFFSET %s
    query = """
        SELECT e.no_kp_pelajar, e.subjek_khas, 
               COALESCE(p.nama_pelajar, 'NULL') AS nama_pelajar
        FROM pelajar_eligibility e
        LEFT JOIN pelajar p ON e.no_kp_pelajar = p.no_kp_pelajar
        WHERE e.no_kp_pelajar LIKE %s
    """
    
    # Executing without offset
    cursor.execute(query, (f"%{search}%",))
    data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Pass data to template
    return render_template('eligible_subject.html', students=data, search=search)

@app.route('/admin/submit_eligibility', methods=['POST'])
def submit_eligibility():
    action = request.form.get('action')
    kp = request.form.get('no_kp_pelajar')
    subjek = request.form.get('subjek_khas')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if action == 'add' or action == 'update':
            cursor.execute("REPLACE INTO pelajar_eligibility (no_kp_pelajar, subjek_khas) VALUES (%s, %s)", (kp, subjek))
        elif action == 'delete':
            cursor.execute("DELETE FROM pelajar_eligibility WHERE no_kp_pelajar = %s AND subjek_khas = %s", (kp, subjek))
        conn.commit()
    except Exception as e:
        flash(f"Ralat: {e}")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('eligible_subject_page'))

@app.route('/admin/koku-list', methods=['GET'])
def admin_koku_list():
    if session.get('role') != 'admin':
        flash("Akses Ditolak.", "danger")
        return redirect(url_for('gateway'))

    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    cat_filter = request.args.get('category')
    act_filter = request.args.get('activity')
    rumah_filter = request.args.get('rumah')

    # 1. Establish database connection FIRST
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 2. Build the base query structure
    base_query = """
        FROM KokurikulumPelajar kp
        JOIN pelajar p ON kp.bil_kemasukan = p.bil_kemasukan
        JOIN UnitKokurikulum uk ON kp.unit_id = uk.unit_id
        WHERE 1=1
    """
    params = []
    
    # 3. Apply filters to the base query and parameters
    if cat_filter:
        base_query += " AND uk.unit_type = %s"
        params.append(cat_filter)
    if act_filter:
        base_query += " AND uk.activity_name = %s"
        params.append(act_filter)
    if rumah_filter:
        base_query += " AND LOWER(p.rumah_sukan) = LOWER(%s)"
        params.append(rumah_filter)
        
    # 4. Count total
    count_query = "SELECT COUNT(*) as total_count " + base_query
    cursor.execute(count_query, params)
    result = cursor.fetchone()
    total = result.get('total_count') or (list(result.values())[0] if result else 0)
    
    # 5. Fetch dropdown data
    cursor.execute("SELECT unit_id, activity_name, unit_type FROM UnitKokurikulum ORDER BY unit_type, activity_name")
    all_units_dropdown = cursor.fetchall()

    # 6. Fetch main student list
    data_query = """
        SELECT kp.kkplr_id, kp.bil_kemasukan, kp.jawatan, p.nama_pelajar, uk.activity_name, uk.unit_type
    """ + base_query + " LIMIT %s OFFSET %s"
    cursor.execute(data_query, params + [per_page, offset])
    students = cursor.fetchall()
    
    # 7. Close resources
    cursor.close()
    conn.close()
    
    return render_template('koku_list.html', 
                           students=students, 
                           all_units=all_units_dropdown,
                           total=total, 
                           page=page, 
                           per_page=per_page,
                           cat=cat_filter,
                           act=act_filter,
                           rumah=rumah_filter)

@app.route('/admin/update-jawatan', methods=['POST'])
def update_jawatan_ajax():
    # Debugging: Log what is received
    print("DEBUG - Form Data:", request.form) 
    
    kkplr_id = request.form.get('kkplr_id')
    new_jawatan = request.form.get('jawatan')
    
    if not kkplr_id or not new_jawatan:
        # This will trigger your flash message
        flash(f"Error: Missing data. ID={kkplr_id}, Jawatan={new_jawatan}", "danger")
        return redirect(request.referrer or url_for('admin_koku_list'))
    
    if kkplr_id and new_jawatan:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Ensure column names match your DB schema (KokurikulumPelajar)
        query = "UPDATE KokurikulumPelajar SET jawatan = %s WHERE kkplr_id = %s"
        cursor.execute(query, (new_jawatan, kkplr_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Position updated successfully!", "success")
    else:
        flash("Failed to update: missing data.", "danger")
        
    return redirect(request.referrer or url_for('admin_koku_list'))

@app.route('/admin/delete-koku-record/<int:kkplr_id>', methods=['POST'])
def delete_koku_record(kkplr_id):
    if session.get('role') != 'admin':
        return redirect(url_for('gateway'))
        
    bil = request.args.get('bil') # Get student bil_kemasukan from URL
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM KokurikulumPelajar WHERE kkplr_id = %s", (kkplr_id,))
    conn.commit()
    cursor.close(); conn.close()
    
    flash("Rekod Kokurikulum telah dipadam.", "info")
    return redirect(url_for('edit_student_koku', bil=bil))

@app.route('/admin/edit-student/<bil>', methods=['GET', 'POST'])
def edit_student_koku(bil):
    if session.get('role') != 'admin':
        return redirect(url_for('gateway'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # 1. Update Student Personal Info (pelajar table)
        tugas_khas = request.form.get('tugas_khas')
        rumah_sukan = request.form.get('rumah_sukan')
        cursor.execute("""
            UPDATE pelajar SET tugas_khas = %s, rumah_sukan = %s 
            WHERE bil_kemasukan = %s
        """, (tugas_khas, rumah_sukan, bil))
        
        # 2. Update Koku Records (KokurikulumPelajar table)
        kkplr_ids = request.form.getlist('kkplr_id[]')
        new_unit_ids = request.form.getlist('unit_id[]')
        jawatans = request.form.getlist('jawatan[]')
        merits = request.form.getlist('merit[]')
        
        for i in range(len(kkplr_ids)):
            cursor.execute("""
                UPDATE KokurikulumPelajar 
                SET unit_id = %s, jawatan = %s, merit = %s 
                WHERE kkplr_id = %s AND bil_kemasukan = %s
            """, (new_unit_ids[i], jawatans[i], merits[i], kkplr_ids[i], bil))
        
        conn.commit()
        flash("Semua maklumat berjaya dikemaskini!", "success")
        return redirect(url_for('admin_koku_list'))
        
    # Fetch Data
    cursor.execute("SELECT * FROM pelajar WHERE bil_kemasukan = %s", (bil,))
    student = cursor.fetchone()
    
    cursor.execute("SELECT unit_id, activity_name FROM UnitKokurikulum")
    all_units = cursor.fetchall()
    
    cursor.execute("""
        SELECT kp.*, uk.activity_name 
        FROM KokurikulumPelajar kp
        JOIN UnitKokurikulum uk ON kp.unit_id = uk.unit_id
        WHERE kp.bil_kemasukan = %s
    """, (bil,))
    koku_records = cursor.fetchall()
    
    cursor.close(); conn.close()
    return render_template('edit_student.html', student=student, records=koku_records, all_units=all_units)


if __name__ == '__main__':
    app.run(debug=True)