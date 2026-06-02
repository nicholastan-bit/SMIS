-- 1. Insert the core subjects into the subjek_stpm table with subject codes
INSERT INTO subjek_stpm (id_subjek, kod_subjek, nama_subjek) VALUES 
(1, 'PA', 'PENGAJIAN AM'),
(2, 'BI', 'BAHASA INGGERIS'),
(3, 'KIM', 'KIMIA'),
(4, 'MT', 'MATEMATIK T'),
(5, 'BIO', 'BIOLOGI'),
(6, 'ICT', 'ICT'),
(7, 'FIZ', 'FIZIK'),
(8, 'EKO', 'EKONOMI'),
(9, 'SEJ', 'SEJARAH'),
(10, 'AK', 'PERAKAUNAN'),
(11, 'SENI', 'SENI VISUAL'),
(12, 'PP', 'PENGAJIAN PERNIAGAAN'),
(13, 'BM', 'BAHASA MELAYU'),
(14, 'SS', 'SAINS SUKAN'),
(15, 'SYA', 'SYARIAH'),
(16, 'GEO', 'GEOGRAFI'),
(17, 'BT', 'BAHASA TAMIL');

INSERT INTO pakej (kod_pakej, nama_pakej, aliran) VALUES
('BK', 'Pakej BK', 'SAINS'), ('BK1', 'Pakej BK1', 'SAINS'), ('BK2', 'Pakej BK2', 'SAINS'), ('BK3', 'Pakej BK3', 'SAINS'), ('BK4', 'Pakej BK4', 'SAINS'),
('CK', 'Pakej CK', 'SAINS'), ('CK1', 'Pakej CK1', 'SAINS'),
('FK', 'Pakej FK', 'SAINS'), ('FK1', 'Pakej FK1', 'SAINS'), ('FK2', 'Pakej FK2', 'SAINS'), ('FK3', 'Pakej FK3', 'SAINS'),
('AH', 'Pakej AH', 'SAINS SOSIAL'), ('AH1', 'Pakej AH1', 'SAINS SOSIAL'),
('CV', 'Pakej CV', 'SAINS SOSIAL'), ('CV1', 'Pakej CV1', 'SAINS SOSIAL'),
('AP', 'Pakej AP', 'SAINS SOSIAL'), ('AP1', 'Pakej AP1', 'SAINS SOSIAL'), ('AP2', 'Pakej AP2', 'SAINS SOSIAL'), ('AP3', 'Pakej AP3', 'SAINS SOSIAL'),
('BP', 'Pakej BP', 'SAINS SOSIAL'), ('BP1', 'Pakej BP1', 'SAINS SOSIAL'),
('BS', 'Pakej BS', 'SAINS SOSIAL'), ('BS1', 'Pakej BS1', 'SAINS SOSIAL'),
('BY', 'Pakej BY', 'SAINS SOSIAL'), ('BY1', 'Pakej BY1', 'SAINS SOSIAL'),
('GB', 'Pakej GB', 'SAINS SOSIAL'), ('GB1', 'Pakej GB1', 'SAINS SOSIAL'),
('GP', 'Pakej GP', 'SAINS SOSIAL'), ('GP1', 'Pakej GP1', 'SAINS SOSIAL'),
('HT', 'Pakej HT', 'SAINS SOSIAL'), ('HT1', 'Pakej HT1', 'SAINS SOSIAL'),
('HP', 'Pakej HP', 'SAINS SOSIAL'), ('HP1', 'Pakej HP1', 'SAINS SOSIAL'),
('HY', 'Pakej HY', 'SAINS SOSIAL'), ('HY1', 'Pakej HY1', 'SAINS SOSIAL'),
('VB', 'Pakej VB', 'SAINS SOSIAL'), ('VB1', 'Pakej VB1', 'SAINS SOSIAL'),
('VS', 'Pakej VS', 'SAINS SOSIAL'), ('VS1', 'Pakej VS1', 'SAINS SOSIAL');

INSERT INTO pakej_subjek (id_pakej, id_subjek)
SELECT p.id_pakej, s.id_subjek
FROM pakej p, subjek_stpm s
WHERE (p.kod_pakej IN ('BK', 'BK1', 'BK2', 'BK3', 'BK4') AND s.kod_subjek IN ('PA', 'BI', 'KIM', 'MT', 'BIO'))
   OR (p.kod_pakej IN ('CK', 'CK1') AND s.kod_subjek IN ('PA', 'BI', 'KIM', 'MT', 'ICT'))
   OR (p.kod_pakej IN ('FK', 'FK1', 'FK2', 'FK3') AND s.kod_subjek IN ('PA', 'BI', 'KIM', 'MT', 'FIZ'))
   OR (p.kod_pakej IN ('AH', 'AH1') AND s.kod_subjek IN ('PA', 'BI', 'EKO', 'SEJ', 'AK'))
   OR (p.kod_pakej IN ('CV', 'CV1') AND s.kod_subjek IN ('PA', 'BI', 'EKO', 'SENI', 'ICT'))
   OR (p.kod_pakej IN ('AP', 'AP1', 'AP2', 'AP3') AND s.kod_subjek IN ('PA', 'BI', 'PP', 'EKO', 'AK'))
   OR (p.kod_pakej IN ('BP', 'BP1') AND s.kod_subjek IN ('PA', 'BI', 'PP', 'EKO', 'BM'))
   OR (p.kod_pakej IN ('BS', 'BS1') AND s.kod_subjek IN ('PA', 'BI', 'PP', 'SS', 'BM'))
   OR (p.kod_pakej IN ('BY', 'BY1') AND s.kod_subjek IN ('PA', 'BI', 'BM', 'SYA', 'GEO'))
   OR (p.kod_pakej IN ('GB', 'GB1') AND s.kod_subjek IN ('PA', 'BI', 'PP', 'BM', 'GEO'))
   OR (p.kod_pakej IN ('GP', 'GP1') AND s.kod_subjek IN ('PA', 'BI', 'PP', 'EKO', 'GEO'))
   OR (p.kod_pakej IN ('HT', 'HT1') AND s.kod_subjek IN ('PA', 'BI', 'PP', 'SEJ', 'BT'))
   OR (p.kod_pakej IN ('HP', 'HP1') AND s.kod_subjek IN ('PA', 'BI', 'PP', 'EKO', 'SEJ'))
   OR (p.kod_pakej IN ('HY', 'HY1') AND s.kod_subjek IN ('PA', 'BI', 'BM', 'SEJ', 'SYA'))
   OR (p.kod_pakej IN ('VB', 'VB1') AND s.kod_subjek IN ('PA', 'BI', 'BM', 'PP', 'SENI'))
   OR (p.kod_pakej IN ('VS', 'VS1') AND s.kod_subjek IN ('PA', 'BI', 'PP', 'SENI', 'SS'));