-- 1. Hapus tabel jika sudah ada (Urutan dari yang memiliki Foreign Key terbanyak)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS form_settings;
DROP TABLE IF EXISTS pakej;
DROP TABLE IF EXISTS pakej_subjek;
DROP TABLE IF EXISTS subjek_stpm;

DROP TABLE IF EXISTS pelajar;
DROP TABLE IF EXISTS pelajar_eligibility;
DROP TABLE IF EXISTS penjaga;
DROP TABLE IF EXISTS spm_hasil;
SET FOREIGN_KEY_CHECKS = 1;

# form_settings and pelajar_eligibility are left alone
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE pelajar;
SET FOREIGN_KEY_CHECKS = 1;
-- the code below resets the entire stpm package and subjects
-- WARN: pelajar's id_pakej will be NULL if they picked
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS pakej;
DROP TABLE IF EXISTS pakej_subjek;
DROP TABLE IF EXISTS subjek_stpm;
SET FOREIGN_KEY_CHECKS = 1;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE pakej_subjek;
TRUNCATE TABLE subjek_stpm;
TRUNCATE TABLE pakej;
SET FOREIGN_KEY_CHECKS = 1;

-- the code below resets data for all tables related to pelajar
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE pelajar;
TRUNCATE TABLE spm_hasil;
TRUNCATE TABLE penjaga;
TRUNCATE TABLE pelajar_eligibility; -- extra
SET FOREIGN_KEY_CHECKS = 1;
ALTER TABLE pelajar AUTO_INCREMENT = 19207;

UPDATE PELAJAR
SET status_study = NULL
WHERE bil_kemasukan = 19207;

SELECT * FROM PELAJAR;

SELECT * FROM pelajar_eligibility;
SELECT * FROM pakej;
SELECT * FROM pakej_subjek;
SELECT * FROM subjek_stpm;

ALTER TABLE pelajar RENAME COLUMN aliran_dipohon TO aliran_ditawar;
ALTER TABLE pelajar AUTO_INCREMENT = 19207;

DESCRIBE pelajar;

--
SELECT * FROM pakej;
SELECT * FROM pakej WHERE semester = 2;
SELECT * FROM pelajar WHERE bil_kemasukan = 19225;
SELECT * FROM spm_hasil WHERE bil_kemasukan = 19225;

-- rewriting keadaan mata to masalah_penglihatan

ALTER TABLE pelajar
MODIFY COLUMN keadaan_mata ENUM('BAIK', 'KURANG BAIK', 'YA', 'TIDAK');

UPDATE pelajar
SET keadaan_mata =
    CASE
        WHEN keadaan_mata = 'BAIK' THEN 'TIDAK'
        WHEN keadaan_mata = 'KURANG BAIK' THEN 'YA'
    END;
    
ALTER TABLE pelajar
CHANGE COLUMN keadaan_mata masalah_penglihatan ENUM('YA', 'TIDAK') DEFAULT NULL;

--
UPDATE pelajar
SET nama_pelajar = UPPER(nama_pelajar);

--

ALTER TABLE pelajar 
ADD tugas_khas VARCHAR(50),
ADD rumah_sukan VARCHAR(20);

INSERT INTO form_settings (form_id, is_enabled) VALUES 
('kokurikulum_form', TRUE);

ALTER TABLE UnitKokurikulum 
RENAME COLUMN activity_name TO unit_name;

SELECT * FROM kokurikulumpelajar;