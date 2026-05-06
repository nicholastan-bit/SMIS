-- student info table
CREATE TABLE pelajar (
	no_pendaftaran_pelajar INT AUTO_INCREMENT PRIMARY KEY,
    nama_pelajar VARCHAR(100),
    email VARCHAR(100),
    no_kp_pelajar VARCHAR(20),
    jantina ENUM('LELAKI', 'PEREMPUAN'),
    bangsa VARCHAR(20),
    agama VARCHAR(20),
    tarikh_lahir DATE,
    alamat_rumah TEXT,
    telefonNo VARCHAR(20),
    warganegara TINYINT(1),
    sekolah_tamat DATE,
    masalah_kesihatan TEXT,
    cara_datang_sekolah ENUM('JALAN', 'KERETA', 'MOTOR', 'BASIKAL', 'BAS', 'LAIN-LAIN'),
    status_study TINYINT(1)
);

-- guardian info table
CREATE TABLE penjaga (
	no_penjaga INT AUTO_INCREMENT PRIMARY KEY,
    no_pendaftaran_pelajar INT,
    nama_penjaga VARCHAR(100),
    no_kp_penjaga VARCHAR(20),
	penjaga ENUM('IBU', 'BAPA', 'PENJAGA'),
    pekerjaan VARCHAR(50),
    pendapatan DECIMAL(10, 2),
    alamat_tempat_kerja TEXT,
    FOREIGN KEY (no_pendaftaran_pelajar) REFERENCES pelajar(no_pendaftaran_pelajar)
);
