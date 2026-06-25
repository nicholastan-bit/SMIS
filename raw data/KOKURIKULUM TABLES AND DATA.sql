-- FILE FOR KOKURIKULUM
CREATE TABLE UnitKokurikulum (
    unit_id INT AUTO_INCREMENT PRIMARY KEY,
    unit_type ENUM('Kelab', 'Badan Beruniform', 'Sukan dan Permainan') NOT NULL,
    unit_name VARCHAR(100) NOT NULL
);

CREATE TABLE KokurikulumPelajar (
    kkplr_id INT AUTO_INCREMENT PRIMARY KEY,
    bil_kemasukan INT NOT NULL, -- Links to your pelajar table
    unit_id INT NOT NULL,       -- Links to UnitKokurikulum
    jawatan VARCHAR(30) DEFAULT 'AHLI',
    merit INT DEFAULT 0,
    
	-- Prevents the same student from being added to the same unit twice
    UNIQUE KEY unique_student_unit (bil_kemasukan, unit_id),

    -- Foreign Keys
    CONSTRAINT fk_kp_pelajar FOREIGN KEY (bil_kemasukan) REFERENCES pelajar(bil_kemasukan) ON DELETE CASCADE,
    CONSTRAINT fk_kp_unit FOREIGN KEY (unit_id) REFERENCES UnitKokurikulum(unit_id) ON DELETE CASCADE
);
-- insert code

INSERT INTO UnitKokurikulum (unit_type, unit_name) VALUES
-- Kelab
('Kelab', 'PERSATUAN BAHASA DAN KESUSASTERAAN'),
('Kelab', 'KELAB ALAM SEKITAR TINGKATAN ENAM'),
('Kelab', 'KELAB FOTOGRAFI'),
('Kelab', 'KELAB INOVASI/REKACIPTA'),
('Kelab', 'KELAB PENGGUNA'),
('Kelab', 'KELAB KESENIAN DAN KEBUDAYAAN'),
('Kelab', 'KELAB KOPERASI SEKOLAH'),
('Kelab', 'KELAB RUKUN NEGARA'),
('Kelab', 'PERSATUAN SAINS TEKNOLOGI, KEJURUTERAAN DAN MATEMATIK'),
('Kelab', 'PERSATUAN SEJARAH DAN PATRIOTISME TINGKATAN ENAM'),
('Kelab', 'PERSATUAN SENI VISUAL'),

-- Badan Beruniform
('Badan Beruniform', 'PANDU PUTERI MALAYSIA'),
('Badan Beruniform', 'PASUKAN KOR KADET POLIS'),
('Badan Beruniform', 'PERGERAKAN PUTERI ISLAM MALAYSIA'),
('Badan Beruniform', 'PERSEKUTUAN PENGAKAP MALAYSIA'),
('Badan Beruniform', 'PISPA'),
('Badan Beruniform', 'BULAN SABIT MERAH MALAYSIA'),

-- Sukan dan Permainan
('Sukan dan Permainan', 'BADMINTON'),
('Sukan dan Permainan', 'BOLA KERANJANG'),
('Sukan dan Permainan', 'BOLA JARING'),
('Sukan dan Permainan', 'BOLA TAMPAR'),
('Sukan dan Permainan', 'CATUR'),
('Sukan dan Permainan', 'FUTSAL'),
('Sukan dan Permainan', 'PETANQUE'),
('Sukan dan Permainan', 'PING PONG');