-- 1. Insert the core subjects into the subjek_stpm table with subject codes
INSERT INTO subjek_stpm (id_subjek, kod_pakej_subjek, nama_subjek) VALUES 
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

INSERT INTO pakej (kod_pakej, nama_pakej, aliran, semester) VALUES
-- Decoy (Kekal asal, Semester 1)
('BK', 'Pakej BK', 'SAINS', 1), ('CK', 'Pakej CK', 'SAINS', 1), ('FK', 'Pakej FK', 'SAINS', 1),
('AH', 'Pakej AH', 'SAINS SOSIAL', 1), ('CV', 'Pakej CV', 'SAINS SOSIAL', 1), ('AP', 'Pakej AP', 'SAINS SOSIAL', 1),
('BP', 'Pakej BP', 'SAINS SOSIAL', 1), ('BS', 'Pakej BS', 'SAINS SOSIAL', 1), ('BY', 'Pakej BY', 'SAINS SOSIAL', 1),
('GB', 'Pakej GB', 'SAINS SOSIAL', 1), ('GP', 'Pakej GP', 'SAINS SOSIAL', 1), ('HT', 'Pakej HT', 'SAINS SOSIAL', 1),
('HP', 'Pakej HP', 'SAINS SOSIAL', 1), ('HY', 'Pakej HY', 'SAINS SOSIAL', 1), ('VB', 'Pakej VB', 'SAINS SOSIAL', 1),
('VS', 'Pakej VS', 'SAINS SOSIAL', 1),

-- Pakej Bernombor (Dengan akhiran /1, /2, /3)
('BK1/1', 'Pakej BK1 Sem 1', 'SAINS', 1), ('BK1/2', 'Pakej BK1 Sem 2', 'SAINS', 2), ('BK1/3', 'Pakej BK1 Sem 3', 'SAINS', 3),
('BK2/1', 'Pakej BK2 Sem 1', 'SAINS', 1), ('BK2/2', 'Pakej BK2 Sem 2', 'SAINS', 2), ('BK2/3', 'Pakej BK2 Sem 3', 'SAINS', 3),
('BK3/1', 'Pakej BK3 Sem 1', 'SAINS', 1), ('BK3/2', 'Pakej BK3 Sem 2', 'SAINS', 2), ('BK3/3', 'Pakej BK3 Sem 3', 'SAINS', 3),
('BK4/1', 'Pakej BK4 Sem 1', 'SAINS', 1), ('BK4/2', 'Pakej BK4 Sem 2', 'SAINS', 2), ('BK4/3', 'Pakej BK4 Sem 3', 'SAINS', 3),

('CK1/1', 'Pakej CK1 Sem 1', 'SAINS', 1), ('CK1/2', 'Pakej CK1 Sem 2', 'SAINS', 2), ('CK1/3', 'Pakej CK1 Sem 3', 'SAINS', 3),

('FK1/1', 'Pakej FK1 Sem 1', 'SAINS', 1), ('FK1/2', 'Pakej FK1 Sem 2', 'SAINS', 2), ('FK1/3', 'Pakej FK1 Sem 3', 'SAINS', 3),
('FK2/1', 'Pakej FK2 Sem 1', 'SAINS', 1), ('FK2/2', 'Pakej FK2 Sem 2', 'SAINS', 2), ('FK2/3', 'Pakej FK2 Sem 3', 'SAINS', 3),
('FK3/1', 'Pakej FK3 Sem 1', 'SAINS', 1), ('FK3/2', 'Pakej FK3 Sem 2', 'SAINS', 2), ('FK3/3', 'Pakej FK3 Sem 3', 'SAINS', 3),

('AH1/1', 'Pakej AH1 Sem 1', 'SAINS SOSIAL', 1), ('AH1/2', 'Pakej AH1 Sem 2', 'SAINS SOSIAL', 2), ('AH1/3', 'Pakej AH1 Sem 3', 'SAINS SOSIAL', 3),
('CV1/1', 'Pakej CV1 Sem 1', 'SAINS SOSIAL', 1), ('CV1/2', 'Pakej CV1 Sem 2', 'SAINS SOSIAL', 2), ('CV1/3', 'Pakej CV1 Sem 3', 'SAINS SOSIAL', 3),
('AP1/1', 'Pakej AP1 Sem 1', 'SAINS SOSIAL', 1), ('AP1/2', 'Pakej AP1 Sem 2', 'SAINS SOSIAL', 2), ('AP1/3', 'Pakej AP1 Sem 3', 'SAINS SOSIAL', 3),
('AP2/1', 'Pakej AP2 Sem 1', 'SAINS SOSIAL', 1), ('AP2/2', 'Pakej AP2 Sem 2', 'SAINS SOSIAL', 2), ('AP2/3', 'Pakej AP2 Sem 3', 'SAINS SOSIAL', 3),
('AP3/1', 'Pakej AP3 Sem 1', 'SAINS SOSIAL', 1), ('AP3/2', 'Pakej AP3 Sem 2', 'SAINS SOSIAL', 2), ('AP3/3', 'Pakej AP3 Sem 3', 'SAINS SOSIAL', 3),
('BP1/1', 'Pakej BP1 Sem 1', 'SAINS SOSIAL', 1), ('BP1/2', 'Pakej BP1 Sem 2', 'SAINS SOSIAL', 2), ('BP1/3', 'Pakej BP1 Sem 3', 'SAINS SOSIAL', 3),
('BS1/1', 'Pakej BS1 Sem 1', 'SAINS SOSIAL', 1), ('BS1/2', 'Pakej BS1 Sem 2', 'SAINS SOSIAL', 2), ('BS1/3', 'Pakej BS1 Sem 3', 'SAINS SOSIAL', 3),
('BY1/1', 'Pakej BY1 Sem 1', 'SAINS SOSIAL', 1), ('BY1/2', 'Pakej BY1 Sem 2', 'SAINS SOSIAL', 2), ('BY1/3', 'Pakej BY1 Sem 3', 'SAINS SOSIAL', 3),
('GB1/1', 'Pakej GB1 Sem 1', 'SAINS SOSIAL', 1), ('GB1/2', 'Pakej GB1 Sem 2', 'SAINS SOSIAL', 2), ('GB1/3', 'Pakej GB1 Sem 3', 'SAINS SOSIAL', 3),
('GP1/1', 'Pakej GP1 Sem 1', 'SAINS SOSIAL', 1), ('GP1/2', 'Pakej GP1 Sem 2', 'SAINS SOSIAL', 2), ('GP1/3', 'Pakej GP1 Sem 3', 'SAINS SOSIAL', 3),
('HT1/1', 'Pakej HT1 Sem 1', 'SAINS SOSIAL', 1), ('HT1/2', 'Pakej HT1 Sem 2', 'SAINS SOSIAL', 2), ('HT1/3', 'Pakej HT1 Sem 3', 'SAINS SOSIAL', 3),
('HP1/1', 'Pakej HP1 Sem 1', 'SAINS SOSIAL', 1), ('HP1/2', 'Pakej HP1 Sem 2', 'SAINS SOSIAL', 2), ('HP1/3', 'Pakej HP1 Sem 3', 'SAINS SOSIAL', 3),
('HY1/1', 'Pakej HY1 Sem 1', 'SAINS SOSIAL', 1), ('HY1/2', 'Pakej HY1 Sem 2', 'SAINS SOSIAL', 2), ('HY1/3', 'Pakej HY1 Sem 3', 'SAINS SOSIAL', 3),
('VB1/1', 'Pakej VB1 Sem 1', 'SAINS SOSIAL', 1), ('VB1/2', 'Pakej VB1 Sem 2', 'SAINS SOSIAL', 2), ('VB1/3', 'Pakej VB1 Sem 3', 'SAINS SOSIAL', 3),
('VS1/1', 'Pakej VS1 Sem 1', 'SAINS SOSIAL', 1), ('VS1/2', 'Pakej VS1 Sem 2', 'SAINS SOSIAL', 2), ('VS1/3', 'Pakej VS1 Sem 3', 'SAINS SOSIAL', 3);

INSERT IGNORE INTO pakej_subjek (id_pakej, id_subjek)
SELECT p.id_pakej, s.id_subjek
FROM pakej p, subjek_stpm s
WHERE (p.kod_pakej IN ('BK', 'BK1', 'BK2', 'BK3', 'BK4') OR p.kod_pakej REGEXP '^(BK1|BK2|BK3|BK4)/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'KIM', 'MT', 'BIO')
   OR (p.kod_pakej IN ('CK', 'CK1') OR p.kod_pakej REGEXP '^CK1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'KIM', 'MT', 'ICT')
   OR (p.kod_pakej IN ('FK', 'FK1', 'FK2', 'FK3') OR p.kod_pakej REGEXP '^(FK1|FK2|FK3)/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'KIM', 'MT', 'FIZ')
   OR (p.kod_pakej IN ('AH', 'AH1') OR p.kod_pakej REGEXP '^AH1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'EKO', 'SEJ', 'AK')
   OR (p.kod_pakej IN ('CV', 'CV1') OR p.kod_pakej REGEXP '^CV1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'EKO', 'SENI', 'ICT')
   OR (p.kod_pakej IN ('AP', 'AP1', 'AP2', 'AP3') OR p.kod_pakej REGEXP '^(AP1|AP2|AP3)/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'PP', 'EKO', 'AK')
   OR (p.kod_pakej IN ('BP', 'BP1') OR p.kod_pakej REGEXP '^BP1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'PP', 'EKO', 'BM')
   OR (p.kod_pakej IN ('BS', 'BS1') OR p.kod_pakej REGEXP '^BS1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'PP', 'SS', 'BM')
   OR (p.kod_pakej IN ('BY', 'BY1') OR p.kod_pakej REGEXP '^BY1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'BM', 'SYA', 'GEO')
   OR (p.kod_pakej IN ('GB', 'GB1') OR p.kod_pakej REGEXP '^GB1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'PP', 'BM', 'GEO')
   OR (p.kod_pakej IN ('GP', 'GP1') OR p.kod_pakej REGEXP '^GP1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'PP', 'EKO', 'GEO')
   OR (p.kod_pakej IN ('HT', 'HT1') OR p.kod_pakej REGEXP '^HT1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'PP', 'SEJ', 'BT')
   OR (p.kod_pakej IN ('HP', 'HP1') OR p.kod_pakej REGEXP '^HP1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'PP', 'EKO', 'SEJ')
   OR (p.kod_pakej IN ('HY', 'HY1') OR p.kod_pakej REGEXP '^HY1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'BM', 'SEJ', 'SYA')
   OR (p.kod_pakej IN ('VB', 'VB1') OR p.kod_pakej REGEXP '^VB1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'BM', 'PP', 'SENI')
   OR (p.kod_pakej IN ('VS', 'VS1') OR p.kod_pakej REGEXP '^VS1/[1-3]$') AND s.kod_pakej_subjek IN ('PA', 'BI', 'PP', 'SENI', 'SS');
