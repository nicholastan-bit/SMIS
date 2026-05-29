-- 1. Hapus tabel jika sudah ada (Urutan dari yang memiliki Foreign Key terbanyak)
DROP TABLE IF EXISTS spm_hasil;
DROP TABLE IF EXISTS penjaga;
DROP TABLE IF EXISTS pelajar;
DROP TABLE IF EXISTS pakej_subjek;
DROP TABLE IF EXISTS pakej;
DROP TABLE IF EXISTS subjek_stpm;

# form_settings and pelajar_eligibility are left alone

-- the code below resets the entire stpm package and subjects
-- WARN: pelajar's id_pakej will be NULL if they picked
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
SET aliran_ditawar = 'SAINS SOSIAL'
WHERE no_kp_pelajar = 1;

SELECT * FROM PELAJAR;

SELECT * FROM pelajar_eligibility;
SELECT * FROM pakej;
SELECT * FROM pakej_subjek;
SELECT * FROM subjek_stpm;

ALTER TABLE pelajar
RENAME COLUMN aliran_dipohon TO aliran_ditawar;
ALTER TABLE pelajar AUTO_INCREMENT = 19207;

DESCRIBE pelajar;
