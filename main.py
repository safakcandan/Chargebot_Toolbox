import streamlit as st
import pandas as pd
import yaml
import os
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import xlsxwriter
import numpy as np

# --- 1. AYARLAR VE IMPORTLAR ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
base_path = os.path.dirname(os.path.abspath(__file__))

from src.models import calculate_needs, chargebot_logic, calculate_grid_load

config_path = os.path.join(base_path, "..", "config.yaml")
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

csv_path = os.path.join(base_path, "..", "data", "cities.csv")
df = pd.read_csv(csv_path)

# --- SAYFA VE TEMA AYARLARI (CHARGEBOT KURUMSAL TEMASI) ---
st.set_page_config(page_title="ChargeBot Karar Destek", layout="wide")

st.markdown("""
    <style>
    /* Genel Arka Plan ve Yazı Tipleri */
    .stApp {
        background-color: #F8F9FA !important;
        font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }
    
    /* Ana Başlık ve Tüm Metinler İçin Koyu ve Net Renkler */
    h1, h2, h3, h4, h5, h6 { color: #111827 !important; font-weight: 800 !important; }
    p, span, div, label { color: #1f2937 !important; font-weight: 500 !important; }

    /* YAN MENÜ (SIDEBAR) DÜZENLEMELERİ (Okunabilirlik İçin) */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #E5E7EB !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #111827 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
    }
    /* Selectbox ve Slider Yazıları */
    .stSelectbox label, .stSlider label {
        color: #111827 !important;
        font-weight: 700 !important;
    }

    /* Sekme (Tab) Tasarımı */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 3px solid transparent !important;
        color: #4B5563 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding-bottom: 10px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00CC96 !important;
        border-bottom: 3px solid #00CC96 !important;
    }

    /* Metrik Kutuları */
    div[data-testid="stMetric"] { 
        background-color: #FFFFFF !important; 
        padding: 20px !important; 
        border-radius: 12px !important; 
        border-left: 6px solid #00CC96 !important; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.06) !important; 
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="stMetric"]:hover { transform: translateY(-3px); }
    [data-testid="stMetricLabel"] p { color: #374151 !important; font-weight: 700 !important; font-size: 1.05rem !important; }
    [data-testid="stMetricValue"] { color: #111827 !important; font-size: 2.2rem !important; font-weight: 900 !important; }
    [data-testid="stMetricDelta"] svg { display: none; }
    [data-testid="stMetricDelta"] > div { color: #4B5563 !important; font-size: 1rem !important; font-weight: 600 !important; }
    
    /* İndirme Butonu */
    [data-testid="stDownloadButton"] button {
        background-color: #00CC96 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100%;
        padding: 0.75rem !important;
        font-size: 1.1rem !important;
    }
    [data-testid="stDownloadButton"] button:hover { background-color: #00b383 !important; }

    /* Bilgi ve Uyarı Kutuları */
    div.stAlert {
        border-radius: 10px !important;
        border: 1px solid #E5E7EB !important;
        background-color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    div.stAlert > div { color: #111827 !important; font-weight: 500 !important; }

    /* Logo Konteyneri */
    .logo-container svg { height: 55px !important; width: auto !important; }
    .header-container { display: flex; align-items: center; gap: 20px; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #E5E7EB; }
    </style>
    """, unsafe_allow_html=True)

# --- SVG LOGO OKUMA ---
logo_path = os.path.join(base_path, "chargebot-logo.svg")
svg_content = ""
if os.path.exists(logo_path):
    with open(logo_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

st.markdown(f"""
    <div class="header-container">
        <div class="logo-container">{svg_content}</div>
        <div>
            <h1 style="margin: 0; padding: 0; font-size: 2.2rem; line-height: 1.2; letter-spacing: -0.5px;">ChargeBot: Mobil Şarj Yatırım ve Fizibilite Simülatörü</h1>
            <p style="margin: 5px 0 0 0; font-size: 1.05rem; color: #4B5563;">Pazar verilerine dayalı stratejik altyapı ve kârlılık karar destek sistemi.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- EXCEL MOTORU ---
def generate_master_excel(new_ev_target, city_name, bots_count, stations_count, infra_mult):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        pd.DataFrame({"Yıl": ["2021", "2022", "2023", "2024", "2025"], "EV": [7694, 14896, 80826, 185513, 310668]}).to_excel(writer, sheet_name='1-Trend', index=False)
    buffer.seek(0)
    return buffer

# --- 3. YAN MENÜ (SIDEBAR) ---
st.sidebar.markdown("<h2 style='color:#00CC96; margin-bottom:20px;'>Simülasyon Ayarları</h2>", unsafe_allow_html=True)
selected_city = st.sidebar.selectbox("Analiz Bölgesi", df['city'])
city_row = df[df['city'] == selected_city].iloc[0]
new_evs = st.sidebar.slider("Yeni EV Hedefi", 0, 5000, 1000)

needs = calculate_needs(new_evs, config['simulation']['ev_to_socket_ratio'])
# GERÇEK DÜNYA MANTIĞI: 1 İstasyon = 2 Soket
stations_count = max(1, int(needs['total'] / 2)) 

# ELMA İLE ELMA: CHARGEBOT SAYISI İSTASYON SAYISINA EŞİTLENDİ
bots = stations_count 

excel_buffer = generate_master_excel(new_evs, selected_city, bots, stations_count, city_row['infra_cost_factor'])
st.sidebar.divider()
st.sidebar.download_button("📥 Kapsamlı Finansal Excel'i İndir", data=excel_buffer.getvalue(), file_name=f"ChargeBot_Analiz_{selected_city}.xlsx")

# --- 4. ANA EKRAN SEKMELERİ ---
tab_trend, tab_infra, tab_calc, tab_gaap = st.tabs([
    "📈 Pazar Trendi", 
    "⚡ Altyapı İhtiyacı",
    "🔌 Piyasa Şarj Analizi",
    "💰 Kârlılık ve ROI"
])

# 1. Pazar Trendi
with tab_trend:
    st.subheader("Türkiye EV ve Sabit İstasyon Makası")
    trend_data = pd.DataFrame({"Yıl": ["2021", "2022", "2023", "2024", "2025(Ağu)"], "EV_Sayısı": [7694, 14896, 80826, 185513, 310668], "Soket_Sayısı": [1500, 3009, 12265, 26046, 33592]})
    trend_data['Arac_Bolü_Soket'] = trend_data['EV_Sayısı'] / trend_data['Soket_Sayısı']
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=trend_data["Yıl"], y=trend_data["EV_Sayısı"], name="Elektrikli Araç Sayısı", marker_color="#1d4ed8"))
    fig_trend.add_trace(go.Scatter(x=trend_data["Yıl"], y=trend_data["Soket_Sayısı"], name="Şarj Soketi Sayısı", mode="lines+markers", marker=dict(color="#00CC96", size=12), line=dict(width=4)))
    
    fig_trend.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)", 
        barmode='group', 
        hovermode="x unified", 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(color="#111827", size=14)
    )
    fig_trend.update_xaxes(type='category', showgrid=False, tickfont=dict(color="#111827", weight="bold"))
    fig_trend.update_yaxes(showgrid=True, gridcolor="#E5E7EB", tickfont=dict(color="#111827", weight="bold"))
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    c_t1, c_t2, c_t3 = st.columns(3)
    c_t1.metric("2023-2025 EV Büyümesi", "%284", "Hızlı Artış")
    c_t2.metric("2023-2025 Soket Büyümesi", "%173", "Altyapı Geride Kalıyor")
    c_t3.metric("Araç / Soket Oranı (Güncel)", f"{trend_data['Arac_Bolü_Soket'].iloc[-1]:.1f}", "İdeal oran 10-12 arasıdır")

# 2. Altyapı & Şebeke Analizi
with tab_infra:
    st.subheader(f"Bölgesel Şebeke Analizi: {selected_city}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Gereken Şarj İstasyonu Sayısı", f"{stations_count} Adet", "Geleneksel Çözüm (Çift Soketli)")
    c2.metric("Trafoya Binen Ek Yük", f"{calculate_grid_load(new_evs):,.0f} kW", "Riskli Bölge")
    c3.metric("Önerilen ChargeBot Filosu", f"{bots} Adet", "0 kW Ek Yük (Peak Shaving)")
    st.divider()
    
    # 80 kW Cihaz İçin Güncellenen Maliyet: İstasyon Başına 42.000 € 
    sabit_donanim = stations_count * 42000
    sabit_kazi = stations_count * 10000 * city_row['infra_cost_factor']
    sabit_sebeke = stations_count * 5000 * city_row['infra_cost_factor']
    sabit_izin = stations_count * 2000 * city_row['infra_cost_factor']
    sabit_toplam = sabit_donanim + sabit_kazi + sabit_sebeke + sabit_izin
    chargebot_toplam = bots * 50000

    comp_df = pd.DataFrame([
        {"Kalem": "1. Donanım (Cihaz)", "Sabit Yatırım (€)": sabit_donanim, "ChargeBot (€)": chargebot_toplam},
        {"Kalem": "2. İnşaat & Kazı", "Sabit Yatırım (€)": sabit_kazi, "ChargeBot (€)": 0},
        {"Kalem": "3. Şebeke & Trafo", "Sabit Yatırım (€)": sabit_sebeke, "ChargeBot (€)": 0},
        {"Kalem": "4. İzinler & Proje", "Sabit Yatırım (€)": sabit_izin, "ChargeBot (€)": 0}
    ])

    col_chart, col_totals = st.columns([7, 3])

    with col_chart:
        fig_comp = go.Figure(data=[
            go.Bar(name='Sabit Altyapı Maliyeti (€)', x=comp_df['Kalem'], y=comp_df['Sabit Yatırım (€)'], marker_color='#ef4444'),
            go.Bar(name='ChargeBot Mobil Maliyeti (€)', x=comp_df['Kalem'], y=comp_df['ChargeBot (€)'], marker_color='#00CC96')
        ])
        fig_comp.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)", 
            barmode='group', 
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            font=dict(color="#111827", size=14)
        )
        fig_comp.update_yaxes(showgrid=True, gridcolor="#E5E7EB", tickfont=dict(color="#111827", weight="bold"))
        fig_comp.update_xaxes(tickfont=dict(color="#111827", weight="bold"))
        st.plotly_chart(fig_comp, use_container_width=True)

    with col_totals:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background-color: white; padding: 25px; border-radius: 12px; border-left: 6px solid #ef4444; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <p style="color: #6C757D; font-weight: 700; font-size: 1rem; margin:0 0 5px 0;">Toplam Sabit Yatırım</p>
            <p style="color: #ef4444; font-size: 2.2rem; font-weight: 900; margin: 0;">€ {sabit_toplam:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background-color: white; padding: 25px; border-radius: 12px; border-left: 6px solid #00CC96; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <p style="color: #6C757D; font-weight: 700; font-size: 1rem; margin:0 0 5px 0;">Toplam ChargeBot Yatırımı</p>
            <p style="color: #00CC96; font-size: 2.2rem; font-weight: 900; margin: 0;">€ {chargebot_toplam:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)

        if sabit_toplam > chargebot_toplam:
            st.success(f"💡 **Net Yatırım Tasarrufu:** € {sabit_toplam - chargebot_toplam:,.0f}")

# 3. Menzil & Şarj Piyasası
with tab_calc:
    st.subheader("Tüketici Şarj Maliyeti ve Menzil ")
    col1, col2 = st.columns(2)
    with col1:
        bat_kwh = st.slider("Batarya Kapasitesi (kWh)", 30, 120, 77)
        temp = st.slider("Dış Hava Sıcaklığı (°C)", -10, 40, 20)
    with col2:
        cons = st.number_input("Araç Tüketimi (Wh/km)", min_value=100, max_value=300, value=160, step=10)
        real_range = ((bat_kwh * 1000) / cons) * (1.0 - (abs(20 - temp) * 0.005))
        st.success(f"Sıcaklık Düzeltmeli Gerçek Dünya Menzili: **{real_range:.0f} km**")

    st.divider()
    charge_amount = st.slider("Şarj Edilecek Miktar (kWh)", 10, 100, 50, 5)
    
    brands_data = [
        {"Marka": "Trugo", "AC_Fiyat": 9.95, "DC_Fiyat": 15.36, "İstasyon_Sayısı": 3500},
        {"Marka": "ZES", "AC_Fiyat": 9.99, "DC_Fiyat": 16.49, "İstasyon_Sayısı": 6500},
        {"Marka": "Eşarj", "AC_Fiyat": 10.50, "DC_Fiyat": 15.80, "İstasyon_Sayısı": 3200},
        {"Marka": "AstorŞarj", "AC_Fiyat": 7.99, "DC_Fiyat": 10.99, "İstasyon_Sayısı": 447},
        {"Marka": "Beefull", "AC_Fiyat": 8.99, "DC_Fiyat": 12.99, "İstasyon_Sayısı": 1390},
        {"Marka": "Voltrun", "AC_Fiyat": 9.25, "DC_Fiyat": 12.90, "İstasyon_Sayısı": 2390},
        {"Marka": "Otowatt", "AC_Fiyat": 7.99, "DC_Fiyat": 9.99, "İstasyon_Sayısı": 1470},
        {"Marka": "Petrol Ofisi e-POwer", "AC_Fiyat": 7.50, "DC_Fiyat": 9.50, "İstasyon_Sayısı": 2430},
        {"Marka": "Aksa Şarj", "AC_Fiyat": 8.99, "DC_Fiyat": 10.99, "İstasyon_Sayısı": 2424},
        {"Marka": "Otopriz", "AC_Fiyat": 7.88, "DC_Fiyat": 9.87, "İstasyon_Sayısı": 2500},
        {"Marka": "Sharz.net", "AC_Fiyat": 7.99, "DC_Fiyat": 10.99, "İstasyon_Sayısı": 1200},
        {"Marka": "OnCharge", "AC_Fiyat": 9.99, "DC_Fiyat": 13.00, "İstasyon_Sayısı": 450}
    ]
    df_brands = pd.DataFrame(brands_data)
    
    df_brands[f"AC Toplam ({charge_amount} kWh)"] = df_brands['AC_Fiyat'] * charge_amount
    df_brands[f"DC Toplam ({charge_amount} kWh)"] = df_brands['DC_Fiyat'] * charge_amount
    display_df = df_brands[['Marka', 'AC_Fiyat', f"AC Toplam ({charge_amount} kWh)", 'DC_Fiyat', f"DC Toplam ({charge_amount} kWh)", 'İstasyon_Sayısı']].sort_values(by="DC_Fiyat", ascending=True)
    
    st.dataframe(
        display_df,
        column_config={
            "Marka": st.column_config.TextColumn("Şarj Ağı", width="medium"),
            "AC_Fiyat": st.column_config.NumberColumn("AC Birim Fiyat", format="%.2f ₺"),
            f"AC Toplam ({charge_amount} kWh)": st.column_config.NumberColumn(f"AC Fatura", format="%.2f ₺"),
            "DC_Fiyat": st.column_config.NumberColumn("DC Birim Fiyat", format="%.2f ₺"),
            f"DC Toplam ({charge_amount} kWh)": st.column_config.NumberColumn(f"DC Fatura", format="%.2f ₺"),
            "İstasyon_Sayısı": st.column_config.ProgressColumn("Pazar Ağı (İstasyon)", format="%f Adet", min_value=0, max_value=int(df_brands['İstasyon_Sayısı'].max())),
        },
        hide_index=True, use_container_width=True, height=450
    )

# 4. GAAP FİNANSAL PERFORMANS
with tab_gaap:
    st.subheader("10 Yıllık Finansal Yatırım ve Kârlılık Projeksiyonu")
    
    c_f1, c_f2, c_f3, c_f4 = st.columns(4)
    eur_tl_rate = c_f1.number_input("Kur (₺/€)", value=36.0, step=1.0)
    # Varsayılan güç 80 kW olarak güncellendi!
    charger_kw = c_f2.number_input("Cihaz Gücü (kW)", value=80)
    utilization = c_f3.slider("Kullanım (Saat/Gün)", 1.0, 24.0, 4.0)
    discount_rate = c_f4.slider("İskonto/Faiz (%)", 1, 30, 10) / 100
    
    c_f5, c_f6, c_f7, c_f8 = st.columns(4)
    elec_buy_fixed = c_f5.number_input("Alış - Sabit (₺/kWh)", value=4.50)
    elec_buy_bot = c_f6.number_input("Alış - ChargeBot (₺/kWh)", value=2.50, help="Gece ucuz tarife")
    elec_sell_price = c_f7.number_input("Satış Fiyatı (₺/kWh)", value=9.50)
    tax_rate = c_f8.number_input("Kurumlar Vergisi (%)", value=25) / 100

    fixed_capex_tl = comp_df['Sabit Yatırım (€)'].sum() * eur_tl_rate
    bot_capex_tl = comp_df['ChargeBot (€)'].sum() * eur_tl_rate

    annual_energy_kwh = stations_count * charger_kw * utilization * 365
    bot_annual_energy = bots * charger_kw * utilization * 365

    fixed_revenue = annual_energy_kwh * elec_sell_price
    fixed_elec_cost = annual_energy_kwh * elec_buy_fixed
    fixed_demand_cost = stations_count * charger_kw * 150.0 * 12 
    fixed_infra_amortization = fixed_capex_tl / 10 
    fixed_maint_cost = fixed_capex_tl * 0.05
    fixed_total_cost = fixed_elec_cost + fixed_demand_cost + fixed_maint_cost + fixed_infra_amortization
    
    bot_revenue = bot_annual_energy * elec_sell_price
    bot_elec_cost = bot_annual_energy * elec_buy_bot
    bot_demand_cost = 0 
    bot_infra_amortization = bot_capex_tl / 10 
    bot_maint_cost = bot_capex_tl * 0.03
    bot_total_cost = bot_elec_cost + bot_demand_cost + bot_maint_cost + bot_infra_amortization

    fixed_breakeven = fixed_total_cost / annual_energy_kwh if annual_energy_kwh > 0 else 0
    bot_breakeven = bot_total_cost / bot_annual_energy if bot_annual_energy > 0 else 0

    fixed_net_cash = fixed_revenue - (fixed_elec_cost + fixed_demand_cost + fixed_maint_cost)
    bot_net_cash = bot_revenue - (bot_elec_cost + bot_demand_cost + bot_maint_cost)

    fixed_payback = fixed_capex_tl / fixed_net_cash if fixed_net_cash > 0 else 0
    bot_payback = bot_capex_tl / bot_net_cash if bot_net_cash > 0 else 0

    def calc_npv(rate, cash_flow, capex, years=10):
        return sum([cash_flow / ((1 + rate)**t) for t in range(1, years+1)]) - capex
    
    fixed_npv = calc_npv(discount_rate, fixed_net_cash * (1-tax_rate), fixed_capex_tl) 
    bot_npv = calc_npv(discount_rate, bot_net_cash * (1-tax_rate), bot_capex_tl)

    st.divider()
    
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 12px; border-left: 5px solid #111827; box-shadow: 0 2px 10px rgba(0,0,0,0.05); height: 100%;">
            <p style="color: #4B5563; font-weight: 700; font-size: 0.95rem; margin:0 0 5px 0;">Yatırım Amortisman Süresi (ROI)</p>
            <p style="color: #ef4444; font-size: 1.2rem; font-weight: 700; margin: 0 0 5px 0;">Sabit Altyapı: {fixed_payback:.1f} Yıl</p>
            <p style="color: #00CC96; font-size: 1.8rem; font-weight: 900; margin: 0;">ChargeBot: {bot_payback:.1f} Yıl</p>
        </div>
        """, unsafe_allow_html=True)

    with col_res2:
        st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 12px; border-left: 5px solid #111827; box-shadow: 0 2px 10px rgba(0,0,0,0.05); height: 100%;">
            <p style="color: #4B5563; font-weight: 700; font-size: 0.95rem; margin:0 0 5px 0;">10 Yıllık Net Bugünkü Değer (NPV)</p>
            <p style="color: #ef4444; font-size: 1.2rem; font-weight: 700; margin: 0 0 5px 0;">Sabit Altyapı: ₺ {fixed_npv/1000000:,.1f} M</p>
            <p style="color: #00CC96; font-size: 1.8rem; font-weight: 900; margin: 0;">ChargeBot: ₺ {bot_npv/1000000:,.1f} M</p>
        </div>
        """, unsafe_allow_html=True)

    with col_res3:
        st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 12px; border-left: 5px solid #111827; box-shadow: 0 2px 10px rgba(0,0,0,0.05); height: 100%;">
            <p style="color: #4B5563; font-weight: 700; font-size: 0.95rem; margin:0 0 5px 0;">Birim Başabaş Maliyeti (Kw/TL)</p>
            <p style="color: #ef4444; font-size: 1.2rem; font-weight: 700; margin: 0 0 5px 0;">Sabit Altyapı: ₺ {fixed_breakeven:.2f}</p>
            <p style="color: #00CC96; font-size: 1.8rem; font-weight: 900; margin: 0;">ChargeBot: ₺ {bot_breakeven:.2f}</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("") 
    st.info("""
    💡 **Stratejik Kârlılık ve Altyapı Bilgilendirmesi:**
    
    Geleneksel sabit şarj istasyonu yatırımlarında; yüksek cihaz, kazı, trafo ve inşaat masraflarına ek olarak her ay şebekeye ödenen **Kapasite (Talep) Ücretleri**, işletmenin başabaş (kurtarma) maliyetini ciddi oranda yükseltir. Bu durum, piyasa ortalamasında rekabetçi fiyatlar sunulurken kâr marjını büyük ölçüde eritmektedir.
    
    **ChargeBot** ise mobil ve bağımsız yapısı sayesinde bu gizli altyapı masraflarını ve aylık kapasite cezalarını tamamen ortadan kaldırır. Üstelik enerjiyi şebeke yükünün ve fiyatların en düşük olduğu saatlerde depolama imkanı sunarak, birim şarj maliyetinizi minimize eder. Geleneksel sistemlerin görünmez maliyetlerle mücadele ettiği bir pazarda ChargeBot, yatırımcıya maksimum kâr marjı ve esnek fiyatlama gücü sağlar.
    """)

    years_list = [f"Yıl {i}" for i in range(1, 11)]
    fixed_cash_flow_cumulative = [-fixed_capex_tl + (fixed_net_cash * (1-tax_rate) * i) for i in range(1, 11)]
    bot_cash_flow_cumulative = [-bot_capex_tl + (bot_net_cash * (1-tax_rate) * i) for i in range(1, 11)]

    fig_cf = go.Figure()
    fig_cf.add_trace(go.Scatter(x=years_list, y=fixed_cash_flow_cumulative, name='Sabit Altyapı Nakit Akışı', line=dict(color='#ef4444', width=5)))
    fig_cf.add_trace(go.Scatter(x=years_list, y=bot_cash_flow_cumulative, name='ChargeBot Nakit Akışı', line=dict(color='#00CC96', width=5)))
    fig_cf.add_hline(y=0, line_dash="dash", line_color="#111827", annotation_text="Kâra Geçiş Noktası", annotation_font=dict(color="#111827", size=12, weight="bold"))
    
    fig_cf.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)", 
        title="Yatırımın Geri Dönüşü ve Kâr Eğrisi (Vergi Sonrası)", 
        hovermode="x unified", 
        yaxis_title="Toplam Kâr/Zarar (₺)",
        font=dict(color="#111827", size=14, weight="bold")
    )
    fig_cf.update_yaxes(showgrid=True, gridcolor="#E5E7EB", tickfont=dict(color="#111827", weight="bold"))
    fig_cf.update_xaxes(tickfont=dict(color="#111827", weight="bold"))
    
    st.plotly_chart(fig_cf, use_container_width=True)