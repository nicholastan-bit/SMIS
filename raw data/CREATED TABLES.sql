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
('penjaga_form', TRUE),
('kokurikulum_form', TRUE);

CREATE TABLE pelajar_eligibility (
    no_kp_pelajar VARCHAR(20) NOT NULL,
    subjek_khas ENUM('SYARIAH', 'SAINS SUKAN') NOT NULL,
    PRIMARY KEY (no_kp_pelajar, subjek_khas)
);

-- ignore above if already insert

-- 1. MASTER TABLE: PAKEJ
CREATE TABLE pakej (
    id_pakej INT AUTO_INCREMENT PRIMARY KEY,
    kod_pakej VARCHAR(20) NOT NULL UNIQUE, -- Increased length for the /1 suffix
    nama_pakej VARCHAR(100) NULL,
    aliran ENUM('SAINS', 'SAINS SOSIAL') NOT NULL,
    status_aktif TINYINT(1) DEFAULT 1,
    semester INT NOT NULL DEFAULT 1
);

CREATE TABLE subjek_stpm (
    id_subjek INT AUTO_INCREMENT PRIMARY KEY,
    kod_pakej_subjek VARCHAR(10) NOT NULL UNIQUE, -- Renamed for clarity
    nama_subjek VARCHAR(100) NOT NULL
);

CREATE TABLE pakej_subjek (
    id_pakej INT NOT NULL,
    id_subjek INT NOT NULL,
    PRIMARY KEY (id_pakej, id_subjek),
    FOREIGN KEY (id_pakej) REFERENCES pakej(id_pakej) ON DELETE CASCADE,
    FOREIGN KEY (id_subjek) REFERENCES subjek_stpm(id_subjek) ON DELETE RESTRICT
);

CREATE TABLE pelajar (
	bil_kemasukan INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
	nama_pelajar VARCHAR(100) DEFAULT NULL,
	email VARCHAR(100) DEFAULT NULL,
	no_kp_pelajar VARCHAR(20) UNIQUE DEFAULT NULL,
	jantina ENUM('LELAKI', 'PEREMPUAN') DEFAULT NULL,
	bangsa ENUM('MELAYU', 'CINA', 'INDIA', 'SABAH/SARAWAK', 'BUKAN WARGANEGARA') DEFAULT NULL,
	agama ENUM('ISLAM', 'BUDDHA', 'HINDU', 'KRISTIAN', 'SIKH', 'LAIN-LAIN') DEFAULT NULL,
	tarikh_lahir DATE DEFAULT NULL,
	alamat_rumah TEXT,
	telefonNo VARCHAR(20) DEFAULT NULL,
	sekolah_tamat DATE DEFAULT NULL, -- SEKOLAH TAMAT UNTUK STPM
	masalah_kesihatan TEXT,
	cara_datang_sekolah ENUM('JALAN', 'KERETA', 'MOTOR', 'BASIKAL', 'BAS', 'LAIN-LAIN') DEFAULT NULL,
	tempat_lahir VARCHAR(200) DEFAULT NULL,
	no_surat_beranak VARCHAR(50) DEFAULT NULL,
	masalah_penglihatan ENUM('YA', 'TIDAK') DEFAULT NULL,
	status_study TINYINT(1) DEFAULT NULL,
	spm_slip_blob LONGBLOB,
	spm_slip_filename VARCHAR(100) DEFAULT NULL,
	surat_tawaran_path VARCHAR(255) DEFAULT NULL,
	ic_photo_path VARCHAR(255) DEFAULT NULL,
	id_pakej INT DEFAULT NULL,
    aliran_ditawar ENUM('SAINS', 'SAINS SOSIAL') DEFAULT NULL,
    status_oku ENUM('TIDAK', 'YA') DEFAULT 'TIDAK',
    kelas VARCHAR(10),
    tarikh_pendaftaran DATE,
    tugas_khas VARCHAR(50) DEFAULT NULL,
	rumah_sukan VARCHAR(20) DEFAULT NULL,
    semester TINYINT(1) DEFAULT NULL,
	CONSTRAINT fk_pelajar_pakej FOREIGN KEY (id_pakej) REFERENCES pakej (id_pakej) ON DELETE SET NULL
) AUTO_INCREMENT = 19207 ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Jadual Penjaga
CREATE TABLE penjaga (
    no_penjaga INT AUTO_INCREMENT PRIMARY KEY,
    bil_kemasukan INT,
    nama_penjaga VARCHAR(100),
    no_kp_penjaga VARCHAR(20),
    no_telefon VARCHAR(20),
    hubungan ENUM('IBU', 'BAPA', 'PENJAGA'),
    pekerjaan VARCHAR(50),
    pendapatan DECIMAL(10, 2),
    alamat_tempat_kerja TEXT,
    FOREIGN KEY (bil_kemasukan) REFERENCES pelajar(bil_kemasukan) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Jadual Keputusan SPM
CREATE TABLE spm_hasil (
    id_spm INT AUTO_INCREMENT PRIMARY KEY,
    bil_kemasukan INT,
    subjek VARCHAR(100) NOT NULL,
    gred VARCHAR(5) NOT NULL,
    FOREIGN KEY (bil_kemasukan) REFERENCES pelajar(bil_kemasukan) ON DELETE CASCADE,
    UNIQUE KEY student_subject (bil_kemasukan, subjek)
) ENGINE=InnoDB;

-- new changes 25/6/2026: SEMESTER ATTR REPLACEMENT
ALTER TABLE pelajar
ADD COLUMN semester TINYINT;