from flask import Flask, render_template, request, redirect, url_for, session, flash
from db.db_config import db_config
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'smis_admin_secret_key'

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Tambah laluan folder baru untuk dokumen tambahan di bawah konfigurasi sedia ada
UPLOAD_FOLDER_SPM = os.path.join(app.root_path, 'static', 'uploads', 'spm_slips')
UPLOAD_FOLDER_DOCS = os.path.join(app.root_path, 'static', 'uploads', 'student_docs')

app.config['UPLOAD_FOLDER_SPM'] = UPLOAD_FOLDER_SPM
app.config['UPLOAD_FOLDER_DOCS'] = UPLOAD_FOLDER_DOCS
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # Kekalkan had keselamatan 2MB

# Pastikan kedua-dua folder wujud di dalam direktori
os.makedirs(UPLOAD_FOLDER_SPM, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_DOCS, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'png', 'jpg', 'jpeg'}

def is_form_enabled(form_id):
    conn = get_db_connection() # Use your defined helper
    cursor = conn.cursor(dictionary=True)
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
        cursor = conn.cursor(dictionary=True)
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
        
        if username == "admin" and password == "12345": # (or whatever your admin check is)
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
    # If an admin is logged in, immediately redirect or show the administrative template view
    if session.get('role') == 'admin':
        return render_template('admin_dashboard.html')
        
    kp = session.get('verified_kp')
    
    # Default statuses if not logged in
    completion_status = {
        'profil': False,
        'spm': False,
        'tambahan': False,
        'pakej': False
    }
    
    if kp:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch student details to check Step 1, Step 3, and Step 4
        cursor.execute("""
            SELECT nama_pelajar, tempat_lahir, no_surat_beranak, keadaan_mata, id_pakej 
            FROM pelajar WHERE no_kp_pelajar = %s
        """, (kp,))
        student = cursor.fetchone()
        
        # Fetch SPM rows to check Step 2
        cursor.execute("""
            SELECT COUNT(*) as total FROM spm_hasil 
            WHERE no_pendaftaran_pelajar = (
                SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s
            )
        """, (kp,))
        spm_count = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if student:
            # Step 1 is complete if they exist in the system database
            completion_status['profil'] = True
            
            # Step 2 is complete if they have records in spm_hasil
            if spm_count and spm_count['total'] > 0:
                completion_status['spm'] = True
                
            # Step 3 (Tambahan) is complete if these custom criteria are filled
            if student['tempat_lahir'] and student['no_surat_beranak'] and student['keadaan_mata']:
                completion_status['tambahan'] = True
                
            # Step 4 (Pakej) is complete if an assignment key is saved
            if student['id_pakej'] is not None and student['id_pakej'] != 0:
                completion_status['pakej'] = True

    return render_template('index.html', completion_status=completion_status)

@app.route('/register')
def register_page():
    if not is_form_enabled('profil_form'):
        flash("Borang ini sedang ditutup oleh pentadbir.", "warning")
        return redirect(url_for('index'))
    
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))
        
    # Check if student profile already exists in the 'pelajar' table
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    existing_student = cursor.fetchone()
    cursor.close()
    conn.close()

    if existing_student:
        flash("Anda telah mengisi maklumat bagi seksyen PROFIL PELAJAR sebelum ini. Sila hubungi guru bertugas untuk ubahsuai maklumat.", "error_profil")
        return redirect(url_for('index'))

    # Your original return remains unchanged
    return render_template('register.html', verified_kp=kp, student=None)

@app.route('/submit', methods=['POST'])
def submit_registration():
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    existing_student = cursor.fetchone()
    
    if existing_student:
        cursor.close()
        conn.close()
        flash("Rekod profil sudah wujud bagi No. KP ini.", "error_profil")
        return redirect(url_for('index'))

    # Extracted data array (Exactly 12 form parameters)
    data = (
        request.form.get('nama_pelajar'),
        request.form.get('email'),
        kp,
        request.form.get('jantina'),
        request.form.get('bangsa'),
        request.form.get('agama'),
        request.form.get('tarikh_lahir'),
        request.form.get('alamat_rumah'),
        request.form.get('telefonNo'),
        request.form.get('sekolah_tamat'),
        request.form.get('masalah_kesihatan'),
        request.form.get('cara_datang_sekolah')
    )

    try:
        # 13 columns named explicitly (status_study is hardcoded as '1' at the end)
        query = """INSERT INTO pelajar (
                    nama_pelajar, email, no_kp_pelajar, jantina, bangsa, agama, 
                    tarikh_lahir, alamat_rumah, telefonNo, sekolah_tamat, masalah_kesihatan, 
                    cara_datang_sekolah, status_study
                   ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)"""
        
        cursor.execute(query, data)
        conn.commit()
        flash("Tahniah! Maklumat Profil Pelajar berjaya dihantar.", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error: {err}") 
        flash(f"Ralat pangkalan data berlaku semasa menyimpan maklumat: {err}", "warning")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

# --- MAKLUMAT TAMBAHAN ROUTES ---

@app.route('/additional', methods=['GET'])
def additional_page():
    if not is_form_enabled('tambahan_form'):
        flash("Borang ini sedang ditutup oleh pentadbir.", "warning")
        return redirect(url_for('index'))
    
    """Renders the additional details form ONLY if it hasn't been completed yet,
    explicitly passing down the verified identity card number to prevent empty form fields.
    """
    kp = session.get('verified_kp')
    if not kp:
        flash("Sila masukkan No. KP anda terlebih dahulu.", "warning")
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if student exists and see if fields are already filled
    cursor.execute("""
        SELECT no_pendaftaran_pelajar, tempat_lahir, no_surat_beranak, keadaan_mata 
        FROM pelajar WHERE no_kp_pelajar = %s
    """, (kp,))
    student = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if not student:
        flash("Sila lengkapkan Profil Pendaftaran utama terlebih dahulu di Langkah 1.", "warning")
        return redirect(url_for('index'))

    # GATEKEEPER CHECK: Block access if Maklumat Tambahan is already completely filled
    if student['tempat_lahir'] and student['no_surat_beranak'] and student['keadaan_mata']:
        flash("Akses Ditutup: Maklumat Tambahan & Dokumen Sokongan anda telah lengkap diisi. Sila hubungi guru bertugas untuk ubahsuai maklumat.", "warning")
        return redirect(url_for('index'))

    # FIX: Explicitly send both student record AND verified_kp down to the HTML template
    return render_template('additional.html', student=student, verified_kp=kp)


@app.route('/submit_additional', methods=['POST'])
def submit_additional():
    """Handles submission of extra student documents and personal details with precise error logging."""
    kp = session.get('verified_kp')
    if not kp:
        flash("Sila masukkan No. KP anda terlebih dahulu.", "warning")
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Fetch current record
    cursor.execute("""
        SELECT no_pendaftaran_pelajar, tempat_lahir, no_surat_beranak, keadaan_mata 
        FROM pelajar WHERE no_kp_pelajar = %s
    """, (kp,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        flash("Sila lengkapkan Profil Pendaftaran utama terlebih dahulu di Langkah 1.", "warning")
        return redirect(url_for('index'))

    student_id = student['no_pendaftaran_pelajar']

    # 2. Extract input values directly from HTML form elements safely
    tempat_lahir = request.form.get('tempat_lahir_pelajar')
    no_surat_beranak = request.form.get('no_surat_beranak_pelajar')
    keadaan_mata = request.form.get('keadaan_mata', 'BAIK')

    # Debug checkpoint: Prints to your terminal running Flask so you can inspect incoming form values
    print("--- DEBUG FORM DATA RECEIVED FROM BROWSER ---")
    print(f"Raw Tempat Lahir: '{tempat_lahir}'")
    print(f"Raw Surat Beranak: '{no_surat_beranak}'")
    print(f"Raw Keadaan Mata: '{keadaan_mata}'")
    print("---------------------------------------------")

    # Clean the input strings safely if they are not None objects
    if tempat_lahir is not None:
        tempat_lahir = tempat_lahir.strip().upper()
    if no_surat_beranak is not None:
        no_surat_beranak = no_surat_beranak.strip().upper()
    if keadaan_mata is not None:
        keadaan_mata = keadaan_mata.strip().upper()

    # 3. Validation Check: Ensure they are not empty strings or None objects
    if not tempat_lahir or not no_surat_beranak or tempat_lahir == "" or no_surat_beranak == "":
        cursor.close()
        conn.close()
        flash("Gagal Menyimpan: Sila pastikan semua ruangan wajib diisi.", "danger")
        return redirect(url_for('additional_page'))

    # Handle document attachment uploads
    file_ic = request.files.get('ic_photo')
    file_offer = request.files.get('surat_tawaran')
    filename_ic = None
    filename_offer = None

    if file_ic and file_ic.filename != '':
        if allowed_file(file_ic.filename):
            ext = file_ic.filename.rsplit('.', 1)[1].lower()
            filename_ic = secure_filename(f"IC_{student_id}.{ext}")
            file_ic.save(os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename_ic))

    if file_offer and file_offer.filename != '':
        if allowed_file(file_offer.filename):
            ext = file_offer.filename.rsplit('.', 1)[1].lower()
            filename_offer = secure_filename(f"OFFER_{student_id}.{ext}")
            file_offer.save(os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename_offer))

# 4. Commit values to the MySQL database with strict error trapping
    try:
        # FIX: Added ic_photo_path and surat_tawaran_path to the SQL query update statement
        cursor.execute("""
            UPDATE pelajar 
            SET tempat_lahir = %s, 
                no_surat_beranak = %s, 
                keadaan_mata = %s,
                ic_photo_path = %s,
                surat_tawaran_path = %s
            WHERE no_kp_pelajar = %s
        """, (tempat_lahir, no_surat_beranak, keadaan_mata, filename_ic, filename_offer, kp))
        
        conn.commit()
        flash("Maklumat tambahan dan dokumen sokongan anda berjaya didaftarkan!", "success")
        return redirect(url_for('index'))
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"!!! DATABASE CRASH ERROR !!!: {err}")
        flash(f"Ralat Sistem Database: {err}", "danger")
        return redirect(url_for('additional_page'))
        
    finally:
        cursor.close()
        conn.close()

@app.route('/register_guardian')
def guardian_page():
    if not is_form_enabled('penjaga_form'):
        flash("Borang ini sedang ditutup oleh pentadbir.", "warning")
        return redirect(url_for('index'))
    
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))
        
    # Get the internal student ID first
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    student_record = cursor.fetchone()
    
    if not student_record:
        cursor.close()
        conn.close()
        flash("Sila lengkapkan Maklumat Profil Pelajar (Langkah 1) terlebih dahulu.", "warning")
        return redirect(url_for('index'))
        
    student_id = student_record[0]
    
    # Check if guardian details already exist for this student in the 'penjaga' table
    cursor.execute("SELECT no_penjaga FROM penjaga WHERE no_pendaftaran_pelajar = %s", (student_id,))
    existing_guardian = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if existing_guardian:
        flash("Anda telah mengisi maklumat bagi seksyen MAKLUMAT PENJAGA sebelum ini. Sila hubungi guru bertugas untuk ubahsuai maklumat.", "error_penjaga")
        return redirect(url_for('index'))
        
    # Your original return remains unchanged
    return render_template('guardian.html', existing_guardians=None)

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
                    (no_pendaftaran_pelajar, nama_penjaga, no_kp_penjaga, penjaga, no_telefon, pekerjaan, pendapatan, alamat_tempat_kerja) 
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
        flash("Borang ini sedang ditutup oleh pentadbir.", "warning")
        return redirect(url_for('index'))

    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))
        
    # Get the internal student ID first
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    student_record = cursor.fetchone()
    
    if not student_record:
        cursor.close()
        conn.close()
        flash("Sila lengkapkan Maklumat Profil Pelajar (Langkah 1) terlebih dahulu.", "warning")
        return redirect(url_for('index'))
        
    student_id = student_record[0]
    
    # FIX: Using SELECT 1 checks for row existence safely without needing a 'no_spm' column
    cursor.execute("SELECT 1 FROM spm_hasil WHERE no_pendaftaran_pelajar = %s LIMIT 1", (student_id,))
    existing_spm = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if existing_spm:
        flash("Anda telah mengisi maklumat bagi seksyen KEPUTUSAN SPM sebelum ini. Sila hubungi guru bertugas untuk ubahsuai maklumat.", "error_spm")
        return redirect(url_for('index'))
        
    return render_template('spm.html', existing_spm=None)

@app.route('/submit_spm', methods=['POST'])
def submit_spm():
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve internal index identifier targeting active session identity
    cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
    student_record = cursor.fetchone()

    if not student_record:
        cursor.close()
        conn.close()
        flash("Sila lengkapkan Profil Pelajar terlebih dahulu.", "warning")
        return redirect(url_for('index'))

    student_id = student_record[0]

    # --- NEW: SAFE FILE UPLOAD PROCESSING SEGMENT ---
    file_path_to_save = None
    if 'spm_slip' in request.files:
        file = request.files['spm_slip']
        if file and file.filename != '' and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            
            # Format clean, uniform filename bound to student identification keys
            secure_new_name = f"{kp}_slip.{file_ext}"
            file_path_to_save = os.path.join(app.config['UPLOAD_FOLDER'], secure_new_name)
            file.save(file_path_to_save)
    # ------------------------------------------------

    # Extract dynamic arrays representing subjects and grades from frontend inputs
    subjek_list = request.form.getlist('subjek[]')
    gred_list = request.form.getlist('gred[]')

    try:
        # Purge existing stale academic rows to overwrite with fresh data structures cleanly
        cursor.execute("DELETE FROM spm_hasil WHERE no_pendaftaran_pelajar = %s", (student_id,))

        # Batch insert operation utilizing normalized values
        for subjek, gred in zip(subjek_list, gred_list):
            if subjek.strip() != "" and gred.strip() != "":
                cursor.execute(
                    "INSERT INTO spm_hasil (no_pendaftaran_pelajar, subjek, gred) VALUES (%s, %s, %s)",
                    (student_id, subjek.upper(), gred.upper())
                )

        conn.commit()
        flash("Keputusan SPM anda berjaya disimpan!", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Ralat Operasi Akademik: {err}")
        flash("Gagal mengemaskini maklumat akademik.", "warning")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

@app.route('/students_list')
def view_students():
    if not session.get('admin_logged'):
        flash("Admin access only.")
        return redirect(url_for('login'))
    
    # Get all filter arguments (Rujukan 'citizen' telah dibuang)
    search_query = request.args.get('search', '')
    gender = request.args.get('gender', '')
    race = request.args.get('race', '')
    religion = request.args.get('religion', '')
    transport = request.args.get('transport', '')
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

# --- PILIHAN PAKEJ ROUTES ---

@app.route('/package', methods=['GET'])
def package_page():
    if not is_form_enabled('pakej_form'):
        flash("Borang ini sedang ditutup oleh pentadbir.", "warning")
        return redirect(url_for('index'))

    """Evaluates student qualifications and dynamic class capacity limits to 
    display only open, eligible Form 6 packages. Blocks entry if already selected.
    """
    kp = session.get('verified_kp')
    if not kp:
        flash("Sila masukkan No. KP anda terlebih dahulu.", "warning")
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Fetch student base details
    cursor.execute("""
        SELECT no_pendaftaran_pelajar, tempat_lahir, no_surat_beranak, keadaan_mata, id_pakej 
        FROM pelajar WHERE no_kp_pelajar = %s
    """, (kp,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        flash("Sila lengkapkan Profil Pendaftaran utama terlebih dahulu di Langkah 1.", "warning")
        return redirect(url_for('index'))

    # =========================================================================
    # 🔒 NEW GATEKEEPER CHECK: Block access if a package has already been chosen
    # =========================================================================
    if student['id_pakej'] is not None and student['id_pakej'] != 0:
        cursor.close()
        conn.close()
        flash("Akses Ditutup: Anda telah menghantar pilihan pakej aliran pengajian anda. Sila hubungi guru bertugas untuk ubahsuai maklumat.", "warning")
        return redirect(url_for('index'))
    # =========================================================================

    # REQUIREMENT CHECK: Ensure Step 3 (Maklumat Tambahan) is complete first
    if not student['tempat_lahir'] or not student['no_surat_beranak'] or not student['keadaan_mata']:
        cursor.close()
        conn.close()
        flash("Akses Disekat: Sila lengkapkan Borang Maklumat Tambahan & Dokumen Sokongan terlebih dahulu.", "warning")
        return redirect(url_for('index'))

    student_id = student['no_pendaftaran_pelajar']
    eyes_status = str(student['keadaan_mata']).strip().upper()
    eyes_good = (eyes_status == 'BAIK')
    current_package_id = student['id_pakej']

    # 2. Fetch student's SPM grades
    cursor.execute("SELECT subjek, gred FROM spm_hasil WHERE no_pendaftaran_pelajar = %s", (student_id,))
    spm_results = cursor.fetchall()

    if not spm_results:
        cursor.close()
        conn.close()
        flash("Akses Disekat: Sila masukkan Keputusan Akademik SPM anda terlebih dahulu.", "warning")
        return redirect(url_for('index'))

    # Clean subject and grade collections
    grades = {str(row['subjek']).strip().upper(): str(row['gred']).strip().upper() for row in spm_results}

    def pass_c(subject_name):
        gred = grades.get(subject_name)
        return gred in ['A+', 'A', 'A-', 'B+', 'B', 'C+', 'C']

    has_math_c = pass_c('MATEMATIK')
    has_science_c = (
        pass_c('SAINS') or pass_c('KIMIA') or pass_c('BIOLOGI') or 
        pass_c('FIZIK') or pass_c('KIMIA BIOLOGI')
    )

    # 3. Qualification filter lists matching institutional matrices
    eligible_prefixes = []
    if has_math_c:
        if has_science_c:
            eligible_prefixes = ['BK', 'CK', 'FK', 'AH', 'CV', 'AP', 'BP', 'BS', 'BY', 'GB', 'GP', 'HT', 'HP', 'HY', 'VB', 'VS'] if eyes_good else ['BK', 'CK', 'FK', 'AH', 'AP', 'BP', 'BS', 'BY', 'GB', 'GP', 'HT', 'HP', 'HY']
        else:
            eligible_prefixes = ['AH', 'CV', 'AP', 'BP', 'BS', 'BY', 'GB', 'GP', 'HT', 'HP', 'HY', 'VB', 'VS'] if eyes_good else ['AH', 'AP', 'BP', 'BS', 'BY', 'GB', 'GP', 'HT', 'HP', 'HY']
    else:
        if has_science_c:
            eligible_prefixes = ['AH', 'CV', 'AP', 'BP', 'BS', 'BY', 'GB', 'GP', 'HT', 'HP', 'HY', 'VB', 'VS'] if eyes_good else ['AH', 'AP', 'BP', 'BS', 'BY', 'GB', 'GP', 'HT', 'HP', 'HY']
        else:
            eligible_prefixes = ['AH', 'CV', 'AP', 'BP', 'BS', 'BY', 'GB', 'GP', 'HT', 'HP', 'HY', 'VB', 'VS'] if eyes_good else ['AH', 'AP', 'BP', 'BY', 'GB', 'GP', 'HT', 'HP', 'HY']

    # 4. Fetch the real-time registration counts per package dynamically
    cursor.execute("""
        SELECT id_pakej, COUNT(*) as total_registered 
        FROM pelajar 
        WHERE id_pakej IS NOT NULL AND id_pakej != 0 
        GROUP BY id_pakej
    """)
    counts_rows = cursor.fetchall()
    package_counts = {row['id_pakej']: row['total_registered'] for row in counts_rows}

    # 5. Pull internal institutional packages alongside their mapped subjects
    cursor.execute("""
        SELECT p.id_pakej, p.kod_pakej, p.aliran, s.nama_subjek 
        FROM pakej p
        JOIN pakej_subjek ps ON p.id_pakej = ps.id_pakej
        JOIN subjek_stpm s ON ps.id_subjek = s.id_subjek
        WHERE p.status_aktif = 1
        ORDER BY p.kod_pakej, s.nama_subjek
    """)
    all_rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # 6. Build the dynamic view list filtering by requirements and full capacity limits
    packages_map = {}
    for row in all_rows:
        raw_kod = str(row['kod_pakej']).strip()
        kod_upper = raw_kod.upper()
        p_id = row['id_pakej']
        
        # Strip trailing numeric tokens to extract clean letters (e.g., BK1 -> BK)
        prefix = ''.join([char for char in kod_upper if char.isalpha()])
        
        # Rule Check A: Remove package from visibility if student lacks prerequisites
        if prefix not in eligible_prefixes:
            continue

        # Rule Check B: Enforce customized institutional seating caps
        current_enrollment = package_counts.get(p_id, 0)
        
        if prefix in ['BK', 'FK', 'CK']:
            max_limit = 20
        elif prefix == 'CV':
            max_limit = 30
        else:
            max_limit = 45

        # If a class is full, hide it entirely.
        # Exception: Keep showing the choice if the current student is already the one holding that seat!
        if current_enrollment >= max_limit and p_id != current_package_id:
            continue

        if raw_kod not in packages_map:
            packages_map[raw_kod] = {
                'id_pakej': p_id,
                'kod_pakej': raw_kod, 
                'aliran': row['aliran'],
                'kekosongan': max_limit - current_enrollment,
                'had_maksimum': max_limit,
                'subjek': []
            }
        packages_map[raw_kod]['subjek'].append(row['nama_subjek'])

    return render_template(
        'package.html', 
        packages=list(packages_map.values()), 
        current_package_id=current_package_id,
        math_pass=has_math_c,
        science_pass=has_science_c,
        eyes_good=eyes_good
    )

@app.route('/submit_package', methods=['POST'])
def submit_package():
    """Saves the student's chosen package ID directly to the MySQL database."""
    kp = session.get('verified_kp')
    if not kp:
        flash("Sila masukkan No. KP anda terlebih dahulu.", "warning")
        return redirect(url_for('gateway'))

    selected_package_id = request.form.get('pilihan_pakej')
    
    if not selected_package_id:
        flash("Gagal menyimpan: Anda tidak memilih sebarang pakej aliran.", "danger")
        return redirect(url_for('package_page'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Save the choice directly into the student table row
        cursor.execute("""
            UPDATE pelajar 
            SET id_pakej = %s 
            WHERE no_kp_pelajar = %s
        """, (selected_package_id, kp))
        
        conn.commit()
        flash("Pilihan pakej aliran pengajian anda berjaya didaftarkan ke dalam sistem!", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f"Ralat Sistem: Gagal menyimpan data pakej. Puncanya: {err}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))


# =====================================================================
# --- ADMINISTRATIVE CONTROL PANEL MODULES ---
# =====================================================================

@app.route('/admin/students-list', methods=['GET'])
def admin_view_students_list():
    """
    Unified endpoint yang menarik data pelajar, mengira jumlah pendapatan waris,
    serta bilangan gred A secara dinamik berpandukan schema SQL SMIS yang tepat.
    """
    if session.get('role') != 'admin':
        flash("Akses Ditolak: Hak pentadbir sistem diperlukan untuk melihat halaman ini.", "warning")
        return redirect(url_for('gateway'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Mengambil parameter tapisan daripada URL (?search=...&gender=...)
    search_query = request.args.get('search', '').strip()
    gender_filter = request.args.get('gender', '')
    race_filter = request.args.get('race', '')
    
    try:
        # Query yang diselaraskan tepat dengan lajur jadual pelajar, penjaga, dan pakej anda
        query = """
            SELECT 
                p.no_pendaftaran_pelajar,
                p.nama_pelajar,
                p.no_kp_pelajar,
                p.jantina,
                p.bangsa,
                p.status_study,
                k.kod_pakej,
                COALESCE((
                    SELECT SUM(j.pendapatan) 
                    FROM penjaga j 
                    WHERE j.no_pendaftaran_pelajar = p.no_pendaftaran_pelajar
                ), 0.00) AS total_income,
                COALESCE((
                    SELECT COUNT(*) 
                    FROM spm_hasil s 
                    WHERE s.no_pendaftaran_pelajar = p.no_pendaftaran_pelajar 
                      AND (s.gred = 'A+' OR s.gred = 'A' OR s.gred = 'A-')
                ), 0) AS total_as
            FROM pelajar p
            LEFT JOIN pakej k ON p.id_pakej = k.id_pakej
            WHERE 1=1
        """
        params = []
        
        # Tapisan carian nama atau IC
        if search_query:
            query += " AND (p.nama_pelajar LIKE %s OR p.no_kp_pelajar LIKE %s)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
            
        # Tapisan Jantina (LELAKI / PEREMPUAN)
        if gender_filter:
            query += " AND p.jantina = %s"
            params.append(gender_filter)
            
        # Tapisan Bangsa (MELAYU / CINA / INDIA / LAIN-LAIN / BUKAN WARGANEGARA)
        if race_filter:
            query += " AND p.bangsa = %s"
            params.append(race_filter)
            
        query += " ORDER BY p.no_pendaftaran_pelajar ASC"
        
        cursor.execute(query, tuple(params))
        all_students = cursor.fetchall()
        
    except mysql.connector.Error as err:
        # AMAT PENTING: Ini akan mencetak ralat sebenar di terminal/command prompt anda untuk rujukan debugging
        print(f"\n[Ralat SQL Terperinci]: {err}\n")
        all_students = []
        flash(f"Ralat pangkalan data: Mesej gagal dimuat turun.", "danger")
        
    finally:
        cursor.close()
        conn.close()
        
    return render_template('students_list.html', students=all_students)


@app.route('/admin/student-profile/<int:student_id>', methods=['GET'])
def admin_view_profile(student_id):
    """
    Fetches every data point submitted by a specific student, 
    including profile information, guardians, and academic results.
    """
    if session.get('role') != 'admin':
        flash("Akses Ditolak: Hak pentadbir sistem diperlukan.", "warning")
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch complete profile data from the pelajar table joined with the chosen package
        student_query = """
            SELECT p.*, k.kod_pakej, k.aliran 
            FROM pelajar p
            LEFT JOIN pakej k ON p.id_pakej = k.id_pakej
            WHERE p.no_pendaftaran_pelajar = %s
        """
        cursor.execute(student_query, (student_id,))
        student_data = cursor.fetchone()

        if not student_data:
            flash("Rekod pelajar tidak ditemui dalam sistem.", "danger")
            return redirect(url_for('admin_view_students_list'))

        # Fetch all registered parents/guardians for this student
        cursor.execute("""
            SELECT * FROM penjaga 
            WHERE no_pendaftaran_pelajar = %s 
            ORDER BY no_penjaga ASC
        """, (student_id,))
        guardians_data = cursor.fetchall()

        # Fetch academic summary list from spm_hasil
        cursor.execute("""
            SELECT subjek, gred FROM spm_hasil 
            WHERE no_pendaftaran_pelajar = %s 
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

    return render_template(
        'profile.html', 
        student=student_data, 
        guardians=guardians_data, 
        spm=spm_data, 
        is_admin=True
    )

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if session.get('role') != 'admin':
        flash("Akses Ditolak.", "warning")
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        enabled_forms = request.form.getlist('enabled_forms')
        
        # Disable all first
        cursor.execute("UPDATE form_settings SET is_enabled = FALSE")
        # Enable the checked ones
        for form_id in enabled_forms:
            cursor.execute("UPDATE form_settings SET is_enabled = TRUE WHERE form_id = %s", (form_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return redirect(url_for('admin_settings'))
        
    # Display settings
    cursor.execute("SELECT * FROM form_settings")
    settings = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_settings.html', settings=settings)

@app.route('/admin/statistics')
def admin_statistics():
    # Ensure only admins can access this route
    if session.get('role') != 'admin':
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. KPI Numbers
    cursor.execute("SELECT COUNT(*) as total FROM pelajar")
    total_students = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(DISTINCT id_pakej) as total FROM pakej")
    total_packages = cursor.fetchall()[0]['total']

    # 2. Get list of packages for the filter
    cursor.execute("SELECT id_pakej, kod_pakej FROM pakej")
    all_packages = cursor.fetchall()

    # 3. Handle Filters
    category = request.args.get('type', 'jantina')
    selected_pkg = request.args.get('package_id', 'all')
    
    map_cols = {
        'jantina': 'jantina',
        'bangsa': 'bangsa',
        'agama': 'agama',
        'cara_datang': 'cara_datang_sekolah'
    }
    col = map_cols.get(category, 'jantina')
    
    # 4. Construct Dynamic Query
    query = f"""
        SELECT 
            COALESCE(k.nama_pakej, 'Belum Dipilih') as nama_pakej, 
            p.{col} as category, 
            COUNT(*) as total
        FROM pelajar p
        LEFT JOIN pakej k ON p.id_pakej = k.id_pakej
        WHERE 1=1
    """
    params = []
    if selected_pkg != 'all':
        query += " AND p.id_pakej = %s"
        params.append(selected_pkg)
    
    query += f" GROUP BY k.nama_pakej, p.{col} ORDER BY k.nama_pakej ASC"

    cursor.execute(query, tuple(params))
    stats = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return render_template('statistics.html', 
                           stats=stats, 
                           total_students=total_students, 
                           total_packages=total_packages,
                           all_packages=all_packages,
                           current_type=category,
                           current_pkg=selected_pkg)

if __name__ == '__main__':
    app.run(debug=True)