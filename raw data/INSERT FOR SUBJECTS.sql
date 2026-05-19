-- 1. Insert the core subjects into the subjek_stpm table with subject codes
INSERT INTO subjek_stpm (id_subjek, kod_subjek, nama_subjek) VALUES 
(1, 'PA', 'PENGAJIAN AM'),
(2, 'MUET', 'MUET'),
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

-- 2. Insert your individual packages into the pakej table
INSERT INTO pakej (id_pakej, kod_pakej, aliran, status_aktif) VALUES
(1, 'BK1', 'SAINS', 1), (2, 'BK2', 'SAINS', 1), (3, 'BK3', 'SAINS', 1), (4, 'BK4', 'SAINS', 1),
(5, 'CK1', 'SAINS', 1),
(6, 'FK1', 'SAINS', 1), (7, 'FK2', 'SAINS', 1), (8, 'FK3', 'SAINS', 1),
(9, 'AH1', 'SAINS SOSIAL', 1),
(10, 'CV1', 'SAINS SOSIAL', 1),
(11, 'AP1', 'SAINS SOSIAL', 1), (12, 'AP2', 'SAINS SOSIAL', 1), (13, 'AP3', 'SAINS SOSIAL', 1),
(14, 'BP1', 'SAINS SOSIAL', 1),
(15, 'BS1', 'SAINS SOSIAL', 1);

-- 3. Link packages to subjects in the pakej_subjek bridge table
-- BK1, BK2, BK3, BK4 (PA, MUET, KIM, MT, BIO)
INSERT INTO pakej_subjek (id_pakej, id_subjek) VALUES 
(1,1),(1,2),(1,3),(1,4),(1,5),
(2,1),(2,2),(2,3),(2,4),(2,5),
(3,1),(3,2),(3,3),(3,4),(3,5),
(4,1),(4,2),(4,3),(4,4),(4,5);

-- CK1 (PA, MUET, KIM, MT, ICT)
INSERT INTO pakej_subjek (id_pakej, id_subjek) VALUES (5,1),(5,2),(5,3),(5,4),(5,6);

-- FK1, FK2, FK3 (PA, MUET, KIM, MT, FIZ)
INSERT INTO pakej_subjek (id_pakej, id_subjek) VALUES 
(6,1),(6,2),(6,3),(6,4),(6,7),
(7,1),(7,2),(7,3),(7,4),(7,7),
(8,1),(8,2),(8,3),(8,4),(8,7);

-- AH1 (PA, MUET, EKO, SEJ, AK)
INSERT INTO pakej_subjek (id_pakej, id_subjek) VALUES (9,1),(9,2),(9,8),(9,9),(9,10);

-- CV1 (PA, MUET, EKO, SENI, ICT)
INSERT INTO pakej_subjek (id_pakej, id_subjek) VALUES (10,1),(10,2),(10,8),(10,11),(10,6);

-- AP1, AP2, AP3 (PA, MUET, PP, EKO, AK)
INSERT INTO pakej_subjek (id_pakej, id_subjek) VALUES 
(11,1),(11,2),(11,12),(11,8),(11,10),
(12,1),(12,2),(12,12),(12,8),(12,10),
(13,1),(13,2),(13,12),(13,8),(13,10);

-- BP1 (PA, MUET, PP, EKO, BM)
INSERT INTO pakej_subjek (id_pakej, id_subjek) VALUES (14,1),(14,2),(14,12),(14,8),(14,13);

-- BS1 (PA, MUET, PP, S.SUKAN, BM)
INSERT INTO pakej_subjek (id_pakej, id_subjek) VALUES (15,1),(15,2),(15,12),(15,14),(15,13);

SELECT p.id_pakej, p.kod_pakej, p.aliran, s.nama_subjek 
FROM pakej p
JOIN pakej_subjek ps ON p.id_pakej = ps.id_pakej
JOIN subjek_stpm s ON ps.id_subjek = s.id_subjek