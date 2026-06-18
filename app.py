import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- İLK BİLEŞEN YAPILANDIRMASI ---
st.set_page_config(page_title="Araç Filo Merkezi", page_icon="🚗", layout="wide")

# Excel sayfalarıyla tam eşleşen yerel veri tabanı hedef yolları
LOCAL_FLEET = "rental business.xlsx - Fleet Master.csv"
LOCAL_DEALS = "rental business.xlsx - Rental Deals Sheet.csv"

st.sidebar.info("💾 Veri Tabanı Bağlantısı: Yerel Excel/CSV Sayfalarına Bağlandı")

# --- GÜVENLİ TAMSAYI DÖNÜŞTÜRME YARDIMCISI ---
def safe_int(value, default=100):
    """Veri tabanı alanlarından temiz tamsayı oranlarını güvenli bir şekilde çeker."""
    try:
        if pd.isna(value):
            return default
        cleaned = str(value).replace('$', '').replace(',', '').strip()
        return int(float(cleaned))
    except (ValueError, TypeError):
        return default

# --- CANLI VERİ TABANI OKUMA/YAZMA KONTROLLERİ ---
def fetch_fleet_data():
    if os.path.exists(LOCAL_FLEET):
        df = pd.read_csv(LOCAL_FLEET)
        df.columns = df.columns.str.strip()
        return df
    else:
        st.error(f"Eksik Veri Tabanı Dosyası: {LOCAL_FLEET}")
        return pd.DataFrame()

def fetch_deals_data():
    if os.path.exists(LOCAL_DEALS):
        df = pd.read_csv(LOCAL_DEALS)
        df.columns = df.columns.str.strip()
        return df
    else:
        st.error(f"Eksik Veri Tabanı Dosyası: {LOCAL_DEALS}")
        return pd.DataFrame()

def commit_to_database(target_mode, dataframe):
    dataframe_filled = dataframe.fillna("")
    file_path = LOCAL_FLEET if target_mode == "fleet" else LOCAL_DEALS
    dataframe_filled.to_csv(file_path, index=False)

# Uygulama yenilendiğinde canlı dosya durumlarını senkronize et
fleet_df = fetch_fleet_data()
deals_df = fetch_deals_data()

# --- ARAYÜZ GÖRÜNÜM SEÇENEKLERİ (ANA MENÜLER) ---
view_mode = st.radio("Arayüz Görünümünü Seçin", ["🛎️ Resepsiyon Paneli", "🛠️ Canlı Filo Durum Yöneticisi"], horizontal=True)

if view_mode == "🛎️ Resepsiyon Paneli":
    st.title("ÖN OFİS: ARAÇ UYGUNLUK KONTROLÜ")
    col_input, col_grid = st.columns([1, 2.8])
    
    with col_input:
        st.markdown("### 📅 Rezervasyon Tarih Aralığı")
        start_date = st.date_input("Başlangıç Tarihi:", datetime.today())
        num_days = st.number_input("Gün Sayısı:", min_value=1, max_value=90, value=5, step=1)
        expected_return = start_date + timedelta(days=int(num_days))
        st.info(f"🔮 **Beklenen İade Tarihi:** {expected_return.strftime('%Y-%m-%d')}")
        
        # Fleet Master veri tabanından uygun araçları filtrele
        if not fleet_df.empty and 'Status' in fleet_df.columns:
            available_cars = fleet_df[fleet_df['Status'].astype(str).str.strip() == 'Available']
        else:
            available_cars = pd.DataFrame()
            
        st.metric(label="EŞLEŞEN UYGUN ARAÇ SAYISI", value=len(available_cars))

    with col_grid:
        st.markdown("### 🚘 Dinamik Filo Envanter Matrisi")
        if available_cars.empty:
            st.warning("⚠️ Veri tabanınızda şu anda 'Uygun' olarak işaretlenmiş hiçbir araç bulunamadı.")
        else:
            # Tablo tarzı başlık sütunları
            hdr_c1, hdr_c2, hdr_c3, hdr_c4, hdr_c5, hdr_c6, hdr_c7 = st.columns([1, 1.8, 1.2, 1.5, 1.2, 1.2, 1.2])
            with hdr_c1: st.caption("⚡ **Araç ID**")
            with hdr_c2: st.caption("🚗 **Model / Marka**")
            with hdr_c3: st.caption("🎨 **Renk**")
            with hdr_c4: st.caption("🔢 **Plaka**")
            with hdr_c5: st.caption("💰 **Günlük Ücret**")
            with hdr_c6: st.caption("📊 **Toplam Tutar**")
            with hdr_c7: st.caption("🎟️ **İşlem**")
            st.markdown("---")

            # Fleet Master tablosundan çekilen kayıtları listele
            for index, row in available_cars.iterrows():
                car_id = row.get('Car ID', 'N/A')
                model_mark = row.get('Make/Model', 'N/A')
                color = row.get('Color', 'N/A')
                plate = row.get('License Plate', 'N/A')
                rate = safe_int(row.get('Base Daily Rate ($)', 100))
                total_price = rate * num_days

                with st.container(border=True):
                    c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1.8, 1.2, 1.5, 1.2, 1.2, 1.2])
                    with c1: st.markdown(f"`{car_id}`")
                    with c2: st.markdown(model_mark)
                    with c3: st.markdown(f"**{color}**")   # Rengi görünür şekilde vurgular
                    with c4: st.markdown(f"`{plate}`")
                    with c5: st.markdown(f"${rate}")
                    with c6: st.markdown(f"${total_price}")
                    with c7:
                        if st.button("Aracı Kirala", key=f"bk_{car_id}", use_container_width=True):
                            st.session_state.selected_car = row
                            st.session_state.booking_days = num_days
                            st.session_state.show_form = True

    # Sözleşme Formu Mantığı
    if st.session_state.get('show_form', False):
        car = st.session_state.selected_car
        rate = safe_int(car.get('Base Daily Rate ($)', 100))
        with st.form("contract_form"):
            st.subheader(f"📑 Hızlı Sözleşme Oluşturucu — Seçilen Araç: {car.get('Make/Model')} ({car.get('Color')})")
            client_name = st.text_input("Müşteri Adı Soyadı:")
            client_phone = st.text_input("Telefon / WhatsApp:")
            client_id = st.text_input("Kimlik / Pasaport / Doküman No:")
            
            if st.form_submit_button("Kiralamayı Onayla"):
                if client_name and client_phone:
                    deal_id = f"RENT-{datetime.today().strftime('%Y%m')}-{len(deals_df)+1:03d}"
                    
                    # Bilgileri kiralama sözleşmeleri veri tabanına kaydet
                    new_deal = {
                        'Deal ID': deal_id, 
                        'Client Name': client_name, 
                        'Phone/WhatsApp': client_phone, 
                        'ID/Passport': client_id,
                        'Rental Start Date': start_date.strftime('%Y-%m-%d'),
                        'Rental End Date': expected_return.strftime('%Y-%m-%d'),
                        'Rental Days': int(st.session_state.booking_days),
                        'Time of Rental': datetime.now().strftime('%I:%M %p'),
                        'Car ID': car.get('Car ID'), 
                        'Daily Rate': rate,
                        'Total Amount': rate * int(st.session_state.booking_days),
                        'Deposit': 0,
                        'Payment Status': 'Pending',
                        'Overdue Days': 0,
                        'Contract Signed': 'No',
                        'Return Condition Notes': '',
                        'Car Make/Model': car.get('Make/Model'),
                        'Car Status Link': ''
                    }
                    
                    # Verileri birleştir ve CSV tablolarına geri yaz
                    deals_df = pd.concat([deals_df, pd.DataFrame([new_deal])], ignore_index=True)
                    commit_to_database("deals", deals_df)
                    
                    # Araç durumunu "Rented" (Kiralandı) olarak güncelle
                    fleet_df.loc[fleet_df['Car ID'] == car.get('Car ID'), 'Status'] = 'Rented'
                    commit_to_database("fleet", fleet_df)
                    
                    st.success("✔️ Veri tabanı tabloları başarıyla güncellendi ve kiralama kaydedildi!")
                    st.session_state.show_form = False
                    st.rerun()

else:
    st.title("🛠️ CANLI FİLO DURUM YÖNETİCİSİ")
    if fleet_df.empty:
        st.warning("Filo kayıtları bulunamadı.")
    else:
        for index, row in fleet_df.iterrows():
            current_status = str(row.get('Status', 'Available')).strip()
            
            # Durum rozetlerini Türkçeleştirme
            status_badge = "🟢 Uygun" if current_status == 'Available' else "🔴 Kiralandı" if current_status == 'Rented' else "🛠️ Bakımda"
            
            with st.container(border=True):
                o_c1, o_c2, o_c3, o_c4 = st.columns([1, 2, 2, 3])
                with o_c1: st.markdown(f"### `{row.get('Car ID')}`")
                with o_c2: st.markdown(f"**{row.get('Make/Model')}** ({row.get('Color')})")
                with o_c3: st.markdown(f"Durum: **{status_badge}**")
                with o_c4:
                    a1, a2 = st.columns(2)
                    with a1:
                        # Eğer araç uygun değilse aktif olan "Uygun Yap" butonu
                        if current_status != 'Available' and st.button("✅ Uygun Yap", key=f"av_{row.get('Car ID')}", use_container_width=True):
                            fleet_df.at[index, 'Status'] = 'Available'
                            commit_to_database("fleet", fleet_df)
                            st.rerun()
                    with a2:
                        # Eğer araç bakımda değilse aktif olan "Bakıma Al" butonu
                        if current_status != 'Maintenance' and st.button("🛠️ Bakıma Al", key=f"mn_{row.get('Car ID')}", use_container_width=True):
                            fleet_df.at[index, 'Status'] = 'Maintenance'
                            commit_to_database("fleet", fleet_df)
                            st.rerun()