# Dashboard Risiko & Collection Kredit Mikro

## Isi folder
- `app.py` = aplikasi Streamlit
- `fact_pinjaman_final.csv` = data utama
- `requirements.txt` = library yang diperlukan

## Menjalankan di komputer
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy ke Streamlit Community Cloud
1. Upload `app.py`, `requirements.txt`, dan `fact_pinjaman_final.csv` ke repository GitHub.
2. Buka Streamlit Community Cloud.
3. Pilih repository tersebut.
4. Pilih file utama `app.py`.
5. Deploy.

## Pertanyaan analitik yang dijawab
1. Persentase NPL dan cabang dengan NPL tertinggi.
2. Rata-rata DPD dan produk dengan DPD tertinggi.
3. Selisih NPL dengan agunan dan tanpa agunan.
4. Petugas/jenis usaha dengan total tunggakan terbesar.
5. Collection rate keseluruhan dan cabang dengan collection rate terendah.

## Definisi
- NPL = kolektibilitas 3 + 4 + 5.
- DPD = `hari_tunggakan_terlama`.
- Dengan agunan = `total_nilai_agunan > 0`.
- Collection rate = `total_realisasi / total_kewajiban`.
- Karena fact yang tersedia tidak memuat rincian jadwal pembayaran dan nominal tunggakan per angsuran, `baki_debet` digunakan sebagai proxy nilai tunggakan.
