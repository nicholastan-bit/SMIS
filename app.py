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
            
        return redirect(url_for('register_page'))
        
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
            return redirect(url_for('view_students')) 
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
    return render_template('index.html')

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
        # Check if we are updating or inserting
        kp = request.form['no_kp_pelajar']
        cursor.execute("SELECT no_pendaftaran_pelajar FROM pelajar WHERE no_kp_pelajar = %s", (kp,))
        existing = cursor.fetchone()

        student_data = (
            request.form['nama_pelajar'], request.form['email'], kp,
            request.form['jantina'], request.form['bangsa'], request.form['agama'],
            request.form['tarikh_lahir'], request.form['alamat_rumah'],
            request.form['telefonNo'], 1 if 'warganegara' in request.form else 0,
            request.form['sekolah_tamat'], request.form['masalah_kesihatan'],
            request.form['cara_datang_sekolah'], 1
        )

        if existing:
            # UPDATE existing record
            s_id = existing[0]
            update_query = """UPDATE pelajar SET 
                nama_pelajar=%s, email=%s, no_kp_pelajar=%s, jantina=%s, bangsa=%s, agama=%s, 
                tarikh_lahir=%s, alamat_rumah=%s, telefonNo=%s, warganegara=%s, 
                sekolah_tamat=%s, masalah_kesihatan=%s, cara_datang_sekolah=%s, status_study=%s 
                WHERE no_pendaftaran_pelajar=%s"""
            cursor.execute(update_query, student_data + (s_id,))
            flash("Maklumat berjaya dikemaskini!")
        else:
            # INSERT new record
            insert_query = """INSERT INTO pelajar 
                (nama_pelajar, email, no_kp_pelajar, jantina, bangsa, agama, tarikh_lahir, alamat_rumah, 
                telefonNo, warganegara, sekolah_tamat, masalah_kesihatan, cara_datang_sekolah, status_study) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(insert_query, student_data)
            s_id = cursor.lastrowid
            
            # Also handle new guardian record if it's a new student
            guardian_data = (
                s_id, request.form['g_nama_penjaga'], request.form['g_no_kp_penjaga'],
                request.form['g_hubungan'], request.form['g_pekerjaan'],
                request.form['g_pendapatan'], request.form['g_alamat_kerja']
            )
            guardian_query = """INSERT INTO penjaga 
                (no_pendaftaran_pelajar, nama_penjaga, no_kp_penjaga, penjaga, pekerjaan, pendapatan, alamat_tempat_kerja) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(guardian_query, guardian_data)
            flash("Pendaftaran baru berjaya!")

        conn.commit()
        session.pop('verified_kp', None) # Clear verification after submission
        session.pop('existing_data', None)
    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

@app.route('/students_list')
def view_students():
    if not session.get('admin_logged'):
        flash("Akses Pentadbir sahaja.")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            p.no_pendaftaran_pelajar, p.nama_pelajar, p.no_kp_pelajar, p.jantina, p.telefonNo,
            g.nama_penjaga, g.penjaga AS hubungan
        FROM pelajar p
        LEFT JOIN penjaga g ON p.no_pendaftaran_pelajar = g.no_pendaftaran_pelajar
    """
    cursor.execute(query)
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('students_list.html', students=students)

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