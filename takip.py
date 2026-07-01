import streamlit as st
import json
import base64
from datetime import datetime
import urllib.request
import urllib.parse

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Yaz Tatili Yıldız Takip Sistemi", page_icon="⭐", layout="wide")

# ==============================================================================
# ⚠️ GÜNCEL GOOGLE APPS SCRIPT WEB APP URL'NİZ
# ==============================================================================
API_URL = "https://script.google.com/macros/s/AKfycbwnjldQgtcFdv3kQ8aZupBq6cWbUeyGnBxhJtVxjzUDxiByFwEMVDqCRIOygQSqlED1/exec"

def veri_yukle():
    if "canli_bulut_db" not in st.session_state:
        try:
            req = urllib.request.Request(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                ham_veri = response.read().decode('utf-8').strip()
                if not ham_veri or ham_veri.startswith("Error") or "Internal Server Error" in ham_veri:
                    raise Exception("BozukVeri")
                st.session_state.canli_bulut_db = json.loads(ham_veri)
        except:
            st.session_state.canli_bulut_db = {"ogrenciler": {}, "ayarlar": {"tatil_baslangic": "2026-06-15"}, "genel_mesajlar": []}
    return st.session_state.canli_bulut_db

def veri_kaydet(data):
    st.session_state.canli_bulut_db = data
    try:
        veri_string = json.dumps(data, ensure_ascii=False)
        req = urllib.request.Request(API_URL, data=veri_string.encode('utf-8'), headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlopen(req)
    except:
        pass

data = veri_yukle()

# --- SABİT KİTAP İSİMLERİ ---
KITAP_ISIMLERI = [
    "10 Fasikül 10 Hafta",
    "Yaz Testim ve Problemler",
    "Okuduğunu Anlama",
    "Bilsem'e Hazırlık"
]

def hafta_hesapla(baslangic_str):
    try:
        baslangic = datetime.strptime(baslangic_str, "%Y-%m-%d")
        gecen_gun = (datetime.now() - baslangic).days
        return max(1, min(10, (gecen_gun // 7) + 1))
    except:
        return 1

su_anki_hafta = hafta_hesapla(data["ayarlar"]["tatil_baslangic"])

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
if 'hizli_mesaj_onay' not in st.session_state:
    st.session_state.hizli_mesaj_onay = False

# --- CSS İLE GÖRSELLEŞTİRME ---
st.markdown("""
    <style>
    .main { background-color: #f7f9fc; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Comic Sans MS', cursive, sans-serif; }
    .yildiz-seridi { font-size: 28px; letter-spacing: 5px; margin-bottom: 10px; text-align: center; }
    .ozet-kutu { padding: 12px; border-radius: 10px; background-color: white; border-left: 5px solid #ff823a; margin-bottom: 10px; box-shadow: 1px 1px 5px rgba(0,0,0,0.05); }
    .edit-box { background-color: #f0f4f8; padding: 12px; border-radius: 10px; margin-top: 10px; border: 1px dashed #ff823a; }
    .mesaj-uyari { background-color: #f39c12 !important; color: white !important; padding: 15px !important; border-radius: 12px !important; font-weight: bold !important; font-size: 16px !important; text-align: center !important; margin-bottom: 15px !important; animation: blink 2s infinite !important; }
    .mesaj-kutusu { background-color: white !important; padding: 15px !important; border-radius: 10px !important; border-left: 5px solid #3498db !important; margin-bottom: 10px !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important; }
    @keyframes blink { 0% { opacity: 0.85; } 50% { opacity: 1; background-color: #e67e22; } 100% { opacity: 0.85; } }
    .stButton > button, .stFormSubmitButton > button { background-color: #ff823a !important; color: white !important; border: 2px solid #ff823a !important; border-radius: 20px !important; font-weight: bold !important; font-size: 14px !important; width: 100% !important; padding: 0.6rem 1rem !important; margin-top: 5px !important; }
    .stButton > button:has(div:contains("Düzenle")), .stButton > button:has(div:contains("✏️")) { background-color: #3498db !important; border-color: #3498db !important; }
    .stButton > button:has(div:contains("Sil")), .stButton > button:has(div:contains("🗑️")), .stButton > button:has(div:contains("❌")) { background-color: #e74c3c !important; border-color: #e74c3c !important; }
    </style>
    """, unsafe_allow_html=True)

# --- GİRİŞ EKRANI ---
if st.session_state.login_status is None:
    st.title("☀️ Yaz Tatili Takip Sistemi ☀️")
    giris_rolu = st.selectbox("Lütfen Giriş Panelini Seçin:", ["Öğrenci Girişi 🎒", "Öğretmen Girişi 🎓"])
    
    if giris_rolu == "Öğretmen Girişi 🎓":
        pw = st.text_input("Giriş Kodu (Öğretmen)", type="password", key="teacher_pw_input")
        if st.button("Giriş Yap", key="save_teacher_login"):
            if pw == "1234": st.session_state.login_status = "teacher"; st.rerun()
            else: st.error("Hatalı Giriş Kodu!")
    else:
        ogr_listesi = list(data["ogrenciler"].keys())
        if not ogr_listesi: st.warning("Sistemde henüz kayıtlı öğrenci yok.")
        else:
            secilen_ogr = st.selectbox("Adını Seç", ogr_listesi, key="student_name_select")
            ogr_pw = st.text_input("Giriş Anahtarın", key="student_pw_input")
            if st.button("Giriş Yap", key="save_student_login"):
                if data["ogrenciler"][secilen_ogr]["sifre"] == ogr_pw:
                    st.session_state.login_status = "student"; st.session_state.user = secilen_ogr; st.rerun()
                else: st.error("Hatalı Giriş Anahtarı!")

# --- ÖĞRENCİ PANELİ ---
elif st.session_state.login_status == "student":
    ogr_adi = st.session_state.user
    ogr_veri = data["ogrenciler"][ogr_adi]
    if "ilerleme" not in ogr_veri: ogr_veri["ilerleme"] = {}
    if "mesajlar" not in ogr_veri: ogr_veri["mesajlar"] = []

    st.title(f"Hoş geldin, {ogr_adi}! 🎉")
    if 'mesaj_okundu' not in st.session_state: st.session_state.mesaj_okundu = False
        
    toplam_mesaj_sayisi = len(data["genel_mesajlar"]) + len(ogr_veri["mesajlar"])
    if toplam_mesaj_sayisi > 0 and not st.session_state.mesaj_okundu:
        st.markdown(f"<div class='mesaj-uyari'>✉️ Öğretmeninizden Yeni Mesajınız Var! Sol menüden 'Mesajlar' bölümüne bakın.</div>", unsafe_allow_html=True)

    if st.session_state.kutlama == "balon": st.balloons(); st.session_state.kutlama = None
    elif st.session_state.kutlama == "kar": st.snow(); st.session_state.kutlama = None

    if haftalik_durum_hesapla(ogr_veri, su_anki_hafta) == "yildiz":
        st.success(f"⭐ **Tebrikler! {su_anki_hafta}. Hafta görevlerini başarıyla tamamladın ve Haftanın Yıldızı oldun!** ⭐")

    yildizlar = "".join(["⭐" if haftalik_durum_hesapla(ogr_veri, h) == "yildiz" else "💔" if haftalik_durum_hesapla(ogr_veri, h) == "yarim" else "🤍" for h in range(1, 11)])
    st.markdown(f"<div class='yildiz-seridi'>{yildizlar}</div>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("Menü", ["🎯 Bu Haftaki Görevlerim", "📊 Geçmiş Ödevlerim", f"✉️ Mesajlar ({toplam_mesaj_sayisi})", "🚪 Çıkış Yap"])

    if menu == "🎯 Bu Haftaki Görevlerim":
        st.markdown("### 📅 Ödev Girişi Yapılacak Hafta")
        secilen_calisma_haftasi = st.selectbox("Çalışmasını eklemek veya tamamlamak istediğiniz haftayı seçin:", list(range(1, 11)), index=su_anki_hafta-1)
        h_str = str(secilen_calisma_haftasi)
        if h_str not in ogr_veri["ilerleme"]: ogr_veri["ilerleme"][h_str] = {"fasikuller": [False]*4, "kitaplar": [], "deyimler": []}
        current_data = ogr_veri["ilerleme"][h_str]

        st.subheader(f"📚 {secilen_calisma_haftasi}. Hafta Fasikül Takibi")
        f1 = st.checkbox(f"{KITAP_ISIMLERI[0]} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][0])
        f2 = st.checkbox(f"{KITAP_ISIMLERI[1]} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][1])
        f3 = st.checkbox(f"{KITAP_ISIMLERI[2]} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][2])
        f4 = st.checkbox(f"{KITAP_ISIMLERI[3] if len(KITAP_ISIMLERI)>3 else 'Fasikül 4'} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][3])
        
        if st.button("Fasikül Durumunu Kaydet", key="fasikul_save_btn"):
            current_data["fasikuller"] = [f1, f2, f3, f4]
            veri_kaydet(data); st.session_state.kutlama = "balon"; st.rerun()

        st.divider()
        st.subheader(f"📖 {secilen_calisma_haftasi}. Hafta Kitap Okuma Takibi (En Az 2 Kitap)")
        st.write(f"Seçilen haftada okunan kitap sayısı: **{len(current_data.get('kitaplar', []))}**")
        
        k_ad = st.text_input("Okuduğun Kitabın Adı", key="k_ad_input_field")
        k_sayfa = st.number_input("Sayfa Sayısı", min_value=1, value=50, key="k_sayfa_input_field")
        k_foto = st.file_uploader("📝 Okuma Defteri Sayfa Fotoğrafı", type=["jpg", "jpeg", "png"], key="k_foto_input_field")
        
        if st.button("Kitap Girişini Kaydet 💾", key="kitap_save_direct_btn"):
            if k_ad:
                if k_foto is not None:
                    foto_b64 = base64.b64encode(k_foto.read()).decode('utf-8')
                    current_data["kitaplar"].append({"ad": k_ad, "sayfa": k_sayfa, "foto": foto_b64, "tarih": str(datetime.now().date())})
                    veri_kaydet(data)
                    st.session_state.kutlama = "kar"
                    st.rerun()
                else: st.error("⚠️ Lütfen defter sayfasının fotoğrafını ekleyin!")
            else: st.error("Lütfen kitap adını boş bırakmayın!")

        if current_data["kitaplar"]:
            for idx, k in enumerate(current_data["kitaplar"]):
                c_k1, c_k2, c_k3 = st.columns([3, 1, 1])
                with c_k1: st.write(f"📖 {k['ad']} ({k['sayfa']} S.)")
                with c_k2:
                    if st.button("Düzenle ✏️", key=f"edit_k_btn_{idx}"): st.session_state[f"editing_k_now_{idx}"] = True
                with c_k3:
                    if st.button("Sil 🗑️", key=f"sil_k_{idx}"): current_data["kitaplar"].pop(idx); veri_kaydet(data); st.rerun()
                
                if st.session_state.get(f"editing_k_now_{idx}", False):
                    with st.container():
                        st.markdown("<div class='edit-box'>", unsafe_allow_html=True)
                        yeni_k_ad = st.text_input("Yeni Kitap Adı", value=k['ad'], key=f"new_kad_{idx}")
                        yeni_k_sayfa = st.number_input("Yeni Sayfa Sayısı", min_value=1, value=k['sayfa'], key=f"new_ksayfa_{idx}")
                        yeni_k_foto = st.file_uploader("Yeni Defter Sayfası Fotoğrafı (Değiştirmek istemiyorsanız boş bırakın)", type=["jpg", "jpeg", "png"], key=f"new_kfoto_up_{idx}")
                        
                        if st.button("Değişiklikleri Kaydet", key=f"edit_save_k_change_{idx}"):
                            current_data["kitaplar"][idx]["ad"] = yeni_k_ad
                            current_data["kitaplar"][idx]["sayfa"] = yeni_k_sayfa
                            if yeni_k_foto is not None:
                                current_data["kitaplar"][idx]["foto"] = base64.b64encode(yeni_k_foto.read()).decode('utf-8')
                            veri_kaydet(data)
                            st.session_state[f"editing_k_now_{idx}"] = False
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        st.subheader(f"🗣️ {secilen_calisma_haftasi}. Hafta Deyim ve Atasözü Girişi (En Az 3 Adet)")
        st.write(f"Seçilen haftada öğrenilen deyim/atasözü sayısı: **{len(current_data.get('deyimler', []))}**")
        
        d_tur = st.selectbox("Tür", ["Deyim", "Atasözü"], key="d_tur_input_field")
        d_ad = st.text_input("Deyim / Atasözü Adı", key="d_ad_input_field")
        d_foto = st.file_uploader("📝 Defter Sayfa Fotoğrafı", type=["jpg", "jpeg", "png"], key="d_foto_input_field")
        
        if st.button("Deyimi Kaydet 💾", key="deyim_save_direct_btn"):
            if d_ad:
                if d_foto is not None:
                    dfoto_b64 = base64.b64encode(d_foto.read()).decode('utf-8')
                    current_data["deyimler"].append({"tur": d_tur, "ad": d_ad, "foto": dfoto_b64})
                    veri_kaydet(data)
                    st.session_state.kutlama = "kar"
                    st.rerun()
                else: st.error("⚠️ Lütfen defter sayfasının fotoğrafını ekleyin!")
            else: st.error("Lütfen deyim veya atasözü adını boş bırakmayın!")

        if current_data["deyimler"]:
            for idx, d in enumerate(current_data["deyimler"]):
                c_d1, c_d2, c_d3 = st.columns([3, 1, 1])
                with c_d1: st.write(f"💡 {d['ad']} ({d.get('tur','Deyim')})")
                with c_d2:
                    if st.button("Düzenle ✏️", key=f"edit_d_btn_{idx}"): st.session_state[f"editing_d_now_{idx}"] = True
                with c_d3:
                    if st.button("Sil 🗑️", key=f"sil_d_{idx}"): current_data["deyimler"].pop(idx); veri_kaydet(data); st.rerun()
                
                if st.session_state.get(f"editing_d_now_{idx}", False):
                    with st.container():
                        st.markdown("<div class='edit-box'>", unsafe_allow_html=True)
                        yeni_d_tur = st.selectbox("Yeni Tür", ["Deyim", "Atasözü"], index=0 if d.get('tur','Deyim')=="Deyim" else 1, key=f"new_dtur_{idx}")
                        yeni_d_ad = st.text_input("Yeni Adı", value=d['ad'], key=f"new_dad_{idx}")
                        yeni_d_foto = st.file_uploader("Yeni Defter Fotoğrafı (Değiştirmek istemiyorsanız boş bırakın)", type=["jpg", "jpeg", "png"], key=f"new_dfoto_up_{idx}")
                        
                        if st.button("Değişiklikleri Kaydet", key=f"edit_save_d_change_{idx}"):
                            current_data["deyimler"][idx]["tur"] = yeni_d_tur
                            current_data["deyimler"][idx]["ad"] = yeni_d_ad
                            if yeni_d_foto is not None:
                                current_data["deyimler"][idx]["foto"] = base64.b64encode(yeni_d_foto.read()).decode('utf-8')
                            veri_kaydet(data)
                            st.session_state[f"editing_d_now_{idx}"] = False
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "📊 Geçmiş Ödevlerim":
        for h_no in sorted([int(x) for x in ogr_veri["ilerleme"].keys()]):
            with st.expander(f"📅 {h_no}. Hafta Detayları", expanded=False):
                if st.button(f"🚨 {h_no}. Haftayı Komple Sil", key=f"komple_sil_{h_no}"):
                    ogr_veri["ilerleme"].pop(str(h_no)); veri_kaydet(data); st.rerun()
                h_veri = ogr_veri["ilerleme"][str(h_no)]
                for f_idx, b_dur in enumerate(h_veri.get("fasikuller", [False]*4)): st.write(f"- {KITAP_ISIMLERI[f_idx]}: {'✅' if b_dur else '❌'}")
                
                for k in h_veri.get("kitaplar", []):
                    st.write(f"- 📖 **{k['ad']}** ({k.get('sayfa', 50)} S.)")
                    if k.get("foto"):
                        try: st.image(base64.b64decode(k["foto"]), width=280)
                        except: st.caption("📸 Resim yükleniyor veya formatı hatalı.")
                        
                for d in h_veri.get("deyimler", []):
                    st.write(f"- 💡 **{d['ad']}** ({d.get('tur', 'Deyim')})")
                    if d.get("foto"):
                        try: st.image(base64.b64decode(d["foto"]), width=280)
                        except: st.caption("📸 Resim yükleniyor veya formatı hatalı.")

    elif menu.startswith("✉️ Mesajlar"):
        st.session_state.mesaj_okundu = True
        for m in reversed(data["genel_mesajlar"]): st.markdown(f"<div class='mesaj-kutusu'><b>📢 Sınıf:</b> {m['mesaj']}</div>", unsafe_allow_html=True)
        for m in reversed(ogr_veri["mesajlar"]): st.markdown(f"<div class='mesaj-kutusu' style='border-left-color: #e67e22;'><b>🔒 Özel:</b> {m['mesaj']}</div>", unsafe_allow_html=True)

    elif menu == "🚪 Çıkış Yap": st.session_state.login_status = None; st.rerun()

# --- ÖĞRETMEN PANELİ ---
elif st.session_state.login_status == "teacher":
    st.title("🎓 Öğretmen Yönetim Paneli")
    st.sidebar.header("⚙️ Sistem Ayarları")
    t_baslangic = st.sidebar.date_input("Yaz Tatili Başlangıç Tarihi", value=datetime.strptime(data["ayarlar"]["tatil_baslangic"], "%Y-%m-%d"))
    if str(t_baslangic) != data["ayarlar"]["tatil_baslangic"]:
        data["ayarlar"]["tatil_baslangic"] = str(t_baslangic)
        veri_kaydet(data); st.rerun()
        
    MENU_LISTESI = ["📊 Haftalık Özet Raporu", "🔍 Öğrenci Detaylı Analizi", "✉️ Mesaj Gönderme Paneli", "📋 Sınıf Listesi & Şifreler", "➕ Toplu Öğrenci Ekle", "🚪 Çıkış Yap"]
    
    if st.session_state.ogretmen_alt_menu not in MENU_LISTESI:
        st.session_state.ogretmen_alt_menu = "📊 Haftalık Özet Raporu"
        
    menu = st.sidebar.radio("İşlem Menüsü", MENU_LISTESI, index=MENU_LISTESI.index(st.session_state.ogretmen_alt_menu))
    if menu != st.session_state.ogretmen_alt_menu: st.session_state.hizli_mesaj_onay = False; st.session_state.ogretmen_alt_menu = menu

    if menu == "📊 Haftalık Özet Raporu":
        st.subheader("📈 Sınıf Haftalık Durum Özeti")
        secilen_rapor_haftasi = st.selectbox("Hafta Seç", list(range(1, 11)), index=su_anki_hafta-1)
        y_list, yar_list, h_list = [], [], []
        for ogr, v in data["ogrenciler"].items():
            durum = haftalik_durum_hesapla(v, secilen_rapor_haftasi)
            if durum == "yildiz": y_list.append(ogr)
            elif durum == "yarim": yar_list.append(ogr)
            else: h_list.append(ogr)
        st.success(f"⭐ **Haftanın Yıldızları ({len(y_list)}):**")
        for o in y_list:
            if st.button(f"✅ {o}", key=f"lnk_y_{o}"): st.session_state.secilen_detay_ogrenci = o; st.session_state.ogretmen_alt_menu = "🔍 Öğrenci Detaylı Analizi"; st.rerun()
        st.warning(f"💔 **Eksik Görevi Olanlar ({len(yar_list)}):**")
        for o in yar_list:
            if st.button(f"⚠️ {o}", key=f"lnk_yar_{o}"): st.session_state.secilen_detay_ogrenci = o; st.session_state.ogretmen_alt_menu = "🔍 Öğrenci Detaylı Analizi"; st.rerun()
        st.error(f"🤍 **Hiç Giriş Yapmayanlar ({len(h_list)}):**")
        for o in h_list:
            if st.button(f"❌ {o}", key=f"lnk_h_{o}"): st.session_state.secilen_detay_ogrenci = o; st.session_state.ogretmen_alt_menu = "🔍 Öğrenci Detaylı Analizi"; st.rerun()

    elif menu == "✉️ Mesaj Gönderme Paneli":
        st.subheader("✉️ Öğrenci Mesaj ve Hatırlatma Yönetimi")
        mesaj_hedefi = st.selectbox("Mesaj Kimlere Gitsin?", ["Tüm Sınıfa (Genel Duyuru) 📢", "Belirli Bir Öğrenciye Özel 🔒"])
        mesaj_metni = st.text_area("Mesajınızı Yazın:")
        if mesaj_hedefi == "Belirli Bir Öğrenciye Özel 🔒": 
            hedef_ogr = st.selectbox("Öğrenci Seçin:", list(data["ogrenciler"].keys()))
        if st.button("Mesajı Gönder"):
            if mesaj_metni.strip():
                obj = {"tarih": datetime.now().strftime("%d.%m.%Y %H:%M"), "mesaj": mesaj_metni.strip()}
                if mesaj_hedefi.startswith("Tüm Sınıfa"): data["genel_mesajlar"].append(obj)
                else: data["ogrenciler"][hedef_ogr]["mesajlar"].append(obj)
                veri_kaydet(data); st.success("Mesaj başarıyla iletildi!")

    elif menu == "📋 Gönderilen Mesaj Geçmişi":
        st.subheader("📋 Gönderilen Mesajların Yönetimi & Geçmişi")
        sekme1, sekme2 = st.tabs(["📢 Genel Sınıf Duyuruları", "🔒 Öğrencilere Özel Mesajlar"])
        
        with sekme1:
            st.markdown("#### Sınıf Geneline Ortak Gönderilen Duyurular")
            if data.get("genel_mesajlar"):
                for idx, m in enumerate(list(data["genel_mesajlar"])):
                    st.markdown(f"<div class='mesaj-kutusu'><b>📅 Tarih/Saat:</b> {m['tarih']}<br><b>💬 Duyuru:</b> {m['mesaj']}</div>", unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([1, 6])
                    with c1:
                        if st.button("Sil 🗑️", key=f"del_genel_msg_{idx}"):
                            data["genel_mesajlar"].pop(idx)
                            veri_kaydet(data); st.rerun()
                    with c2:
                        if st.button("Düzenle ✏️", key=f"edit_genel_msg_{idx}"):
                            st.session_state[f"editing_genel_msg_{idx}"] = True
                            
                    if st.session_state.get(f"editing_genel_msg_{idx}", False):
                        yeni_duyuru_metni = st.text_area("Mesajı Düzenleyin:", value=m['mesaj'], key=f"txt_genel_msg_{idx}")
                        if st.button("Duyuruyu Güncelle ✅", key=f"save_genel_msg_{idx}"):
                            data["genel_mesajlar"][idx]["mesaj"] = yeni_duyuru_metni.strip()
                            veri_kaydet(data)
                            st.session_state[f"editing_genel_msg_{idx}"] = False
                            st.rerun()
                    st.divider()
            else: st.caption("Henüz sınıf geneline gönderilmiş ortak duyuru bulunmuyor.")
                
        with sekme2:
            st.markdown("#### Öğrencilerin Şahsına Özel Gönderilen Hatırlatmalar")
            ozel_mesaj_var_mi = False
            
            for ogr_isim, ogr_kutu in data["ogrenciler"].items():
                if ogr_kutu.get("mesajlar"):
                    ozel_mesaj_var_mi = True
                    st.markdown(f"##### 🎒 {ogr_isim} Öğrencisine Ait Mesajlar")
                    
                    for idx, m in enumerate(list(ogr_kutu["mesajlar"])):
                        st.markdown(f"<div class='mesaj-kutusu' style='border-left-color: #e67e22;'><b>📅 Tarih/Saat:</b> {m['tarih']}<br><b>💬 Hatırlatma:</b> {m['mesaj']}</div>", unsafe_allow_html=True)
                        
                        c1, c2 = st.columns([1, 6])
                        with c1:
                            if st.button("Sil 🗑️", key=f"del_ozel_{ogr_isim}_{idx}"):
                                data["ogrenciler"][ogr_isim]["mesajlar"].pop(idx)
                                veri_kaydet(data); st.rerun()
                        with c2:
                            if st.button("Düzenle ✏️", key=f"edit_ozel_{ogr_isim}_{idx}"):
                                st.session_state[f"editing_ozel_{ogr_isim}_{idx}"] = True
                                
                        if st.session_state.get(f"editing_ozel_{ogr_isim}_{idx}", False):
                            yeni_ozel_metni = st.text_area("Özel Mesajı Düzenleyin:", value=m['mesaj'], key=f"txt_ozel_{ogr_isim}_{idx}")
                            if st.button("Özel Mesajı Güncelle ✅", key=f"save_ozel_{ogr_isim}_{idx}"):
                                data["ogrenciler"][ogr_isim]["mesajlar"][idx]["mesaj"] = yeni_ozel_metni.strip()
                                veri_kaydet(data)
                                st.session_state[f"editing_ozel_{ogr_isim}_{idx}"] = False
                                st.rerun()
                        st.write("")
                    st.divider()
            
            if not ozel_mesaj_var_mi: st.caption("Henüz hiçbir studentöğrenciye özel hatırlatma mesajı gönderilmemiş.")

    elif menu == "🔍 Öğrenci Detaylı Analizi":
        ogr_secenekleri = list(data["ogrenciler"].keys())
        if ogr_secenekleri:
            default_idx = 0
            if st.session_state.secilen_detay_ogrenci in ogr_secenekleri: 
                default_idx = ogr_secenekleri.index(st.session_state.secilen_detay_ogrenci)
            
            secilen_detay_ogr = st.selectbox("İncelenecek Öğrenciyi Seçin", ogr_secenekleri, index=default_idx)
            if secilen_detay_ogr != st.session_state.secilen_detay_ogrenci:
                st.session_state.hizli_mesaj_onay = False
                st.session_state.secilen_detay_ogrenci = secilen_detay_ogr
                st.rerun()
                
            o_veri = data["ogrenciler"][secilen_detay_ogr]
            if st.session_state.hizli_mesaj_onay: st.success("📬 Özel hatırlatma başarıyla gönderildi! 🔒")
            hizli_msg = st.text_input("Hızlı Mesaj:")
            if st.button("Hızlı Mesajı İlet"):
                if hizli_msg.strip():
                    o_veri["mesajlar"].append({"tarih": datetime.now().strftime("%d.%m.%Y %H:%M"), "mesaj": hizli_msg.strip()})
                    veri_kaydet(data); st.session_state.hizli_mesaj_onay = True; st.rerun()
                    
            for h_no in sorted([int(x) for x in o_veri.get("ilerleme", {}).keys()]):
                with st.expander(f"📅 {h_no}. Hafta Kayıtları", expanded=True):
                    detay_h_veri = o_veri["ilerleme"][str(h_no)]
                    for f_idx, b_dur in enumerate(detay_h_veri.get("fasikuller", [False]*4)): st.write(f"- {KITAP_ISIMLERI[f_idx]}: {'✅' if b_dur else '❌'}")
                    
                    for k in detay_h_veri.get("kitaplar", []):
                        st.write(f"- 📖 **{k['ad']}** ({k.get('sayfa', 50)} S.)")
                        if k.get("foto"):
                            try: st.image(base64.b64decode(k["foto"]), width=320)
                            except: st.caption("📸 Resim yükleniyor veya formatı hatalı.")
                            
                    for d in detay_h_veri.get("deyimler", []):
                        st.write(f"- 💡 **{d['ad']}** ({d.get('tur', 'Deyim')})")
                        if d.get("foto"):
                            try: st.image(base64.b64decode(d["foto"]), width=320)
                            except: st.caption("📸 Resim yükleniyor veya formatı hatalı.")

    elif menu == "📋 Sınıf Listesi & Şifreler":
        for isim in list(data["ogrenciler"].keys()):
            icerik = data["ogrenciler"][isim]
            yeni_isim = st.text_input("Öğrenci Adı", value=isim, key=f"edit_name_{isim}")
            yeni_sifre = st.text_input("Giriş Kodu", value=icerik['sifre'], key=f"edit_pw_{isim}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Güncelle ✏️", key=f"up_{isim}"):
                    if yeni_isim != isim: data["ogrenciler"][yeni_isim] = {"sifre": yeni_sifre, "ilerleme": icerik.get("ilerleme",{}), "mesajlar": icerik.get("mesajlar",[])}; data["ogrenciler"].pop(isim)
                    else: data["ogrenciler"][isim]["sifre"] = yeni_sifre
                    veri_kaydet(data); st.rerun()
            with c2:
                if st.button("Öğrenciyi Sil ❌", key=f"del_{isim}"): data["ogrenciler"].pop(isim); veri_kaydet(data); st.rerun()

    elif menu == "➕ Toplu Öğrenci Ekle":
        yeni_liste = st.text_area("Örnek: Ahmet Yılmaz,123")
        if st.button("Sınıf Listesine Ekle", key="mass_save_students"):
            if yeni_liste:
                for satir in yeni_liste.split("\n"):
                    cleaned_satir = satir.replace("\r", "").strip()
                    if "," in cleaned_satir:
                        isim, sifre = cleaned_satir.split(",")
                        data["ogrenciler"][isim.strip()] = {"sifre": sifre.strip(), "ilerleme": {}, "mesajlar": []}
                veri_kaydet(data); st.success("Sınıf listesi temizlenerek eklendi!"); st.rerun()

    elif menu == "🚪 Çıkış Yap": st.session_state.login_status = None; st.rerun()
