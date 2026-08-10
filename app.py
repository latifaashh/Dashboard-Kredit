import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================

st.set_page_config(
    page_title="Dashboard Risiko & Collection Kredit Mikro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

    .main {
        background-color: #f8f9fc;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1 {
        font-weight: 700;
    }

    h2 {
        font-weight: 650;
    }

    h3 {
        font-weight: 600;
    }

    [data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #eeeeee;
    }

    [data-testid="stMetricValue"] {
        font-size: 27px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    df = pd.read_csv(
        "fact_pinjaman_final.csv"
    )

    return df


df = load_data()


# ============================================================
# VALIDASI JUMLAH DATA
# ============================================================

total_data_asli = len(df)


# ============================================================
# JUDUL
# ============================================================

st.title(
    "💰 Dashboard Risiko & Collection Kredit Mikro"
)

st.markdown(
    """
    Dashboard ini digunakan untuk menganalisis kualitas portofolio kredit
    berdasarkan **NPL, DPD, agunan, tunggakan, dan collection rate**.
    """
)

st.caption(
    f"Dataset yang digunakan: **{total_data_asli:,} pinjaman**"
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Filter Dashboard")

st.sidebar.markdown(
    "Gunakan filter untuk melihat analisis berdasarkan periode, "
    "cabang, dan produk."
)


# ============================================================
# FILTER TAHUN
# ============================================================

tahun_data = df["tahun"]

tahun_tersedia = sorted(
    tahun_data.dropna().unique().tolist()
)

tahun_tersedia = [
    int(x)
    for x in tahun_tersedia
]

# Tambahkan kategori untuk 57 data yang tidak memiliki tahun
tahun_options = [
    str(x)
    for x in tahun_tersedia
]

tahun_options.append(
    "Tahun Tidak Tersedia"
)


selected_year = st.sidebar.multiselect(
    "Tahun Akad",
    options=tahun_options,
    default=tahun_options
)


# ============================================================
# FILTER CABANG
# ============================================================

cabang_options = sorted(
    df["nama_cabang"]
    .dropna()
    .unique()
    .tolist()
)

selected_branch = st.sidebar.multiselect(
    "Cabang",
    options=cabang_options,
    default=cabang_options
)


# ============================================================
# FILTER PRODUK
# ============================================================

produk_options = sorted(
    df["nama_produk"]
    .dropna()
    .unique()
    .tolist()
)

selected_product = st.sidebar.multiselect(
    "Produk Kredit",
    options=produk_options,
    default=produk_options
)


# ============================================================
# FILTER STATUS AGUNAN
# ============================================================

# Tidak mengubah data asli.
# Hanya membuat kategori untuk kebutuhan analisis.

status_agunan = pd.Series(
    "Tanpa Agunan",
    index=df.index
)

status_agunan[
    df["total_nilai_agunan"].fillna(0) > 0
] = "Dengan Agunan"

df["status_agunan_dashboard"] = status_agunan


agunan_options = [
    "Dengan Agunan",
    "Tanpa Agunan"
]

selected_agunan = st.sidebar.multiselect(
    "Status Agunan",
    options=agunan_options,
    default=agunan_options
)


# ============================================================
# FILTER DATA
# ============================================================

filtered_df = df.copy()


# ------------------------------------------------------------
# FILTER TAHUN
# ------------------------------------------------------------

mask_tahun = pd.Series(
    False,
    index=df.index
)

for tahun in selected_year:

    if tahun == "Tahun Tidak Tersedia":

        mask_tahun = (
            mask_tahun
            |
            df["tahun"].isna()
        )

    else:

        mask_tahun = (
            mask_tahun
            |
            (
                df["tahun"]
                == int(tahun)
            )
        )


filtered_df = filtered_df[
    mask_tahun
]


# ------------------------------------------------------------
# FILTER CABANG
# ------------------------------------------------------------

filtered_df = filtered_df[
    filtered_df["nama_cabang"]
    .isin(selected_branch)
]


# ------------------------------------------------------------
# FILTER PRODUK
# ------------------------------------------------------------

filtered_df = filtered_df[
    filtered_df["nama_produk"]
    .isin(selected_product)
]


# ------------------------------------------------------------
# FILTER AGUNAN
# ------------------------------------------------------------

filtered_df = filtered_df[
    filtered_df[
        "status_agunan_dashboard"
    ].isin(selected_agunan)
]


# ============================================================
# CEK DATA HASIL FILTER
# ============================================================

if filtered_df.empty:

    st.warning(
        "Tidak terdapat data yang sesuai dengan filter."
    )

    st.stop()


# ============================================================
# DEFINISI NPL
# ============================================================

filtered_df["is_npl_dashboard"] = (
    filtered_df[
        "kode_kolektibilitas"
    ].isin([3, 4, 5])
)


# ============================================================
# FUNGSI FORMAT
# ============================================================

def format_rupiah(value):

    if pd.isna(value):
        value = 0

    return (
        "Rp "
        + f"{value:,.0f}"
        .replace(",", ".")
    )


def format_percent(value):

    if pd.isna(value):
        value = 0

    return f"{value * 100:.2f}%"


# ============================================================
# KPI PORTOFOLIO
# ============================================================

total_pinjaman = len(
    filtered_df
)


total_plafon = filtered_df[
    "plafon"
].sum()


npl_rate = filtered_df[
    "is_npl_dashboard"
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


if total_kewajiban != 0:

    collection_rate = (
        total_realisasi
        /
        total_kewajiban
    )

else:

    collection_rate = 0


# ============================================================
# RINGKASAN PORTOFOLIO
# ============================================================

st.divider()

st.header(
    "📌 Ringkasan Portofolio"
)


col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "Total Pinjaman",
        f"{total_pinjaman:,}"
    )


with col2:

    st.metric(
        "Total Plafon",
        format_rupiah(
            total_plafon
        )
    )


with col3:

    st.metric(
        "NPL",
        format_percent(
            npl_rate
        )
    )


with col4:

    st.metric(
        "Rata-rata DPD",
        f"{avg_dpd:.1f} hari"
    )


with col5:

    st.metric(
        "Collection Rate",
        format_percent(
            collection_rate
        )
    )


# ============================================================
# INFORMASI DATA
# ============================================================

st.info(
    f"""
    **Data yang sedang dianalisis: {len(filtered_df):,} pinjaman.**
    
    Total dataset asli adalah **{total_data_asli:,} pinjaman**.
    Data dengan tahun akad yang tidak tersedia tetap dipertahankan
    dan masuk dalam kategori **Tahun Tidak Tersedia**.
    """
)


# ============================================================
# PERTANYAAN 1
# NPL PORTOFOLIO
# ============================================================

st.divider()

st.header(
    "1️⃣ NPL Portofolio dan Cabang dengan NPL Tertinggi"
)


st.markdown(
    f"""
    Persentase **Non-Performing Loan (NPL)** pada portofolio
    yang sedang ditampilkan adalah **{format_percent(npl_rate)}**.
    
    NPL dihitung berdasarkan pinjaman dengan kolektibilitas
    **3 (Kurang Lancar), 4 (Diragukan), dan 5 (Macet)**.
    """
)


# ============================================================
# NPL CABANG
# ============================================================

branch_npl = (

    filtered_df

    .groupby(
        "nama_cabang"
    )

    .agg(

        jumlah_pinjaman=(
            "pinjaman_id",
            "count"
        ),

        jumlah_npl=(
            "is_npl_dashboard",
            "sum"
        ),

        baki_debet=(
            "baki_debet",
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
    branch_npl["npl_rate"]
    * 100
)


branch_npl = branch_npl.sort_values(
    "npl_rate",
    ascending=False
)


# ============================================================
# CABANG NPL TERTINGGI
# ============================================================

worst_branch_npl = (
    branch_npl.iloc[0]
)


col1, col2 = st.columns(2)


with col1:

    st.metric(
        "Cabang dengan NPL Tertinggi",
        worst_branch_npl[
            "nama_cabang"
        ]
    )


with col2:

    st.metric(
        "NPL Tertinggi",
        f"{worst_branch_npl['npl_rate'] * 100:.2f}%"
    )


# ============================================================
# GRAFIK NPL CABANG
# ============================================================

fig_npl = px.bar(

    branch_npl,

    x="nama_cabang",

    y="npl_persen",

    text="npl_persen",

    labels={
        "nama_cabang":
            "Cabang",

        "npl_persen":
            "NPL (%)"
    },

    title="NPL Kredit Mikro Berdasarkan Cabang"

)


fig_npl.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)


fig_npl.update_layout(
    yaxis_title="NPL (%)",
    xaxis_title="",
    uniformtext_minsize=8,
    uniformtext_mode="hide"
)


st.plotly_chart(
    fig_npl,
    use_container_width=True
)


# ============================================================
# TABEL NPL
# ============================================================

st.dataframe(

    branch_npl.rename(
        columns={

            "nama_cabang":
                "Cabang",

            "jumlah_pinjaman":
                "Jumlah Pinjaman",

            "jumlah_npl":
                "Jumlah NPL",

            "npl_persen":
                "NPL (%)",

            "baki_debet":
                "Baki Debet"

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

st.divider()

st.header(
    "2️⃣ Rata-rata DPD dan Produk dengan Keterlambatan Tertinggi"
)


avg_dpd = filtered_df[
    "hari_tunggakan_terlama"
].mean()


st.markdown(
    f"""
    Rata-rata hari keterlambatan pembayaran (**DPD**) 
    pada portofolio adalah **{avg_dpd:.1f} hari**.
    """
)


# ============================================================
# DPD PER PRODUK
# ============================================================

product_dpd = (

    filtered_df

    .groupby(
        "nama_produk"
    )

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

    .sort_values(
        "rata_rata_dpd",
        ascending=False
    )

)


worst_product_dpd = (
    product_dpd.iloc[0]
)


col1, col2 = st.columns(2)


with col1:

    st.metric(
        "Produk dengan DPD Tertinggi",
        worst_product_dpd[
            "nama_produk"
        ]
    )


with col2:

    st.metric(
        "Rata-rata DPD",
        f"{worst_product_dpd['rata_rata_dpd']:.1f} hari"
    )


# ============================================================
# GRAFIK DPD
# ============================================================

fig_dpd = px.bar(

    product_dpd,

    x="nama_produk",

    y="rata_rata_dpd",

    text="rata_rata_dpd",

    labels={

        "nama_produk":
            "Produk Kredit",

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
    xaxis_tickangle=-45,
    xaxis_title="",
    yaxis_title="Hari"
)


st.plotly_chart(
    fig_dpd,
    use_container_width=True
)


# ============================================================
# PERTANYAAN 3
# AGUNAN
# ============================================================

st.divider()

st.header(
    "3️⃣ Perbandingan NPL dengan Agunan dan Tanpa Agunan"
)


collateral_npl = (

    filtered_df

    .groupby(
        "status_agunan_dashboard"
    )

    .agg(

        jumlah_pinjaman=(
            "pinjaman_id",
            "count"
        ),

        jumlah_npl=(
            "is_npl_dashboard",
            "sum"
        )

    )

    .reset_index()

)


collateral_npl["npl_rate"] = (

    collateral_npl[
        "jumlah_npl"
    ]
    /
    collateral_npl[
        "jumlah_pinjaman"
    ]

)


collateral_npl["npl_persen"] = (
    collateral_npl[
        "npl_rate"
    ]
    * 100
)


# ============================================================
# NILAI NPL AGUNAN
# ============================================================

npl_dengan_agunan = collateral_npl.loc[
    collateral_npl[
        "status_agunan_dashboard"
    ] == "Dengan Agunan",
    "npl_rate"
]

npl_tanpa_agunan = collateral_npl.loc[
    collateral_npl[
        "status_agunan_dashboard"
    ] == "Tanpa Agunan",
    "npl_rate"
]


if len(npl_dengan_agunan) > 0:

    npl_dengan_agunan = (
        npl_dengan_agunan.iloc[0]
    )

else:

    npl_dengan_agunan = 0


if len(npl_tanpa_agunan) > 0:

    npl_tanpa_agunan = (
        npl_tanpa_agunan.iloc[0]
    )

else:

    npl_tanpa_agunan = 0


selisih_npl = abs(
    npl_dengan_agunan
    -
    npl_tanpa_agunan
)


# ============================================================
# KPI AGUNAN
# ============================================================

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "NPL Dengan Agunan",
        format_percent(
            npl_dengan_agunan
        )
    )


with col2:

    st.metric(
        "NPL Tanpa Agunan",
        format_percent(
            npl_tanpa_agunan
        )
    )


with col3:

    st.metric(
        "Selisih NPL",
        f"{selisih_npl * 100:.2f} pp"
    )


# ============================================================
# GRAFIK AGUNAN
# ============================================================

fig_agunan = px.bar(

    collateral_npl,

    x="status_agunan_dashboard",

    y="npl_persen",

    text="npl_persen",

    labels={

        "status_agunan_dashboard":
            "Status Agunan",

        "npl_persen":
            "NPL (%)"

    },

    title="NPL Berdasarkan Status Agunan"

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
# PERTANYAAN 4
# TUNGGAKAN
# ============================================================

st.divider()

st.header(
    "4️⃣ Petugas Kredit atau Segmen Usaha dengan Tunggakan Terbesar"
)


st.caption(
    "Nilai tunggakan ditampilkan menggunakan **baki debet** "
    "sebagai indikator outstanding kredit."
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

        .groupby(
            "nama_petugas"
        )

        .agg(

            total_tunggakan=(
                "baki_debet",
                "sum"
            ),

            jumlah_pinjaman=(
                "pinjaman_id",
                "count"
            ),

            jumlah_npl=(
                "is_npl_dashboard",
                "sum"
            )

        )

        .reset_index()

        .sort_values(
            "total_tunggakan",
            ascending=False
        )

    )


    top_officer = (
        officer.iloc[0]
    )


    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "Petugas dengan Tunggakan Terbesar",
            top_officer[
                "nama_petugas"
            ]
        )


    with col2:

        st.metric(
            "Total Baki Debet",
            format_rupiah(
                top_officer[
                    "total_tunggakan"
                ]
            )
        )


    # Grafik

    fig_officer = px.bar(

        officer.head(15),

        x="nama_petugas",

        y="total_tunggakan",

        text="total_tunggakan",

        labels={

            "nama_petugas":
                "Petugas Kredit",

            "total_tunggakan":
                "Baki Debet"

        },

        title="15 Petugas dengan Baki Debet Terbesar"

    )


    fig_officer.update_traces(
        texttemplate="Rp %{text:,.0f}",
        textposition="outside"
    )


    fig_officer.update_layout(
        xaxis_tickangle=-45,
        xaxis_title="",
        yaxis_title="Baki Debet"
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
                    "Baki Debet",

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

        .groupby(
            "jenis_usaha",
            dropna=False
        )

        .agg(

            total_tunggakan=(
                "baki_debet",
                "sum"
            ),

            jumlah_pinjaman=(
                "pinjaman_id",
                "count"
            ),

            jumlah_npl=(
                "is_npl_dashboard",
                "sum"
            )

        )

        .reset_index()

        .sort_values(
            "total_tunggakan",
            ascending=False
        )

    )


    top_business = (
        business.iloc[0]
    )


    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "Jenis Usaha dengan Tunggakan Terbesar",
            str(
                top_business[
                    "jenis_usaha"
                ]
            )
        )


    with col2:

        st.metric(
            "Total Baki Debet",
            format_rupiah(
                top_business[
                    "total_tunggakan"
                ]
            )
        )


    # Grafik

    fig_business = px.bar(

        business,

        x="jenis_usaha",

        y="total_tunggakan",

        text="total_tunggakan",

        labels={

            "jenis_usaha":
                "Jenis Usaha",

            "total_tunggakan":
                "Baki Debet"

        },

        title="Baki Debet Berdasarkan Jenis Usaha"

    )


    fig_business.update_traces(
        texttemplate="Rp %{text:,.0f}",
        textposition="outside"
    )


    fig_business.update_layout(
        xaxis_tickangle=-45,
        xaxis_title="",
        yaxis_title="Baki Debet"
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
                    "Baki Debet",

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

st.divider()

st.header(
    "5️⃣ Collection Rate Kredit Mikro"
)


# ============================================================
# COLLECTION RATE KESELURUHAN
# ============================================================

total_realisasi = (
    filtered_df[
        "total_realisasi"
    ].sum()
)


total_kewajiban = (
    filtered_df[
        "total_kewajiban"
    ].sum()
)


if total_kewajiban != 0:

    collection_rate = (
        total_realisasi
        /
        total_kewajiban
    )

else:

    collection_rate = 0


st.markdown(
    f"""
    Tingkat **collection rate** pada portofolio yang sedang
    dianalisis adalah **{format_percent(collection_rate)}**.
    """
)


# ============================================================
# COLLECTION RATE CABANG
# ============================================================

branch_collection = (

    filtered_df

    .groupby(
        "nama_cabang"
    )

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
    ]

)


branch_collection = (
    branch_collection
    .sort_values(
        "collection_rate",
        ascending=True
    )
)


# ============================================================
# CABANG COLLECTION RATE TERENDAH
# ============================================================

worst_collection = (
    branch_collection.iloc[0]
)


col1, col2 = st.columns(2)


with col1:

    st.metric(
        "Cabang Collection Rate Terendah",
        worst_collection[
            "nama_cabang"
        ]
    )


with col2:

    st.metric(
        "Collection Rate",
        format_percent(
            worst_collection[
                "collection_rate"
            ]
        )
    )


# ============================================================
# GRAFIK COLLECTION RATE
# ============================================================

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
    yaxis_tickformat=".0%",
    xaxis_title="",
    yaxis_title="Collection Rate"
)


st.plotly_chart(
    fig_collection,
    use_container_width=True
)


# ============================================================
# DISTRIBUSI KOLEKTIBILITAS
# ============================================================

st.divider()

st.header(
    "📊 Distribusi Kolektibilitas"
)


kolektibilitas = (

    filtered_df

    .groupby(
        [
            "kode_kolektibilitas",
            "kolektibilitas"
        ],
        dropna=False
    )

    .size()

    .reset_index(
        name="jumlah"
    )

)


fig_kolektibilitas = px.pie(

    kolektibilitas,

    names="kolektibilitas",

    values="jumlah",

    hole=0.45,

    title="Komposisi Kolektibilitas Kredit"

)


st.plotly_chart(
    fig_kolektibilitas,
    use_container_width=True
)


# ============================================================
# TABEL DETAIL
# ============================================================

st.divider()

st.header(
    "📋 Detail Data Kredit"
)


detail_columns = [

    "pinjaman_id",
    "nasabah_id",
    "nama_produk",
    "segmen",
    "nama_cabang",
    "nama_petugas",
    "tahun",
    "tanggal_akad",
    "plafon",
    "baki_debet",
    "hari_tunggakan_terlama",
    "kolektibilitas",
    "kode_kolektibilitas",
    "total_nilai_agunan",
    "jenis_usaha",
    "total_kewajiban",
    "total_realisasi"

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
    "⬇️ Download Data Hasil Filter"
)


download_data = filtered_df[
    detail_columns
].to_csv(
    index=False
).encode(
    "utf-8"
)


st.download_button(

    label="📥 Download CSV",

    data=download_data,

    file_name="hasil_filter_kredit_mikro.csv",

    mime="text/csv"

)


# ============================================================
# CATATAN METODOLOGI
# ============================================================

st.divider()

st.subheader(
    "📝 Catatan Metodologi"
)

st.markdown(
    """
    **NPL** dihitung sebagai proporsi pinjaman dengan
    kolektibilitas 3 (Kurang Lancar), 4 (Diragukan), dan 5 (Macet).

    **DPD** menggunakan variabel `hari_tunggakan_terlama`.

    **Status agunan** dibedakan berdasarkan keberadaan nilai
    pada `total_nilai_agunan`.

    **Collection Rate** dihitung sebagai:

    `Total Realisasi / Total Kewajiban`

    **Tunggakan** pada dashboard direpresentasikan menggunakan
    `baki_debet` sebagai indikator outstanding kredit.

    Dataset tidak dilakukan proses pembersihan atau penghapusan data.
    Seluruh **3.400 pinjaman** tetap dipertahankan dalam dataset.
    Sebanyak data yang tidak memiliki tahun akad tetap dipertahankan
    dalam kategori **Tahun Tidak Tersedia**.
    """
)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Dashboard Risiko & Collection Kredit Mikro | Analisis Portofolio Kredit"
)
