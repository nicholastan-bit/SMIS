-- 1. Hapus tabel jika sudah ada (Urutan dari yang memiliki Foreign Key terbanyak)
DROP TABLE IF EXISTS edit_logs;
DROP TABLE IF EXISTS spm_hasil;
DROP TABLE IF EXISTS penjaga;
DROP TABLE IF EXISTS pelajar;

-- 2. Buat ulang tabel Pelajar (Tabel Utama)
CREATE TABLE pelajar (
    no_pendaftaran_pelajar INT AUTO_INCREMENT PRIMARY KEY,
    nama_pelajar VARCHAR(100),
    email VARCHAR(100),
    no_kp_pelajar VARCHAR(20),
    jantina ENUM('LELAKI', 'PEREMPUAN'),
    bangsa ENUM('MELAYU','CINA','INDIA','LAIN-LAIN'),
    agama ENUM('ISLAM', 'BUDDHA', 'HINDU', 'KRISTIAN', 'SIKH', 'LAIN-LAIN'),
    tarikh_lahir DATE,
    alamat_rumah TEXT,
    telefonNo VARCHAR(20),
    warganegara TINYINT(1),
    sekolah_tamat DATE,
    masalah_kesihatan TEXT,
    cara_datang_sekolah ENUM('JALAN', 'KERETA', 'MOTOR', 'BASIKAL', 'BAS', 'LAIN-LAIN'),
    status_study TINYINT(1)
);

-- 3. Buat ulang tabel Penjaga
CREATE TABLE penjaga (
    no_penjaga INT AUTO_INCREMENT PRIMARY KEY,
    no_pendaftaran_pelajar INT,
    nama_penjaga VARCHAR(100),
    no_kp_penjaga VARCHAR(20),
    penjaga ENUM('IBU', 'BAPA', 'PENJAGA'),
    pekerjaan VARCHAR(50),
    pendapatan DECIMAL(10, 2),
    alamat_tempat_kerja TEXT,
    FOREIGN KEY (no_pendaftaran_pelajar) REFERENCES pelajar(no_pendaftaran_pelajar) ON DELETE CASCADE
);

-- 4. Buat ulang tabel Keputusan SPM
CREATE TABLE spm_hasil (
    id_spm INT AUTO_INCREMENT PRIMARY KEY,
    no_pendaftaran_pelajar INT,
    subjek VARCHAR(100) NOT NULL,
    gred VARCHAR(5) NOT NULL,
    FOREIGN KEY (no_pendaftaran_pelajar) REFERENCES pelajar(no_pendaftaran_pelajar) ON DELETE CASCADE,
    UNIQUE KEY student_subject (no_pendaftaran_pelajar, subjek)
);

-- 5. Buat ulang tabel Log Edit (Audit Trail)
CREATE TABLE edit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    no_pendaftaran_pelajar INT,
    edited_by VARCHAR(50), 
    action_details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (no_pendaftaran_pelajar) REFERENCES pelajar(no_pendaftaran_pelajar) ON DELETE CASCADE
);