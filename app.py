from flask import Flask, render_template, request, redirect, url_for, flash
from db.db_config import db_config
import mysql.connector

app = Flask(__name__)
app.secret_key = 'vibe_coding_key'

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/submit', methods=['POST'])
def submit():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Grab Student Data from Form
        student_data = (
            request.form['nama_pelajar'], request.form['email'], request.form['no_kp_pelajar'],
            request.form['jantina'], request.form['bangsa'], request.form['agama'],
            request.form['tarikh_lahir'], request.form['alamat_rumah'],
            request.form['telefonNo'], 1 if 'warganegara' in request.form else 0,
            request.form['sekolah_tamat'], request.form['masalah_kesihatan'],
            request.form['cara_datang_sekolah'], 1 # status_study default active
        )

        # 2. Insert into 'pelajar'
        student_query = """INSERT INTO pelajar 
            (nama_pelajar, email, no_kp_pelajar, jantina, bangsa, agama, tarikh_lahir, alamat_rumah, 
            telefonNo, warganegara, sekolah_tamat, masalah_kesihatan, cara_datang_sekolah, status_study) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        cursor.execute(student_query, student_data)
        
        # 3. Get the ID of the student we just created
        student_id = cursor.lastrowid

        # 4. Grab Guardian Data
        guardian_data = (
            student_id, request.form['g_nama_penjaga'], request.form['g_no_kp_penjaga'],
            request.form['g_hubungan'], request.form['g_pekerjaan'],
            request.form['g_pendapatan'], request.form['g_alamat_kerja']
        )

        # 5. Insert into 'penjaga'
        guardian_query = """INSERT INTO penjaga 
            (no_pendaftaran_pelajar, nama_penjaga, no_kp_penjaga, penjaga, pekerjaan, pendapatan, alamat_tempat_kerja) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        
        cursor.execute(guardian_query, guardian_data)

        conn.commit()
        flash("Registration Successful!")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))

@app.route('/students')
def view_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Join the two tables using the foreign key
    query = """
        SELECT 
            p.no_pendaftaran_pelajar, p.nama_pelajar, p.no_kp_pelajar, p.jantina, p.telefonNo,
            g.nama_penjaga AS nama_penjaga, g.penjaga AS hubungan, g.no_kp_penjaga AS g_kp
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
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch ALL columns from both tables for this specific student
    query = """
        SELECT p.*, g.* 
        FROM pelajar p
        LEFT JOIN penjaga g ON p.no_pendaftaran_pelajar = g.no_pendaftaran_pelajar
        WHERE p.no_pendaftaran_pelajar = %s
    """

    cursor.execute(query, (student_id,))
    student_data = cursor.fetchone()

    cursor.close()
    conn.close()

    if student_data:
        return render_template('profile.html', student=student_data)
    else:
        flash("Pelajar tidak dijumpai.")
        return redirect(url_for('view_students'))

if __name__ == '__main__':
    app.run(debug=True) 