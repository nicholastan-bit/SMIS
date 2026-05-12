-- 1. DATA PELAJAR (10 Orang)
INSERT INTO pelajar (nama_pelajar, email, no_kp_pelajar, jantina, bangsa, agama, tarikh_lahir, alamat_rumah, telefonNo, warganegara, sekolah_tamat, masalah_kesihatan, cara_datang_sekolah, status_study) VALUES
('Aiman Hakim Bin Norazmi', 'aiman@email.com', '080512101133', 'LELAKI', 'MELAYU', 'ISLAM', '2008-05-12', 'No 23, Jalan Melati, Puchong', '0134455661', 1, '2024-12-31', 'Tiada', 'MOTOR', 1),
('Lee Jia Xin', 'jiaxin@email.com', '080922145562', 'PEREMPUAN', 'CINA', 'BUDDHA', '2008-09-22', 'Lot 102, Apartment Suria, Kepong', '0172233445', 1, '2024-12-31', 'Tiada', 'KERETA', 1),
('Arul Selvam A/L Mani', 'arul@email.com', '080130104433', 'LELAKI', 'INDIA', 'HINDU', '2008-01-30', 'No 5, Taman Seri Sentosa, Klang', '0149988771', 1, '2024-12-31', 'Tiada', 'BAS', 1),
('Nur Balkis Binti Zamri', 'balkis@email.com', '081102035544', 'PEREMPUAN', 'MELAYU', 'ISLAM', '2008-11-02', 'No 14, Jalan Teratai, Gombak', '0112233445', 1, '2024-12-31', 'Tiada', 'JALAN', 1),
('Kevin Low Wei Jian', 'kevinl@email.com', '080415147789', 'LELAKI', 'CINA', 'KRISTIAN', '2008-04-15', 'C-3-4, Sri Maya Condo, Setiawangsa', '0198877665', 1, '2024-12-31', 'Tiada', 'KERETA', 1),
('Siti Aishah Binti Bakri', 'aishah@email.com', '080228016672', 'PEREMPUAN', 'MELAYU', 'ISLAM', '2008-02-28', 'No 9, Kampung Tengah, Rawang', '0165544332', 1, '2024-12-31', 'Tiada', 'BASIKAL', 1),
('Rizal Bin Ramli', 'rizal@email.com', '081212038891', 'LELAKI', 'MELAYU', 'ISLAM', '2008-12-12', 'No 55, Jalan USJ 9, Subang Jaya', '0123344556', 1, '2024-12-31', 'Tiada', 'MOTOR', 1),
('Michelle Tan', 'mich@email.com', '080618109982', 'PEREMPUAN', 'CINA', 'KRISTIAN', '2008-06-18', 'No 7, Jalan SS15, Subang Jaya', '0189900112', 1, '2024-12-31', 'Tiada', 'BAS', 1),
('Hafiz Bin Hamidun', 'hafiz@email.com', '080303031121', 'LELAKI', 'MELAYU', 'ISLAM', '2008-03-03', 'No 1, Taman Melawati, KL', '0136677889', 1, '2024-12-31', 'Tiada', 'KERETA', 1),
('Priya A/P Govinda', 'priya@email.com', '081010103342', 'PEREMPUAN', 'INDIA', 'HINDU', '2008-10-10', 'No 88, Jalan Klang Lama, KL', '0175566778', 1, '2024-12-31', 'Tiada', 'JALAN', 1);

-- 2. DATA PENJAGA (Campuran Bapa, Ibu, dan Penjaga Lain)
INSERT INTO penjaga (no_pendaftaran_pelajar, nama_penjaga, no_kp_penjaga, penjaga, pekerjaan, pendapatan, alamat_tempat_kerja) VALUES
-- Pelajar 1: Ada Bapa & Ibu
(1, 'Norazmi Bin Kassim', '750401105533', 'BAPA', 'PEGAWAI TLDM', 6500.00, 'Pangkalan TLDM Lumut'),
(1, 'Zaiton Binti Ali', '780505106644', 'IBU', 'KERANI', 3200.00, 'Pejabat Tanah Puchong'),
-- Pelajar 2: Hanya Bapa
(2, 'Lee Kok Seng', '700912145531', 'BAPA', 'PENIAGA', 15000.00, 'Pasar Borong Selayang'),
-- Pelajar 3: Hanya Penjaga (Pakcik)
(3, 'Maniam A/L Rajoo', '650120104421', 'PENJAGA', 'PESARA', 2200.00, 'Tiada'),
-- Pelajar 4: Ada Bapa & Ibu
(4, 'Zamri Bin Sidek', '731102035511', 'BAPA', 'PEMANDU TEKSI', 2800.00, 'Kuala Lumpur'),
(4, 'Faridah Binti Ahmad', '761212034422', 'IBU', 'SURI RUMAH', 0.00, 'Tiada'),
-- Pelajar 5: Hanya Ibu
(5, 'Wong Mei Yee', '800415143342', 'IBU', 'AGEN INSURANS', 7500.00, 'Prudential KLCC'),
-- Pelajar 6: Ada Bapa & Ibu
(6, 'Bakri Bin Ahmad', '710228014451', 'BAPA', 'PETANI', 1800.00, 'Kebun Getah Rawang'),
(6, 'Salmah Binti Dolah', '750315015562', 'IBU', 'PENJUAL NASI LEMAK', 1500.00, 'Gerai Simpang Tiga'),
-- Pelajar 7: Hanya Bapa
(7, 'Ramli Bin Omar', '681212031123', 'BAPA', 'KONTRAKTOR', 9500.00, 'Damansara'),
-- Pelajar 8: Hanya Penjaga (Nenek)
(8, 'Tan Siew Lan', '550618102232', 'PENJAGA', 'PESARA GURU', 3500.00, 'Tiada'),
-- Pelajar 9: Ada Bapa & Ibu
(9, 'Hamidun Bin Salleh', '740303031141', 'BAPA', 'JURUTERA', 11000.00, 'Petronas Twin Towers'),
(9, 'Mastura Binti Ibrahim', '770404032252', 'IBU', 'PENSYARAH', 8500.00, 'Universiti Malaya'),
-- Pelajar 10: Hanya Bapa
(10, 'Govindaran A/L Arumugam', '721010103311', 'BAPA', 'PEGAWAI POLIS', 5800.00, 'IPD Brickfields');

-- 3. DATA KEPUTUSAN SPM (7 Subjek untuk setiap Pelajar)
INSERT INTO spm_hasil (no_pendaftaran_pelajar, subjek, gred) VALUES
-- Pelajar 1 (7 subjek)
(1, 'BAHASA MELAYU', 'A'), (1, 'BAHASA INGGERIS', 'A-'), (1, 'SEJARAH', 'A'), (1, 'MATEMATIK', 'B+'), (1, 'PENDIDIKAN ISLAM', 'A+'), (1, 'SAINS', 'B'), (1, 'GEOGRAFI', 'B+'),
-- Pelajar 2 (7 subjek)
(2, 'BAHASA MELAYU', 'A'), (2, 'BAHASA INGGERIS', 'A+'), (2, 'SEJARAH', 'B+'), (2, 'MATEMATIK', 'A+'), (2, 'MATEMATIK TAMBAHAN', 'A'), (2, 'FIZIK', 'A-'), (2, 'KIMIA', 'B+'),
-- Pelajar 3 (7 subjek)
(3, 'BAHASA MELAYU', 'B'), (3, 'BAHASA INGGERIS', 'C+'), (3, 'SEJARAH', 'A-'), (3, 'MATEMATIK', 'B'), (3, 'PENDIDIKAN MORAL', 'A'), (3, 'SAINS', 'B'), (3, 'PERNIAGAAN', 'C'),
-- Pelajar 4 (7 subjek)
(4, 'BAHASA MELAYU', 'A+'), (4, 'BAHASA INGGERIS', 'B'), (4, 'SEJARAH', 'A'), (4, 'MATEMATIK', 'A-'), (4, 'PENDIDIKAN ISLAM', 'A'), (4, 'SAINS', 'A'), (4, 'PRINSIP PERAKAUNAN', 'B+'),
-- Pelajar 5 (7 subjek)
(5, 'BAHASA MELAYU', 'A'), (5, 'BAHASA INGGERIS', 'A'), (5, 'SEJARAH', 'B'), (5, 'MATEMATIK', 'A+'), (5, 'FIZIK', 'A'), (5, 'KIMIA', 'A-'), (5, 'BIOLOGI', 'B+'),
-- Pelajar 6 (7 subjek)
(6, 'BAHASA MELAYU', 'A'), (6, 'BAHASA INGGERIS', 'B'), (6, 'SEJARAH', 'A'), (6, 'MATEMATIK', 'C+'), (6, 'PENDIDIKAN ISLAM', 'A'), (6, 'SAINS', 'B'), (6, 'EKONOMI', 'B'),
-- Pelajar 7 (7 subjek)
(7, 'BAHASA MELAYU', 'A-'), (7, 'BAHASA INGGERIS', 'A-'), (7, 'SEJARAH', 'B+'), (7, 'MATEMATIK', 'A'), (7, 'MATEMATIK TAMBAHAN', 'B'), (7, 'FIZIK', 'B'), (7, 'SAINS KOMPUTER', 'A'),
-- Pelajar 8 (7 subjek)
(8, 'BAHASA MELAYU', 'B+'), (8, 'BAHASA INGGERIS', 'A'), (8, 'SEJARAH', 'A'), (8, 'MATEMATIK', 'B'), (8, 'SAINS', 'A-'), (8, 'PRINSIP PERAKAUNAN', 'A'), (8, 'EKONOMI', 'B+'),
-- Pelajar 9 (7 subjek)
(9, 'BAHASA MELAYU', 'A+'), (9, 'BAHASA INGGERIS', 'A+'), (9, 'SEJARAH', 'A+'), (9, 'MATEMATIK', 'A+'), (9, 'MATEMATIK TAMBAHAN', 'A'), (9, 'FIZIK', 'A'), (9, 'KIMIA', 'A'),
-- Pelajar 10 (7 subjek)
(10, 'BAHASA MELAYU', 'A'), (10, 'BAHASA INGGERIS', 'A-'), (10, 'SEJARAH', 'B+'), (10, 'MATEMATIK', 'B'), (10, 'PENDIDIKAN MORAL', 'A'), (10, 'SAINS', 'B+'), (10, 'GEOGRAFI', 'A');