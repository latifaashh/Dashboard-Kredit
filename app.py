
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Dashboard Risiko Kredit Mikro",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# KONFIGURASI
# ============================================================
DATA_FILE = "fact_pinjaman_final.csv"

st.title("📊 Dashboard Risiko & Collection Kredit Mikro")
st.caption(
    "Dashboard analitik portofolio kredit mikro berdasarkan NPL, DPD, agunan, "
    "tunggakan, dan collection rate."
)

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        path = Path(DATA_FILE)
        if not path.exists():
            return None
        df = pd.read_csv(path)

    # Pastikan tipe data
    for col in ["plafon", "total_kewajiban", "total_realisasi",
                "baki_debet", "hari_tunggakan_terlama",
                "total_nilai_agunan"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "is_batal" in df.columns:
        # normalisasi boolean
        df["is_batal"] = df["is_batal"].astype(str).str.lower().isin(
            ["true", "1", "yes", "ya"]
        )

    # Hanya portofolio mikro dan pinjaman tidak batal
    if "segmen" in df.columns:
        df = df[df["segmen"].astype(str).str.lower() == "mikro"].copy()

    if "is_batal" in df.columns:
        df = df[df["is_batal"] == False].copy()

    # Flag NPL: kolektibilitas 3, 4, 5
    if "kode_kolektibilitas" in df.columns:
        df["kode_kolektibilitas"] = pd.to_numeric(
            df["kode_kolektibilitas"], errors="coerce"
        )
        df["is_npl"] = df["kode_kolektibilitas"].isin([3, 4, 5])
    else:
        df["is_npl"] = False

    # Flag agunan
    if "total_nilai_agunan" in df.columns:
        df["ada_agunan"] = df["total_nilai_agunan"].fillna(0) > 0
    else:
        df["ada_agunan"] = False

    # Proxy tunggakan:
    # Karena file fact yang tersedia tidak memuat tabel pembayaran/jadwal
    # secara detail, baki_debet digunakan sebagai proxy saldo/tunggakan.
    if "baki_debet" in df.columns:
        df["nilai_tunggakan"] = df["baki_debet"].fillna(0).clip(lower=0)
    else:
        df["nilai_tunggakan"] = 0

    # Collection rate per pinjaman
    if {"total_realisasi", "total_kewajiban"}.issubset(df.columns):
        df["collection_rate_individu"] = (
            df["total_realisasi"] /
            df["total_kewajiban"].replace(0, pd.NA)
        ).fillna(0)
        df["collection_rate_individu"] = (
            df["collection_rate_individu"].clip(lower=0, upper=1)
        )
    else:
        df["collection_rate_individu"] = 0

    return df


st.sidebar.header("⚙️ Pengaturan Data")

uploaded = st.sidebar.file_uploader(
    "Upload fact_pinjaman_final.csv",
    type=["csv"],
    help="Jika file tidak diletakkan satu folder dengan app.py, upload file di sini."
)

df = load_data(uploaded)

if df is None:
    st.error(
        "File fact_pinjaman_final.csv belum ditemukan. "
        "Letakkan file tersebut satu folder dengan app.py atau upload melalui sidebar."
    )
    st.stop()

# ============================================================
# FILTER
# ============================================================
st.sidebar.subheader("🔎 Filter")

df["tanggal_akad"] = pd.to_datetime(df["tanggal_akad"], errors="coerce")

years = sorted(df["tanggal_akad"].dt.year.dropna().astype(int).unique())
selected_year = st.sidebar.multiselect(
    "Tahun akad",
    years,
    default=years
)

branches = sorted(df["nama_cabang"].dropna().unique())
selected_branch = st.sidebar.multiselect(
    "Cabang",
    branches,
    default=branches
)

products = sorted(df["nama_produk"].dropna().unique())
selected_product = st.sidebar.multiselect(
    "Produk kredit",
    products,
    default=products
)

collateral_filter = st.sidebar.multiselect(
    "Agunan",
    ["Dengan Agunan", "Tanpa Agunan"],
    default=["Dengan Agunan", "Tanpa Agunan"]
)

f = df[
    df["tanggal_akad"].dt.year.isin(selected_year) &
    df["nama_cabang"].isin(selected_branch) &
    df["nama_produk"].isin(selected_product)
].copy()

coll_map = {
    "Dengan Agunan": True,
    "Tanpa Agunan": False
}
selected_collateral_values = [coll_map[x] for x in collateral_filter]
f = f[f["ada_agunan"].isin(selected_collateral_values)].copy()

if f.empty:
    st.warning("Tidak ada data yang sesuai dengan filter.")
    st.stop()

# ============================================================
# HELPER
# ============================================================
def pct(x):
    return f"{x * 100:.2f}%"

def rupiah(x):
    return f"Rp{x:,.0f}".replace(",", ".")

# ============================================================
# KPI
# ============================================================
total_pinjaman = len(f)
total_plafon = f["plafon"].sum()
total_baki = f["baki_debet"].sum()

npl_rate = f["is_npl"].mean()
avg_dpd = f["hari_tunggakan_terlama"].mean()

collection_rate = (
    f["total_realisasi"].sum() /
    f["total_kewajiban"].sum()
    if f["total_kewajiban"].sum() != 0 else 0
)

npl_exposure = (
    f.loc[f["is_npl"], "baki_debet"].sum() /
    f["baki_debet"].sum()
    if f["baki_debet"].sum() != 0 else 0
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Pinjaman", f"{total_pinjaman:,}")
k2.metric("Total Plafon", rupiah(total_plafon))
k3.metric("NPL", pct(npl_rate))
k4.metric("Rata-rata DPD", f"{avg_dpd:,.1f} hari")
k5.metric("Collection Rate", pct(collection_rate))

st.divider()

# ============================================================
# RINGKASAN EKSEKUTIF
# ============================================================
st.subheader("📌 Ringkasan Analitik")

# Cabang NPL tertinggi
branch_npl = (
    f.groupby("nama_cabang")
    .agg(
        total_pinjaman=("pinjaman_id", "count"),
        npl=("is_npl", "mean"),
        baki_debet=("baki_debet", "sum")
    )
    .reset_index()
)
branch_npl["npl_pct"] = branch_npl["npl"] * 100
worst_branch_npl = branch_npl.sort_values("npl", ascending=False).iloc[0]

# Produk DPD tertinggi
product_dpd = (
    f.groupby("nama_produk")
    .agg(
        rata_rata_dpd=("hari_tunggakan_terlama", "mean"),
        jumlah_pinjaman=("pinjaman_id", "count")
    )
    .reset_index()
)
worst_product_dpd = product_dpd.sort_values(
    "rata_rata_dpd", ascending=False
).iloc[0]

# Agunan
collateral_npl = (
    f.groupby("ada_agunan")
    .agg(npl=("is_npl", "mean"), jumlah=("pinjaman_id", "count"))
    .reset_index()
)
with_coll = collateral_npl.loc[
    collateral_npl["ada_agunan"] == True, "npl"
]
without_coll = collateral_npl.loc[
    collateral_npl["ada_agunan"] == False, "npl"
]
with_coll = float(with_coll.iloc[0]) if len(with_coll) else 0
without_coll = float(without_coll.iloc[0]) if len(without_coll) else 0
npl_gap = with_coll - without_coll

# Collection terendah
branch_collection = (
    f.groupby("nama_cabang")
    .agg(
        total_realisasi=("total_realisasi", "sum"),
        total_kewajiban=("total_kewajiban", "sum"),
        jumlah_pinjaman=("pinjaman_id", "count")
    )
    .reset_index()
)
branch_collection["collection_rate"] = (
    branch_collection["total_realisasi"] /
    branch_collection["total_kewajiban"].replace(0, pd.NA)
).fillna(0)
worst_collection = branch_collection.sort_values(
    "collection_rate", ascending=True
).iloc[0]

c1, c2 = st.columns(2)

with c1:
    st.info(
        f"**NPL portofolio:** {pct(npl_rate)}. "
        f"Cabang dengan NPL tertinggi adalah **{worst_branch_npl['nama_cabang']}** "
        f"sebesar **{worst_branch_npl['npl_pct']:.2f}%**."
    )

    st.info(
        f"**Rata-rata DPD:** {avg_dpd:.1f} hari. "
        f"Produk dengan keterlambatan tertinggi adalah "
        f"**{worst_product_dpd['nama_produk']}** "
        f"dengan rata-rata **{worst_product_dpd['rata_rata_dpd']:.1f} hari**."
    )

with c2:
    st.info(
        f"**Selisih NPL berdasarkan agunan:** "
        f"{abs(npl_gap) * 100:.2f} percentage point. "
        f"Dengan agunan: **{pct(with_coll)}**, tanpa agunan: **{pct(without_coll)}**."
    )

    st.info(
        f"**Collection rate:** {pct(collection_rate)}. "
        f"Cabang dengan collection rate terendah adalah "
        f"**{worst_collection['nama_cabang']}** sebesar "
        f"**{worst_collection['collection_rate'] * 100:.2f}%**."
    )

st.divider()

# ============================================================
# 1. NPL PER CABANG
# ============================================================
st.subheader("1️⃣ NPL Portofolio dan Cabang dengan NPL Tertinggi")

fig = px.bar(
    branch_npl.sort_values("npl_pct", ascending=False),
    x="nama_cabang",
    y="npl_pct",
    text="npl_pct",
    labels={
        "nama_cabang": "Cabang",
        "npl_pct": "NPL (%)"
    },
    title="NPL per Cabang"
)
fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
fig.update_layout(yaxis_title="NPL (%)", xaxis_title="")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    branch_npl.sort_values("npl", ascending=False).rename(columns={
        "nama_cabang": "Cabang",
        "total_pinjaman": "Jumlah Pinjaman",
        "npl_pct": "NPL (%)",
        "baki_debet": "Baki Debet"
    })[
        ["Cabang", "Jumlah Pinjaman", "NPL (%)", "Baki Debet"]
    ],
    use_container_width=True,
    hide_index=True
)

# ============================================================
# 2. DPD PER PRODUK
# ============================================================
st.subheader("2️⃣ Rata-rata DPD dan Produk dengan Keterlambatan Tertinggi")

fig = px.bar(
    product_dpd.sort_values("rata_rata_dpd", ascending=False),
    x="nama_produk",
    y="rata_rata_dpd",
    text="rata_rata_dpd",
    labels={
        "nama_produk": "Produk",
        "rata_rata_dpd": "Rata-rata DPD (hari)"
    },
    title="Rata-rata DPD per Produk"
)
fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
fig.update_layout(yaxis_title="Hari", xaxis_title="")
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 3. NPL AGUNAN VS TANPA AGUNAN
# ============================================================
st.subheader("3️⃣ Perbandingan NPL: Dengan Agunan vs Tanpa Agunan")

collateral_display = collateral_npl.copy()
collateral_display["status_agunan"] = collateral_display["ada_agunan"].map({
    True: "Dengan Agunan",
    False: "Tanpa Agunan"
})
collateral_display["npl_pct"] = collateral_display["npl"] * 100

fig = px.bar(
    collateral_display,
    x="status_agunan",
    y="npl_pct",
    text="npl_pct",
    labels={
        "status_agunan": "Status Agunan",
        "npl_pct": "NPL (%)"
    },
    title="NPL Berdasarkan Status Agunan"
)
fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
fig.update_layout(yaxis_title="NPL (%)", xaxis_title="")
st.plotly_chart(fig, use_container_width=True)

st.metric(
    "Selisih NPL",
    f"{abs(npl_gap) * 100:.2f} percentage point",
    delta=(
        "NPL dengan agunan lebih tinggi"
        if npl_gap > 0 else
        "NPL tanpa agunan lebih tinggi"
        if npl_gap < 0 else
        "NPL sama"
    )
)

# ============================================================
# 4. TUNGGAKAN PETUGAS / SEGMEN USAHA
# ============================================================
st.subheader("4️⃣ Total Tunggakan Terbesar")

tab1, tab2 = st.tabs(["👤 Petugas Kredit", "🏪 Segmen/Jenis Usaha"])

with tab1:
    officer = (
        f.groupby("nama_petugas")
        .agg(
            total_tunggakan=("nilai_tunggakan", "sum"),
            jumlah_pinjaman=("pinjaman_id", "count"),
            npl=("is_npl", "mean")
        )
        .reset_index()
        .sort_values("total_tunggakan", ascending=False)
    )

    fig = px.bar(
        officer.head(15),
        x="nama_petugas",
        y="total_tunggakan",
        text="total_tunggakan",
        labels={
            "nama_petugas": "Petugas",
            "total_tunggakan": "Total Tunggakan"
        },
        title="15 Petugas dengan Tunggakan Terbesar"
    )
    fig.update_traces(
        texttemplate="Rp%{text:,.0f}",
        textposition="outside"
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        officer.rename(columns={
            "nama_petugas": "Petugas",
            "total_tunggakan": "Total Tunggakan",
            "jumlah_pinjaman": "Jumlah Pinjaman",
            "npl": "NPL"
        }),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    business = (
        f.groupby("jenis_usaha")
        .agg(
            total_tunggakan=("nilai_tunggakan", "sum"),
            jumlah_pinjaman=("pinjaman_id", "count"),
            npl=("is_npl", "mean")
        )
        .reset_index()
        .sort_values("total_tunggakan", ascending=False)
    )

    fig = px.bar(
        business,
        x="jenis_usaha",
        y="total_tunggakan",
        text="total_tunggakan",
        labels={
            "jenis_usaha": "Jenis Usaha",
            "total_tunggakan": "Total Tunggakan"
        },
        title="Total Tunggakan Berdasarkan Jenis Usaha"
    )
    fig.update_traces(
        texttemplate="Rp%{text:,.0f}",
        textposition="outside"
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        business.rename(columns={
            "jenis_usaha": "Jenis Usaha",
            "total_tunggakan": "Total Tunggakan",
            "jumlah_pinjaman": "Jumlah Pinjaman",
            "npl": "NPL"
        }),
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# 5. COLLECTION RATE
# ============================================================
st.subheader("5️⃣ Collection Rate Kredit Mikro")

fig = px.bar(
    branch_collection.sort_values("collection_rate"),
    x="nama_cabang",
    y="collection_rate",
    text="collection_rate",
    labels={
        "nama_cabang": "Cabang",
        "collection_rate": "Collection Rate"
    },
    title="Collection Rate per Cabang"
)
fig.update_traces(texttemplate="%{text:.2%}", textposition="outside")
fig.update_layout(yaxis_tickformat=".0%")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    branch_collection.sort_values("collection_rate").rename(columns={
        "nama_cabang": "Cabang",
        "total_realisasi": "Total Realisasi",
        "total_kewajiban": "Total Kewajiban",
        "jumlah_pinjaman": "Jumlah Pinjaman",
        "collection_rate": "Collection Rate"
    }),
    use_container_width=True,
    hide_index=True
)

# ============================================================
# KUALITAS PORTOFOLIO
# ============================================================
st.subheader("📈 Distribusi Kolektibilitas")

kol = (
    f["kolektibilitas"]
    .value_counts()
    .reset_index()
)
kol.columns = ["Kolektibilitas", "Jumlah"]

fig = px.pie(
    kol,
    names="Kolektibilitas",
    values="Jumlah",
    hole=0.45,
    title="Komposisi Kolektibilitas Kredit Mikro"
)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# DOWNLOAD DATA FILTER
# ============================================================
st.subheader("⬇️ Download Data")

download_cols = [
    "pinjaman_id", "nasabah_id", "nama_produk", "nama_cabang",
    "nama_petugas", "tanggal_akad", "plafon", "baki_debet",
    "hari_tunggakan_terlama", "kolektibilitas", "kode_kolektibilitas",
    "total_nilai_agunan", "jenis_usaha", "is_npl", "ada_agunan"
]
download_cols = [c for c in download_cols if c in f.columns]

csv = f[download_cols].to_csv(index=False).encode("utf-8")

st.download_button(
    "📥 Download Data Hasil Filter",
    data=csv,
    file_name="hasil_filter_kredit_mikro.csv",
    mime="text/csv"
)

st.caption(
    "Catatan metodologi: NPL dihitung sebagai proporsi pinjaman dengan "
    "kolektibilitas 3 (Kurang Lancar), 4 (Diragukan), dan 5 (Macet). "
    "Collection rate dihitung dari total realisasi dibandingkan total kewajiban. "
    "Pada fact yang tersedia, tidak terdapat rincian pembayaran/jadwal angsuran "
    "per transaksi, sehingga baki debet digunakan sebagai proxy nilai tunggakan."
)
