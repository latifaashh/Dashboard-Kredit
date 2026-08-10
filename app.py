import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


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


def col(df, names):

    mapping = {
        str(x).lower().strip(): x
        for x in df.columns
    }

    # Cari nama yang persis
    for name in names:

        if name.lower() in mapping:
            return mapping[name.lower()]

    # Cari nama yang mengandung
    for name in names:

        for x in df.columns:

            if name.lower() in str(x).lower():
                return x

    return None


def add_dim(
    fact,
    dim,
    key,
    attributes
):

    if dim is None:
        return fact

    if key not in fact.columns:
        return fact

    if key not in dim.columns:
        return fact

    d = dim.drop_duplicates(
        subset=[key]
    ).copy()

    keep = [
        key
    ]

    for attribute in attributes:

        if (
            attribute in d.columns
            and attribute not in fact.columns
        ):

            keep.append(attribute)

    if len(keep) > 1:

        fact = fact.merge(
            d[keep],
            on=key,
            how="left",
            validate="many_to_one"
        )

    return fact


# ============================================================
# LOAD DATA
# ============================================================
from pathlib import Path
import pandas as pd

# Lokasi folder tempat app.py berada
BASE_DIR = Path(__file__).resolve().parent

# File CSV berada satu folder dengan app.py
CSV_PATH = BASE_DIR / "fact_pinjaman_final.csv"

fact = pd.read_csv(CSV_PATH)

dim_nasabah = pd.read_csv(
    f"{DATA_PATH}/dim_nasabah.csv"
)


dim_produk = pd.read_csv(
    f"{DATA_PATH}/dim_produk.csv"
)


dim_cabang = pd.read_csv(
    f"{DATA_PATH}/dim_cabang.csv"
)


dim_petugas = pd.read_csv(
    f"{DATA_PATH}/dim_petugas.csv"
)


dim_waktu = pd.read_csv(
    f"{DATA_PATH}/dim_waktu.csv"
)


# ============================================================
# TAMBAHKAN DIMENSI KE FACT
# ============================================================

fact = add_dim(
    fact,
    dim_nasabah,
    "nasabah_id",
    [
        "nik_terenkripsi",
        "tanggal_lahir",
        "jenis_kelamin",
        "jenis_usaha",
        "pendapatan_bulanan",
        "lama_usaha_tahun",
        "kota",
        "provinsi"
    ]
)


fact = add_dim(
    fact,
    dim_produk,
    "produk_id",
    [
        "nama_produk",
        "segmen",
        "plafon_min",
        "plafon_maks",
        "bunga_acuan_tahunan"
    ]
)


fact = add_dim(
    fact,
    dim_cabang,
    "cabang_id",
    [
        "nama_cabang",
        "kota",
        "provinsi",
        "wilayah",
        "tanggal_operasional"
    ]
)


fact = add_dim(
    fact,
    dim_petugas,
    "petugas_id",
    [
        "nama_petugas",
        "status_kepegawaian"
    ]
)


# ============================================================
# IDENTIFIKASI KOLOM
# ============================================================

pid = col(
    fact,
    ["pinjaman_id"]
)


date = col(
    fact,
    ["tanggal_akad"]
)


plafon = col(
    fact,
    [
        "plafon",
        "jumlah_pinjaman",
        "nilai_pinjaman"
    ]
)


kewajiban = col(
    fact,
    [
        "total_kewajiban"
    ]
)


realisasi = col(
    fact,
    [
        "total_realisasi",
        "total_realisasi_pembayaran"
    ]
)


baki = col(
    fact,
    [
        "baki_debet",
        "baki_debet_berjalan"
    ]
)


agunan = col(
    fact,
    [
        "total_nilai_agunan",
        "nilai_agunan"
    ]
)


tunggakan = col(
    fact,
    [
        "hari_tunggakan_terlama",
        "hari_tunggakan",
        "maks_hari_keterlambatan"
    ]
)


kolek = col(
    fact,
    [
        "kode_kolektibilitas"
    ]
)


kolek_nama = col(
    fact,
    [
        "kolektibilitas",
        "kolektibilitas_pinjaman",
        "kategori_kolektibilitas"
    ]
)


status = col(
    fact,
    [
        "status_pinjaman",
        "status"
    ]
)


# ============================================================
# DATA TIDAK DIBERSIHKAN
# ============================================================
#
# Data asli tetap dipertahankan.
# Tidak ada:
# - dropna
# - drop_duplicates
# - filter is_batal
# - filter segmen
# - penghapusan baris
#
# Hanya tanggal digunakan untuk membuat tahun/periode
# untuk kebutuhan visualisasi.
# ============================================================

if date:

    fact[date] = pd.to_datetime(
        fact[date],
        errors="coerce"
    )

    fact["tahun_dashboard"] = (
        fact[date]
        .dt.year
    )

    fact["periode_dashboard"] = (
        fact[date]
        .dt.to_period("M")
        .astype(str)
    )


# ============================================================
# JUMLAH DATA ASLI
# ============================================================

total_data_asli = len(fact)

# ============================================================
# FILTER
# ============================================================

st.sidebar.header("🔎 Filter")

# Tahun
if "tahun_dashboard" in fact.columns:

    tahun_list = sorted(
        fact["tahun_dashboard"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    tahun_dipilih = st.sidebar.multiselect(
        "Tahun",
        tahun_list,
        default=[]
    )

else:
    tahun_dipilih = []


# Provinsi
if "provinsi" in fact.columns:

    provinsi_list = sorted(
        fact["provinsi"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    provinsi_dipilih = st.sidebar.multiselect(
        "Provinsi",
        provinsi_list,
        default=[]
    )

else:
    provinsi_dipilih = []


# Wilayah
if "wilayah" in fact.columns:

    wilayah_list = sorted(
        fact["wilayah"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    wilayah_dipilih = st.sidebar.multiselect(
        "Wilayah",
        wilayah_list,
        default=[]
    )

else:
    wilayah_dipilih = []


# Cabang
if "nama_cabang" in fact.columns:

    cabang_list = sorted(
        fact["nama_cabang"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    cabang_dipilih = st.sidebar.multiselect(
        "Cabang",
        cabang_list,
        default=[]
    )

else:
    cabang_dipilih = []


# Produk
if "nama_produk" in fact.columns:

    produk_list = sorted(
        fact["nama_produk"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    produk_dipilih = st.sidebar.multiselect(
        "Produk",
        produk_list,
        default=[]
    )

else:
    produk_dipilih = []


# ============================================================
# FILTER DATA
# ============================================================

df = fact.copy()

if tahun_dipilih:

    df = df[
        df["tahun_dashboard"]
        .isin(tahun_dipilih)
    ]

if provinsi_dipilih:

    df = df[
        df["provinsi"]
        .astype(str)
        .isin(provinsi_dipilih)
    ]

if wilayah_dipilih:

    df = df[
        df["wilayah"]
        .astype(str)
        .isin(wilayah_dipilih)
    ]

if cabang_dipilih:

    df = df[
        df["nama_cabang"]
        .astype(str)
        .isin(cabang_dipilih)
    ]

if produk_dipilih:

    df = df[
        df["nama_produk"]
        .astype(str)
        .isin(produk_dipilih)
    ]


# ============================================================
# DEFINISI NPL
# ============================================================

if kolek:

    df["is_npl"] = df[kolek].isin([3, 4, 5])

else:

    df["is_npl"] = False


# ============================================================
# JUDUL
# ============================================================

st.title("💳 Dashboard Risiko & Collection Kredit Mikro")

# ============================================================
# RINGKASAN PORTOFOLIO
# ============================================================

jumlah_pinjaman = (
    df[pid].nunique()
    if pid
    else len(df)
)

total_kewajiban = (
    df[kewajiban].sum()
    if kewajiban
    else 0
)

total_realisasi = (
    df[realisasi].sum()
    if realisasi
    else 0
)

npl_rate = (
    df["is_npl"].mean() * 100
    if len(df) > 0
    else 0
)

avg_dpd = (
    df[tunggakan].mean()
    if tunggakan and len(df) > 0
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
        "NPL",
        f"{npl_rate:.2f}%"
    )

with k5:
    st.metric(
        "Rata-rata DPD",
        f"{avg_dpd:.1f} hari"
        if pd.notna(avg_dpd)
        else "N/A"
    )   
    
# ============================================================
# NPL PER CABANG
# ============================================================

st.divider()

st.header("NPL Berdasarkan Cabang")

branch_npl = (

    df.groupby("nama_cabang")

    .agg(
        jumlah_pinjaman=(
            pid,
            "nunique"
        ) if pid else (
            "nama_cabang",
            "size"
        ),

        jumlah_npl=(
            "is_npl",
            "sum"
        )
    )

    .reset_index()
)

branch_npl["npl_rate"] = (
    branch_npl["jumlah_npl"]
    /
    branch_npl["jumlah_pinjaman"]
)

branch_npl["npl_persen"] = (
    branch_npl["npl_rate"] * 100
)

branch_npl = branch_npl.sort_values(
    "npl_rate",
    ascending=False
)


worst_branch = branch_npl.iloc[0]


a, b = st.columns(2)

a.metric(
    "Cabang dengan NPL Tertinggi",
    worst_branch["nama_cabang"]
)

b.metric(
    "NPL Tertinggi",
    f"{worst_branch['npl_rate'] * 100:.2f}%"
)


fig_npl = px.bar(
    branch_npl,
    x="nama_cabang",
    y="npl_persen",
    text="npl_persen",
    labels={
        "nama_cabang": "Cabang",
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


# ============================================================
# DPD PER PRODUK
# ============================================================

st.divider()

st.header("Rata-rata DPD Berdasarkan Produk")

product_dpd = (

    df.groupby("nama_produk")

    .agg(
        rata_rata_dpd=(
            tunggakan,
            "mean"
        ),

        jumlah_pinjaman=(
            pid,
            "nunique"
        ) if pid else (
            "nama_produk",
            "size"
        )
    )

    .reset_index()

    .sort_values(
        "rata_rata_dpd",
        ascending=False
    )
)


worst_product = product_dpd.iloc[0]


a, b = st.columns(2)

a.metric(
    "Produk dengan DPD Tertinggi",
    worst_product["nama_produk"]
)

b.metric(
    "Rata-rata DPD Tertinggi",
    f"{worst_product['rata_rata_dpd']:.1f} hari"
)


fig_dpd = px.bar(
    product_dpd,
    x="nama_produk",
    y="rata_rata_dpd",
    text="rata_rata_dpd",
    labels={
        "nama_produk": "Produk Kredit",
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


# ============================================================
# NPL BERDASARKAN AGUNAN
# ============================================================

st.divider()

st.header("NPL Berdasarkan Status Agunan")

df["status_agunan"] = np.where(
    df[agunan] > 0,
    "Dengan Agunan",
    "Tanpa Agunan"
)


agunan_npl = (

    df.groupby("status_agunan")

    .agg(
        jumlah_pinjaman=(
            pid,
            "nunique"
        ) if pid else (
            "status_agunan",
            "size"
        ),

        jumlah_npl=(
            "is_npl",
            "sum"
        )
    )

    .reset_index()
)


agunan_npl["npl_rate"] = (
    agunan_npl["jumlah_npl"]
    /
    agunan_npl["jumlah_pinjaman"]
)


agunan_npl["npl_persen"] = (
    agunan_npl["npl_rate"] * 100
)


npl_agunan = (
    agunan_npl.loc[
        agunan_npl["status_agunan"]
        == "Dengan Agunan",
        "npl_rate"
    ]
)

npl_tanpa_agunan = (
    agunan_npl.loc[
        agunan_npl["status_agunan"]
        == "Tanpa Agunan",
        "npl_rate"
    ]
)


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
    npl_agunan
    -
    npl_tanpa_agunan
)


a, b, c = st.columns(3)

a.metric(
    "NPL Dengan Agunan",
    f"{npl_agunan * 100:.2f}%"
)

b.metric(
    "NPL Tanpa Agunan",
    f"{npl_tanpa_agunan * 100:.2f}%"
)

c.metric(
    "Selisih NPL",
    f"{selisih * 100:.2f} pp"
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

    st.subheader(
        "Petugas Kredit"
    )


    officer = (

        df.groupby("nama_petugas")

        .agg(
            total_tunggakan=(
                baki,
                "sum"
            ),

            jumlah_pinjaman=(
                pid,
                "nunique"
            ) if pid else (
                "nama_petugas",
                "size"
            )
        )

        .reset_index()

        .sort_values(
            "total_tunggakan",
            ascending=False
        )

    )


    top_officer = officer.iloc[0]


    st.metric(
        "Tunggakan Terbesar",
        top_officer["nama_petugas"],
        rupiah(
            top_officer[
                "total_tunggakan"
            ]
        )
    )


    fig_officer = px.bar(
        officer.head(10),
        x="total_tunggakan",
        y="nama_petugas",
        orientation="h",
        text="total_tunggakan",
        labels={
            "nama_petugas":
                "Petugas Kredit",

            "total_tunggakan":
                "Total Tunggakan"
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


# ------------------------------------------------------------
# JENIS USAHA
# ------------------------------------------------------------

with right:

    st.subheader(
        "Jenis Usaha"
    )


    business = (

        df.groupby(
            "jenis_usaha",
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
            ) if pid else (
                "jenis_usaha",
                "size"
            )
        )

        .reset_index()

        .sort_values(
            "total_tunggakan",
            ascending=False
        )
    )


    top_business = business.iloc[0]


    st.metric(
        "Tunggakan Terbesar",
        str(
            top_business[
                "jenis_usaha"
            ]
        ),
        rupiah(
            top_business[
                "total_tunggakan"
            ]
        )
    )


    fig_business = px.bar(
        business.head(10),
        x="total_tunggakan",
        y="jenis_usaha",
        orientation="h",
        text="total_tunggakan",
        labels={
            "jenis_usaha":
                "Jenis Usaha",

            "total_tunggakan":
                "Total Tunggakan"
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


# ============================================================
# COLLECTION RATE
# ============================================================

st.divider()

st.header("Collection Rate Berdasarkan Cabang")

st.caption(
    "Menunjukkan cabang dengan tingkat collection rate "
    "terendah."
)


branch_collection = (

    df.groupby("nama_cabang")

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


branch_collection["collection_rate"] = (
    branch_collection["total_realisasi"]
    /
    branch_collection["total_kewajiban"]
)


branch_collection = (
    branch_collection
    .sort_values(
        "collection_rate",
        ascending=True
    )
)


worst_collection = (
    branch_collection.iloc[0]
)


a, b = st.columns(2)

a.metric(
    "Cabang dengan Collection Rate Terendah",
    worst_collection["nama_cabang"]
)

b.metric(
    "Collection Rate Terendah",
    f"{worst_collection['collection_rate'] * 100:.2f}%"
)


fig_collection = px.bar(
    branch_collection,
    x="nama_cabang",
    y="collection_rate",
    text="collection_rate",
    labels={
        "nama_cabang": "Cabang",
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

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    f"Total data awal: {total_data_asli:,} pinjaman | "
    f"Data yang sedang dianalisis: {jumlah_pinjaman:,} pinjaman"
)
