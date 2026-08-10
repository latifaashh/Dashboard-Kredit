import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Dashboard Portofolio Kredit", page_icon="💳", layout="wide")

st.title("💳 Dashboard Portofolio Kredit")
st.caption("Dashboard interaktif berdasarkan fact_pinjaman dan dimensi hasil pengolahan data.")

# ---------- helper ----------
def rupiah(x):
    if pd.isna(x): return "N/A"
    x = float(x)
    if abs(x) >= 1e12: return f"Rp{x/1e12:.2f} T"
    if abs(x) >= 1e9: return f"Rp{x/1e9:.2f} M"
    if abs(x) >= 1e6: return f"Rp{x/1e6:.2f} Jt"
    return f"Rp{x:,.0f}"

def col(df, names):
    mp = {str(x).lower().strip(): x for x in df.columns}
    for n in names:
        if n.lower() in mp: return mp[n.lower()]
    for n in names:
        for x in df.columns:
            if n.lower() in str(x).lower(): return x
    return None

def add_dim(fact, dim, key, attributes):
    if dim is None or key not in fact.columns or key not in dim.columns:
        return fact
    d = dim.drop_duplicates(key).copy()
    keep = [key] + [x for x in attributes if x in d.columns and x not in fact.columns]
    if len(keep) > 1:
        return fact.merge(d[keep], on=key, how="left", validate="many_to_one")
    return fact
    
# ============================================================
# LOAD DATA OTOMATIS DARI FOLDER DATA
# ============================================================

DATA_PATH = "data"

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

dims = {
    "nasabah": dim_nasabah,
    "produk": dim_produk,
    "cabang": dim_cabang,
    "petugas": dim_petugas
}

# Tambahkan atribut dimensi jika belum ada di fact
fact = add_dim(fact, dims["nasabah"], "nasabah_id",
    ["nik_terenkripsi","tanggal_lahir","jenis_kelamin","jenis_usaha",
     "pendapatan_bulanan","lama_usaha_tahun","kota","provinsi"])
fact = add_dim(fact, dims["produk"], "produk_id",
    ["nama_produk","segmen","plafon_min","plafon_maks","bunga_acuan_tahunan"])
fact = add_dim(fact, dims["cabang"], "cabang_id",
    ["nama_cabang","kota","provinsi","wilayah","tanggal_operasional"])
fact = add_dim(fact, dims["petugas"], "petugas_id",
    ["nama_petugas","status_kepegawaian"])

# ---------- important columns ----------
pid = col(fact, ["pinjaman_id"])
date = col(fact, ["tanggal_akad"])
plafon = col(fact, ["plafon","jumlah_pinjaman","nilai_pinjaman"])
kewajiban = col(fact, ["total_kewajiban"])
realisasi = col(fact, ["total_realisasi","total_realisasi_pembayaran"])
baki = col(fact, ["baki_debet","baki_debet_berjalan"])
agunan = col(fact, ["total_nilai_agunan","nilai_agunan"])
rasio = col(fact, ["rasio_kredit_agunan","rasio_nilai_kredit_agunan","rasio_kredit_terhadap_agunan"])
tunggakan = col(fact, ["hari_tunggakan_terlama","hari_tunggakan","maks_hari_keterlambatan"])
kolek = col(fact, ["kolektibilitas","kolektibilitas_pinjaman","kategori_kolektibilitas"])
status = col(fact, ["status_pinjaman","status"])

if date:
    fact[date] = pd.to_datetime(fact[date], errors="coerce")
    fact["tahun"] = fact[date].dt.year
    fact["periode"] = fact[date].dt.to_period("M").astype(str)

for x in [plafon,kewajiban,realisasi,baki,agunan,rasio,tunggakan]:
    if x: fact[x] = pd.to_numeric(fact[x], errors="coerce")

# ---------- filters ----------
st.sidebar.header("🔎 Filter")
df = fact.copy()

if "tahun" in df:
    years = sorted(df["tahun"].dropna().astype(int).unique())
    ys = st.sidebar.multiselect("Tahun", years, default=years)
    if ys: df = df[df["tahun"].isin(ys)]

filter_cols = [
    ("provinsi","Provinsi"),("wilayah","Wilayah"),("nama_cabang","Cabang"),
    ("nama_produk","Produk"),("segmen","Segmen"),("jenis_usaha","Jenis Usaha"),
    ("jenis_kelamin","Jenis Kelamin"),(kolek,"Kolektibilitas"),(status,"Status Pinjaman")
]
for c, label in filter_cols:
    if c and c in df.columns:
        vals = sorted(df[c].dropna().astype(str).unique())
        chosen = st.sidebar.multiselect(label, vals, default=vals)
        if chosen: df = df[df[c].astype(str).isin(chosen)]

n = df[pid].nunique() if pid else len(df)
tot_plafon = df[plafon].sum() if plafon else np.nan
tot_kewajiban = df[kewajiban].sum() if kewajiban else np.nan
tot_realisasi = df[realisasi].sum() if realisasi else np.nan
rate = tot_realisasi / tot_kewajiban * 100 if kewajiban and tot_kewajiban else np.nan

# ---------- KPI ----------
st.subheader("Ringkasan Portofolio")
a,b,c,d,e = st.columns(5)
a.metric("Jumlah Pinjaman", f"{n:,}".replace(",","."), help="Jumlah pinjaman_id unik")
b.metric("Total Plafon", rupiah(tot_plafon))
c.metric("Total Kewajiban", rupiah(tot_kewajiban))
d.metric("Total Realisasi", rupiah(tot_realisasi))
e.metric("Realisasi / Kewajiban", f"{rate:.2f}%" if pd.notna(rate) else "N/A")

# ---------- trend ----------
st.subheader("📈 Tren Lintas Waktu")
if date and df[date].notna().any():
    t = df.dropna(subset=[date]).copy()
    t["periode"] = t[date].dt.to_period("M").astype(str)
    agg = t.groupby("periode").agg(
        jumlah_pinjaman=(pid, "nunique") if pid else (date,"size"),
        total_plafon=(plafon,"sum") if plafon else (date,"size")
    ).reset_index()
    fig = px.line(agg, x="periode", y="jumlah_pinjaman", markers=True,
                  title="Jumlah Pinjaman per Bulan")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("tanggal_akad tidak tersedia/valid.")

# ---------- category ----------
st.subheader("📊 Perbandingan Antar Kategori")
x1,x2 = st.columns(2)

cat = next((x for x in ["nama_produk","segmen","jenis_usaha","wilayah","nama_cabang"] if x in df.columns), None)
with x1:
    if cat:
        q = df.groupby(cat).agg(jumlah=(pid,"nunique") if pid else (cat,"size")).reset_index()
        q = q.sort_values("jumlah", ascending=False).head(10)
        st.plotly_chart(px.bar(q, x=cat, y="jumlah", text="jumlah",
                                title=f"Top {cat} berdasarkan Jumlah Pinjaman"),
                        use_container_width=True)
    else: st.info("Kolom kategori belum tersedia.")

with x2:
    if "wilayah" in df.columns and plafon:
        q = df.groupby("wilayah")[plafon].sum().reset_index()
        q = q.sort_values(plafon, ascending=False)
        st.plotly_chart(px.bar(q, x="wilayah", y=plafon,
                                title="Total Plafon berdasarkan Wilayah"),
                        use_container_width=True)
    elif "provinsi" in df.columns and plafon:
        q = df.groupby("provinsi")[plafon].sum().reset_index().sort_values(plafon, ascending=False).head(10)
        st.plotly_chart(px.bar(q, x="provinsi", y=plafon,
                                title="Top Provinsi berdasarkan Total Plafon"),
                        use_container_width=True)
    else: st.info("Kolom wilayah/provinsi belum tersedia.")

# ---------- distribution ----------
st.subheader("📦 Visual Distribusi")
x1,x2 = st.columns(2)
with x1:
    if plafon:
        st.plotly_chart(px.histogram(df, x=plafon, nbins=30, marginal="box",
                                     title="Distribusi Nilai Plafon"),
                        use_container_width=True)
    else: st.info("Kolom plafon belum tersedia.")
with x2:
    if kolek and kolek in df.columns:
        q = df[kolek].fillna("Tidak diketahui").astype(str).value_counts().reset_index()
        q.columns = [kolek,"jumlah"]
        st.plotly_chart(px.pie(q, names=kolek, values="jumlah", hole=.45,
                                title="Distribusi Kolektibilitas"),
                        use_container_width=True)
    else: st.info("Kolom kolektibilitas belum tersedia.")

# ---------- risk ----------
st.subheader("⚠️ Risiko dan Agunan")
r1,r2,r3 = st.columns(3)
r1.metric("Rata-rata Rasio Kredit/Agunan",
          f"{df[rasio].dropna().mean()*100:.2f}%" if rasio and df[rasio].notna().any() else "N/A")
r2.metric("Rata-rata Hari Tunggakan",
          f"{df[tunggakan].dropna().mean():.1f} hari" if tunggakan and df[tunggakan].notna().any() else "N/A")
r3.metric("Total Baki Debet", rupiah(df[baki].sum()) if baki else "N/A")

# ---------- customer ----------
st.subheader("👥 Profil Nasabah")
x1,x2 = st.columns(2)
with x1:
    if "jenis_usaha" in df.columns:
        q = df["jenis_usaha"].fillna("Tidak diketahui").astype(str).value_counts().head(10).reset_index()
        q.columns = ["jenis_usaha","jumlah"]
        st.plotly_chart(px.bar(q, x="jumlah", y="jenis_usaha", orientation="h",
                                title="10 Jenis Usaha Terbanyak"),
                        use_container_width=True)
with x2:
    if "jenis_kelamin" in df.columns:
        q = df["jenis_kelamin"].fillna("Tidak diketahui").astype(str).value_counts().reset_index()
        q.columns = ["jenis_kelamin","jumlah"]
        st.plotly_chart(px.pie(q, names="jenis_kelamin", values="jumlah", hole=.45,
                                title="Distribusi Jenis Kelamin"),
                        use_container_width=True)

# ---------- data ----------
with st.expander("🔎 Lihat Data Hasil Filter"):
    st.dataframe(df, use_container_width=True, height=400)
    st.download_button("⬇️ Download CSV hasil filter",
                       df.to_csv(index=False).encode("utf-8"),
                       "fact_pinjaman_filtered.csv", "text/csv")

st.caption(f"Data setelah filter: {len(df):,} baris | {n:,} pinjaman unik")
