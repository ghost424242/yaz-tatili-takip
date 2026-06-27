import streamlit as st
import json
import os
import base64
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Yaz Tatili Yıldız Takip Sistemi", page_icon="⭐", layout="wide")

# --- CSS İLE GÖRSELLEŞTİRME ---
st.markdown("""
    <style>
    .main { background-color: #f7f9fc; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Comic Sans MS', cursive, sans-serif; }
    .yildiz-seridi { font-size: 28px; letter-spacing: 5px; margin-bottom: 10px; text-align: center; }
    .ozet-kutu { padding: 12px; border-radius: 10px; background-color: white; border-left: 5px solid #ff823a; margin-bottom: 10px; box-shadow: 1px 1px 5px rgba(0,0,0,0.05); }
    .edit-box { background-color: #f0f4f8; padding: 12px; border-radius: 10px; margin-top: 10px; border: 1px dashed #ff823a; }
    
    /* MOBİL İÇİN BUTON BOYUTLANDIRMALARI */
    .stButton > button, .stFormSubmitButton > button {
        background-color: #ff823a !important;
        color: white !important;
        border: 2px solid #ff823a !important;
        border-radius: 20px !important;
        font-weight: bold !important;
        font-size: 14px !important;
        width: 100% !important;
        padding: 0.6rem 1rem !important;
        margin-top: 5px !important;
    }
    
    /* İÇİNDE 'Düzenle' GEÇEN MAVİ BUTONLAR */
    .stButton > button:has(div:contains("Düzenle")), 
    .stButton > button:has(div:contains("✏️")) {
        background-color: #3498db !important;
        border-color: #3498db !important;
    }
    
    /* İÇİNDE 'Sil' GEÇEN KIRMIZI BUTONLAR */
    .stButton > button:has(div:contains("Sil")), 
    .stButton > button:has(div:contains("🗑️")),
    .stButton > button:has(div:contains("❌")) {
        background-color: #e74c3c !important;
        border-color: #e74c3c !important;
    }

    /* FOTOĞRAF YÜKLEME ALANI MOBİL AYARI */
    [data-testid="stFileUploaderDropzone"] {
        border: 2px dashed #ff823a !important;
        background-color: #fffaf7 !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }
    [data-testid="stFileUploaderDropzone"] section > div {
        font-size: 0 !important;
    }
    [data-testid="stFileUploaderDropzone"] section > div::after {
        content: "Fotoğraf Seçmek İçin Tıkla 📸";
        font-size: 14px !important;
        color: #2c3e50 !important;
        font-weight: bold !important;
    }
    [data-testid="stFileUploaderDropzone"] section > small {
        font-size: 0 !important;
    }
    [data-testid="stFileUploaderDropzone"] section > small::after {
        content: "Resim formatı: JPG, JPEG veya PNG";
        font-size: 11px !important;
        color: #7f8c8d !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ TABANI İŞLEMLERİ ---
DB_FILE = "veri.json"

def veri_yukle():
    if not os.path.exists(DB_FILE):
        return {"ogrenciler": {}, "ayarlar": {"tatil_baslangic": "2026-06-15"}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def veri_kaydet(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

data = veri_yukle()

# --- SABİT KİTAP İSİMLERİ ANA LİSTESİ ---
KITAP_ISIMLERI = [
    "10 Fasikül 10 Hafta",
    "Yaz Testim ve Problemler",
    "Okuduğunu Anlama",
    "Bilsem'e Hazırlık"
]

# --- HAFTA HESAPLAMA ---
def hafta_hesapla(baslangic_str):
    try:
        baslangic = datetime.strptime(baslangic_str, "%Y-%m-%d")
        gecen_gun = (datetime.now() - baslangic).days
        return max(1, min(10, (gecen_gun // 7) + 1))
    except:
        return 1

su_anki_hafta = hafta_hesapla(data["ayarlar"]["tatil_baslangic"])

# --- HAFTANIN YILDIZI KONTROLÜ ---
def haftalik_durum_hesapla(ogr_veri, hafta_no):
    h_str = str(hafta_no)
    if h_str not in ogr_veri.get("ilerleme", {}):
        return "hiç yok"
    
    hafta = ogr_veri["ilerleme"][h_str]
    fasikul_tam = all(hafta.get("fasikuller", [False]*4))
    kitap_tam = len(hafta.get("kitaplar", [])) >= 2
    deyim_tam = len(hafta.get("deyimler", [])) >= 3
    
    if fasikul_tam and kitap_tam and deyim_tam:
        return "yildiz"
    elif (any(hafta.get("fasikuller", [])) or hafta.get("kitaplar") or hafta.get("deyimler")):
        return "yarim"
    else:
        return "hiç yok"

# --- STATE KONTROLLERİ ---
if 'login_status' not in st.session_state:
    st.session_state.login_status = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'kutlama' not in st.session_state:
    st.session_state.kutlama = None
if 'secilen_detay_ogrenci' not in st.session_state:
    st.session_state.secilen_detay_ogrenci = None
if 'ogretmen_alt_menu' not in st.session_state:
    st.session_state.ogretmen_alt_menu = "📊 Haftalık Özet Raporu"

# --- GİRİŞ EKRANI ---
if st.session_state.login_status is None:
    st.title("☀️ Yaz Tatili Takip Sistemi ☀️")
    giris_rolu = st.selectbox("Lütfen Giriş Panelini Seçin:", ["Öğrenci Girişi 🎒", "Öğretmen Girişi 🎓"])
    
    if giris_rolu == "Öğretmen Girişi 🎓":
        # Tarayıcıların "Şifre/Password" algısını kırmak ve güçlü şifre önerisini kapatmak için başlık değiştirildi ve autocomplete pasif kılındı.
        pw = st.text_input("Giriş Kodu (Öğretmen)", type="password", key="teacher_pw_input", help="Lütfen öğretmen kodunuzu girin.")
        if st.button("Öğretmen Paneline Giriş Yap"):
            if pw == "1234":
                st.session_state.login_status = "teacher"
                st.rerun()
            else:
                st.error("Hatalı Giriş Kodu!")
    else:
        ogr_listesi = list(data["ogrenciler"].keys())
        if not ogr_listesi:
            st.warning("Sistemde henüz kayıtlı öğrenci yok.")
        else:
            secilen_ogr = st.selectbox("Adını Seç", ogr_listesi, key="student_name_select")
            # "Şifren" kelimesi yerine "Giriş Anahtarın" yazılarak mobil tarayıcıların otomatik hesap oluşturma ekranı tetiklemesi engellendi.
            ogr_pw = st.text_input("Giriş Anahtarın", type="password", key="student_pw_input", help="Sana verilen özel kodu gir.")
            if st.button("Öğrenci Paneline Giriş Yap"):
                if data["ogrenciler"][secilen_ogr]["sifre"] == ogr_pw:
                    st.session_state.login_status = "student"
                    st.session_state.user = secilen_ogr
                    st.rerun()
                else:
                    st.error("Hatalı Giriş Anahtarı!")

# --- ÖĞRENCİ PANELİ ---
elif st.session_state.login_status == "student":
    ogr_adi = st.session_state.user
    ogr_veri = data["ogrenciler"][ogr_adi]
    
    if "ilerleme" not in ogr_veri:
        ogr_veri["ilerleme"] = {}

    st.title(f"Hoş geldin, {ogr_adi}! 🎉")
    
    if st.session_state.kutlama == "balon":
        st.balloons()
        st.session_state.kutlama = None
    elif st.session_state.kutlama == "kar":
        st.snow()
        st.session_state.kutlama = None

    su_anki_hafta_durumu = haftalik_durum_hesapla(ogr_veri, su_anki_hafta)
    if su_anki_hafta_durumu == "yildiz":
        st.success(f"⭐ **Tebrikler! {su_anki_hafta}. Hafta görevlerini başarıyla tamamladın ve Haftanın Yıldızı oldun!** ⭐")

    yildizlar = ""
    for h in range(1, 11):
        durum = haftalik_durum_hesapla(ogr_veri, h)
        if durum == "yildiz": yildizlar += "⭐"
        elif durum == "yarim": yildizlar += "💔"
        else: yildizlar += "🤍"
    
    st.markdown(f"<div class='yildiz-seridi'>{yildizlar}</div>", unsafe_allow_html=True)
    st.info(f"📅 Bugün tatilin **{su_anki_hafta}. haftasındayız.**")

    menu = st.sidebar.radio("Menü", ["🎯 Bu Haftaki Görevlerim", "📊 Geçmiş Ödevlerim", "🚪 Çıkış Yap"])

    if menu == "🎯 Bu Haftaki Görevlerim":
        st.markdown("### 📅 Ödev Girişi Yapılacak Hafta")
        secilen_calisma_haftasi = st.selectbox(
            "Çalışmasını eklemek veya tamamlamak istediğiniz haftayı seçin:",
            list(range(1, 11)),
            index=su_anki_hafta-1
        )
        
        h_str = str(secilen_calisma_haftasi)
        if h_str not in ogr_veri["ilerleme"]:
            ogr_veri["ilerleme"][h_str] = {"fasikuller": [False]*4, "kitaplar": [], "deyimler": []}
        
        current_data = ogr_veri["ilerleme"][h_str]

        st.subheader(f"📚 {secilen_calisma_haftasi}. Hafta Fasikül Takibi")
        f1 = st.checkbox(f"{KITAP_ISIMLERI[0]} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][0])
        f2 = st.checkbox(f"{KITAP_ISIMLERI[1]} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][1])
        f3 = st.checkbox(f"{KITAP_ISIMLERI[2]} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][2])
        f4 = st.checkbox(f"{KITAP_ISIMLERI[3]} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][3])
        
        if st.button("Fasikül Durumunu Kaydet", key="fasikul_save_btn"):
            current_data["fasikuller"] = [f1, f2, f3, f4]
            veri_kaydet(data)
            st.session_state.kutlama = "balon"
            st.rerun()

        st.divider()

        st.subheader(f"📖 {secilen_calisma_haftasi}. Hafta Kitap Okuma Takibi (En Az 2 Kitap)")
        st.write(f"Seçilen haftada okunan kitap sayısı: **{len(current_data.get('kitaplar', []))}**")
        
        with st.form("kitap_form", clear_on_submit=True):
            k_ad = st.text_input("Okuduğun Kitabın Adı")
            k_sayfa = st.number_input("Sayfa Sayısı", min_value=1, value=50)
            k_foto = st.file_uploader("📝 Okuma Defteri Sayfa Fotoğrafı", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("Kitap Girişini Kaydet"):
                if k_ad:
                    foto_b64 = ""
                    if k_foto is not None:
                        foto_b64 = base64.b64encode(k_foto.read()).decode('utf-8')
                    current_data["kitaplar"].append({
                        "ad": k_ad, "sayfa": k_sayfa, "foto": foto_b64, "tarih": str(datetime.now().date())
                    })
                    veri_kaydet(data)
                    st.session_state.kutlama = "kar"
                    st.rerun()

        if current_data["kitaplar"]:
            for idx, k in enumerate(current_data["kitaplar"]):
                col_m1, col_m2 = st.columns([3, 1])
                with col_m1: st.caption(f"📖 {k['ad']} ({k['sayfa']} S.)")
                with col_m2:
                    if st.button("Sil 🗑️", key=f"sil_k_{idx}"):
                        current_data["kitaplar"].pop(idx)
                        veri_kaydet(data)
                        st.rerun()

        st.divider()

        st.subheader(f"🗣️ {secilen_calisma_haftasi}. Hafta Deyim ve Atasözü Girişi (En Az 3 Adet)")
        st.write(f"Seçilen haftada öğrenilen deyim/atasözü sayısı: **{len(current_data.get('deyimler', []))}**")
        
        with st.form("deyim_form", clear_on_submit=True):
            d_tur = st.selectbox("Tür", ["Deyim", "Atasözü"])
            d_ad = st.text_input("Deyim / Atasözü Adı")
            d_foto = st.file_uploader("📝 Defter Sayfa Fotoğrafı", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("Deyimi Kaydet"):
                if d_ad:
                    dfoto_b64 = ""
                    if d_foto is not None:
                        dfoto_b64 = base64.b64encode(d_foto.read()).decode('utf-8')
                    current_data["deyimler"].append({"tur": d_tur, "ad": d_ad, "foto": dfoto_b64})
                    veri_kaydet(data)
                    st.session_state.kutlama = "kar"
                    st.rerun()

        if current_data["deyimler"]:
            for idx, d in enumerate(current_data["deyimler"]):
                col_md1, col_md2 = st.columns([3, 1])
                with col_md1: st.caption(f"💡 {d['ad']} ({d.get('tur','Deyim')})")
                with col_md2:
                    if st.button("Sil 🗑️", key=f"sil_d_{idx}"):
                        current_data["deyimler"].pop(idx)
                        veri_kaydet(data)
                        st.rerun()

    elif menu == "📊 Geçmiş Ödevlerim":
        st.subheader("🔍 Tüm Girişlerin")
        for h_no in sorted([int(x) for x in ogr_veri["ilerleme"].keys()]):
            h_str = str(h_no)
            with st.expander(f"📅 {h_no}. Hafta Detayları", expanded=False):
                if st.button(f"🚨 {h_no}. Haftayı Komple Sil", key=f"komple_sil_{h_str}"):
                    ogr_veri["ilerleme"].pop(h_str)
                    veri_kaydet(data)
                    st.rerun()
                
                f_durum = ogr_veri["ilerleme"][h_str].get("fasikuller", [False]*4)
                st.markdown("**Fasikül Durumları:**")
                for f_idx, b_dur in enumerate(f_durum):
                    dur_yazisi = "✅ Tamamlandı" if b_dur else "❌ Yapılmadı"
                    st.write(f"- {KITAP_ISIMLERI[f_idx]} {h_no}. Fasikül: {dur_yazisi}")
                
                if ogr_veri["ilerleme"][h_str].get("kitaplar"):
                    st.markdown("**Okunan Kitaplar:**")
                    for k in ogr_veri["ilerleme"][h_str]["kitaplar"]:
                        st.write(f"- 📖 {k['ad']}")
                        if k.get("foto"): st.image(base64.b64decode(k["foto"]), width=120)
                if ogr_veri["ilerleme"][h_str].get("deyimler"):
                    st.markdown("**Öğrenilen Deyimler:**")
                    for d in ogr_veri["ilerleme"][h_str]["deyimler"]:
                        st.write(f"- 💡 {d['ad']}")
                        if d.get("foto"): st.image(base64.b64decode(d["foto"]), width=120)

    elif menu == "🚪 Çıkış Yap":
        st.session_state.login_status = None
        st.rerun()

# --- ÖĞRETMEN PANELİ ---
elif st.session_state.login_status == "teacher":
    st.title("🎓 Öğretmen Yönetim Paneli")
    
    st.sidebar.header("⚙️ Sistem Ayarları")
    t_baslangic = st.sidebar.date_input("Yaz Tatili Başlangıç Tarihi", value=datetime.strptime(data["ayarlar"]["tatil_baslangic"], "%Y-%m-%d"))
    if str(t_baslangic) != data["ayarlar"]["tatil_baslangic"]:
        data["ayarlar"]["tatil_baslangic"] = str(t_baslangic)
        veri_kaydet(data)
        st.rerun()
        
    menu = st.sidebar.radio("İşlem Menüsü", [
        "📊 Haftalık Özet Raporu", 
        "🔍 Öğrenci Detaylı Analizi", 
        "📋 Sınıf Listesi & Şifreler", 
        "➕ Toplu Öğrenci Ekle", 
        "🚪 Çıkış Yap"
    ], index=["📊 Haftalık Özet Raporu", "🔍 Öğrenci Detaylı Analizi", "📋 Sınıf Listesi & Şifreler", "➕ Toplu Öğrenci Ekle", "🚪 Çıkış Yap"].index(st.session_state.ogretmen_alt_menu))
    
    st.session_state.ogretmen_alt_menu = menu

    if menu == "📊 Haftalık Özet Raporu":
        st.subheader("📈 Sınıf Haftalık Durum Özeti")
        secilen_rapor_haftasi = st.selectbox("Hafta Seç", list(range(1, 11)), index=su_anki_hafta-1)
        
        y_list, yar_list, h_list = [], [], []
        for ogr, v in data["ogrenciler"].items():
            durum = haftalik_durum_hesapla(v, secilen_rapor_haftasi)
            if durum == "yildiz": y_list.append(ogr)
            elif durum == "yarim": yar_list.append(ogr)
            else: h_list.append(ogr)
            
        st.write("💡 *Öğrencinin ödev detaylarını incelemek için ismine tıklayabilirsiniz:*")
        
        st.success(f"⭐ **Haftanın Yıldızları ({len(y_list)}):**")
        for o in y_list:
            if st.button(f"✅ {o}", key=f"lnk_y_{o}"):
                st.session_state.secilen_detay_ogrenci = o
                st.session_state.ogretmen_alt_menu = "🔍 Öğrenci Detaylı Analizi"
                st.rerun()
                
        st.warning(f"💔 **Eksik Görevi Olanlar ({len(yar_list)}):**")
        for o in yar_list:
            if st.button(f"⚠️ {o}", key=f"lnk_yar_{o}"):
                st.session_state.secilen_detay_ogrenci = o
                st.session_state.ogretmen_alt_menu = "🔍 Öğrenci Detaylı Analizi"
                st.rerun()
                
        st.error(f"🤍 **Hiç Giriş Yapmayanlar ({len(h_list)}):**")
        for o in h_list:
            if st.button(f"❌ {o}", key=f"lnk_h_{o}"):
                st.session_state.secilen_detay_ogrenci = o
                st.session_state.ogretmen_alt_menu = "🔍 Öğrenci Detaylı Analizi"
                st.rerun()

    elif menu == "🔍 Öğrenci Detaylı Analizi":
        st.subheader("🔍 Öğrenci Girişleri Ayrıntılı İnceleme")
        ogr_secenekleri = list(data["ogrenciler"].keys())
        
        if ogr_secenekleri:
            default_idx = 0
            if st.session_state.secilen_detay_ogrenci in ogr_secenekleri:
                default_idx = ogr_secenekleri.index(st.session_state.secilen_detay_ogrenci)
                
            secilen_detay_ogr = st.selectbox("İncelenecek Öğrenciyi Seçin", ogr_secenekleri, index=default_idx)
            st.session_state.secilen_detay_ogrenci = secilen_detay_ogr
            
            o_veri = data["ogrenciler"][secilen_detay_ogr]
            st.markdown(f"### 📋 {secilen_detay_ogr} - Detaylı Çalışma Geçmişi")
            
            if "ilerleme" not in o_veri or not o_veri["ilerleme"]:
                st.info("Bu öğrenci henüz tatil boyunca hiçbir veri girişi yapmadı.")
            else:
                for h_no in sorted([int(x) for x in o_veri["ilerleme"].keys()]):
                    h_str = str(h_no)
                    with st.expander(f"📅 {h_no}. Hafta Kayıtları", expanded=False):
                        if st.button("Haftayı Komple Sil 🗑️", key=f"t_komple_sil_{h_str}"):
                            o_veri["ilerleme"].pop(h_str)
                            veri_kaydet(data)
                            st.rerun()
                            
                        detay_h_veri = o_veri["ilerleme"][h_str]
                        
                        st.write("**📚 Kitap Fasikül Durumları:**")
                        f_dur = detay_h_veri.get("fasikuller", [False]*4)
                        for f_idx, b_dur in enumerate(f_dur):
                            isaret = "✅ Tamamlandı" if b_dur else "❌ Yapılmadı"
                            st.write(f"- {KITAP_ISIMLERI[f_idx]} {h_no}. Fasikül: **{isaret}**")
                            
                        st.write("**📚 Okunan Kitap Ödev Defterleri:**")
                        if detay_h_veri.get("kitaplar"):
                            for k_idx, k in enumerate(detay_h_veri["kitaplar"]):
                                col_t1, col_t2 = st.columns([3, 1])
                                with col_t1:
                                    st.write(f"- {k['ad']} ({k['sayfa']} Sayfa)")
                                    if k.get("foto"): st.image(base64.b64decode(k["foto"]), width=280)
                                with col_t2:
                                    if st.button("Sil 🗑️", key=f"sil_t_k_{h_str}_{k_idx}"):
                                        detay_h_veri["kitaplar"].pop(k_idx)
                                        veri_kaydet(data)
                                        st.rerun()
                        else:
                            st.caption("Kitap girilmemiş.")
                            
                        st.write("**🗣️ Öğrenilen Deyim Defterleri:**")
                        if detay_h_veri.get("deyimler"):
                            for d_idx, d in enumerate(detay_h_veri["deyimler"]):
                                col_td1, col_td2 = st.columns([3, 1])
                                with col_td1:
                                    st.write(f"- **{d['ad']}** ({d.get('tur','Deyim')})")
                                    if d.get("foto"): st.image(base64.b64decode(d["foto"]), width=280)
                                with col_td2:
                                    if st.button("Sil 🗑️", key=f"sil_t_d_{h_str}_{d_idx}"):
                                        detay_h_veri["deyimler"].pop(d_idx)
                                        veri_kaydet(data)
                                        st.rerun()
                        else:
                            st.caption("Deyim girilmemiş.")

    elif menu == "📋 Sınıf Listesi & Şifreler":
        for isim in list(data["ogrenciler"].keys()):
            icerik = data["ogrenciler"][isim]
            yeni_isim = st.text_input("Öğrenci Adı", value=isim, key=f"edit_name_{isim}")
            # Yönetim listesindeki şifre düzenleme alanlarının da kafası karışmasın diye label isimleri optimize edildi.
            yeni_sifre = st.text_input("Giriş Kodu", value=icerik['sifre'], key=f"edit_pw_{isim}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Güncelle ✏️", key=f"edit_save_up_{isim}"):
                    if yeni_isim != isim:
                        data["ogrenciler"][yeni_isim] = {"sifre": yeni_sifre, "ilerleme": icerik["ilerleme"]}
                        data["ogrenciler"].pop(isim)
                    else:
                        data["ogrenciler"][isim]["sifre"] = yeni_sifre
                    veri_kaydet(data)
                    st.rerun()
            with c2:
                if st.button("Öğrenciyi Sil ❌", key=f"sil_btn_del_{isim}"):
                    data["ogrenciler"].pop(isim)
                    veri_kaydet(data)
                    st.rerun()

    elif menu == "➕ Toplu Öğrenci Ekle":
        yeni_liste = st.text_area("Örnek: Ahmet Yılmaz,123")
        if st.button("Sınıf Listesine Ekle", key="mass_save_students"):
            if yeni_liste:
                for satir in yeni_liste.split("\n"):
                    if "," in satir:
                        isim, sifre = satir.split(",")
                        data["ogrenciler"][isim.strip()] = {"sifre": sifre.strip(), "ilerleme": {}}
                veri_kaydet(data)
                st.success("Sınıf listesi eklendi!")
                st.rerun()

    elif menu == "🚪 Çıkış Yap":
        st.session_state.login_status = None
        st.session_state.secilen_detay_ogrenci = None
        st.rerun()
