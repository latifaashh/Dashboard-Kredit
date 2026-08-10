import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================

st.set_page_config(
    page_title="Dashboard Kredit Mikro",
    page_icon="💰",
    layout="wide"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }

    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    h1 {
        font-weight: 700;
    }

    h2, h3 {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# JUDUL
# ============================================================

st.title("💰 Dashboard Risiko & Collection Kredit Mikro")

st.markdown(
    """
    Dashboard ini digunakan untuk menganalisis kualitas portofolio kredit mikro
    berdasarkan **NPL, DPD, agunan, tunggakan, dan collection rate**.
    """
)

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    file_path = Path("fact_pinjaman_final.csv")

    if not file_path.exists():
        return None

    df = pd.read_csv(file_path)

    return df


df = load_data()

# ============================================================
# CEK DATA
# ============================================================

if df is None:

    st.error(
        "File `fact_pinjaman_final.csv` tidak ditemukan. "
        "Pastikan file berada dalam folder yang sama dengan `app.py`."
    )

    uploaded_file = st.file_uploader(
        "Atau upload file fact_pinjaman_final.csv",
        type=["csv"]
    )

    if uploaded_file is not None:

        df = pd.read_csv(uploaded_file)

    else:

        st.stop()

# ============================================================
# PEMBERSIHAN DATA
# ============================================================

# Kolom numerik
numeric_columns = [
    "plafon",
    "total_kewajiban",
    "total_realisasi",
    "baki_debet",
    "hari_tunggakan_terlama",
    "total_nilai_agunan",
    "kode_kolektibilitas"
]

for col in numeric_columns:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

# Tanggal
if "tanggal_akad" in df.columns:

    df["tanggal_akad"] = pd.to_datetime(
        df["tanggal_akad"],
        errors="coerce"
    )


# ============================================================
# PORTOFOLIO KREDIT
# ============================================================

# Gunakan seluruh 3.400 data pinjaman
# Tidak melakukan filter segmen
# Tidak menghapus pinjaman berdasarkan is_batal
df = df.copy()

# ============================================================
# DEFINISI NPL
# ============================================================

# Kolektibilitas:
# 1 = Lancar
# 2 = Dalam Perhatian Khusus
# 3 = Kurang Lancar
# 4 = Diragukan
# 5 = Macet

if "kode_kolektibilitas" in df.columns:

    df["is_npl"] = df[
        "kode_kolektibilitas"
    ].isin([3, 4, 5])

else:

    df["is_npl"] = False

# ============================================================
# STATUS AGUNAN
# ============================================================

if "total_nilai_agunan" in df.columns:

    df["ada_agunan"] = (
        df["total_nilai_agunan"]
        .fillna(0)
        > 0
    )

else:

    df["ada_agunan"] = False

# ============================================================
# NILAI TUNGGAKAN
# ============================================================

# Karena fact utama tidak mempunyai
# nominal tunggakan per angsuran,
# baki debet digunakan sebagai proxy.

if "baki_debet" in df.columns:

    df["nilai_tunggakan"] = (
        df["baki_debet"]
        .fillna(0)
        .clip(lower=0)
    )

else:

    df["nilai_tunggakan"] = 0

# ============================================================
# COLLECTION RATE PER PINJAMAN
# ============================================================

if (
    "total_realisasi" in df.columns
    and
    "total_kewajiban" in df.columns
):

    df["collection_rate_individu"] = (
        df["total_realisasi"]
        /
        df["total_kewajiban"]
        .replace(0, pd.NA)
    )

    df["collection_rate_individu"] = (
        df["collection_rate_individu"]
        .fillna(0)
        .clip(0, 1)
    )

else:

    df["collection_rate_individu"] = 0


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Filter Dashboard")

# ------------------------------------------------------------
# Tahun
# ------------------------------------------------------------

if "tanggal_akad" in df.columns:

    years = sorted(
        df["tanggal_akad"]
        .dt.year
        .dropna()
        .astype(int)
        .unique()
    )

else:

    years = []

selected_year = st.sidebar.multiselect(
    "Tahun Akad",
    options=years,
    default=years
)

# ------------------------------------------------------------
# Cabang
# ------------------------------------------------------------

branches = sorted(
    df["nama_cabang"]
    .dropna()
    .unique()
)

selected_branch = st.sidebar.multiselect(
    "Cabang",
    options=branches,
    default=branches
)

# ------------------------------------------------------------
# Produk
# ------------------------------------------------------------

products = sorted(
    df["nama_produk"]
    .dropna()
    .unique()
)

selected_product = st.sidebar.multiselect(
    "Produk Kredit",
    options=products,
    default=products
)

# ------------------------------------------------------------
# Agunan
# ------------------------------------------------------------

selected_collateral = st.sidebar.multiselect(
    "Status Agunan",
    options=[
        "Dengan Agunan",
        "Tanpa Agunan"
    ],
    default=[
        "Dengan Agunan",
        "Tanpa Agunan"
    ]
)

# ============================================================
# APPLY FILTER
# ============================================================

filtered_df = df.copy()

if years:

    filtered_df = filtered_df[
        filtered_df["tanggal_akad"]
        .dt.year
        .isin(selected_year)
    ]

filtered_df = filtered_df[
    filtered_df["nama_cabang"]
    .isin(selected_branch)
]

filtered_df = filtered_df[
    filtered_df["nama_produk"]
    .isin(selected_product)
]

collateral_map = {
    "Dengan Agunan": True,
    "Tanpa Agunan": False
}

selected_collateral_values = [
    collateral_map[x]
    for x in selected_collateral
]

filtered_df = filtered_df[
    filtered_df["ada_agunan"]
    .isin(selected_collateral_values)
]

# ============================================================
# CEK FILTER
# ============================================================

if filtered_df.empty:

    st.warning(
        "Tidak terdapat data yang sesuai dengan filter."
    )

    st.stop()

# ============================================================
# FUNGSI FORMAT
# ============================================================

def format_rupiah(value):

    return (
        "Rp "
        + f"{value:,.0f}"
        .replace(",", ".")
    )


def format_percent(value):

    return f"{value * 100:.2f}%"


# ============================================================
# PERHITUNGAN KPI
# ============================================================

total_pinjaman = len(
    filtered_df
)

total_plafon = filtered_df[
    "plafon"
].sum()

total_baki_debet = filtered_df[
    "baki_debet"
].sum()

npl_rate = filtered_df[
    "is_npl"
].mean()

avg_dpd = filtered_df[
    "hari_tunggakan_terlama"
].mean()

total_realisasi = filtered_df[
    "total_realisasi"
].sum()

total_kewajiban = filtered_df[
    "total_kewajiban"
].sum()

if total_kewajiban > 0:

    collection_rate = (
        total_realisasi
        /
        total_kewajiban
    )

else:

    collection_rate = 0

# ============================================================
# KPI
# ============================================================

st.subheader("📌 Ringkasan Portofolio")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:

    st.metric(
        "Total Pinjaman",
        f"{total_pinjaman:,}"
    )

with col2:

    st.metric(
        "Total Plafon",
        format_rupiah(total_plafon)
    )

with col3:

    st.metric(
        "NPL",
        format_percent(npl_rate)
    )

with col4:

    st.metric(
        "Rata-rata DPD",
        f"{avg_dpd:.1f} hari"
    )

with col5:

    st.metric(
        "Collection Rate",
        format_percent(collection_rate)
    )

st.divider()

# ============================================================
# PERTANYAAN 1
# NPL
# ============================================================

st.header(
    "1️⃣ NPL Portofolio dan Cabang dengan NPL Tertinggi"
)

# ------------------------------------------------------------
# NPL keseluruhan
# ------------------------------------------------------------

st.markdown(
    f"""
    **NPL seluruh portofolio kredit mikro adalah
    {format_percent(npl_rate)}.**
    """
)

# ------------------------------------------------------------
# NPL CABANG
# ------------------------------------------------------------

branch_npl = (

    filtered_df

    .groupby("nama_cabang")

    .agg(

        jumlah_pinjaman=(
            "pinjaman_id",
            "count"
        ),

        jumlah_npl=(
            "is_npl",
            "sum"
        ),

        baki_debet=(
            "baki_debet",
            "sum"
        )

    )

    .reset_index()

)

branch_npl["npl"] = (

    branch_npl["jumlah_npl"]
    /
    branch_npl["jumlah_pinjaman"]

)

branch_npl["npl_persen"] = (
    branch_npl["npl"] * 100
)

# ------------------------------------------------------------
# Cabang tertinggi
# ------------------------------------------------------------

worst_branch = (
    branch_npl
    .sort_values(
        "npl",
        ascending=False
    )
    .iloc[0]
)

c1, c2 = st.columns(2)

with c1:

    st.metric(
        "Cabang NPL Tertinggi",
        worst_branch["nama_cabang"]
    )

with c2:

    st.metric(
        "NPL Tertinggi",
        f"{worst_branch['npl'] * 100:.2f}%"
    )

# ------------------------------------------------------------
# Grafik
# ------------------------------------------------------------

fig_npl = px.bar(

    branch_npl
    .sort_values(
        "npl_persen",
        ascending=False
    ),

    x="nama_cabang",

    y="npl_persen",

    text="npl_persen",

    labels={
        "nama_cabang": "Cabang",
        "npl_persen": "NPL (%)"
    },

    title="NPL Kredit Mikro Berdasarkan Cabang"

)

fig_npl.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

fig_npl.update_layout(
    yaxis_title="NPL (%)",
    xaxis_title=""
)

st.plotly_chart(
    fig_npl,
    use_container_width=True
)

# ------------------------------------------------------------
# Tabel
# ------------------------------------------------------------

st.dataframe(

    branch_npl
    .sort_values(
        "npl",
        ascending=False
    )
    .rename(
        columns={
            "nama_cabang": "Cabang",
            "jumlah_pinjaman": "Jumlah Pinjaman",
            "jumlah_npl": "Jumlah NPL",
            "npl_persen": "NPL (%)",
            "baki_debet": "Baki Debet"
        }
    )[[
        "Cabang",
        "Jumlah Pinjaman",
        "Jumlah NPL",
        "NPL (%)",
        "Baki Debet"
    ]],

    use_container_width=True,

    hide_index=True

)

# ============================================================
# PERTANYAAN 2
# DPD
# ============================================================

st.header(
    "2️⃣ Rata-rata DPD dan Produk dengan Keterlambatan Tertinggi"
)

avg_dpd = filtered_df[
    "hari_tunggakan_terlama"
].mean()

st.markdown(
    f"""
    **Rata-rata hari keterlambatan pembayaran (DPD)
    seluruh portofolio adalah {avg_dpd:.1f} hari.**
    """
)

# ------------------------------------------------------------
# DPD PRODUK
# ------------------------------------------------------------

product_dpd = (

    filtered_df

    .groupby("nama_produk")

    .agg(

        rata_rata_dpd=(
            "hari_tunggakan_terlama",
            "mean"
        ),

        jumlah_pinjaman=(
            "pinjaman_id",
            "count"
        )

    )

    .reset_index()

)

product_dpd = product_dpd.sort_values(
    "rata_rata_dpd",
    ascending=False
)

worst_product = product_dpd.iloc[0]

st.metric(
    "Produk dengan Rata-rata DPD Tertinggi",
    worst_product["nama_produk"],
    f"{worst_product['rata_rata_dpd']:.1f} hari"
)

# ------------------------------------------------------------
# Grafik DPD
# ------------------------------------------------------------

fig_dpd = px.bar(

    product_dpd,

    x="nama_produk",

    y="rata_rata_dpd",

    text="rata_rata_dpd",

    labels={
        "nama_produk": "Produk",
        "rata_rata_dpd":
            "Rata-rata DPD (Hari)"
    },

    title="Rata-rata DPD Berdasarkan Produk"

)

fig_dpd.update_traces(
    texttemplate="%{text:.1f}",
    textposition="outside"
)

fig_dpd.update_layout(
    xaxis_tickangle=-45
)

st.plotly_chart(
    fig_dpd,
    use_container_width=True
)

# ============================================================
# PERTANYAAN 3
# AGUNAN
# ============================================================

st.header(
    "3️⃣ Perbandingan NPL dengan Agunan dan Tanpa Agunan"
)

collateral_npl = (

    filtered_df

    .groupby("ada_agunan")

    .agg(

        jumlah_pinjaman=(
            "pinjaman_id",
            "count"
        ),

        jumlah_npl=(
            "is_npl",
            "sum"
        )

    )

    .reset_index()

)

collateral_npl["npl"] = (

    collateral_npl["jumlah_npl"]
    /
    collateral_npl["jumlah_pinjaman"]

)

collateral_npl["status_agunan"] = (
    collateral_npl["ada_agunan"]
    .map({
        True: "Dengan Agunan",
        False: "Tanpa Agunan"
    })
)

with_collateral = (
    collateral_npl[
        collateral_npl["ada_agunan"] == True
    ]["npl"]
)

without_collateral = (
    collateral_npl[
        collateral_npl["ada_agunan"] == False
    ]["npl"]
)

with_collateral = (
    with_collateral.iloc[0]
    if len(with_collateral) > 0
    else 0
)

without_collateral = (
    without_collateral.iloc[0]
    if len(without_collateral) > 0
    else 0
)

difference_npl = abs(
    with_collateral
    -
    without_collateral
)

# ------------------------------------------------------------
# KPI AGUNAN
# ------------------------------------------------------------

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "NPL Dengan Agunan",
        format_percent(with_collateral)
    )

with c2:

    st.metric(
        "NPL Tanpa Agunan",
        format_percent(without_collateral)
    )

with c3:

    st.metric(
        "Selisih NPL",
        f"{difference_npl * 100:.2f} pp"
    )

# ------------------------------------------------------------
# Grafik
# ------------------------------------------------------------

collateral_npl["npl_persen"] = (
    collateral_npl["npl"]
    * 100
)

fig_collateral = px.bar(

    collateral_npl,

    x="status_agunan",

    y="npl_persen",

    text="npl_persen",

    labels={
        "status_agunan":
            "Status Agunan",
        "npl_persen":
            "NPL (%)"
    },

    title="NPL Berdasarkan Status Agunan"

)

fig_collateral.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

st.plotly_chart(
    fig_collateral,
    use_container_width=True
)

# ============================================================
# PERTANYAAN 4
# TUNGGAKAN PETUGAS
# ============================================================

st.header(
    "4️⃣ Petugas Kredit atau Segmen Usaha dengan Tunggakan Terbesar"
)

tab_petugas, tab_usaha = st.tabs(
    [
        "👤 Petugas Kredit",
        "🏪 Jenis Usaha"
    ]
)

# ============================================================
# PETUGAS
# ============================================================

with tab_petugas:

    officer = (

        filtered_df

        .groupby("nama_petugas")

        .agg(

            total_tunggakan=(
                "nilai_tunggakan",
                "sum"
            ),

            jumlah_pinjaman=(
                "pinjaman_id",
                "count"
            ),

            jumlah_npl=(
                "is_npl",
                "sum"
            )

        )

        .reset_index()

        .sort_values(
            "total_tunggakan",
            ascending=False
        )

    )

    # Top petugas
    top_officer = officer.iloc[0]

    st.metric(
        "Petugas dengan Tunggakan Terbesar",
        top_officer["nama_petugas"],
        format_rupiah(
            top_officer["total_tunggakan"]
        )
    )

    fig_officer = px.bar(

        officer.head(15),

        x="nama_petugas",

        y="total_tunggakan",

        text="total_tunggakan",

        labels={
            "nama_petugas":
                "Petugas Kredit",
            "total_tunggakan":
                "Total Tunggakan"
        },

        title="15 Petugas dengan Total Tunggakan Terbesar"

    )

    fig_officer.update_traces(
        texttemplate="Rp %{text:,.0f}",
        textposition="outside"
    )

    fig_officer.update_layout(
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig_officer,
        use_container_width=True
    )

    st.dataframe(

        officer.rename(
            columns={
                "nama_petugas":
                    "Petugas",
                "total_tunggakan":
                    "Total Tunggakan",
                "jumlah_pinjaman":
                    "Jumlah Pinjaman",
                "jumlah_npl":
                    "Jumlah NPL"
            }
        ),

        use_container_width=True,

        hide_index=True

    )

# ============================================================
# JENIS USAHA
# ============================================================

with tab_usaha:

    business = (

        filtered_df

        .groupby("jenis_usaha")

        .agg(

            total_tunggakan=(
                "nilai_tunggakan",
                "sum"
            ),

            jumlah_pinjaman=(
                "pinjaman_id",
                "count"
            ),

            jumlah_npl=(
                "is_npl",
                "sum"
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
        "Jenis Usaha dengan Tunggakan Terbesar",
        top_business["jenis_usaha"],
        format_rupiah(
            top_business["total_tunggakan"]
        )
    )

    fig_business = px.bar(

        business,

        x="jenis_usaha",

        y="total_tunggakan",

        text="total_tunggakan",

        labels={
            "jenis_usaha":
                "Jenis Usaha",
            "total_tunggakan":
                "Total Tunggakan"
        },

        title="Total Tunggakan Berdasarkan Jenis Usaha"

    )

    fig_business.update_traces(
        texttemplate="Rp %{text:,.0f}",
        textposition="outside"
    )

    fig_business.update_layout(
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig_business,
        use_container_width=True
    )

    st.dataframe(

        business.rename(
            columns={
                "jenis_usaha":
                    "Jenis Usaha",
                "total_tunggakan":
                    "Total Tunggakan",
                "jumlah_pinjaman":
                    "Jumlah Pinjaman",
                "jumlah_npl":
                    "Jumlah NPL"
            }
        ),

        use_container_width=True,

        hide_index=True

    )

# ============================================================
# PERTANYAAN 5
# COLLECTION RATE
# ============================================================

st.header(
    "5️⃣ Collection Rate Kredit Mikro"
)

# ------------------------------------------------------------
# COLLECTION RATE KESELURUHAN
# ------------------------------------------------------------

total_realisasi = filtered_df[
    "total_realisasi"
].sum()

total_kewajiban = filtered_df[
    "total_kewajiban"
].sum()

if total_kewajiban > 0:

    collection_rate = (
        total_realisasi
        /
        total_kewajiban
    )

else:

    collection_rate = 0

st.metric(
    "Collection Rate Keseluruhan",
    format_percent(collection_rate)
)

# ------------------------------------------------------------
# COLLECTION RATE CABANG
# ------------------------------------------------------------

branch_collection = (

    filtered_df

    .groupby("nama_cabang")

    .agg(

        total_realisasi=(
            "total_realisasi",
            "sum"
        ),

        total_kewajiban=(
            "total_kewajiban",
            "sum"
        ),

        jumlah_pinjaman=(
            "pinjaman_id",
            "count"
        )

    )

    .reset_index()

)

branch_collection["collection_rate"] = (

    branch_collection[
        "total_realisasi"
    ]
    /
    branch_collection[
        "total_kewajiban"
    ].replace(0, pd.NA)

).fillna(0)

branch_collection = branch_collection.sort_values(
    "collection_rate"
)

# ------------------------------------------------------------
# Cabang terendah
# ------------------------------------------------------------

worst_collection = (
    branch_collection.iloc[0]
)

c1, c2 = st.columns(2)

with c1:

    st.metric(
        "Collection Rate Terendah",
        f"{worst_collection['collection_rate'] * 100:.2f}%"
    )

with c2:

    st.metric(
        "Cabang",
        worst_collection["nama_cabang"]
    )

# ------------------------------------------------------------
# Grafik
# ------------------------------------------------------------

fig_collection = px.bar(

    branch_collection,

    x="nama_cabang",

    y="collection_rate",

    text="collection_rate",

    labels={
        "nama_cabang":
            "Cabang",

        "collection_rate":
            "Collection Rate"
    },

    title="Collection Rate Berdasarkan Cabang"

)

fig_collection.update_traces(
    texttemplate="%{text:.2%}",
    textposition="outside"
)

fig_collection.update_layout(
    yaxis_tickformat=".0%"
)

st.plotly_chart(
    fig_collection,
    use_container_width=True
)

# ============================================================
# DISTRIBUSI KOLEKTIBILITAS
# ============================================================

st.header(
    "📊 Distribusi Kolektibilitas Kredit"
)

if "kolektibilitas" in filtered_df.columns:

    kolektibilitas = (

        filtered_df[
            "kolektibilitas"
        ]

        .value_counts()

        .reset_index()

    )

    kolektibilitas.columns = [
        "Kolektibilitas",
        "Jumlah"
    ]

    fig_kolektibilitas = px.pie(

        kolektibilitas,

        names="Kolektibilitas",

        values="Jumlah",

        hole=0.45,

        title="Komposisi Kolektibilitas Kredit Mikro"

    )

    st.plotly_chart(
        fig_kolektibilitas,
        use_container_width=True
    )

# ============================================================
# DATA DETAIL
# ============================================================

st.header(
    "📋 Detail Data Kredit"
)

detail_columns = [

    "pinjaman_id",
    "nasabah_id",
    "nama_produk",
    "nama_cabang",
    "nama_petugas",
    "tanggal_akad",
    "plafon",
    "baki_debet",
    "hari_tunggakan_terlama",
    "kolektibilitas",
    "kode_kolektibilitas",
    "total_nilai_agunan",
    "jenis_usaha",
    "is_npl"

]

detail_columns = [
    col
    for col in detail_columns
    if col in filtered_df.columns
]

st.dataframe(

    filtered_df[
        detail_columns
    ],

    use_container_width=True,

    hide_index=True

)

# ============================================================
# DOWNLOAD
# ============================================================

st.header(
    "⬇️ Download Data"
)

csv_data = filtered_df[
    detail_columns
].to_csv(
    index=False
).encode("utf-8")

st.download_button(

    label="📥 Download Hasil Filter",

    data=csv_data,

    file_name="hasil_analisis_kredit_mikro.csv",

    mime="text/csv"

)

# ============================================================
# CATATAN METODOLOGI
# ============================================================

st.divider()

st.caption(
    """
    **Catatan metodologi:** NPL dihitung sebagai proporsi pinjaman dengan
    kolektibilitas 3 (Kurang Lancar), 4 (Diragukan), dan 5 (Macet).
    DPD menggunakan variabel `hari_tunggakan_terlama`.
    Status dengan agunan ditentukan berdasarkan `total_nilai_agunan > 0`.
    Collection rate dihitung sebagai `total_realisasi / total_kewajiban`.
    Karena fact utama tidak memuat rincian nominal tunggakan per angsuran,
    `baki_debet` digunakan sebagai proxy nilai tunggakan.
    """
)
