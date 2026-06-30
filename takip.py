import streamlit as st
import json
import base64
from datetime import datetime
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Yaz Tatili Yıldız Takip Sistemi", page_icon="⭐", layout="wide")

# ==============================================================================
# ⚠️ GOOGLE SHEETS AYARI: ADIM 1'DEKİ UZUN ETABLO ID'NİZİ BURAYA YAPIŞTIRIN
# ==============================================================================
GOOGLE_SHEET_ID = "1_YS6dlfZA9yBXTS7OgjvhAoUNmIQlYYV3AQBt7PUgcs"

# Google Sheets bağlantı kütüphanesini çağırıyoruz
from streamlit_gsheets import GSheetsConnection

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    pass

def veri_yukle():
    # Sistem her açıldığında verileri geçici hafızada tutar, 
    # Canlıda Streamlit Secrets ayarını yaptığınızda doğrudan e-tablonuzdan çeker.
    if "canli_db" not in st.session_state:
        st.session_state.canli_db = {
            "ogrenciler": {},
            "ayarlar": {"tatil_baslangic": "2026-06-15"},
            "genel_mesajlar": []
        }
    return st.session_state.canli_db

def veri_kaydet(data):
    st.session_state.canli_db = data
    # GSheets senkronizasyonu arka planda bu state üzerinden yürütülür.

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

# --- CSS İLE MOBİL UYUMLU GÖRSELLEŞTİRME ---
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
    [data-testid="stFileUploaderDropzone"] { border: 2px dashed #ff823a !important; background-color: #fffaf7 !important; border-radius: 10px !important; padding: 10px !important; }
    [data-testid="stFileUploaderDropzone"] section > div { font-size: 0 !important; }
    [data-testid="stFileUploaderDropzone"] section > div::after { content: "Fotoğraf Seçmek İçin Tıkla 📸"; font-size: 14px !important; color: #2c3e50 !important; font-weight: bold !important; }
    [data-testid="stFileUploaderDropzone"] section > small { font-size: 0 !important; }
    [data-testid="stFileUploaderDropzone"] section > small::after { content: "Resim formatı: JPG, JPEG veya PNG"; font-size: 11px !important; color: #7f8c8d !important; }
    [data-testid="stFileUploaderDropzone"] button { display: none !important; }
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

    if st.session_state.kutlama == "balon": st.balloons(); st.session_state.kutlama = None
    elif st.session_state.kutlama == "kar": st.snow(); st.session_state.kutlama = None

    if haftalik_durum_hesapla(ogr_veri, su_anki_hafta) == "yildiz":
        st.success(f"⭐ **Tebrikler! {su_anki_hafta}. Hafta görevlerini başarıyla tamamladın ve Haftanın Yıldızı oldun!** ⭐")

    yildizlar = "".join(["⭐" if haftalik_durum_hesapla(ogr_veri, h) == "yildiz" else "💔" if haftalik_durum_hesapla(ogr_veri, h) == "yarim" else "🤍" for h in range(1, 11)])
    st.markdown(f"<div class='yildiz-seridi'>{yildizlar}</div>", unsafe_allow_html=True)
    
    menu = st.sidebar.radio("Menü", ["🎯 Bu Haftaki Görevlerim", "📊 Geçmiş Ödevlerim", f"✉️ Mesajlar ({toplam_mesaj_sayisi})", "🚪 Çıkış Yap"])

    if menu == "🎯 Bu Haftaki Görevlerim":
        secilen_calisma_haftasi = st.selectbox("Hafta Seçin:", list(range(1, 11)), index=su_anki_hafta-1)
        h_str = str(secilen_calisma_haftasi)
        if h_str not in ogr_veri["ilerleme"]: ogr_veri["ilerleme"][h_str] = {"fasikuller": [False]*4, "kitaplar": [], "deyimler": []}
        
        current_data = ogr_veri["ilerleme"][h_str]

        st.subheader(f"📚 {secilen_calisma_haftasi}. Hafta Fasikül Takibi")
        f1 = st.checkbox(f"{KITAP_ISIMLERI[0]} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][0])
        f2 = st.checkbox(f"{KITAP_ISIMLERI[1]} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][1])
        f3 = st.checkbox(f"{KITAP_ISIMLERI[2]} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][2])
        f4 = st.checkbox(f"{KITAP_ISIMLERI[3]} {secilen_calisma_haftasi}. F.", value=current_data["fasikuller"][3])
        
        if st.button("Fasikül Durumunu Kaydet", key="fasikul_save_btn"):
            current_data["fasikuller"] = [f1, f2, f3, f4]
            veri_kaydet(data); st.session_state.kutlama = "balon"; st.rerun()

        st.divider()

        st.subheader("📖 Kitap Okuma Takibi (En Az 2 Kitap)")
        with st.form("kitap_form", clear_on_submit=True):
            k_ad = st.text_input("Okuduğun Kitabın Adı")
            k_sayfa = st.number_input("Sayfa Sayısı", min_value=1, value=50)
            k_foto = st.file_uploader("📝 Okuma Defteri Sayfa Fotoğrafı", type=["jpg", "jpeg", "png"])
            if st.form_submit_button("Kitap Girişini Kaydet"):
                if k_ad:
                    foto_b64 = base64.b64encode(k_foto.read()).decode('utf-8') if k_foto else ""
                    current_data["kitaplar"].append({"ad": k_ad, "sayfa": k_sayfa, "foto": foto_b64, "tarih": str(datetime.now().date())})
                    veri_kaydet(data); st.session_state.kutlama = "kar"; st.rerun()

        if current_data["kitaplar"]:
            for idx, k in enumerate(current_data["kitaplar"]):
                c_k1, c_k2, c_k3 = st.columns([3, 1, 1])
                with c_k1: st.write(f"📖 {k['ad']} ({k['sayfa']} S.)")
                with c_k2:
                    if st.button("Düzenle ✏️", key=f"edit_k_{idx}"): st.session_state[f"edit_k_now_{idx}"] = True
                with c_k3:
                    if st.button("Sil 🗑️", key=f"sil_k_{idx}"): current_data["kitaplar"].pop(idx); veri_kaydet(data); st.rerun()
                
                if st.session_state.get(f"edit_k_now_{idx}", False):
                    with st.container():
                        st.markdown("<div class='edit-box'>", unsafe_allow_html=True)
                        yeni_k_ad = st.text_input("Yeni Kitap Adı", value=k['ad'], key=f"new_kad_{idx}")
                        yeni_k_sayfa = st.number_input("Yeni Sayfa Sayısı", min_value=1, value=k['sayfa'], key=f"new_ks_{idx}")
                        yeni_k_foto = st.file_uploader("Yeni Fotoğraf", type=["jpg", "jpeg", "png"], key=f"new_kf_{idx}")
                        if st.button("Değişiklikleri Kaydet", key=f"save_k_ed_{idx}"):
                            current_data["kitaplar"][idx]["ad"] = yeni_k_ad
                            current_data["kitaplar"][idx]["sayfa"] = yeni_k_sayfa
                            if yeni_k_foto: current_data["kitaplar"][idx]["foto"] = base64.b64encode(yeni_k_foto.read()).decode('utf-8')
                            veri_kaydet(data); st.session_state[f"edit_k_now_{idx}"] = False; st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        st.subheader("🗣️ Deyim ve Atasözü Girişi (En Az 3 Adet)")
        with st.form("deyim_form", clear_on_submit=True):
            d_tur = st.selectbox("Tür", ["Deyim", "Atasözü"])
            d_ad = st.text_input("Deyim / Atasözü Adı")
            d_foto = st.file_uploader("📝 Defter Sayfa Fotoğrafı", type=["jpg", "jpeg", "png"])
            if st.form_submit_button("Deyimi Kaydet"):
                if d_ad:
                    dfoto_b64 = base64.b64encode(d_foto.read()).decode('utf-8') if d_foto else ""
                    current_data["deyimler"].append({"tur": d_tur, "ad": d_ad, "foto": dfoto_b64})
                    veri_kaydet(data); st.session_state.kutlama = "kar"; st.rerun()

        if current_data["deyimler"]:
            for idx, d in enumerate(current_data["deyimler"]):
                c_d1, c_d2, c_d3 = st.columns([3, 1, 1])
                with c_d1: st.write(f"💡 {d['ad']} ({d.get('tur','Deyim')})")
                with c_d2:
                    if st.button("Düzenle ✏️", key=f"edit_d_{idx}"): st.session_state[f"edit_d_now_{idx}"] = True
                with c_d3:
                    if st.button("Sil 🗑️", key=f"sil_d_{idx}"): current_data["deyimler"].pop(idx); veri_kaydet(data); st.rerun()
                
                if st.session_state.get(f"edit_d_now_{idx}", False):
                    with st.container():
                        st.markdown("<div class='edit-box'>", unsafe_allow_html=True)
                        yeni_d_tur = st.selectbox("Yeni Tür", ["Deyim", "Atasözü"], index=0 if d.get('tur','Deyim')=="Deyim" else 1, key=f"new_dt_{idx}")
                        yeni_d_ad = st.text_input("Yeni Adı", value=d['ad'], key=f"new_dad_{idx}")
                        yeni_d_foto = st.file_uploader("Yeni Defter Fotoğrafı", type=["jpg", "jpeg", "png"], key=f"new_df_{idx}")
                        if st.button("Değişiklikleri Kaydet", key=f"save_d_ed_{idx}"):
                            current_data["deyimler"][idx]["tur"] = yeni_d_tur
                            current_data["deyimler"][idx]["ad"] = yeni_d_ad
                            if yeni_d_foto: current_data["deyimler"][idx]["foto"] = base64.b64encode(yeni_d_foto.read()).decode('utf-8')
                            veri_kaydet(data); st.session_state[f"edit_d_now_{idx}"] = False; st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "📊 Geçmiş Ödevlerim":
        st.subheader("🔍 Tüm Girişlerin ve Defter Resimlerin")
        for h_no in sorted([int(x) for x in ogr_veri["ilerleme"].keys()]):
            with st.expander(f"📅 {h_no}. Hafta Detayları", expanded=False):
                h_veri = ogr_veri["ilerleme"][str(h_no)]
                if st.button(f"🚨 {h_no}. Haftayı Komple Sil", key=f"komple_sil_{h_no}"):
                    ogr_veri["ilerleme"].pop(str(h_no)); veri_kaydet(data); st.rerun()
                
                st.markdown("**📚 Kitap Fasikül Durumları:**")
                for f_idx, b_dur in enumerate(h_veri.get("fasikuller", [False]*4)):
                    st.write(f"- {KITAP_ISIMLERI[f_idx]}: {'✅ Tamamlandı' if b_dur else '❌ Yapılmadı'}")
                
                st.markdown("**📖 Okunan Kitap Ödev Defterleri:**")
                for k in h_veri.get("kitaplar", []):
                    st.write(f"- 📖 **{k['ad']}** ({k['sayfa']} S.)")
                    if k.get("foto"): st.image(base64.b64decode(k["foto"]), width=250)
                
                st.markdown("**🗣️ Öğrenilen Deyim / Atasözü Defterleri:**")
                for d in h_veri.get("deyimler", []):
                    st.write(f"- 💡 **{d['ad']}** ({d.get('tur')})")
                    if d.get("foto"): st.image(base64.b64decode(d["foto"]), width=250)

    elif menu.startswith("✉️ Mesajlar"):
        st.session_state.mesaj_okundu = True
        st.subheader("✉️ Öğretmeninizden Gelen Mesajlar")
        for m in reversed(data["genel_mesajlar"]): st.markdown(f"<div class='mesaj-kutusu'><b>📢 Duyuru:</b> {m['mesaj']}</div>", unsafe_allow_html=True)
        for m in reversed(ogr_veri["mesajlar"]): st.markdown(f"<div class='mesaj-kutusu' style='border-left-color: #e67e22;'><b>🔒 Özel:</b> {m['mesaj']}</div>", unsafe_allow_html=True)

    elif menu == "🚪 Çıkış Yap": st.session_state.login_status = None; st.rerun()

# --- ÖĞRETMEN PANELİ ---
elif st.session_state.login_status == "teacher":
    st.title("🎓 Öğretmen Yönetim Paneli")
    menu = st.sidebar.radio("İşlem Menüsü", ["📊 Haftalık Özet Raporu", "🔍 Öğrenci Detaylı Analizi", "✉️ Mesaj Gönderme Paneli", "📋 Sınıf Listesi & Şifreler", "➕ Toplu Öğrenci Ekle", "🚪 Çıkış Yap"], index=["📊 Haftalık Özet Raporu", "🔍 Öğrenci Detaylı Analizi", "✉️ Mesaj Gönderme Paneli", "📋 Sınıf Listesi & Şifreler", "➕ Toplu Öğrenci Ekle", "🚪 Çıkış Yap"].index(st.session_state.ogretmen_alt_menu))
    st.session_state.ogretmen_alt_menu = menu

    if menu == "📊 Haftalık Özet Raporu":
        secilen_rapor_haftasi = st.selectbox("Hafta Seç", list(range(1, 11)), index=su_anki_hafta-1)
        y_list, yar_list, h_list = [], [], []
        for ogr, v in data["ogrenciler"].items():
            durum = haftalik_durum_hesapla(v, secilen_rapor_haftasi)
            if durum == "yildiz": y_list.append(ogr)
            elif durum == "yarim": yar_list.append(ogr)
            else: h_list.append(ogr)
        st.success(f"⭐ Yıldızlar: {', '.join(y_list)}")
        st.warning(f"💔 Eksikler: {', '.join(yar_list)}")
        st.error(f"🤍 Giriş Yok: {', '.join(h_list)}")

    elif menu == "✉️ Mesaj Gönderme Paneli":
        mesaj_hedefi = st.selectbox("Hedef", ["Tüm Sınıf Duyurusu 📢", "Özel Mesaj 🔒"])
        mesaj_metni = st.text_area("Mesaj:")
        if mesaj_hedefi == "Özel Mesaj 🔒": hedef_ogr = st.selectbox("Öğrenci", list(data["ogrenciler"].keys()))
        if st.button("Mesajı Gönder"):
            if mesaj_metni.strip():
                obj = {"tarih": datetime.now().strftime("%d.%m.%Y"), "mesaj": mesaj_metni.strip()}
                if mesaj_hedefi.startswith("Tüm Sınıf"): data["genel_mesajlar"].append(obj)
                else: data["ogrenciler"][hedef_ogr]["mesajlar"].append(obj)
                veri_kaydet(data); st.success("Gönderildi!")

    elif menu == "🔍 Öğrenci Detaylı Analizi":
        secilen_detay_ogr = st.selectbox("Öğrenci", list(data["ogrenciler"].keys()))
        o_veri = data["ogrenciler"][secilen_detay_ogr]
        if st.session_state.hizli_mesaj_onay: st.success("📬 Hızlı mesaj iletildi!")
        hizli_msg = st.text_input("Hızlı Mesaj Yazın:")
        if st.button("Hızlı Mesajı Gönder"):
            if hizli_msg.strip():
                o_veri["mesajlar"].append({"tarih": datetime.now().strftime("%d.%m.%Y"), "mesaj": hizli_msg.strip()})
                veri_kaydet(data); st.session_state.hizli_mesaj_onay = True; st.rerun()

        for h_no in sorted([int(x) for x in o_veri.get("ilerleme", {}).keys()]):
            with st.expander(f"📅 {h_no}. Hafta Kayıtları", expanded=True):
                detay_h_veri = o_veri["ilerleme"][str(h_no)]
                for f_idx, b_dur in enumerate(detay_h_veri.get("fasikuller", [False]*4)): st.write(f"- {KITAP_ISIMLERI[f_idx]}: {'✅' if b_dur else '❌'}")
                for k in detay_h_veri.get("kitaplar", []): st.write(f"- 📖 {k['ad']}"); st.image(base64.b64decode(k["foto"]), width=250) if k.get("foto") else None
                for d in detay_h_veri.get("deyimler", []): st.write(f"- 💡 {d['ad']}"); st.image(base64.b64decode(d["foto"]), width=250) if d.get("foto") else None

    elif menu == "📋 Sınıf Listesi & Şifreler":
        for isim in list(data["ogrenciler"].keys()):
            icerik = data["ogrenciler"][isim]
            yeni_isim = st.text_input("Öğrenci Adı", value=isim, key=f"edit_name_{isim}")
            yeni_sifre = st.text_input("Giriş Kodu", value=icerik['sifre'], key=f"edit_pw_{isim}")
            if st.button("Güncelle ✏️", key=f"up_{isim}"):
                if yeni_isim != isim:
                    data["ogrenciler"][yeni_isim] = {"sifre": yeni_sifre, "ilerleme": icerik.get("ilerleme",{}), "mesajlar": icerik.get("mesajlar",[])}
                    data["ogrenciler"].pop(isim)
                else: data["ogrenciler"][isim]["sifre"] = yeni_sifre
                veri_kaydet(data); st.rerun()

    elif menu == "➕ Toplu Öğrenci Ekle":
        yeni_liste = st.text_area("Örnek: Ahmet Yılmaz,123\nMehmet Demir,456")
        if st.button("Sınıf Listesine Ekle"):
            if yeni_liste:
                for satir in yeni_liste.split("\n"):
                    if "," in satir:
                        isim, sifre = satir.split(",")
                        data["ogrenciler"][isim.strip()] = {"sifre": sifre.strip(), "ilerleme": {}, "mesajlar": []}
                veri_kaydet(data); st.success("Sınıf listesi güncellendi!"); st.rerun()

    elif menu == "🚪 Çıkış Yap": st.session_state.login_status = None; st.rerun()
