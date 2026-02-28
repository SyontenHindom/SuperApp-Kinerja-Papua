import streamlit as st
import google.generativeai as genai
import PyPDF2
import pandas as pd
import json

# ==========================================
# 1. KONFIGURASI SISTEM & TEMA ANTI-CRASH
# ==========================================
st.set_page_config(page_title="AI Merit System Papua", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

# CSS Super Bersih (Hanya menargetkan container utama, tidak merusak layout Streamlit)
st.markdown("""
    <style>
    /* Latar Belakang Pemandangan */
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1570527418731-893da047e1d5?q=80&w=2000&auto=format&fit=crop"); 
        background-size: cover; background-attachment: fixed; background-position: center;
    }
    
    /* Membungkus seluruh area tengah dengan SATU efek kaca agar tidak bertumpuk */
    .block-container {
        background: rgba(255, 255, 255, 0.95) !important;
        padding: 3rem !important;
        border-radius: 15px;
        margin-top: 30px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }

    /* Warna Teks yang Pasti Terbaca (Anti Dark-Mode Clash) */
    h1, h2, h3, h4, h5, p, span, label, div {
        color: #1E293B !important; 
    }

    .papua-header {
        background: linear-gradient(135deg, rgba(21, 128, 61, 1) 0%, rgba(194, 65, 12, 1) 50%, rgba(202, 138, 4, 1) 100%);
        padding: 25px 30px; border-radius: 12px; color: white !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2); margin-bottom: 25px;
        display: flex; align-items: center; gap: 25px;
    }
    .papua-header p { color: white !important; }
    .papua-title {font-size: 36px !important; font-weight: 900; margin-bottom: 4px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);}
    .papua-subtitle {font-size: 16px !important; font-weight: 400; margin: 0; opacity: 0.9;}
    .step-title {font-size: 22px !important; font-weight: 800; color: #1E3A8A !important; border-bottom: 3px solid #F59E0B; padding-bottom: 8px; margin-bottom: 15px;}
    .jabatan-title {font-size: 18px !important; font-weight: 700; color: #0F172A !important; background: linear-gradient(90deg, #E0F2FE 0%, #F8FAFC 100%); padding: 10px 15px; border-radius: 6px; margin-top: 20px; border-left: 5px solid #0284C7;}
    .diagnostic-box {background: #F8FAFC; border: 1px solid #CBD5E1; border-left: 6px solid #3B82F6; padding: 20px; border-radius: 8px; margin-top: 20px;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI INTI
# ==========================================
for key in ['target_jpt', 'struktur_sotk', 'parsed_data', 'dokumen_terbaca']:
    if key not in st.session_state: st.session_state[key] = None if key == 'parsed_data' else ""

def extract_text(pdf_file, max_pages=60):
    if not pdf_file: return ""
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        return "".join([page.extract_text() + "\n" for page in reader.pages[:min(max_pages, len(reader.pages))]])
    except Exception: return ""

def clean_json_response(text):
    text = text.strip()
    if text.startswith("```json"): text = text[7:]
    elif text.startswith("```"): text = text[3:]
    if text.endswith("```"): text = text[:-3]
    return text.strip()

def generate_html_print(df, nama_jabatan, instansi, skpd, tahun):
    return f"""
    <html><head><style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; color: #222; }}
        h2 {{ text-align: center; margin-bottom: 2px; color: #000; text-transform: uppercase; }}
        h3, h4 {{ text-align: center; margin: 5px 0; color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #000; padding: 6px; text-align: left; vertical-align: top; }}
        th {{ background-color: #e2e8f0; text-align: center; font-weight: bold; }}
        td:empty {{ border-top: none; border-bottom: none; }} 
        @media print {{ @page {{ size: landscape; margin: 12mm; }} }}
    </style></head><body>
        <h2>MATRIKS SASARAN KINERJA PEGAWAI (SKP) TAHUN {tahun}</h2>
        <h3>{instansi} - {skpd}</h3>
        <h4>Formulir Jabatan: <b>{nama_jabatan}</b></h4>
        {df.to_html(index=False, classes='table')}
    </body></html>
    """

DAFTAR_PEMDA = [
    "Pemerintah Provinsi Papua", "Pemerintah Kota Jayapura", "Pemerintah Kab. Jayapura", "Pemerintah Kab. Keerom", "Pemerintah Kab. Sarmi", "Pemerintah Kab. Mamberamo Raya", "Pemerintah Kab. Biak Numfor", "Pemerintah Kab. Supiori", "Pemerintah Kab. Kepulauan Yapen", "Pemerintah Kab. Waropen",
    "Pemerintah Provinsi Papua Barat", "Pemerintah Kab. Manokwari", "Pemerintah Kab. Pegunungan Arfak", "Pemerintah Kab. Manokwari Selatan", "Pemerintah Kab. Teluk Bintuni", "Pemerintah Kab. Teluk Wondama", "Pemerintah Kab. Fakfak", "Pemerintah Kab. Kaimana",
    "Pemerintah Provinsi Papua Tengah", "Pemerintah Kab. Nabire", "Pemerintah Kab. Puncak Jaya", "Pemerintah Kab. Paniai", "Pemerintah Kab. Mimika", "Pemerintah Kab. Puncak", "Pemerintah Kab. Dogiyai", "Pemerintah Kab. Intan Jaya", "Pemerintah Kab. Deiyai",
    "Pemerintah Provinsi Papua Pegunungan", "Pemerintah Kab. Jayawijaya", "Pemerintah Kab. Pegunungan Bintang", "Pemerintah Kab. Yahukimo", "Pemerintah Kab. Tolikara", "Pemerintah Kab. Mamberamo Tengah", "Pemerintah Kab. Yalimo", "Pemerintah Kab. Lanny Jaya", "Pemerintah Kab. Nduga",
    "Pemerintah Provinsi Papua Selatan", "Pemerintah Kab. Merauke", "Pemerintah Kab. Boven Digoel", "Pemerintah Kab. Mappi", "Pemerintah Kab. Asmat",
    "Pemerintah Provinsi Papua Barat Daya", "Pemerintah Kota Sorong", "Pemerintah Kab. Sorong", "Pemerintah Kab. Sorong Selatan", "Pemerintah Kab. Raja Ampat", "Pemerintah Kab. Tambrauw", "Pemerintah Kab. Maybrat"
]

# ==========================================
# 3. SIDEBAR 
# ==========================================
with st.sidebar:
    st.image("[https://upload.wikimedia.org/wikipedia/commons/e/e5/Logo_BKN_Baru.png](https://upload.wikimedia.org/wikipedia/commons/e/e5/Logo_BKN_Baru.png)", width=120)
    st.divider()
    st.header("⚙️ Akses Engine Super AI")
    api_key = st.text_input("API Key (Gemini Pro):", type="password")
    
    st.divider()
    st.header("📍 Data Entitas Organisasi")
    lokus_pemda = st.selectbox("Lokus Instansi Pemda:", DAFTAR_PEMDA)
    tahun_skp = st.number_input("Tahun Kinerja:", min_value=2025, value=2025, step=1)
    nama_skpd = st.text_input("Nama SKPD / Unit Kerja:", placeholder="Cth: Dinas Pendidikan, BKD, RSUD...")
    
    st.divider()
    st.header("📂 Mode Analisis AI")
    mode_pemrosesan = st.radio("Pilih Basis Pengetahuan:", ["1. Upload Renstra/PK", "2. Upload SOTK/Tupoksi", "3. Mode Auto-Indexing"], label_visibility="collapsed")

    uploaded_file = None
    if "1. Upload Renstra" in mode_pemrosesan:
        st.success("✅ Sangat Disarankan. Analisis berdasarkan dokumen asli.")
        uploaded_file = st.file_uploader("Upload Dokumen Perencanaan (PDF)", type="pdf")
    elif "2. Upload Tupoksi" in mode_pemrosesan:
        st.warning("⚠️ Cukup Baik. SOTK presisi, target angka disimulasikan.")
        uploaded_file = st.file_uploader("Upload Perda SOTK (PDF)", type="pdf")
    else:
        st.error("🔥 Autonomous Mode. AI akan menyusun otomatis dari referensi web.")

# ==========================================
# 4. HEADER 
# ==========================================
logo_kpi_cascading = """
<svg viewBox="0 0 100 100" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="width: 80px; height: 80px; min-width:80px;">
    <rect x="35" y="10" width="30" height="20" rx="4" fill="rgba(255, 215, 0, 0.9)" stroke="#FFD700" />
    <circle cx="50" cy="20" r="5" fill="#FFFFFF" stroke="none" />
    <path d="M50 30 L50 45" /> <path d="M20 45 L80 45" />
    <path d="M20 45 L20 60" /> <path d="M50 45 L50 60" /> <path d="M80 45 L80 60" />
    <circle cx="20" cy="75" r="15" stroke="#FFD700" /> <circle cx="20" cy="75" r="5" fill="#FFD700" stroke="none" />
    <circle cx="50" cy="75" r="15" stroke="#FFD700" /> <circle cx="50" cy="75" r="5" fill="#FFD700" stroke="none" />
    <circle cx="80" cy="75" r="15" stroke="#FFD700" /> <circle cx="80" cy="75" r="5" fill="#FFD700" stroke="none" />
</svg>
"""

st.markdown(f"""
<div class="papua-header">
    {logo_kpi_cascading}
    <div>
        <p class="papua-title">SuperApp Kinerja ASN (Otsus Papua)</p>
        <p class="papua-subtitle">Kanreg IX BKN Jayapura | Integrasi SAKIP, PermenPANRB, & UU Otsus No. 2/2021</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 5. KECERDASAN BUATAN UTAMA (PROSES BISNIS)
# ==========================================
if api_key and nama_skpd:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    if uploaded_file is not None and st.session_state.dokumen_terbaca == "":
        st.session_state.dokumen_terbaca = extract_text(uploaded_file)
    dokumen_teks = st.session_state.dokumen_terbaca
    status_mode = mode_pemrosesan.split(" (")[0]

    st.markdown('<p class="step-title">🎯 TAHAP 1: Konstruksi Strategi Pimpinan (JPT)</p>', unsafe_allow_html=True)
    if st.button("🔍 1. Rumuskan Target Kepala SKPD", type="primary", use_container_width=True):
        with st.spinner("Membaca UU 2/2021, RAPPP, dan Regulasi BKN..."):
            prompt_jpt = f"""
            Lokus: {lokus_pemda}. Unit Kerja: {nama_skpd}. Tahun: {tahun_skp}. MODE: {status_mode}.
            Gunakan UU Nomor 2 Tahun 2021 tentang Otsus Papua, Rencana Aksi Percepatan Pembangunan Papua (RAPPP) 2025-2029 (seperti peningkatan SDM OAP, ekonomi, infrastruktur), dan PermenPANRB 6/2022.
            Tugas: Rumuskan TEPAT 4 Rencana Hasil Kerja (RHK) Utama Kepala {nama_skpd} yang mendukung roh Otsus Papua.
            ATURAN MUTLAK 4 PERSPEKTIF BSC:
            1. [Penerima Layanan] - Outcome Pelayanan Teknis untuk Masyarakat/OAP.
            2. [Proses Bisnis Internal] - Outcome Kualitas Tata Kelola/Inovasi.
            3. [Penguatan Internal] - Outcome Peningkatan SDM & Integritas.
            4. [Anggaran] - Outcome Realisasi APBD & SAKIP (PermenPANRB 22/2024).
            Dokumen User: {dokumen_teks[:25000]}
            """
            st.session_state.target_jpt = model.generate_content(prompt_jpt).text

    if st.session_state.target_jpt:
        st.session_state.target_jpt = st.text_area("Validasi Kinerja JPT (Edit jika diperlukan):", st.session_state.target_jpt, height=200)

    st.write("")
    st.markdown('<p class="step-title">🏢 TAHAP 2: Arsitektur Organisasi & Garis Komando</p>', unsafe_allow_html=True)
    if st.button("🏛️ 2. Bangun Struktur Organisasi (SOTK)", type="secondary", use_container_width=True):
        with st.spinner(f"Membangun struktur SOTK via {status_mode}..."):
            prompt_sotk = f"Susun SOTK logis untuk {nama_skpd} di lingkungan {lokus_pemda} berdasarkan referensi Permendagri/JDIH. Format: 1. Kepala -> 1.1 Sekretaris/Kabid -> JF/Pelaksana. Dokumen User: {dokumen_teks[:15000]}"
            st.session_state.struktur_sotk = model.generate_content(prompt_sotk).text
            
    if st.session_state.struktur_sotk:
        st.session_state.struktur_sotk = st.text_area("Cek & Lengkapi Jabatan (Ketik manual jika ada jabatan kurang):", st.session_state.struktur_sotk, height=220)

    st.write("")
    if st.session_state.struktur_sotk and st.session_state.target_jpt:
        st.markdown('<p class="step-title">⚙️ TAHAP 3: Eksekusi Cascading (Multi-RHK per Pegawai)</p>', unsafe_allow_html=True)
        
        if st.button("🚀 3. Proses Engine e-Kinerja BKN (Final)", type="primary", use_container_width=True):
            with st.spinner("AI Sedang Menjahit Cascading Langsung & Tidak Langsung..."):
                prompt_json = f"""
                Lokus: {lokus_pemda}. SKPD: {nama_skpd}. 
                TARGET JPT: "{st.session_state.target_jpt}". 
                SOTK: "{st.session_state.struktur_sotk}"
                
                Anda adalah AI e-Kinerja BKN. Pedomani UU Otsus Papua dan RAPPP 2025-2029 dalam menyusun indikator.
                
                🔥 MULTI-RHK PER PEGAWAI:
                Untuk SETIAP Jabatan bawahan, ciptakan MINIMAL 3 hingga 4 RHK BERBEDA (Campuran Cascading Langsung & Tidak Langsung).
                
                🔥 THE RULE OF THREE & ANTI-REPETISI (SANGAT MUTLAK): 🔥
                Setiap 1 RHK wajib dipecah menjadi 3 baris (Kuantitas, Kualitas, Waktu). 
                NAMUN, untuk baris "Kualitas" dan "Waktu", Anda WAJIB MENGOSONGKAN string pada kolom "Jenis Cascading", "RHK Atasan Yang Diintervensi", dan "Rencana Hasil Kerja" menjadi string kosong (""). Ini agar teks tidak berulang-ulang di tabel aplikasi!
                
                FORMAT JSON MURNI WAJIB:
                {{
                    "Kesimpulan_dan_Rekomendasi": {{"Aturan_Dasar_Digunakan": [], "Evaluasi_Kekurangan_Data": [], "Saran_Tindak_Lanjut": []}},
                    "SKP_JPT": [ {{"Perspektif": "...", "Rencana Hasil Kerja": "...", "Indikator Kinerja Utama": "...", "Target Tahunan": "..."}} ],
                    "SKP_JA": {{ "Nama Jabatan A": [ {{"Jenis Cascading": "Langsung", "RHK Atasan Yang Diintervensi": "...", "Rencana Hasil Kerja": "...", "Aspek": "Kuantitas", "Indikator Kinerja Individu": "...", "Target Tahunan": "...", "Bukti Dukung": "..."}}, {{"Jenis Cascading": "", "RHK Atasan Yang Diintervensi": "", "Rencana Hasil Kerja": "", "Aspek": "Kualitas", "Indikator Kinerja Individu": "...", "Target Tahunan": "...", "Bukti Dukung": "..."}}, {{"Jenis Cascading": "", "RHK Atasan Yang Diintervensi": "", "Rencana Hasil Kerja": "", "Aspek": "Waktu", "Indikator Kinerja Individu": "...", "Target Tahunan": "...", "Bukti Dukung": "..."}} ] }},
                    "SKP_JF": {{ "Nama Jabatan JF": [ ...Pola Sama... ] }},
                    "SKP_Pelaksana": {{ "Nama Pelaksana": [ ...Pola Sama... ] }}
                }}
                """
                raw_response = model.generate_content(prompt_json, generation_config=genai.types.GenerationConfig(temperature=0.1)).text
                st.session_state.parsed_data = json.loads(clean_json_response(raw_response))

        if st.session_state.parsed_data:
            st.success("✅ Matriks Kinerja Sempurna! Tabel tersusun bersih tanpa pengulangan kata.")
            data_skp = st.session_state.parsed_data
            
            diag = data_skp.get("Kesimpulan_dan_Rekomendasi", {})
            if diag:
                st.markdown('<div class="diagnostic-box">', unsafe_allow_html=True)
                st.markdown("### 📊 Laporan Konsultan Eksekutif (AI BKN)")
                st.markdown("**📚 Referensi Hukum & Kebijakan:** " + " | ".join(diag.get("Aturan_Dasar_Digunakan", [])))
                st.markdown("**⚠️ Diagnostik Kelengkapan:** " + " ".join(diag.get("Evaluasi_Kekurangan_Data", [])))
                st.markdown("**💡 Tindak Lanjut Admin:** " + " ".join(diag.get("Saran_Tindak_Lanjut", [])))
                st.markdown('</div>', unsafe_allow_html=True)

            st.write("---")
            tab1, tab2, tab3, tab4 = st.tabs(["👑 1. SKP Pimpinan (JPT)", "👔 2. SKP Administrator (JA)", "🔬 3. SKP Fungsional (JF)", "📋 4. SKP Pelaksana"])
            
            def render_tabel(data_kategori, tab_obj, is_jpt=False):
                with tab_obj:
                    if is_jpt:
                        df_jpt = pd.DataFrame(data_kategori)
                        col_jpt = {"Perspektif": st.column_config.SelectboxColumn(options=["Penerima Layanan", "Proses Bisnis Internal", "Penguatan Internal", "Anggaran"])}
                        edited_jpt = st.data_editor(df_jpt, column_config=col_jpt, num_rows="dynamic", use_container_width=True)
                        
                        c1, c2, c3 = st.columns([1,1,2])
                        with c1: st.download_button("📥 Excel", data=edited_jpt.to_csv(index=False).encode('utf-8'), file_name="SKP_JPT.csv", mime="text/csv", use_container_width=True)
                        with c2: st.download_button("🖨️ Cetak PDF", data=generate_html_print(edited_jpt, "Kepala SKPD", lokus_pemda, nama_skpd, tahun_skp), file_name="SKP_JPT.html", mime="text/html", use_container_width=True)
                    else:
                        if not data_kategori: return
                        for nama_jabatan, list_rhk in data_kategori.items():
                            with st.container(border=True):
                                st.markdown(f'<p class="jabatan-title">👤 {nama_jabatan}</p>', unsafe_allow_html=True)
                                
                                col_cfg = {
                                    "Jenis Cascading": st.column_config.SelectboxColumn("Cascading", options=["Langsung", "Tidak Langsung", ""]),
                                    "Aspek": st.column_config.SelectboxColumn("Aspek", options=["Kuantitas", "Kualitas", "Waktu"])
                                }
                                edited_df = st.data_editor(pd.DataFrame(list_rhk), column_config=col_cfg, num_rows="dynamic", use_container_width=True, key=f"edit_{nama_jabatan}")
                                
                                c1, c2, c3 = st.columns([1,1,2])
                                with c1: st.download_button(f"📥 Excel", data=edited_df.to_csv(index=False).encode('utf-8'), file_name=f"SKP_{nama_jabatan.replace(' ','_')}.csv", mime="text/csv", use_container_width=True, key=f"csv_{nama_jabatan}")
                                with c2: st.download_button(f"🖨️ Cetak PDF", data=generate_html_print(edited_df, nama_jabatan, lokus_pemda, nama_skpd, tahun_skp), file_name=f"SKP_{nama_jabatan.replace(' ','_')}.html", mime="text/html", use_container_width=True, key=f"pdf_{nama_jabatan}")

            render_tabel(data_skp.get("SKP_JPT", []), tab1, is_jpt=True)
            render_tabel(data_skp.get("SKP_JA", {}), tab2, is_jpt=False)
            render_tabel(data_skp.get("SKP_JF", {}), tab3, is_jpt=False)
            render_tabel(data_skp.get("SKP_Pelaksana", {}), tab4, is_jpt=False)

            st.divider()
            st.markdown('<p class="step-title">➕ Tambah Jabatan Baru ke Matriks (AI Auto-Tasking)</p>', unsafe_allow_html=True)
            col_t1, col_t2, col_t3 = st.columns([2, 1, 1])
            with col_t1: new_jabatan = st.text_input("Nama Jabatan Baru:", placeholder="Cth: Tenaga Honorer Satpam", label_visibility="collapsed")
            with col_t2: new_kategori = st.selectbox("Kategori e-Kinerja:", ["SKP_Pelaksana", "SKP_JF", "SKP_JA"], label_visibility="collapsed")
            with col_t3: btn_tambah = st.button("➕ Generate RHK Jabatan", type="primary", use_container_width=True)

            if btn_tambah and new_jabatan:
                with st.spinner(f"AI sedang memikirkan Tupoksi & 3 Aspek Indikator untuk {new_jabatan}..."):
                    prompt_new = f"""
                    TARGET JPT: {st.session_state.target_jpt}
                    Buatkan MINIMAL 3 RHK berbeda (Campuran Jenis Cascading: Langsung & Tidak Langsung) untuk Jabatan: "{new_jabatan}" di {nama_skpd} {lokus_pemda}. Pedomani Otsus Papua.
                    Wajib gunakan Rule of 3 (Kuantitas, Kualitas, Waktu) untuk setiap RHK, dan kosongkan teks pada baris kualitas/waktu agar rapi.
                    Format JSON Murni.
                    """
                    new_json_str = clean_json_response(model.generate_content(prompt_new).text)
                    try:
                        new_data = json.loads(new_json_str)
                        if new_kategori not in st.session_state.parsed_data: st.session_state.parsed_data[new_kategori] = {}
                        st.session_state.parsed_data[new_kategori][new_jabatan] = new_data
                        st.rerun() 
                    except Exception as e:
                        st.error("Gagal men-generate jabatan baru. Pastikan koneksi stabil.")
else:
    st.info("👈 Silakan pilih Lokus Daerah, ketik Nama SKPD, dan masukkan API Key di panel sebelah kiri untuk memantik Super AI ini.")
