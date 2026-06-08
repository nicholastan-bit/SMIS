from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from db.db_config import db_config
import mysql.connector
import os
from werkzeug.utils import secure_filename

PACKAGE_LIMITS = {
    'BK': 80, 'BK1': 20, 'BK2': 20, 'BK3': 20, 'BK4': 20,
    'FK': 60, 'FK1': 20, 'FK2': 20, 'FK3': 20,
    'CK': 20, 'CK1': 20,
    'CV': 30, 'CV1': 30,
    'AP': 135
    
}
DEFAULT_LIMIT = 45

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
        'penjaga': False # Added key
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
                
            # 4. Step 4 (Pakej)
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
        flash("Borang ini sedang ditutup oleh pentadbir.", "warning")
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
            cara_datang_sekolah, tempat_lahir, no_surat_beranak, keadaan_mata, 
            aliran_ditawar, status_oku, kelas, status_study
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
        ON DUPLICATE KEY UPDATE 
            nama_pelajar=VALUES(nama_pelajar), email=VALUES(email), jantina=VALUES(jantina),
            bangsa=VALUES(bangsa), agama=VALUES(agama), tarikh_lahir=VALUES(tarikh_lahir),
            alamat_rumah=VALUES(alamat_rumah), telefonNo=VALUES(telefonNo), 
            sekolah_tamat=VALUES(sekolah_tamat), masalah_kesihatan=VALUES(masalah_kesihatan),
            cara_datang_sekolah=VALUES(cara_datang_sekolah), tempat_lahir=VALUES(tempat_lahir),
            no_surat_beranak=VALUES(no_surat_beranak), keadaan_mata=VALUES(keadaan_mata),
            aliran_ditawar=VALUES(aliran_ditawar), status_oku=VALUES(status_oku), kelas=VALUES(kelas)
    """

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
        request.form.get('no_surat_beranak'), request.form.get('keadaan_mata'),
        request.form.get('aliran_ditawar'), request.form.get('status_oku'), request.form.get('kelas')
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
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    # Check if student exists and see if fields are already filled
    cursor.execute("""
        SELECT bil_kemasukan, tempat_lahir, no_surat_beranak, keadaan_mata 
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
        flash("Sila lengkapkan Profil Pendaftaran utama terlebih dahulu.", "warning")
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
        flash("Borang ini sedang ditutup oleh pentadbir.", "warning")
        return redirect(url_for('index'))
    
    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 1. Fetch student base details
    cursor.execute("""
        SELECT bil_kemasukan, nama_pelajar, no_surat_beranak, keadaan_mata, id_pakej 
        FROM pelajar WHERE no_kp_pelajar = %s
    """, (kp,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        flash("Sila lengkapkan Profil Pendaftaran utama terlebih dahulu.", "warning")
        return redirect(url_for('index'))
    
    if not student.get('nama_pelajar') or not student.get('no_surat_beranak') or not student.get('keadaan_mata'):
        cursor.close()
        conn.close()
        flash("Akses Disekat: Sila lengkapkan Profil dan Borang Dokumen Pelajar.", "warning")
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
        flash("Borang ini sedang ditutup oleh pentadbir.", "warning")
        return redirect(url_for('index'))

    kp = session.get('verified_kp')
    if not kp:
        return redirect(url_for('gateway'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 1. Fetch student base details
    cursor.execute("""
        SELECT bil_kemasukan, tempat_lahir, no_surat_beranak, keadaan_mata, id_pakej 
        FROM pelajar WHERE no_kp_pelajar = %s
    """, (kp,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        flash("Sila lengkapkan Profil Pendaftaran utama terlebih dahulu.", "warning")
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
        flash("Sila lengkapkan Profil Pelajar terlebih dahulu.", "warning")
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
        flash("Gagal mengemaskini maklumat akademik.", "warning")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

# --- PILIHAN PAKEJ ROUTES ---

@app.route('/package', methods=['GET'])
def package_page():
    if not is_form_enabled('pakej_form'):
        flash("Borang ini sedang ditutup oleh pentadbir.", "warning")
        return redirect(url_for('index'))

    kp = session.get('verified_kp')
    if not kp:
        flash("Sila masukkan No. KP anda terlebih dahulu.", "warning")
        return redirect(url_for('gateway'))

    # 1. Define Capacity Limits
    DEFAULT_LIMIT = 45
    DECOY_IDS = [1, 6, 8, 12, 14, 16, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Fetch student details
    cursor.execute("""
        SELECT bil_kemasukan, tempat_lahir, no_surat_beranak, keadaan_mata, id_pakej, aliran_ditawar 
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
        flash("Akses Disekat: Sila lengkapkan keputusan SPM anda terlebih dahulu.", "warning")
        return redirect(url_for('index'))

    # Fetch current enrollment counts for all packages to enforce limits
    cursor.execute("SELECT id_pakej, COUNT(*) as current_count FROM pelajar WHERE id_pakej IS NOT NULL GROUP BY id_pakej")
    enrollment_data = {row['id_pakej']: row['current_count'] for row in cursor.fetchall()}

    # Check for student existence and required docs
    if not student.get('tempat_lahir') or not student.get('no_surat_beranak') or not student.get('keadaan_mata'):
        cursor.close()
        conn.close()
        flash("Akses Disekat: Sila lengkapkan Profil dan Borang Dokumen Pelajar.", "warning")
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
    eyes_good = (str(student['keadaan_mata']).strip().upper() == 'BAIK')

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
    cursor.close()
    conn.close()

    # ... inside your package_page function, after cursor.fetchall() ...

    # Build response map
    packages_map = {}
    for row in all_rows:
        # 1. Filter: ONLY show decoy packages.
        # If the code contains '/', it's a semester-specific class, so skip it.
        if '/' in row['kod_pakej']:
            continue
        
        # 2. Eligibility logic
        is_allowed = any(row['kod_pakej'].startswith(prefix) for prefix in allowed_prefixes)
        
        # 3. Capacity logic
        limit = PACKAGE_LIMITS.get(row['kod_pakej'], DEFAULT_LIMIT)
        current_count = enrollment_data.get(row['id_pakej'], 0)

        # Only add if allowed by stream AND has space
        if is_allowed and current_count < limit:
            if row['kod_pakej'] not in packages_map:
                packages_map[row['kod_pakej']] = {
                    'id_pakej': row['id_pakej'], 
                    'kod_pakej': row['kod_pakej'], 
                    'aliran': row['aliran'], 
                    'subjek': [], 
                    'kekosongan': limit - current_count,
                    'had_maksimum': limit
                }
            if row['nama_subjek']:
                packages_map[row['kod_pakej']]['subjek'].append(row['nama_subjek'])
    
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

    # 1. Fetch package details to get the code and define the limit
    cursor.execute("SELECT kod_pakej FROM pakej WHERE id_pakej = %s", (selected_package_id,))
    pkg = cursor.fetchone()
    
    if not pkg:
        cursor.close()
        conn.close()
        flash("Pakej tidak sah.", "danger")
        return redirect(url_for('package_page'))

    kod_pakej = pkg['kod_pakej']
    limit = PACKAGE_LIMITS.get(kod_pakej, 45)

    # 2. Re-verify the limit based on the actual kod_pakej
    # Match the logic you defined in package_page()

    # 3. Check current count
    cursor.execute("SELECT COUNT(*) as count FROM pelajar WHERE id_pakej = %s", (selected_package_id,))
    current_count = cursor.fetchone()['count']
    
    if current_count >= limit:
        cursor.close()
        conn.close()
        flash(f"Maaf, pakej {kod_pakej} telah penuh ({current_count}/{limit}).", "danger")
        return redirect(url_for('package_page'))
    
    try:
        cursor.execute("""
            UPDATE pelajar 
            SET id_pakej = %s 
            WHERE no_kp_pelajar = %s
        """, (selected_package_id, kp))
        
        conn.commit()
        flash("Pilihan pakej berjaya didaftarkan!", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f"Ralat Sistem: {err}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))


# =====================================================================
# --- ADMINISTRATIVE CONTROL PANEL MODULES ---
# =====================================================================

@app.route('/admin/students-list')
def admin_view_students_list():
    # 1. Pagination Setup
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    sort_filter = request.args.get('sort', '')
    class_filter = request.args.get('class_filter', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 2. Base Query (Used for filtering)
    where_clause = "WHERE 1=1"
    params = []
    
    if search:
        where_clause += " AND (nama_pelajar LIKE %s OR no_kp_pelajar LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    if sort_filter == 'unassigned':
        where_clause += " AND pk.kod_pakej IS NOT NULL AND pk.kod_pakej REGEXP '^[^0-9]+$'"
    elif sort_filter == 'assigned':
        where_clause += " AND pk.kod_pakej IS NOT NULL AND pk.kod_pakej REGEXP '[0-9]'"
    if class_filter:
        where_clause += " AND TRIM(kelas) LIKE %s"
        params.append(class_filter.strip())

    # 3. Get total count for pagination
    count_query = f"SELECT COUNT(*) as total FROM pelajar p LEFT JOIN pakej pk ON p.id_pakej = pk.id_pakej {where_clause}"
    cursor.execute(count_query, params)
    total_students = cursor.fetchone()['total']
    total_pages = (total_students + per_page - 1) // per_page

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
                           search=search, sort=sort_filter, class_filter=class_filter)


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
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    cursor.execute("""
        SELECT bil_kemasukan, tempat_lahir, no_surat_beranak, keadaan_mata, id_pakej, aliran_ditawar 
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
        'email', 'jantina', 'bangsa', 'agama', 'telefonNo', 
        'alamat_rumah', 'cara_datang_sekolah', 'keadaan_mata', 
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
    if session.get('role') != 'admin':
        flash("Akses Ditolak.", "warning")
        return redirect(url_for('gateway'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

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
    
    form_labels = {
        'profil_form': 'Borang Maklumat Pelajar',
        'tambahan_form': 'Borang Dokumen Pelajar',
        'penjaga_form': 'Borang Maklumat Penjaga',
        'spm_form': 'Borang Keputusan SPM',
        'pakej_form': 'Borang Pemilihan Pakej'
    }
        
    # Display settings
    cursor.execute("SELECT * FROM form_settings")
    settings = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_settings.html', settings=settings, form_labels=form_labels)

@app.route('/statistics')
def statistics():
    # 1. Capture View Mode and Filters
    mode = request.args.get('mode', 'pakej')
    category = request.args.get('type', 'bangsa')
    filter_stream = request.args.get('filter_stream', 'semua')
    filter_sem = request.args.get('filter_sem', 'semua') # Capture Semester[cite: 1]
    
    if category not in ['jantina', 'bangsa', 'agama', 'cara_datang_sekolah']: 
        category = 'bangsa'

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 2. Logic: Define Stream
    def is_sains(kod):
        return any(prefix in kod for prefix in ['BK', 'CK', 'FK'])

    # 3. Fetch Items with filtering
    if mode == 'kelas':
        cursor.execute("SELECT DISTINCT kelas as id, kelas as label FROM pelajar WHERE kelas IS NOT NULL ORDER BY kelas")
        items = cursor.fetchall()
        group_col = "kelas"
    else:
        # Fetch packages and filter by semester[cite: 1]
        sem_query = "" if filter_sem == 'semua' else f" AND semester = {filter_sem}"
        cursor.execute(f"SELECT id_pakej as id, kod_pakej as label FROM pakej WHERE kod_pakej REGEXP '[0-9]'{sem_query}")
        all_packages = cursor.fetchall()
        
        # Stream Filtering
        if filter_stream == 'sains':
            items = [p for p in all_packages if is_sains(p['label'])]
        elif filter_stream == 'sosial':
            items = [p for p in all_packages if not is_sains(p['label'])]
        else:
            items = all_packages

        group_col = "p.id_pakej"

    # 4. Get distinct categories
    cursor.execute(f"SELECT DISTINCT {category} as cat FROM pelajar WHERE {category} IS NOT NULL")
    categories = [row['cat'] for row in cursor.fetchall()]
    genders = ['LELAKI', 'PEREMPUAN']

    # 5. Fetch counts with semester filter applied to SQL query[cite: 1]
    sem_filter_sql = "" if filter_sem == 'semua' else f" AND pk.semester = {filter_sem}"
    query = f"""
        SELECT {group_col} as group_id, p.{category} as cat, p.jantina, COUNT(*) as total
        FROM pelajar p
        LEFT JOIN pakej pk ON p.id_pakej = pk.id_pakej
        WHERE p.id_pakej IS NOT NULL {sem_filter_sql}
        GROUP BY group_id, {category}, jantina
    """
    cursor.execute(query)
    results = cursor.fetchall()

    # Initialize structure
    counts = {item['id']: {cat: {g: 0 for g in genders} for cat in categories} for item in items}
    
    for row in results:
        gid = row['group_id']
        cat_val = row['cat']
        if gid in counts and cat_val in counts[gid]:
            counts[gid][cat_val][row['jantina']] = row['total']

    # Totals logic
    col_totals = {cat: {'LELAKI': 0, 'PEREMPUAN': 0} for cat in categories}
    for item in items:
        for cat in categories:
            col_totals[cat]['LELAKI'] += counts[item['id']][cat]['LELAKI']
            col_totals[cat]['PEREMPUAN'] += counts[item['id']][cat]['PEREMPUAN']

    row_totals = {item['id']: sum(sum(counts[item['id']][cat].values()) for cat in categories) for item in items}
    grand_total = sum(row_totals.values())
    
    row_gender_totals = {}
    for item in items:
        iid = item['id']
        row_gender_totals[iid] = {
            'L': sum(counts[iid][cat]['LELAKI'] for cat in categories),
            'P': sum(counts[iid][cat]['PEREMPUAN'] for cat in categories)
        }
    
    grand_total_l = sum(row['L'] for row in row_gender_totals.values())
    grand_total_p = sum(row['P'] for row in row_gender_totals.values())

    return render_template('statistics.html', 
                           categories=categories, items=items, counts=counts,
                           row_totals=row_totals, col_totals=col_totals, grand_total=grand_total,
                           current_type=category, current_mode=mode, row_gender_totals=row_gender_totals,
                           filter_stream=filter_stream, filter_sem=filter_sem, # Pass filter_sem to template[cite: 1]
                           grand_total_l=grand_total_l, grand_total_p=grand_total_p)

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

if __name__ == '__main__':
    app.run(debug=True)