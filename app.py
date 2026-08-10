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
# JUDUL
# ============================================================

st.title("💳 Dashboard Portofolio Kredit")

st.caption(
    "Dashboard analitik portofolio kredit berdasarkan NPL, DPD, "
    "agunan, tunggakan, dan collection rate."
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

DATA_PATH = "data_powerbi"


fact = pd.read_csv(
    f"{DATA_PATH}/fact_pinjaman_final.csv"
)


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
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Filter")


st.sidebar.caption(
    "Filter hanya digunakan untuk analisis. "
    "Data asli tidak dihapus."
)


# ============================================================
# FILTER TAHUN
# ============================================================

if "tahun_dashboard" in fact.columns:

    tahun_list = sorted(
        fact["tahun_dashboard"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    tahun_list = [
        str(x)
        for x in tahun_list
    ]

    tahun_dipilih = st.sidebar.multiselect(
        "Tahun",
        options=tahun_list,
        default=[]
    )

else:

    tahun_dipilih = []


# ============================================================
# FILTER PROVINSI
# ============================================================

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
        options=provinsi_list,
        default=[]
    )

else:

    provinsi_dipilih = []


# ============================================================
# FILTER WILAYAH
# ============================================================

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
        options=wilayah_list,
        default=[]
    )

else:

    wilayah_dipilih = []


# ============================================================
# FILTER CABANG
# ============================================================

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
        options=cabang_list,
        default=[]
    )

else:

    cabang_dipilih = []


# ============================================================
# FILTER PRODUK
# ============================================================

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
        options=produk_list,
        default=[]
    )

else:

    produk_dipilih = []


# ============================================================
# FILTER SEGMEN
# ============================================================

if "segmen" in fact.columns:

    segmen_list = sorted(
        fact["segmen"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    segmen_dipilih = st.sidebar.multiselect(
        "Segmen",
        options=segmen_list,
        default=[]
    )

else:

    segmen_dipilih = []


# ============================================================
# FILTER JENIS USAHA
# ============================================================

if "jenis_usaha" in fact.columns:

    usaha_list = sorted(
        fact["jenis_usaha"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    usaha_dipilih = st.sidebar.multiselect(
        "Jenis Usaha",
        options=usaha_list,
        default=[]
    )

else:

    usaha_dipilih = []


# ============================================================
# FILTER DATA
# ============================================================
#
# PENTING:
# Jika filter kosong = SEMUA DATA
#
# Sehingga ketika dashboard pertama dibuka,
# jumlah pinjaman tetap 3.400.
# ============================================================

df = fact.copy()


# Tahun
if tahun_dipilih:

    df = df[
        df["tahun_dashboard"]
        .astype("Int64")
        .astype(str)
        .isin(tahun_dipilih)
    ]


# Provinsi
if provinsi_dipilih:

    df = df[
        df["provinsi"]
        .astype(str)
        .isin(provinsi_dipilih)
    ]


# Wilayah
if wilayah_dipilih:

    df = df[
        df["wilayah"]
        .astype(str)
        .isin(wilayah_dipilih)
    ]


# Cabang
if cabang_dipilih:

    df = df[
        df["nama_cabang"]
        .astype(str)
        .isin(cabang_dipilih)
    ]


# Produk
if produk_dipilih:

    df = df[
        df["nama_produk"]
        .astype(str)
        .isin(produk_dipilih)
    ]


# Segmen
if segmen_dipilih:

    df = df[
        df["segmen"]
        .astype(str)
        .isin(segmen_dipilih)
    ]


# Jenis usaha
if usaha_dipilih:

    df = df[
        df["jenis_usaha"]
        .astype(str)
        .isin(usaha_dipilih)
    ]


# ============================================================
# DEFINISI NPL
# ============================================================

if kolek:

    df["is_npl_dashboard"] = (
        df[kolek]
        .isin([3, 4, 5])
    )

else:

    df["is_npl_dashboard"] = False


# ============================================================
# RINGKASAN PORTOFOLIO
# ============================================================

st.divider()

st.header(
    "📌 Ringkasan Portofolio"
)


# Jumlah pinjaman
if pid:

    jumlah_pinjaman = (
        df[pid]
        .nunique()
    )

else:

    jumlah_pinjaman = len(df)


# Total plafon
if plafon:

    total_plafon = (
        df[plafon]
        .sum()
    )

else:

    total_plafon = np.nan


# Total kewajiban
if kewajiban:

    total_kewajiban = (
        df[kewajiban]
        .sum()
    )

else:

    total_kewajiban = np.nan


# Total realisasi
if realisasi:

    total_realisasi = (
        df[realisasi]
        .sum()
    )

else:

    total_realisasi = np.nan


# Collection rate
if (
    kewajiban
    and realisasi
    and total_kewajiban != 0
):

    collection_rate = (
        total_realisasi
        /
        total_kewajiban
    )

else:

    collection_rate = np.nan


# ============================================================
# KPI
# ============================================================

k1, k2, k3, k4, k5 = st.columns(5)


with k1:

    st.metric(
        "Jumlah Pinjaman",
        f"{jumlah_pinjaman:,}".replace(
            ",",
            "."
        )
    )


with k2:

    st.metric(
        "Total Plafon",
        rupiah(total_plafon)
    )


with k3:

    st.metric(
        "Total Kewajiban",
        rupiah(total_kewajiban)
    )


with k4:

    st.metric(
        "Total Realisasi",
        rupiah(total_realisasi)
    )


with k5:

    if pd.notna(collection_rate):

        st.metric(
            "Collection Rate",
            f"{collection_rate * 100:.2f}%"
        )

    else:

        st.metric(
            "Collection Rate",
            "N/A"
        )


# ============================================================
# INFO JUMLAH DATA
# ============================================================

if not (
    tahun_dipilih
    or provinsi_dipilih
    or wilayah_dipilih
    or cabang_dipilih
    or produk_dipilih
    or segmen_dipilih
    or usaha_dipilih
):

    st.success(
        f"Menampilkan seluruh **{total_data_asli:,} pinjaman** "
        "tanpa filter."
    )

else:

    st.info(
        f"Data setelah filter: "
        f"**{jumlah_pinjaman:,} pinjaman**."
    )


# ============================================================
# PERTANYAAN ANALITIK 1
# NPL
# ============================================================

st.divider()

st.header(
    "1️⃣ NPL Portofolio dan Cabang dengan NPL Tertinggi"
)


# NPL keseluruhan

npl_rate = (
    df["is_npl_dashboard"]
    .mean()
)


st.markdown(
    f"""
    Persentase **kredit bermasalah (NPL)** pada portofolio
    adalah **{npl_rate * 100:.2f}%**.
    
    NPL dihitung berdasarkan pinjaman dengan kolektibilitas
    **3 (Kurang Lancar), 4 (Diragukan), dan 5 (Macet)**.
    """
)


# ============================================================
# NPL CABANG
# ============================================================

if "nama_cabang" in df.columns:

    branch_npl = (

        df.groupby(
            "nama_cabang"
        )

        .agg(

            jumlah_pinjaman=(
                pid,
                "nunique"
            ) if pid else (
                "nama_cabang",
                "size"
            ),

            jumlah_npl=(
                "is_npl_dashboard",
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


    if len(branch_npl) > 0:

        worst_branch = (
            branch_npl.iloc[0]
        )


        a, b = st.columns(2)


        with a:

            st.metric(
                "Cabang NPL Tertinggi",
                worst_branch[
                    "nama_cabang"
                ]
            )


        with b:

            st.metric(
                "NPL Tertinggi",
                f"{worst_branch['npl_rate'] * 100:.2f}%"
            )


        fig_npl = px.bar(
            branch_npl,
            x="nama_cabang",
            y="npl_persen",
            text="npl_persen",
            title="NPL Berdasarkan Cabang",
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
                        "NPL (%)"
                }
            )[
                [
                    "Cabang",
                    "Jumlah Pinjaman",
                    "Jumlah NPL",
                    "NPL (%)"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# PERTANYAAN ANALITIK 2
# DPD
# ============================================================

st.divider()

st.header(
    "2️⃣ Rata-rata DPD dan Produk dengan Keterlambatan Tertinggi"
)


if tunggakan:

    avg_dpd = (
        df[tunggakan]
        .mean()
    )


    st.metric(
        "Rata-rata DPD",
        f"{avg_dpd:.1f} hari"
    )


    if "nama_produk" in df.columns:

        product_dpd = (

            df.groupby(
                "nama_produk"
            )

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


        if len(product_dpd) > 0:

            worst_product = (
                product_dpd.iloc[0]
            )


            a, b = st.columns(2)


            with a:

                st.metric(
                    "Produk DPD Tertinggi",
                    worst_product[
                        "nama_produk"
                    ]
                )


            with b:

                st.metric(
                    "Rata-rata DPD",
                    f"{worst_product['rata_rata_dpd']:.1f} hari"
                )


            fig_dpd = px.bar(
                product_dpd,
                x="nama_produk",
                y="rata_rata_dpd",
                text="rata_rata_dpd",
                title="Rata-rata DPD Berdasarkan Produk",
                labels={
                    "nama_produk":
                        "Produk Kredit",

                    "rata_rata_dpd":
                        "Rata-rata DPD (Hari)"
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

    st.warning(
        "Kolom DPD tidak tersedia."
    )


# ============================================================
# PERTANYAAN ANALITIK 3
# AGUNAN
# ============================================================

st.divider()

st.header(
    "3️⃣ NPL dengan Agunan vs Tanpa Agunan"
)


if agunan:

    df["status_agunan_dashboard"] = np.where(
        df[agunan] > 0,
        "Dengan Agunan",
        "Tanpa Agunan"
    )


    collateral_npl = (

        df.groupby(
            "status_agunan_dashboard"
        )

        .agg(

            jumlah_pinjaman=(
                pid,
                "nunique"
            ) if pid else (
                "status_agunan_dashboard",
                "size"
            ),

            jumlah_npl=(
                "is_npl_dashboard",
                "sum"
            )

        )

        .reset_index()

    )


    collateral_npl["npl_rate"] = (
        collateral_npl["jumlah_npl"]
        /
        collateral_npl["jumlah_pinjaman"]
    )


    collateral_npl["npl_persen"] = (
        collateral_npl["npl_rate"]
        * 100
    )


    dengan_agunan = collateral_npl[
        collateral_npl[
            "status_agunan_dashboard"
        ] == "Dengan Agunan"
    ]["npl_rate"]


    tanpa_agunan = collateral_npl[
        collateral_npl[
            "status_agunan_dashboard"
        ] == "Tanpa Agunan"
    ]["npl_rate"]


    npl_dengan = (
        dengan_agunan.iloc[0]
        if len(dengan_agunan) > 0
        else 0
    )


    npl_tanpa = (
        tanpa_agunan.iloc[0]
        if len(tanpa_agunan) > 0
        else 0
    )


    selisih_npl = abs(
        npl_dengan
        -
        npl_tanpa
    )


    a, b, c = st.columns(3)


    with a:

        st.metric(
            "NPL Dengan Agunan",
            f"{npl_dengan * 100:.2f}%"
        )


    with b:

        st.metric(
            "NPL Tanpa Agunan",
            f"{npl_tanpa * 100:.2f}%"
        )


    with c:

        st.metric(
            "Selisih NPL",
            f"{selisih_npl * 100:.2f} pp"
        )


    fig_agunan = px.bar(
        collateral_npl,
        x="status_agunan_dashboard",
        y="npl_persen",
        text="npl_persen",
        title="NPL Berdasarkan Status Agunan",
        labels={
            "status_agunan_dashboard":
                "Status Agunan",

            "npl_persen":
                "NPL (%)"
        }
    )


    fig_agunan.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside"
    )


    st.plotly_chart(
        fig_agunan,
        use_container_width=True
    )


else:

    st.warning(
        "Kolom agunan tidak tersedia."
    )


# ============================================================
# PERTANYAAN ANALITIK 4
# TUNGGAKAN PETUGAS / USAHA
# ============================================================

st.divider()

st.header(
    "4️⃣ Petugas Kredit atau Segmen Usaha dengan Tunggakan Terbesar"
)


# ------------------------------------------------------------
# PETUGAS
# ------------------------------------------------------------

if (
    "nama_petugas" in df.columns
    and baki
):

    officer = (

        df.groupby(
            "nama_petugas"
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


    if len(officer) > 0:

        top_officer = (
            officer.iloc[0]
        )


        a, b = st.columns(2)


        with a:

            st.metric(
                "Petugas dengan Tunggakan Terbesar",
                top_officer[
                    "nama_petugas"
                ]
            )


        with b:

            st.metric(
                "Total Tunggakan",
                rupiah(
                    top_officer[
                        "total_tunggakan"
                    ]
                )
            )


        fig_officer = px.bar(
            officer.head(15),
            x="nama_petugas",
            y="total_tunggakan",
            text="total_tunggakan",
            title="15 Petugas dengan Tunggakan Terbesar",
            labels={
                "nama_petugas":
                    "Petugas Kredit",

                "total_tunggakan":
                    "Baki Debet"
            }
        )


        fig_officer.update_traces(
            texttemplate="Rp %{text:,.0f}",
            textposition="outside"
        )


        fig_officer.update_layout(
            xaxis_tickangle=-45,
            xaxis_title=""
        )


        st.plotly_chart(
            fig_officer,
            use_container_width=True
        )


# ------------------------------------------------------------
# JENIS USAHA
# ------------------------------------------------------------

if (
    "jenis_usaha" in df.columns
    and baki
):

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


    if len(business) > 0:

        top_business = (
            business.iloc[0]
        )


        a, b = st.columns(2)


        with a:

            st.metric(
                "Jenis Usaha Tunggakan Terbesar",
                str(
                    top_business[
                        "jenis_usaha"
                    ]
                )
            )


        with b:

            st.metric(
                "Total Tunggakan",
                rupiah(
                    top_business[
                        "total_tunggakan"
                    ]
                )
            )


        fig_business = px.bar(
            business,
            x="jenis_usaha",
            y="total_tunggakan",
            text="total_tunggakan",
            title="Tunggakan Berdasarkan Jenis Usaha",
            labels={
                "jenis_usaha":
                    "Jenis Usaha",

                "total_tunggakan":
                    "Baki Debet"
            }
        )


        fig_business.update_traces(
            texttemplate="Rp %{text:,.0f}",
            textposition="outside"
        )


        fig_business.update_layout(
            xaxis_tickangle=-45,
            xaxis_title=""
        )


        st.plotly_chart(
            fig_business,
            use_container_width=True
        )


# ============================================================
# PERTANYAAN ANALITIK 5
# COLLECTION RATE
# ============================================================

st.divider()

st.header(
    "5️⃣ Collection Rate Kredit Mikro"
)


# Collection keseluruhan

if (
    kewajiban
    and realisasi
):

    total_kewajiban_collection = (
        df[kewajiban]
        .sum()
    )


    total_realisasi_collection = (
        df[realisasi]
        .sum()
    )


    if total_kewajiban_collection != 0:

        collection_rate = (
            total_realisasi_collection
            /
            total_kewajiban_collection
        )

    else:

        collection_rate = 0


    st.metric(
        "Collection Rate Keseluruhan",
        f"{collection_rate * 100:.2f}%"
    )


    # --------------------------------------------------------
    # COLLECTION RATE CABANG
    # --------------------------------------------------------

    if "nama_cabang" in df.columns:

        branch_collection = (

            df.groupby(
                "nama_cabang"
            )

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


        if len(branch_collection) > 0:

            worst_collection = (
                branch_collection.iloc[0]
            )


            a, b = st.columns(2)


            with a:

                st.metric(
                    "Collection Rate Terendah",
                    f"{worst_collection['collection_rate'] * 100:.2f}%"
                )


            with b:

                st.metric(
                    "Cabang",
                    worst_collection[
                        "nama_cabang"
                    ]
                )


            fig_collection = px.bar(
                branch_collection,
                x="nama_cabang",
                y="collection_rate",
                text="collection_rate",
                title="Collection Rate Berdasarkan Cabang",
                labels={
                    "nama_cabang":
                        "Cabang",

                    "collection_rate":
                        "Collection Rate"
                }
            )


            fig_collection.update_traces(
                texttemplate="%{text:.2%}",
                textposition="outside"
            )


            fig_collection.update_layout(
                yaxis_tickformat=".0%",
                xaxis_title=""
            )


            st.plotly_chart(
                fig_collection,
                use_container_width=True
            )


else:

    st.warning(
        "Kolom total kewajiban atau total realisasi tidak tersedia."
    )


# ============================================================
# TREN WAKTU
# ============================================================

st.divider()

st.header(
    "📈 Tren Lintas Waktu"
)


if date:

    trend = df[
        df[date].notna()
    ].copy()


    if len(trend) > 0:

        trend["periode"] = (
            trend[date]
            .dt.to_period("M")
            .astype(str)
        )


        if pid:

            trend_agg = (
                trend
                .groupby("periode")
                .agg(
                    jumlah_pinjaman=(
                        pid,
                        "nunique"
                    )
                )
                .reset_index()
            )

        else:

            trend_agg = (
                trend
                .groupby("periode")
                .size()
                .reset_index(
                    name="jumlah_pinjaman"
                )
            )


        fig_trend = px.line(
            trend_agg,
            x="periode",
            y="jumlah_pinjaman",
            markers=True,
            title="Jumlah Pinjaman per Bulan",
            labels={
                "periode": "Periode",
                "jumlah_pinjaman":
                    "Jumlah Pinjaman"
            }
        )


        st.plotly_chart(
            fig_trend,
            use_container_width=True
        )


# ============================================================
# DISTRIBUSI KOLEKTIBILITAS
# ============================================================

st.divider()

st.header(
    "📊 Distribusi Kolektibilitas"
)


if kolek_nama:

    kolek_dist = (
        df[
            kolek_nama
        ]
        .fillna("Tidak diketahui")
        .astype(str)
        .value_counts()
        .reset_index()
    )


    kolek_dist.columns = [
        "kolektibilitas",
        "jumlah"
    ]


    fig_kolek = px.pie(
        kolek_dist,
        names="kolektibilitas",
        values="jumlah",
        hole=0.45,
        title="Komposisi Kolektibilitas Kredit"
    )


    st.plotly_chart(
        fig_kolek,
        use_container_width=True
    )


# ============================================================
# PROFIL NASABAH
# ============================================================

st.divider()

st.header(
    "👥 Profil Nasabah"
)


p1, p2 = st.columns(2)


# ------------------------------------------------------------
# JENIS USAHA
# ------------------------------------------------------------

with p1:

    if "jenis_usaha" in df.columns:

        usaha_dist = (

            df["jenis_usaha"]
            .fillna("Tidak diketahui")
            .astype(str)
            .value_counts()
            .head(10)
            .reset_index()

        )


        usaha_dist.columns = [
            "jenis_usaha",
            "jumlah"
        ]


        fig_usaha = px.bar(
            usaha_dist,
            x="jumlah",
            y="jenis_usaha",
            orientation="h",
            title="10 Jenis Usaha Terbanyak"
        )


        st.plotly_chart(
            fig_usaha,
            use_container_width=True
        )


# ------------------------------------------------------------
# JENIS KELAMIN
# ------------------------------------------------------------

with p2:

    if "jenis_kelamin" in df.columns:

        gender_dist = (

            df["jenis_kelamin"]
            .fillna("Tidak diketahui")
            .astype(str)
            .value_counts()
            .reset_index()

        )


        gender_dist.columns = [
            "jenis_kelamin",
            "jumlah"
        ]


        fig_gender = px.pie(
            gender_dist,
            names="jenis_kelamin",
            values="jumlah",
            hole=0.45,
            title="Distribusi Jenis Kelamin"
        )


        st.plotly_chart(
            fig_gender,
            use_container_width=True
        )


# ============================================================
# DATA DETAIL
# ============================================================

st.divider()

st.header(
    "📋 Data Detail"
)


with st.expander(
    "🔎 Lihat Data Hasil Filter"
):

    st.dataframe(
        df,
        use_container_width=True,
        height=450
    )


    csv_download = (
        df.to_csv(
            index=False
        )
        .encode("utf-8")
    )


    st.download_button(
        label="⬇️ Download CSV Hasil Filter",
        data=csv_download,
        file_name="fact_pinjaman_filtered.csv",
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

    **NPL berdasarkan agunan** membandingkan pinjaman dengan
    nilai agunan dan pinjaman tanpa nilai agunan.

    **Total tunggakan** menggunakan `baki_debet` sebagai
    indikator outstanding kredit.

    **Collection Rate** dihitung dengan membandingkan
    total realisasi pembayaran terhadap total kewajiban.

    Dataset digunakan sesuai data yang tersedia dan tidak dilakukan
    proses penghapusan atau pembersihan baris data.
    """
)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    f"Total data awal: {total_data_asli:,} pinjaman | "
    f"Data yang sedang dianalisis: {jumlah_pinjaman:,} pinjaman"
)
