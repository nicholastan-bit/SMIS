-- 1. Insert 15 Pelajar (excluding BLOB/Paths)
INSERT INTO pelajar (nama_pelajar, no_kp_pelajar, jantina, bangsa, agama, cara_datang_sekolah, id_pakej, aliran_dipohon) VALUES
('Ahmad Ali', '060101010001', 'LELAKI', 'MELAYU', 'ISLAM', 'BAS', 1, 'SAINS'),
('Siti Aminah', '060102020002', 'PEREMPUAN', 'MELAYU', 'ISLAM', 'KERETA', 6, 'SAINS'),
('Wei Ming', '060203030003', 'LELAKI', 'CINA', 'BUDDHA', 'MOTOR', 8, 'SAINS SOSIAL'),
('Priya Devi', '060304040004', 'PEREMPUAN', 'INDIA', 'HINDU', 'BASIKAL', 12, 'SAINS SOSIAL'),
('John Doe', '060405050005', 'LELAKI', 'BUKAN WARGANEGARA', 'KRISTIAN', 'JALAN', 14, 'SAINS'),
('Tan Lee', '060506060006', 'PEREMPUAN', 'CINA', 'BUDDHA', 'KERETA', 16, 'SAINS SOSIAL'),
('Raj Kumar', '060607070007', 'LELAKI', 'INDIA', 'HINDU', 'MOTOR', 20, 'SAINS'),
('Nur Huda', '060708080008', 'PEREMPUAN', 'MELAYU', 'ISLAM', 'BAS', 22, 'SAINS SOSIAL'),
('Lee Wei', '060809090009', 'LELAKI', 'CINA', 'BUDDHA', 'BASIKAL', 24, 'SAINS'),
('Fatimah', '060910100010', 'PEREMPUAN', 'MELAYU', 'ISLAM', 'KERETA', 26, 'SAINS SOSIAL'),
('Muthu', '061011110011', 'LELAKI', 'INDIA', 'HINDU', 'MOTOR', 28, 'SAINS'),
('Anna Lim', '061112120012', 'PEREMPUAN', 'CINA', 'KRISTIAN', 'JALAN', 30, 'SAINS SOSIAL'),
('Abu Bakar', '061213130013', 'LELAKI', 'MELAYU', 'ISLAM', 'BAS', 32, 'SAINS'),
('Kavin', '061214140014', 'LELAKI', 'INDIA', 'HINDU', 'MOTOR', 34, 'SAINS SOSIAL'),
('Sarah Jane', '061215150015', 'PEREMPUAN', 'SABAH/SARAWAK', 'KRISTIAN', 'KERETA', 36, 'SAINS SOSIAL');

-- 2. Insert 15 Penjaga (One for each student)
INSERT INTO penjaga (bil_kemasukan, nama_penjaga, hubungan, no_telefon) VALUES
(1, 'Ali Bin Ahmad', 'BAPA', '0123456789'), (2, 'Aminah Binti Ali', 'IBU', '0123456790'),
(3, 'Wei Long', 'BAPA', '0123456791'), (4, 'Devi Kumar', 'IBU', '0123456792'),
(5, 'Jane Doe', 'IBU', '0123456793'), (6, 'Tan Soon', 'BAPA', '0123456794'),
(7, 'Kumar Raju', 'BAPA', '0123456795'), (8, 'Huda Ali', 'IBU', '0123456796'),
(9, 'Lee Chong', 'BAPA', '0123456797'), (10, 'Fatimah Razak', 'IBU', '0123456798'),
(11, 'Muthu Sami', 'BAPA', '0123456799'), (12, 'Lim Ah', 'IBU', '0123456800'),
(13, 'Bakar Ahmad', 'BAPA', '0123456801'), (14, 'Kavin Raj', 'BAPA', '0123456802'),
(15, 'Sarah Ali', 'IBU', '0123456803');

-- 3. Insert 5 Pelajar Eligibility
INSERT INTO pelajar_eligibility (no_kp_pelajar, subjek_khas) VALUES
('060101010001', 'SYARIAH'), ('060304040004', 'SAINS SUKAN'), 
('060708080008', 'SYARIAH'), ('061112120012', 'SAINS SUKAN'), 
('061215150015', 'SYARIAH');

-- 4. Insert SPM Results (7 subjects per student)
-- Pattern: MATEMATIK, SAINS, BAHASA MELAYU, SEJARAH, PENDIDIKAN ISLAM, BAHASA INGGERIS, GEOGRAFI
INSERT INTO spm_hasil (bil_kemasukan, subjek, gred) VALUES
(1, 'MATEMATIK', 'A'), (1, 'SAINS', 'A'), (1, 'BAHASA MELAYU', 'B+'), (1, 'SEJARAH', 'A'), (1, 'PENDIDIKAN ISLAM', 'A-'), (1, 'BAHASA INGGERIS', 'B'), (1, 'GEOGRAFI', 'C+'),
(2, 'MATEMATIK', 'A-'), (2, 'SAINS', 'B'), (2, 'BAHASA MELAYU', 'A'), (2, 'SEJARAH', 'B+'), (2, 'PENDIDIKAN ISLAM', 'A'), (2, 'BAHASA INGGERIS', 'B'), (2, 'GEOGRAFI', 'C'),
(3, 'MATEMATIK', 'B+'), (3, 'SAINS', 'B+'), (3, 'BAHASA MELAYU', 'A'), (3, 'SEJARAH', 'A-'), (3, 'PENDIDIKAN ISLAM', 'B'), (3, 'BAHASA INGGERIS', 'A'), (3, 'GEOGRAFI', 'B'),
(4, 'MATEMATIK', 'A'), (4, 'SAINS', 'A'), (4, 'BAHASA MELAYU', 'A'), (4, 'SEJARAH', 'A'), (4, 'PENDIDIKAN ISLAM', 'B+'), (4, 'BAHASA INGGERIS', 'A-'), (4, 'GEOGRAFI', 'B'),
(5, 'MATEMATIK', 'A'), (5, 'SAINS', 'A-'), (5, 'BAHASA MELAYU', 'B'), (5, 'SEJARAH', 'B'), (5, 'PENDIDIKAN ISLAM', 'C+'), (5, 'BAHASA INGGERIS', 'A'), (5, 'GEOGRAFI', 'A'),
(6, 'MATEMATIK', 'B'), (6, 'SAINS', 'B+'), (6, 'BAHASA MELAYU', 'A'), (6, 'SEJARAH', 'A'), (6, 'PENDIDIKAN ISLAM', 'B'), (6, 'BAHASA INGGERIS', 'B+'), (6, 'GEOGRAFI', 'B'),
(7, 'MATEMATIK', 'A'), (7, 'SAINS', 'A'), (7, 'BAHASA MELAYU', 'B'), (7, 'SEJARAH', 'B'), (7, 'PENDIDIKAN ISLAM', 'A'), (7, 'BAHASA INGGERIS', 'A'), (7, 'GEOGRAFI', 'A-'),
(8, 'MATEMATIK', 'B+'), (8, 'SAINS', 'B'), (8, 'BAHASA MELAYU', 'A'), (8, 'SEJARAH', 'A-'), (8, 'PENDIDIKAN ISLAM', 'A'), (8, 'BAHASA INGGERIS', 'B'), (8, 'GEOGRAFI', 'B+'),
(9, 'MATEMATIK', 'A'), (9, 'SAINS', 'A'), (9, 'BAHASA MELAYU', 'B+'), (9, 'SEJARAH', 'B+'), (9, 'PENDIDIKAN ISLAM', 'B'), (9, 'BAHASA INGGERIS', 'A'), (9, 'GEOGRAFI', 'A'),
(10, 'MATEMATIK', 'B'), (10, 'SAINS', 'B'), (10, 'BAHASA MELAYU', 'A'), (10, 'SEJARAH', 'B'), (10, 'PENDIDIKAN ISLAM', 'A'), (10, 'BAHASA INGGERIS', 'B+'), (10, 'GEOGRAFI', 'B'),
(11, 'MATEMATIK', 'A'), (11, 'SAINS', 'A'), (11, 'BAHASA MELAYU', 'B'), (11, 'SEJARAH', 'A-'), (11, 'PENDIDIKAN ISLAM', 'A'), (11, 'BAHASA INGGERIS', 'B'), (11, 'GEOGRAFI', 'B+'),
(12, 'MATEMATIK', 'B+'), (12, 'SAINS', 'B+'), (12, 'BAHASA MELAYU', 'A'), (12, 'SEJARAH', 'B'), (12, 'PENDIDIKAN ISLAM', 'B'), (12, 'BAHASA INGGERIS', 'A'), (12, 'GEOGRAFI', 'A'),
(13, 'MATEMATIK', 'A'), (13, 'SAINS', 'A'), (13, 'BAHASA MELAYU', 'A'), (13, 'SEJARAH', 'A'), (13, 'PENDIDIKAN ISLAM', 'A'), (13, 'BAHASA INGGERIS', 'A'), (13, 'GEOGRAFI', 'B+'),
(14, 'MATEMATIK', 'B'), (14, 'SAINS', 'B'), (14, 'BAHASA MELAYU', 'B+'), (14, 'SEJARAH', 'B+'), (14, 'PENDIDIKAN ISLAM', 'B'), (14, 'BAHASA INGGERIS', 'B'), (14, 'GEOGRAFI', 'C+'),
(15, 'MATEMATIK', 'A'), (15, 'SAINS', 'B+'), (15, 'BAHASA MELAYU', 'A'), (15, 'SEJARAH', 'A'), (15, 'PENDIDIKAN ISLAM', 'A-'), (15, 'BAHASA INGGERIS', 'A'), (15, 'GEOGRAFI', 'B');