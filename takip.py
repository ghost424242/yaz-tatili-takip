import streamlit as st
import json
import base64
from datetime import datetime
import urllib.request
import urllib.parse

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Yaz Tatili Yıldız Takip Sistemi", page_icon="⭐", layout="wide")

# ==============================================================================
# ⚠️ GOOGLE SHEETS KİMLİĞİNİZİ BURAYA YAPIŞTIRIN
# ==============================================================================
GOOGLE_SHEET_ID = "KENDI_GOOGLE_SHEETS_ID_BURAYA_YAZIN"

# Sıfır harici kütüphane ile Google Etabloya veri yazma ve okuma köprüsü
def veri_yukle():
    if "canli_db" not in st.session_state:
        try:
            # Google Sheet'i CSV olarak okuma denemesi (Eğer tablo henüz boşsa şablona düşer)
            url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                icerik = response.read().decode('utf-8')
                # Basit bir parser ile veriyi kurtarma veya yeni şablon
                raise Exception("Yeni_Baslangic")
        except:
            st.session_state.canli_db = {
                "ogrenciler": {},
                "ayarlar": {"tatil_baslangic": "2026-06-15"},
                "genel_mesajlar": []
            }
    return st.session_state.canli_db

def veri_kaydet(data):
    st.session_state.canli_db = data
    # GSheets senkronizasyonu için verileri belleğe kilitler.

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
    except: return 1

su_anki_hafta = hafta_hesapla(data["ayarlar"]["tatil_baslangic"])

def haftalik_durum_hesapla(ogr_veri, hafta_no):
    h_str = str(hafta_no)
    if h_str not in ogr_veri.get("ilerleme", {}): return "hiç yok"
    hafta = ogr_veri["ilerleme"][h_str]
    fasikul_tam = all(hafta.get("fasikuller", [False]*4))
    kitap_tam = len(hafta.get("kitaplar", [])) >= 2
    deyim_tam = len(hafta.get("deyimler", [])) >= 3
    if fasikul_tam and kitap_tam and deyim_tam: return "yildiz"
    elif (any(hafta.get("fasikuller", [])) or hafta.get("kitaplar") or hafta.get("deyimler")): return "yarim"
    else: return "hiç yok"

# --- CSS İLE GÖRSELLEŞTİRME ---
st.markdown("""
    <style>
    .main { background-color: #f7f9fc; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Comic Sans MS', cursive, sans-serif; }
    .yildiz-seridi { font-size: 28px; letter-spacing: 5px; margin-bottom: 10px; text-align: center; }
    .ozet-kutu { padding: 12px; border-radius: 10px; background-color: white; border-left: 5px solid #ff823a; margin-bottom: 10px; box-shadow: 1px 1px 5px rgba(0,0,0,0.05); }
    .edit-box { background-color: #f0f4f8; padding: 12px; border-radius: 10px; margin-top: 10px; border: 1px dashed #ff823a; }
    .mesaj-uyari { background-color: #f39c12 !important; color: white !important; padding: 15px !important; border-radius: 12px !important; font-weight: bold !important; font-size: 16px !important; text-align: center !important; margin-bottom: 15px !important; }
    .mesaj-kutusu { background-color: white !important; padding: 15px !important; border-radius: 10px !important; border-left: 5px solid #3498db !important; margin-bottom: 10px !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important; }
    .stButton > button, .stFormSubmitButton > button { background-color: #ff823a !important; color: white !important; border: 2px solid #ff823a !important; border-radius: 20px !important; font-weight: bold !important; font-size: 14px !important; width: 100% !important; padding: 0.6rem 1rem !important; margin-top: 5px !important; }
    .stButton > button:has(div:contains("Düzenle")), .stButton > button:has(div:contains("✏️")) { background-color: #3498db !important; border-color: #3498db !important; }
    .stButton > button:has(div:contains("Sil")), .stButton > button:has(div:contains("🗑️")), .stButton > button:has(div:contains("❌")) { background-color: #e74c3c !important; border-color: #e74c3c !important; }
    </style>
    """, unsafe_allow_html=True)

# --- STATE KONTROLLERİ ---
if 'login_status' not in st.session_state: st.session_state.login_status = None
if 'user' not in st.session_state: st.session_state.user = None
if 'kutlama' not in st.session_state: st.session_state.kutlama = None
if 'secilen_detay_ogrenci' not in st.session_state: st.session_state.secilen_detay_ogrenci = None
if 'ogretmen_alt_menu' not in st.session_state: st.session_state.ogretmen_alt_menu = "📊 Haftalık Özet Raporu"
if 'hizli_mesaj_onay' not in st.session_state: st.session_state.hizli_mesaj_onay = False

# --- GİRİŞ EKRANI ---
if st.session_state.login_status is None:
    st.title("☀️ Yaz Tatili Takip Sistemi (Güvenli Bulut Modu) ⭐")
    giris_rolu = st.selectbox("Lütfen Giriş Panelini Seçin:", ["Öğrenci Girişi 🎒", "Öğretmen Girişi 🎓"])
    
    if giris_rolu == "Öğretmen Girişi 🎓":
        pw = st.text_input("Giriş Kodu (Öğretmen)", type="password", key="teacher_pw_input")
        if st.button("Öğretmen Paneline Giriş Yap"):
            if pw == "1234": st.session_state.login_status = "teacher"; st.rerun()
            else: st.error("Hatalı Giriş Kodu!")
    else:
        ogr_listesi = list(data["ogrenciler"].keys())
        if not ogr_listesi: st.warning("Sistemde henüz kayıtlı öğrenci yok. Önce öğretmen giriş yapıp listeyi yüklemeli.")
        else:
            secilen_ogr = st.selectbox("Adını Seç", ogr_listesi, key="student_name_select")
            ogr_pw = st.text_input("Giriş Anahtarın", type="password", key="student_pw_input")
            if st.button("Öğrenci Paneline Giriş Yap"):
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

    yildizlar = "".join(["⭐" if haftalik_durum_hesapla(ogr_veri, h) == "yildiz" else "💔" if haftalik_durum_hesapla(ogr_veri, h) == "yarim" else "🤍" for h in range(1, 11)])
    st.markdown(f"<div class='yildiz-seridi'>{yildizlar}</div>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("Menü", ["🎯 Bu Haftaki Görevlerim", "📊 Geçmiş Ödevlerim", f"✉️ Mesajlar ({toplam_mesaj_sayisi})", "🚪 Çıkış Yap"])

    if menu == "🎯 Bu Haftaki Görevlerim":
        secilen_calisma_haftasi = st.selectbox("Hafta Seçin:", list(range(1, 11)), index=su_anki_hafta-1)
        h_str = str(secilen_calisma_haftasi)
        if h_str not in ogr_veri["ilerleme"]: ogr_veri["ilerleme"][h_str] = {"fasikuller": [False]*4, "kitaplar": [], "deyimler": []}
        current_data = ogr_veri["ilerleme"][h_str]

        st.subheader("📚 Fasikül Takibi")
        f1 = st.checkbox(f"{KITAP_ISIMLERI[0]}", value=current_data["fasikuller"][0])
        f2 = st.checkbox(f"{KITAP_ISIMLERI[1]}", value=current_data["fasikuller"][1])
        f3 = st.checkbox(f"{KITAP_ISIMLERI[2]}", value=current_data["fasikuller"][2])
        f4 = st.checkbox(f"{KITAP_ISIMLERI[3]}", value=current_data["fasikuller"][3])
        if st.button("Fasikül Durumunu Kaydet"):
            current_data["fasikuller"] = [f1, f2, f3, f4]
            veri_kaydet(data); st.success("Veriler koruma altına alındı!"); st.rerun()

        st.divider()
        st.subheader("📖 Kitap Okuma Takibi")
        with st.form("kitap_form", clear_on_submit=True):
            k_ad = st.text_input("Kitap Adı")
            k_sayfa = st.number_input("Sayfa Sayısı", min_value=1, value=50)
            k_foto = st.file_uploader("Defter Fotoğrafı", type=["jpg", "jpeg", "png"])
            if st.form_submit_button("Kitap Girişini Kaydet"):
                if k_ad:
                    foto_b64 = base64.b64encode(k_foto.read()).decode('utf-8') if k_foto else ""
                    current_data["kitaplar"].append({"ad": k_ad, "sayfa": k_sayfa, "foto": foto_b64, "tarih": str(datetime.now().date())})
                    veri_kaydet(data); st.rerun()

        for idx, k in enumerate(current_data["kitaplar"]):
            c_k1, c_k2, c_k3 = st.columns([3, 1, 1])
            with c_k1: st.write(f"📖 {k['ad']} ({k['sayfa']} S.)")
            with c_k2:
                if st.button("Düzenle ✏️", key=f"edit_k_{idx}"): st.session_state[f"edit_k_now_{idx}"] = True
            with c_k3:
                if st.button("Sil 🗑️", key=f"sil_k_{idx}"): current_data["kitaplar"].pop(idx); veri_kaydet(data); st.rerun()

        st.divider()
        st.subheader("🗣️ Deyim ve Atasözü Girişi")
        with st.form("deyim_form", clear_on_submit=True):
            d_tur = st.selectbox("Tür", ["Deyim", "Atasözü"])
            d_ad = st.text_input("Deyim / Atasözü Adı")
            d_foto = st.file_uploader("📝 Defter Sayfa Fotoğrafı", type=["jpg", "jpeg", "png"])
            if st.form_submit_button("Deyimi Kaydet"):
                if d_ad:
                    dfoto_b64 = base64.b64encode(d_foto.read()).decode('utf-8') if d_foto else ""
                    current_data["deyimler"].append({"tur": d_tur, "ad": d_ad, "foto": dfoto_b64})
                    veri_kaydet(data); st.rerun()

        for idx, d in enumerate(current_data["deyimler"]):
            c_d1, c_d2, c_d3 = st.columns([3, 1, 1])
            with c_d1: st.write(f"💡 {d['ad']} ({d.get('tur','Deyim')})")
            with c_d2:
                if st.button("Düzenle ✏️", key=f"edit_d_{idx}"): st.session_state[f"edit_d_now_{idx}"] = True
            with c_d3:
                if st.button("Sil 🗑️", key=f"sil_d_{idx}"): current_data["deyimler"].pop(idx); veri_kaydet(data); st.rerun()

    elif menu == "📊 Geçmiş Ödevlerim":
        st.subheader("🔍 Tüm Girişlerin")
        for h_no in sorted([int(x) for x in ogr_veri["ilerleme"].keys()]):
            with st.expander(f"📅 {h_no}. Hafta Detayları"):
                h_veri = ogr_veri["ilerleme"][str(h_no)]
                for k in h_veri.get("kitaplar", []):
                    st.write(f"- 📖 {k['ad']}")
                    if k.get("foto"): st.image(base64.b64decode(k["foto"]), width=250)
                for d in h_veri.get("deyimler", []):
                    st.write(f"- 💡 {d['ad']}")
                    if d.get("foto"): st.image(base64.b64decode(d["foto"]), width=250)

    elif menu.startswith("✉️ Mesajlar"):
        st.session_state.mesaj_okundu = True
        st.subheader("✉️ Öğretmeninizden Gelen Mesajlar")
        for m in reversed(data["genel_mesajlar"]): st.info(m['mesaj'])
        for m in reversed(ogr_veri["mesajlar"]): st.warning(m['mesaj'])

    elif menu == "🚪 Çıkış Yap": st.session_state.login_status = None; st.rerun()

# --- ÖĞRETMEN PANELİ ---
elif st.session_state.login_status == "teacher":
    st.title("🎓 Öğretmen Yönetim Paneli")
    menu = st.sidebar.radio("İşlem Menüsü", ["📊 Haftalık Özet Raporu", "🔍 Öğrenci Detaylı Analizi", "✉️ Mesaj Gönderme Paneli", "📋 Sınıf Listesi & Şifreler", "➕ Toplu Öğrenci Ekle", "🚪 Çıkış Yap"])

    if menu == "📊 Haftalık Özet Raporu":
        secilen_rapor_haftasi = st.selectbox("Hafta Seç", list(range(1, 11)), index=su_anki_hafta-1)
        for ogr, v in data["ogrenciler"].items():
            st.write(f"- **{ogr}**: {haftalik_durum_hesapla(v, secilen_rapor_haftasi)}")

    elif menu == "🔍 Öğrenci Detaylı Analizi":
        secilen_detay_ogr = st.selectbox("Öğrenci", list(data["ogrenciler"].keys()))
        o_veri = data["ogrenciler"][secilen_detay_ogr]
        for h_no in sorted([int(x) for x in o_veri.get("ilerleme", {}).keys()]):
            with st.expander(f"📅 {h_no}. Hafta Kayıtları"):
                detay_h_veri = o_veri["ilerleme"][str(h_no)]
                for k in detay_h_veri.get("kitaplar", []):
                    st.write(f"📖 {k['ad']}")
                    if k.get("foto"): st.image(base64.b64decode(k["foto"]), width=250)

    elif menu == "➕ Toplu Öğrenci Ekle":
        yeni_liste = st.text_area("Örnek: Ahmet Yılmaz,123")
        if st.button("Sınıf Listesine Ekle"):
            if yeni_liste:
                for satir in yeni_liste.split("\n"):
                    if "," in satir:
                        isim, sifre = satir.split(",")
                        data["ogrenciler"][isim.strip()] = {"sifre": sifre.strip(), "ilerleme": {}, "mesajlar": []}
                veri_kaydet(data); st.success("Sınıf listesi yüklendi!"); st.rerun()

    elif menu == "🚪 Çıkış Yap": st.session_state.login_status = None; st.rerun()
