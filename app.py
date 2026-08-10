import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# ============================================================
# KONFIGURASI
# ============================================================

st.set_page_config(
    page_title="Dashboard Portofolio Kredit",
    page_icon="💳",
    layout="wide"
)

# ============================================================
# HELPER
# ============================================================

def rupiah(x):
    if pd.isna(x):
        return "N/A"

    x = float(x)

    if abs(x) >= 1e12:
        return f"Rp{x / 1e12:.2f} T"
    if abs(x) >= 1e9:
        return f"Rp{x / 1e9:.2f} M"
    if abs(x) >= 1e6:
        return f"Rp{x / 1e6:.2f} Jt"

    return f"Rp{x:,.0f}"


def find_col(df, candidates):
    """Mencari nama kolom yang tersedia."""
    # Prioritas exact match
    lower_map = {}
    for c in df.columns:
        lower_map.setdefault(str(c).lower().strip(), c)

    for name in candidates:
        key = str(name).lower().strip()
        if key in lower_map:
            return lower_map[key]

    # Jika tidak ada exact match, cari nama yang mengandung kandidat
    for name in candidates:
        key = str(name).lower().strip()
        for c in df.columns:
            if key in str(c).lower().strip():
                return c

    return None


def safe_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def unique_values(df, column):
    if column is None or column not in df.columns:
        return []
    return sorted(
        df[column]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


# ============================================================
# LOAD DATA
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# Struktur repository saat ini:
# Dashboard-Kredit/
# ├── app.py
# └── data_final/
#     └── data_final/
#         └── fact_pinjaman_final.csv
#
# Beberapa fallback disediakan supaya path tetap aman jika
# struktur folder dipindahkan.

candidate_paths = [
    BASE_DIR / "data_final" / "data_final" / "fact_pinjaman_final.csv",
    BASE_DIR / "data_final" / "fact_pinjaman_final.csv",
    BASE_DIR / "fact_pinjaman_final.csv",
]

CSV_PATH = next((p for p in candidate_paths if p.exists()), None)

if CSV_PATH is None:
    st.error("File fact_pinjaman_final.csv tidak ditemukan.")
    st.write("Folder aplikasi:", str(BASE_DIR))
    st.write(
        "Path yang dicari:",
        [str(p) for p in candidate_paths]
    )
    st.stop()

try:
    fact = pd.read_csv(CSV_PATH, low_memory=False)
except Exception as e:
    st.error(f"Gagal membaca file CSV: {e}")
    st.stop()

# ============================================================
# RAPikan NAMA KOLOM DUPLIKAT
# ============================================================
# Dataset final seharusnya cukup menggunakan satu kolom untuk
# setiap nama. Jika ada nama kolom duplikat akibat merge lama,
# ambil kemunculan pertama.

if fact.columns.duplicated().any():
    fact = fact.loc[:, ~fact.columns.duplicated()].copy()

# ============================================================
# IDENTIFIKASI KOLOM
# ============================================================

pid = find_col(fact, ["pinjaman_id"])

date = find_col(fact, ["tanggal_akad"])

plafon = find_col(
    fact,
    ["plafon", "jumlah_pinjaman", "nilai_pinjaman"]
)

kewajiban = find_col(
    fact,
    ["total_kewajiban"]
)

realisasi = find_col(
    fact,
    ["total_realisasi", "total_realisasi_pembayaran"]
)

baki = find_col(
    fact,
    ["baki_debet", "baki_debet_berjalan"]
)

agunan = find_col(
    fact,
    ["total_nilai_agunan", "nilai_agunan"]
)

tunggakan = find_col(
    fact,
    [
        "hari_tunggakan_terlama",
        "hari_tunggakan",
        "maks_hari_keterlambatan"
    ]
)

kolek = find_col(
    fact,
    ["kode_kolektibilitas"]
)

kolek_nama = find_col(
    fact,
    [
        "kolektibilitas",
        "kolektibilitas_pinjaman",
        "kategori_kolektibilitas"
    ]
)

status = find_col(
    fact,
    ["status_pinjaman", "status"]
)

provinsi = find_col(
    fact,
    ["provinsi", "provinsi_nasabah"]
)

wilayah = find_col(
    fact,
    ["wilayah", "wilayah_cabang"]
)

nama_cabang = find_col(
    fact,
    ["nama_cabang", "nama_cabang_cabang"]
)

nama_produk = find_col(
    fact,
    ["nama_produk", "nama_produk_produk"]
)

nama_petugas = find_col(
    fact,
    ["nama_petugas", "nama_petugas_petugas"]
)

jenis_usaha = find_col(
    fact,
    [
        "jenis_usaha",
        "jenis_usaha_nasabah",
        "jenis_usaha_dim"
    ]
)

# ============================================================
# VALIDASI KOLOM UTAMA
# ============================================================

if pid is None:
    st.error(
        "Kolom 'pinjaman_id' tidak ditemukan pada "
        "fact_pinjaman_final.csv."
    )
    st.write("Kolom yang tersedia:", fact.columns.tolist())
    st.stop()

# ============================================================
# KONVERSI NUMERIK
# ============================================================

numeric_cols = [
    plafon,
    kewajiban,
    realisasi,
    baki,
    agunan,
    tunggakan,
    kolek,
]

for c in numeric_cols:
    if c is not None and c in fact.columns:
        fact[c] = safe_numeric(fact[c])

# ============================================================
# TANGGAL
# ============================================================

if date is not None and date in fact.columns:
    fact[date] = pd.to_datetime(
        fact[date],
        errors="coerce"
    )

    fact["tahun_dashboard"] = fact[date].dt.year
    fact["periode_dashboard"] = (
        fact[date]
        .dt.to_period("M")
        .astype(str)
    )
else:
    fact["tahun_dashboard"] = np.nan
    fact["periode_dashboard"] = ""

# ============================================================
# DEFINISI NPL
# ============================================================
# NPL = kolektibilitas 3, 4, dan 5.
# Dibuat pada DATA FACT sebelum filter agar selalu tersedia.

if kolek is not None and kolek in fact.columns:
    fact["_kode_kolek_num"] = safe_numeric(fact[kolek])

    fact["is_npl"] = (
        fact["_kode_kolek_num"]
        .isin([3, 4, 5])
        .astype(int)
    )
elif "is_npl" in fact.columns:
    fact["is_npl"] = (
        fact["is_npl"]
        .astype(str)
        .str.lower()
        .isin(["1", "true", "yes", "y", "npl"])
        .astype(int)
    )
else:
    fact["is_npl"] = 0

# ============================================================
# JUMLAH DATA ASLI
# ============================================================

total_data_asli = len(fact)

# ============================================================
# FILTER SIDEBAR
# ============================================================

st.sidebar.header("🔎 Filter")

# Tahun
tahun_dipilih = []
if "tahun_dashboard" in fact.columns:
    tahun_series = fact["tahun_dashboard"].dropna()

    if len(tahun_series) > 0:
        tahun_list = sorted(
            tahun_series.astype(int).unique().tolist()
        )

        tahun_dipilih = st.sidebar.multiselect(
            "Tahun",
            tahun_list,
            default=[]
        )

# Provinsi
provinsi_dipilih = []
if provinsi is not None:
    provinsi_list = unique_values(fact, provinsi)

    provinsi_dipilih = st.sidebar.multiselect(
        "Provinsi",
        provinsi_list,
        default=[]
    )

# Wilayah
wilayah_dipilih = []
if wilayah is not None:
    wilayah_list = unique_values(fact, wilayah)

    wilayah_dipilih = st.sidebar.multiselect(
        "Wilayah",
        wilayah_list,
        default=[]
    )

# Cabang
cabang_dipilih = []
if nama_cabang is not None:
    cabang_list = unique_values(fact, nama_cabang)

    cabang_dipilih = st.sidebar.multiselect(
        "Cabang",
        cabang_list,
        default=[]
    )

# Produk
produk_dipilih = []
if nama_produk is not None:
    produk_list = unique_values(fact, nama_produk)

    produk_dipilih = st.sidebar.multiselect(
        "Produk",
        produk_list,
        default=[]
    )

# ============================================================
# FILTER DATA
# ============================================================

df = fact.copy()

if tahun_dipilih:
    df = df[
        df["tahun_dashboard"].isin(tahun_dipilih)
    ]

if provinsi_dipilih and provinsi is not None:
    df = df[
        df[provinsi]
        .astype(str)
        .isin(provinsi_dipilih)
    ]

if wilayah_dipilih and wilayah is not None:
    df = df[
        df[wilayah]
        .astype(str)
        .isin(wilayah_dipilih)
    ]

if cabang_dipilih and nama_cabang is not None:
    df = df[
        df[nama_cabang]
        .astype(str)
        .isin(cabang_dipilih)
    ]

if produk_dipilih and nama_produk is not None:
    df = df[
        df[nama_produk]
        .astype(str)
        .isin(produk_dipilih)
    ]

# ============================================================
# JUDUL
# ============================================================

st.title("💳 Dashboard Risiko & Collection Kredit Mikro")

st.caption(
    f"Sumber data: {CSV_PATH.relative_to(BASE_DIR) if CSV_PATH.is_relative_to(BASE_DIR) else CSV_PATH}"
)

# ============================================================
# RINGKASAN PORTOFOLIO
# ============================================================

jumlah_pinjaman = (
    df[pid].nunique()
    if pid in df.columns
    else len(df)
)

total_kewajiban = (
    df[kewajiban].sum()
    if kewajiban is not None and kewajiban in df.columns
    else 0
)

total_realisasi = (
    df[realisasi].sum()
    if realisasi is not None and realisasi in df.columns
    else 0
)

npl_rate = (
    df["is_npl"].mean() * 100
    if len(df) > 0
    else 0
)

avg_dpd = (
    df[tunggakan].mean()
    if tunggakan is not None
    and tunggakan in df.columns
    and len(df) > 0
    else np.nan
)

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.metric(
        "Jumlah Pinjaman",
        f"{jumlah_pinjaman:,}".replace(",", ".")
    )

with k2:
    st.metric(
        "Total Kewajiban",
        rupiah(total_kewajiban)
    )

with k3:
    st.metric(
        "Total Realisasi Pembayaran",
        rupiah(total_realisasi)
    )

with k4:
    st.metric(
        "Persentase Kredit Bermasalah",
        f"{npl_rate:.2f}%"
    )

with k5:
    st.metric(
        "Keterlambatan Pembayaran",
        f"{avg_dpd:.1f} hari"
        if pd.notna(avg_dpd)
        else "N/A"
    )

# ============================================================
# NPL PER CABANG
# ============================================================

st.divider()
st.header("Persentase Kredit Bermasalah Berdasarkan Cabang")

if nama_cabang is not None:
    branch_npl = (
        df.groupby(nama_cabang, dropna=False)
        .agg(
            jumlah_pinjaman=(
                pid,
                "nunique"
            ),
            jumlah_npl=(
                "is_npl",
                "sum"
            )
        )
        .reset_index()
    )

    branch_npl["npl_rate"] = np.where(
        branch_npl["jumlah_pinjaman"] > 0,
        branch_npl["jumlah_npl"]
        / branch_npl["jumlah_pinjaman"],
        0
    )

    branch_npl["npl_persen"] = (
        branch_npl["npl_rate"] * 100
    )

    branch_npl = branch_npl.sort_values(
        "npl_rate",
        ascending=False
    )

    if len(branch_npl) > 0:
        worst_branch = branch_npl.iloc[0]

        a, b = st.columns(2)

        with a:
            st.metric(
                "Cabang dengan NPL Tertinggi",
                str(worst_branch[nama_cabang])
            )

        with b:
            st.metric(
                "NPL Tertinggi",
                f"{worst_branch['npl_rate'] * 100:.2f}%"
            )

        fig_npl = px.bar(
            branch_npl,
            x=nama_cabang,
            y="npl_persen",
            text="npl_persen",
            labels={
                nama_cabang: "Cabang",
                "npl_persen": "NPL (%)"
            }
        )

        fig_npl.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        fig_npl.update_layout(
            xaxis_title="",
            yaxis_title="NPL (%)"
        )

        st.plotly_chart(
            fig_npl,
            use_container_width=True
        )
    else:
        st.info("Tidak ada data cabang pada filter yang dipilih.")
else:
    st.info("Kolom nama cabang tidak tersedia.")

# ============================================================
# DPD PER PRODUK
# ============================================================

st.divider()
st.header("Rata-rata DPD Berdasarkan Produk")

if nama_produk is not None and tunggakan is not None:
    product_dpd = (
        df.groupby(nama_produk, dropna=False)
        .agg(
            rata_rata_dpd=(
                tunggakan,
                "mean"
            ),
            jumlah_pinjaman=(
                pid,
                "nunique"
            )
        )
        .reset_index()
        .sort_values(
            "rata_rata_dpd",
            ascending=False
        )
    )

    product_dpd = product_dpd.dropna(
        subset=["rata_rata_dpd"]
    )

    if len(product_dpd) > 0:
        worst_product = product_dpd.iloc[0]

        a, b = st.columns(2)

        with a:
            st.metric(
                "Produk dengan DPD Tertinggi",
                str(worst_product[nama_produk])
            )

        with b:
            st.metric(
                "Rata-rata DPD Tertinggi",
                f"{worst_product['rata_rata_dpd']:.1f} hari"
            )

        fig_dpd = px.bar(
            product_dpd,
            x=nama_produk,
            y="rata_rata_dpd",
            text="rata_rata_dpd",
            labels={
                nama_produk: "Produk Kredit",
                "rata_rata_dpd": "Rata-rata DPD (Hari)"
            }
        )

        fig_dpd.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside"
        )

        fig_dpd.update_layout(
            xaxis_tickangle=-45,
            xaxis_title="",
            yaxis_title="Hari"
        )

        st.plotly_chart(
            fig_dpd,
            use_container_width=True
        )
    else:
        st.info("Tidak ada data DPD pada filter yang dipilih.")
else:
    st.info("Kolom produk atau DPD tidak tersedia.")

# ============================================================
# NPL BERDASARKAN AGUNAN
# ============================================================

st.divider()
st.header("Persentase Kredit Bermasalah Berdasarkan Status Agunan")

if agunan is not None:
    df["status_agunan"] = np.where(
        df[agunan].fillna(0) > 0,
        "Dengan Agunan",
        "Tanpa Agunan"
    )

    agunan_npl = (
        df.groupby("status_agunan", dropna=False)
        .agg(
            jumlah_pinjaman=(
                pid,
                "nunique"
            ),
            jumlah_npl=(
                "is_npl",
                "sum"
            )
        )
        .reset_index()
    )

    agunan_npl["npl_rate"] = np.where(
        agunan_npl["jumlah_pinjaman"] > 0,
        agunan_npl["jumlah_npl"]
        / agunan_npl["jumlah_pinjaman"],
        0
    )

    agunan_npl["npl_persen"] = (
        agunan_npl["npl_rate"] * 100
    )

    npl_agunan = agunan_npl.loc[
        agunan_npl["status_agunan"] == "Dengan Agunan",
        "npl_rate"
    ]

    npl_tanpa_agunan = agunan_npl.loc[
        agunan_npl["status_agunan"] == "Tanpa Agunan",
        "npl_rate"
    ]

    npl_agunan = (
        npl_agunan.iloc[0]
        if len(npl_agunan)
        else 0
    )

    npl_tanpa_agunan = (
        npl_tanpa_agunan.iloc[0]
        if len(npl_tanpa_agunan)
        else 0
    )

    selisih = abs(
        npl_agunan - npl_tanpa_agunan
    )

    a, b, c = st.columns(3)

    with a:
        st.metric(
            "NPL Dengan Agunan",
            f"{npl_agunan * 100:.2f}%"
        )

    with b:
        st.metric(
            "NPL Tanpa Agunan",
            f"{npl_tanpa_agunan * 100:.2f}%"
        )

    with c:
        st.metric(
            "Selisih NPL",
            f"{selisih * 100:.2f} %"
        )

    fig_agunan = px.bar(
        agunan_npl,
        x="status_agunan",
        y="npl_persen",
        text="npl_persen",
        labels={
            "status_agunan": "Status Agunan",
            "npl_persen": "NPL (%)"
        }
    )

    fig_agunan.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside"
    )

    fig_agunan.update_layout(
        xaxis_title="",
        yaxis_title="NPL (%)"
    )

    st.plotly_chart(
        fig_agunan,
        use_container_width=True
    )
else:
    st.info("Kolom nilai agunan tidak tersedia.")

# ============================================================
# TUNGGAKAN PETUGAS DAN JENIS USAHA
# ============================================================

st.divider()
st.header("Tunggakan Kredit")

left, right = st.columns(2)

# ------------------------------------------------------------
# PETUGAS
# ------------------------------------------------------------

with left:
    st.subheader("Petugas Kredit")

    if nama_petugas is not None and baki is not None:
        officer = (
            df.groupby(nama_petugas, dropna=False)
            .agg(
                total_tunggakan=(
                    baki,
                    "sum"
                ),
                jumlah_pinjaman=(
                    pid,
                    "nunique"
                )
            )
            .reset_index()
            .sort_values(
                "total_tunggakan",
                ascending=False
            )
        )

        if len(officer) > 0:
            top_officer = officer.iloc[0]

            st.metric(
                "Tunggakan Terbesar",
                str(top_officer[nama_petugas]),
                rupiah(top_officer["total_tunggakan"])
            )

            fig_officer = px.bar(
                officer.head(10),
                x="total_tunggakan",
                y=nama_petugas,
                orientation="h",
                text="total_tunggakan",
                labels={
                    nama_petugas: "Petugas Kredit",
                    "total_tunggakan": "Total Tunggakan"
                }
            )

            fig_officer.update_traces(
                texttemplate="Rp %{text:,.0f}",
                textposition="outside"
            )

            st.plotly_chart(
                fig_officer,
                use_container_width=True
            )
        else:
            st.info("Tidak ada data petugas.")
    else:
        st.info("Kolom petugas atau baki debet tidak tersedia.")

# ------------------------------------------------------------
# JENIS USAHA
# ------------------------------------------------------------

with right:
    st.subheader("Jenis Usaha")

    if jenis_usaha is not None and baki is not None:
        business = (
            df.groupby(
                jenis_usaha,
                dropna=False
            )
            .agg(
                total_tunggakan=(
                    baki,
                    "sum"
                ),
                jumlah_pinjaman=(
                    pid,
                    "nunique"
                )
            )
            .reset_index()
            .sort_values(
                "total_tunggakan",
                ascending=False
            )
        )

        if len(business) > 0:
            top_business = business.iloc[0]

            st.metric(
                "Tunggakan Terbesar",
                str(top_business[jenis_usaha]),
                rupiah(top_business["total_tunggakan"])
            )

            fig_business = px.bar(
                business.head(10),
                x="total_tunggakan",
                y=jenis_usaha,
                orientation="h",
                text="total_tunggakan",
                labels={
                    jenis_usaha: "Jenis Usaha",
                    "total_tunggakan": "Total Tunggakan"
                }
            )

            fig_business.update_traces(
                texttemplate="Rp %{text:,.0f}",
                textposition="outside"
            )

            st.plotly_chart(
                fig_business,
                use_container_width=True
            )
        else:
            st.info("Tidak ada data jenis usaha.")
    else:
        st.info("Kolom jenis usaha atau baki debet tidak tersedia.")

# ============================================================
# COLLECTION RATE
# ============================================================

st.divider()
st.header("Tingkat Keberhasilan Pembayaran Berdasarkan Cabang")

if (
    nama_cabang is not None
    and realisasi is not None
    and kewajiban is not None
):
    branch_collection = (
        df.groupby(nama_cabang, dropna=False)
        .agg(
            total_realisasi=(
                realisasi,
                "sum"
            ),
            total_kewajiban=(
                kewajiban,
                "sum"
            )
        )
        .reset_index()
    )

    branch_collection["collection_rate"] = np.where(
        branch_collection["total_kewajiban"] != 0,
        branch_collection["total_realisasi"]
        / branch_collection["total_kewajiban"],
        0
    )

    branch_collection = (
        branch_collection
        .sort_values(
            "collection_rate",
            ascending=True
        )
    )

    if len(branch_collection) > 0:
        worst_collection = branch_collection.iloc[0]

        a, b = st.columns(2)

        with a:
            st.metric(
                "Cabang dengan Collection Rate Terendah",
                str(worst_collection[nama_cabang])
            )

        with b:
            st.metric(
                "Collection Rate Terendah",
                f"{worst_collection['collection_rate'] * 100:.2f}%"
            )

        fig_collection = px.bar(
            branch_collection,
            x=nama_cabang,
            y="collection_rate",
            text="collection_rate",
            labels={
                nama_cabang: "Cabang",
                "collection_rate": "Collection Rate"
            }
        )

        fig_collection.update_traces(
            texttemplate="%{text:.2%}",
            textposition="outside"
        )

        fig_collection.update_layout(
            yaxis_tickformat=".0%",
            xaxis_title="",
            yaxis_title="Collection Rate"
        )

        st.plotly_chart(
            fig_collection,
            use_container_width=True
        )
    else:
        st.info("Tidak ada data collection rate.")
else:
    st.info(
        "Kolom cabang, realisasi, atau kewajiban tidak tersedia."
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    f"Total data awal: {total_data_asli:,} pinjaman | "
    f"Data yang sedang dianalisis: {jumlah_pinjaman:,} pinjaman"
)
