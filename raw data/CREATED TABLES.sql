-- 1. Hapus tabel jika sudah ada (Urutan dari yang memiliki Foreign Key terbanyak)
DROP TABLE IF EXISTS spm_hasil;
DROP TABLE IF EXISTS penjaga;
DROP TABLE IF EXISTS pelajar;

TRUNCATE TABLE penjaga;
TRUNCATE TABLE spm_hasil;
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE pelajar;
SET FOREIGN_KEY_CHECKS = 1;

SELECT * FROM pelajar;

-- 1. Jadual Pelajar
CREATE TABLE pelajar (
    no_pendaftaran_pelajar INT AUTO_INCREMENT PRIMARY KEY,
    id_pakej INT,
    nama_pelajar VARCHAR(100),
    email VARCHAR(100),
    no_kp_pelajar VARCHAR(20),
    jantina ENUM('LELAKI', 'PEREMPUAN'),
    bangsa ENUM('MELAYU', 'CINA', 'INDIA', 'SABAH/SARAWAK', 'BUKAN WARGANEGARA'),
    agama ENUM('ISLAM', 'BUDDHA', 'HINDU', 'KRISTIAN', 'SIKH', 'LAIN-LAIN'),
    tarikh_lahir DATE,
    alamat_rumah TEXT,
    telefonNo VARCHAR(20),
    sekolah_tamat DATE,
    masalah_kesihatan TEXT,
    cara_datang_sekolah ENUM('JALAN', 'KERETA', 'MOTOR', 'BASIKAL', 'BAS', 'LAIN-LAIN'),
    status_study TINYINT(1) DEFAULT 1,
    spm_slip_blob LONGBLOB,
    spm_slip_filename VARCHAR(100),
    FOREIGN KEY (id_pakej) REFERENCES pakej(id_pakej) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 2. Jadual Penjaga
CREATE TABLE penjaga (
    no_penjaga INT AUTO_INCREMENT PRIMARY KEY,
    no_pendaftaran_pelajar INT,
    nama_penjaga VARCHAR(100),
    no_kp_penjaga VARCHAR(20),
    no_telefon VARCHAR(20),
    penjaga ENUM('IBU', 'BAPA', 'PENJAGA'),
    pekerjaan VARCHAR(50),
    pendapatan DECIMAL(10, 2),
    alamat_tempat_kerja TEXT,
    FOREIGN KEY (no_pendaftaran_pelajar) REFERENCES pelajar(no_pendaftaran_pelajar) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Jadual Keputusan SPM
CREATE TABLE spm_hasil (
    id_spm INT AUTO_INCREMENT PRIMARY KEY,
    no_pendaftaran_pelajar INT,
    subjek VARCHAR(100) NOT NULL,
    gred VARCHAR(5) NOT NULL,
    FOREIGN KEY (no_pendaftaran_pelajar) REFERENCES pelajar(no_pendaftaran_pelajar) ON DELETE CASCADE,
    UNIQUE KEY student_subject (no_pendaftaran_pelajar, subjek)
) ENGINE=InnoDB;

-- 1. MASTER TABLE: PAKEJ
CREATE TABLE pakej (
    id_pakej INT AUTO_INCREMENT PRIMARY KEY,
    kod_pakej VARCHAR(10) NOT NULL UNIQUE,                               -- e.g., 'BK1', 'CK1', 'AH1'
    nama_pakej VARCHAR(100) NULL,                                       -- Optional descriptive name
    aliran ENUM('SAINS', 'SAINS SOSIAL') NOT NULL,                       -- Stream for statistics
    status_aktif TINYINT(1) DEFAULT 1                                    -- To soft-delete obsolete packages later
);

-- 2. MASTER TABLE: SUBJEK STPM
CREATE TABLE subjek_stpm (
    id_subjek INT AUTO_INCREMENT PRIMARY KEY,
    kod_subjek VARCHAR(10) NOT NULL UNIQUE,                             -- e.g., 'PA', 'MUET', 'KIM', 'EKO'
    nama_subjek VARCHAR(100) NOT NULL                                   -- e.g., 'Pengajian Am', 'Ekonomi'
);

-- 3. JUNCTION TABLE: PAKEJ_SUBJEK (Many-to-Many Bridge)
CREATE TABLE pakej_subjek (
    id_pakej INT NOT NULL,
    id_subjek INT NOT NULL,
    PRIMARY KEY (id_pakej, id_subjek),                                  -- Prevents duplicate subjects within the same package
    FOREIGN KEY (id_pakej) REFERENCES pakej(id_pakej) ON DELETE CASCADE,
    FOREIGN KEY (id_subjek) REFERENCES subjek_stpm(id_subjek) ON DELETE RESTRICT
);

CREATE TABLE form_settings (
    form_id VARCHAR(50) PRIMARY KEY,
    is_enabled BOOLEAN DEFAULT TRUE
);

-- Insert the default states
INSERT INTO form_settings (form_id, is_enabled) VALUES 
('profil_form', TRUE),
('spm_form', TRUE),
('tambahan_form', TRUE),
('pakej_form', TRUE),
('penjaga_form', TRUE);
