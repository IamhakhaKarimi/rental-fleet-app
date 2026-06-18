import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- İLK BİLEŞEN YAPILANDIRMASI ---
st.set_page_config(page_title="Finansal Araç Filo Yönetim Merkezi", page_icon="📊", layout="wide")

# Excel sayfalarıyla tam eşleşen yerel veri tabanı hedef yolları
LOCAL_FLEET = "rental business.xlsx - Fleet Master.csv"
LOCAL_DEALS = "rental business.xlsx - Rental Deals Sheet.csv"

st.sidebar.info("💾 Veri Tabanı Bağlantısı: Finansal Modül Aktif")

# --- GÜVENLİ SAYISAL DÖNÜŞTÜRME YARDIMCILARI ---
def safe_int(value, default=100):
    try:
        if pd.isna(value):
            return default
        cleaned = str(value).replace('$', '').replace(',', '').strip()
        return int(float(cleaned))
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        cleaned = str(value).replace('$', '').replace(',', '').strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return default

# --- CANLI VERİ TABANI OKUMA/YAZMA KONTROLLERİ ---
def fetch_fleet_data():
    if os.path.exists(LOCAL_FLEET):
        try:
            df = pd.read_csv(LOCAL_FLEET)
            df.columns = df.columns.str.strip()
            if 'Client Maintenance Charge' not in df.columns:
                df['Client Maintenance Charge'] = 0.0
            return df
        except PermissionError:
            st.error(f"⚠️ HATA: '{LOCAL_FLEET}' dosyası şu anda Excel'de açık olduğu için okunamıyor! Lütfen Excel'i kapatıp sayfayı yenileyin.")
            return pd.DataFrame()
    else:
        st.error(f"Eksik Veri Tabanı Dosyası: {LOCAL_FLEET}")
        return pd.DataFrame()

def fetch_deals_data():
    if os.path.exists(LOCAL_DEALS):
        try:
            df = pd.read_csv(LOCAL_DEALS)
            df.columns = df.columns.str.strip()
            return df
        except PermissionError:
            st.error(f"⚠️ HATA: '{LOCAL_DEALS}' dosyası şu anda Excel'de açık olduğu için okunamıyor! Lütfen Excel'i kapatıp sayfayı yenileyin.")
            return pd.DataFrame()
    else:
        st.error(f"Eksik Veri Tabanı Dosyası: {LOCAL_DEALS}")
        return pd.DataFrame()

def commit_to_database(target_mode, dataframe):
    dataframe_filled = dataframe.fillna("")
    file_path = LOCAL_FLEET if target_mode == "fleet" else LOCAL_DEALS
    try:
        dataframe_filled.to_csv(file_path, index=False)
        return True
    except PermissionError:
        st.error(f"⚠️ İŞLEM ENGELLENDİ: '{file_path}' dosyası şu anda Excel'de açık! Lütfen Excel dosyasını kapatıp butona tekrar tıklayın.")
        return False

# Veri tabanlarını senkronize et
fleet_df = fetch_fleet_data()
deals_df = fetch_deals_data()

if fleet_df.empty or deals_df.empty:
    st.warning("Uygulamanın çalışabilmesi için lütfen açık olan Excel/CSV dosyalarını kapatın.")
    st.stop()

# --- ARAYÜZ GÖRÜNÜM SEÇENEKLERİ ---
view_mode = st.radio(
    "Arayüz Görünümünü Seçin", 
    ["🛎️ Resepsiyon Paneli", "🛠️ Canlı Filo Durum Yöneticisi", "📊 Aylık Finansal Yönetim Paneli"], 
    horizontal=True
)

# ==================== 1. RESEPSİYON PANELİ ====================
if view_mode == "🛎️ Resepsiyon Paneli":
    st.title("ÖN OFİS: ARAÇ UYGUNLUK KONTROLÜ (ÇAKIŞMA KORUMALI)")
    
    col_input, col_grid = st.columns([1.1, 2.7])
    
    with col_input:
        st.markdown("### 📅 Talep Edilen Tarih Aralığı")
        start_date = st.date_input("Başlangıç Tarihi:", datetime.today().date())
        num_days = st.number_input("Gün Sayısı:", min_value=1, max_value=90, value=5, step=1)
        expected_return = start_date + timedelta(days=int(num_days))
        
        st.info(f"🔮 **Yeni Rezervasyon Bitiş:** {expected_return.strftime('%Y-%m-%d')}")
        
        # --- YENİ EKLENEN OPERASYONEL TAKİP: O GÜN DÖNECEK ARAÇLAR ---
        st.markdown("---")
        st.markdown(f"📥 **{expected_return.strftime('%Y-%m-%d')} Tarihinde Dönüşü Beklenen Araçlar:**")
        
        try:
            # Mevcut sözleşmelerin bitiş tarihlerini güvenli bir şekilde tarihe dönüştürüp eşleşenleri buluyoruz
            deals_df['Clean_End_Date'] = pd.to_datetime(deals_df['Rental End Date']).dt.date
            todays_returns = deals_df[deals_df['Clean_End_Date'] == expected_return]
        except:
            todays_returns = pd.DataFrame()
            
        if todays_returns.empty:
            st.caption("🟢 O gün teslim alınması beklenen kiralık araç yok.")
        else:
            for _, r_row in todays_returns.iterrows():
                st.error(f"🚗 **{r_row.get('Car ID')}** - {r_row.get('Car Make/Model')}\n\n👤 Müşteri: {r_row.get('Client Name')}")

        st.markdown("---")
        with st.expander("🗓️ Tüm Aktif Rezervasyon Listesi"):
            st.caption("Filonun mevcut kiralama takvimi:")
            for _, d_row in deals_df.iterrows():
                st.write(f"• **{d_row.get('Car ID')}**: {d_row.get('Rental Start Date')} ➔ {d_row.get('Rental End Date')}")

    with col_grid:
        st.markdown("### 🚘 Seçilen Tarihlerde Müsait Olan Araçlar")
        
        filtered_available_cars = []
        
        for index, car_row in fleet_df.iterrows():
            car_id = car_row.get('Car ID', 'N/A')
            car_status = str(car_row.get('Status', 'Available')).strip()
            
            if car_status == 'Maintenance':
                continue
                
            has_date_conflict = False
            car_specific_deals = deals_df[deals_df['Car ID'] == car_id]
            
            for _, deal_row in car_specific_deals.iterrows():
                try:
                    deal_start = pd.to_datetime(deal_row['Rental Start Date']).date()
                    deal_end = pd.to_datetime(deal_row['Rental End Date']).date()
                    
                    if max(start_date, deal_start) <= min(expected_return, deal_end):
                        has_date_conflict = True
                        break
                except:
                    continue
            
            if not has_date_conflict:
                filtered_available_cars.append(car_row)
        
        if filtered_available_cars:
            available_cars_df = pd.DataFrame(filtered_available_cars)
        else:
            available_cars_df = pd.DataFrame()
            
        st.sidebar.metric(label="SEÇİLEN TARİHTE UYGUN ARAÇ", value=len(available_cars_df))

        if available_cars_df.empty:
            st.warning("⚠️ Seçtiğiniz tarih aralığında filodaki tüm araçlar doludur veya çakışan rezervasyonlar vardır! Lütfen tarihleri değiştirin.")
        else:
            hdr_c1, hdr_c2, hdr_c3, hdr_c4, hdr_c5, hdr_c6, hdr_c7 = st.columns([1, 1.8, 1.2, 1.5, 1.2, 1.2, 1.2])
            with hdr_c1: st.caption("⚡ **Araç ID**")
            with hdr_c2: st.caption("🚗 **Model / Marka**")
            with hdr_c3: st.caption("🎨 **Renk**")
            with hdr_c4: st.caption("🔢 **Plaka**")
            with hdr_c5: st.caption("💰 **Günlük**")
            with hdr_c6: st.caption("📊 **Toplam**")
            with hdr_c7: st.caption("🎟️ **İşlem**")
            st.markdown("---")

            for index, row in available_cars_df.iterrows():
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
                    with c3: st.markdown(f"**{color}**")
                    with c4: st.markdown(f"`{plate}`")
                    with c5: st.markdown(f"${rate}")
                    with c6: st.markdown(f"${total_price}")
                    with c7:
                        if st.button("Aracı Kirala", key=f"bk_{car_id}", use_container_width=True):
                            st.session_state.selected_car = row
                            st.session_state.booking_days = num_days
                            st.session_state.show_form = True

    if st.session_state.get('show_form', False):
        car = st.session_state.selected_car
        rate = safe_int(car.get('Base Daily Rate ($)', 100))
        with st.form("contract_form"):
            st.subheader(f"📑 Hızlı Sözleşme Oluşturucu — {car.get('Make/Model')}")
            client_name = st.text_input("Müşteri Adı Soyadı:")
            client_phone = st.text_input("Telefon / WhatsApp:")
            client_id = st.text_input("Kimlik / Pasaport No:")
            
            if st.form_submit_button("Kiralamayı Onayla"):
                if client_name and client_phone:
                    deal_id = f"RENT-{datetime.today().strftime('%Y%m')}-{len(deals_df)+1:03d}"
                    new_deal = {
                        'Deal ID': deal_id, 'Client Name': client_name, 'Phone/WhatsApp': client_phone, 'ID/Passport': client_id,
                        'Rental Start Date': start_date.strftime('%Y-%m-%d'), 'Rental End Date': expected_return.strftime('%Y-%m-%d'),
                        'Rental Days': int(st.session_state.booking_days), 'Time of Rental': datetime.now().strftime('%I:%M %p'),
                        'Car ID': car.get('Car ID'), 'Daily Rate': rate, 'Total Amount': rate * int(st.session_state.booking_days),
                        'Deposit': 0, 'Payment Status': 'Pending', 'Overdue Days': 0, 'Contract Signed': 'No',
                        'Return Condition Notes': '', 'Car Make/Model': car.get('Make/Model'), 'Car Status Link': ''
                    }
                    # Geçici hesaplama sütununu veri tabanına kaydetmeden önce temizliyoruz
                    if 'Clean_End_Date' in deals_df.columns:
                        deals_df = deals_df.drop(columns=['Clean_End_Date'])
                    deals_df = pd.concat([deals_df, pd.DataFrame([new_deal])], ignore_index=True)
                    if commit_to_database("deals", deals_df):
                        fleet_df.loc[fleet_df['Car ID'] == car.get('Car ID'), 'Status'] = 'Rented'
                        if commit_to_database("fleet", fleet_df):
                            st.success("✔️ Kiralama başarıyla kaydedildi!")
                            st.session_state.show_form = False
                            st.rerun()

# ==================== 2. CANLI FİLO DURUM YÖNETİCİSİ ====================
elif view_mode == "🛠️ Canlı Filo Durum Yöneticisi":
    st.title("🛠️ CANLI FİLO DURUM YÖNETİCİSİ VE HASAR/MALİYET GİRİŞİ")
    
    for index, row in fleet_df.iterrows():
        car_id = row.get('Car ID', 'N/A')
        current_status = str(row.get('Status', 'Available')).strip()
        status_badge = "🟢 Uygun" if current_status == 'Available' else "🔴 Kiralandı" if current_status == 'Rented' else "🛠️ Bakımda"
        current_client_charge = safe_float(row.get('Client Maintenance Charge', 0.0))
        
        with st.container(border=True):
            o_c1, o_c2, o_c3, o_c4 = st.columns([1, 2.2, 1.8, 3])
            with o_c1: 
                st.markdown(f"### `{car_id}`")
            with o_c2: 
                st.markdown(f"**{row.get('Make/Model')}** ({row.get('Color')})")
                st.markdown(f"Durum: **{status_badge}**")
            
            with o_c3:
                new_charge = st.number_input(
                    "Müşteriye Yansıtılan Bakım ($):", 
                    min_value=0.0, 
                    value=current_client_charge, 
                    step=10.0, 
                    key=f"input_charge_{car_id}"
                )
                if new_charge != current_client_charge:
                    if st.button("Maliyeti Güncelle", key=f"btn_charge_{car_id}"):
                        fleet_df.loc[fleet_df['Car ID'] == car_id, 'Client Maintenance Charge'] = new_charge
                        if commit_to_database("fleet", fleet_df):
                            st.success(f"✔️ {car_id} için hasar faturası güncellendi!")
                            st.rerun()
                            
            with o_c4:
                st.markdown("<div style='padding-top:20px;'></div>", unsafe_allow_html=True)
                a1, a2 = st.columns(2)
                with a1:
                    if current_status != 'Available' and st.button("✅ Uygun Yap", key=f"av_{car_id}", use_container_width=True):
                        fleet_df.loc[fleet_df['Car ID'] == car_id, 'Status'] = 'Available'
                        if commit_to_database("fleet", fleet_df): st.rerun()
                with a2:
                    if current_status != 'Maintenance' and st.button("🛠️ Bakıma Al", key=f"mn_{car_id}", use_container_width=True):
                        fleet_df.loc[fleet_df['Car ID'] == car_id, 'Status'] = 'Maintenance'
                        if commit_to_database("fleet", fleet_df): st.rerun()

# ==================== 3. AYLIK FİNANSAL YÖNETİM PANELİ ====================
else:
    st.title("📊 AYLIK ARAÇ BAZLI FİNANSAL PERFORMANS RAPORU")
    
    fin_data = []
    
    for index, row in fleet_df.iterrows():
        car_id = row.get('Car ID', 'N/A')
        model_mark = row.get('Make/Model', 'N/A')
        
        car_deals = deals_df[deals_df['Car ID'] == car_id]
        total_days = int(car_deals['Rental Days'].apply(safe_int, default=0).sum())
        total_rental_income = car_deals['Total Amount'].apply(safe_float).sum()
        client_maintenance_rev = safe_float(row.get('Client Maintenance Charge', 0.0))
        
        gross_income = total_rental_income + client_maintenance_rev
        
        fleet_maintenance_cost = 0.0
        if len(row) > 15:
            fleet_maintenance_cost = safe_float(row.iloc[15])
            
        net_profit = gross_income - fleet_maintenance_cost
        
        fin_data.append({
            "Araç ID": car_id,
            "Model / Marka": model_mark,
            "Toplam Kiralanan Gün": total_days,
            "Kiralama Geliri ($)": total_rental_income,
            "Müşteriye Yansıtılan Hasar ($)": client_maintenance_rev,
            "Filo Bakım Gideri (Sütun P) ($)": fleet_maintenance_cost,
            "Net Finansal Kar/Zarar ($)": net_profit
        })
        
    fin_df = pd.DataFrame(fin_data)
    
    total_fleet_profit = fin_df["Net Finansal Kar/Zarar ($)"].sum()
    total_rented_days_all = fin_df["Toplam Kiralanan Gün"].sum()
    
    m_c1, m_c2 = st.columns(2)
    with m_c1:
        st.metric(label="FİLO TOPLAM NET KÂR / ZARAR DURUMU", value=f"${total_fleet_profit:,.2f}")
    with m_c2:
        st.metric(label="FİLO TOPLAM KİRALANAN GÜN SAYISI", value=f"{total_rented_days_all} Gün")
        
    st.markdown("---")
    st.markdown("### 📋 Detaylı Araç Finans Listesi")
    
    st.dataframe(
        fin_df.style.format({
            "Kiralama Geliri ($)": "{:,.2f}",
            "Müşteriye Yansıtılan Hasar ($)": "{:,.2f}",
            "Filo Bakım Gideri (Sütun P) ($)": "{:,.2f}",
            "Net Finansal Kar/Zarar ($)": "{:,.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )