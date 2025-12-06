"""
============================================================================
DASHBOARD ANALISIS SPASIAL STUNTING JAWA BARAT 2024
Optimized & Inspired by Zoonosis Dashboard
============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import json
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Dashboard Stunting Jawa Barat 2024",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS - Clean & Modern
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    .risk-card {
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .header-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    
    .header-card h1 {
        color: white;
        margin: 0;
        font-size: 1.75rem;
    }
    
    .header-card p {
        color: rgba(255,255,255,0.8);
        margin: 0.5rem 0 0 0;
    }
    
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .badge-very-high { background: #dc2626; color: white; }
    .badge-high { background: #ea580c; color: white; }
    .badge-medium { background: #d97706; color: white; }
    .badge-low { background: #16a34a; color: white; }
    .badge-very-low { background: #15803d; color: white; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING FUNCTIONS - CACHED
# ============================================================================
@st.cache_data
def load_data():
    """Load and preprocess all data - cached for performance"""
    try:
        # Load CSV
        df = pd.read_csv("df_analisis_stunting_jabar_2024.csv")
        
        # Rename columns for consistency
        df = df.rename(columns={
            'prevalensi_stunting': 'persen_stunting',
            'persen_rumah_layak': 'persen_rumah_layak_huni'
        })
        
        # Calculate risk levels based on quartiles
        q1 = df['persen_stunting'].quantile(0.25)
        q2 = df['persen_stunting'].quantile(0.50)
        q3 = df['persen_stunting'].quantile(0.75)
        
        def get_risk_level(value):
            if value >= 25:
                return "Sangat Tinggi"
            elif value >= 20:
                return "Tinggi"
            elif value >= 15:
                return "Sedang"
            elif value >= 10:
                return "Rendah"
            else:
                return "Sangat Rendah"
        
        df['risk_level'] = df['persen_stunting'].apply(get_risk_level)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

@st.cache_data
def load_geojson():
    """Load GeoJSON data - cached"""
    try:
        with open("gdf_analisis_stunting_jabar_2024.geojson", 'r') as f:
            geojson_data = json.load(f)
        return geojson_data
    except Exception as e:
        st.error(f"Error loading GeoJSON: {e}")
        return None

@st.cache_data
def load_geodataframe():
    """Load as GeoDataFrame for spatial analysis - cached"""
    try:
        gdf = gpd.read_file("gdf_analisis_stunting_jabar_2024.geojson")
        return gdf
    except Exception as e:
        st.error(f"Error loading GeoDataFrame: {e}")
        return None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def get_risk_color(risk_level):
    """Get color for risk level"""
    colors = {
        "Sangat Rendah": "#15803d",
        "Rendah": "#16a34a",
        "Sedang": "#d97706",
        "Tinggi": "#ea580c",
        "Sangat Tinggi": "#dc2626"
    }
    return colors.get(risk_level, "#9E9E9E")

def get_risk_badge_class(risk_level):
    """Get badge class for risk level"""
    classes = {
        "Sangat Rendah": "badge-very-low",
        "Rendah": "badge-low",
        "Sedang": "badge-medium",
        "Tinggi": "badge-high",
        "Sangat Tinggi": "badge-very-high"
    }
    return classes.get(risk_level, "")

# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    # Header
    st.markdown("""
    <div class="header-card">
        <h1>📊 Dashboard Analisis Stunting Jawa Barat 2024</h1>
        <p>Studi Cross-Sectional Tingkat Kabupaten/Kota • Data Terintegrasi BPS & Dinkes</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("⚙️ Pengaturan")
    
    # Variable selection
    variable_options = {
        'Prevalensi Stunting (%)': 'persen_stunting',
        'Kepadatan Penduduk (jiwa/km²)': 'kepadatan_penduduk',
        'Air Minum Layak (%)': 'persen_air_minum_layak',
        'Penduduk Miskin (%)': 'persen_miskin',
        'Rumah Layak Huni (%)': 'persen_rumah_layak_huni'
    }
    
    selected_var_label = st.sidebar.selectbox(
        "Pilih Variabel:",
        options=list(variable_options.keys())
    )
    selected_var = variable_options[selected_var_label]
    
    # Color scheme
    color_schemes = ['Reds', 'Blues', 'Greens', 'Viridis', 'Plasma', 'YlOrRd']
    selected_color = st.sidebar.selectbox("Skema Warna:", color_schemes, index=0)
    
    # Load data
    with st.spinner("Memuat data..."):
        df = load_data()
        geojson_data = load_geojson()
        gdf = load_geodataframe()
    
    if df is None or geojson_data is None:
        st.error("Gagal memuat data. Periksa file data.")
        return
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🗺️ Peta Interaktif",
        "🔍 Profil Wilayah",
        "📊 Pola Risiko",
        "📈 Model Statistik",
        "📋 Ringkasan Data",
        "ℹ️ Panduan"
    ])
    
    # =========================================================================
    # TAB 1: PETA INTERAKTIF
    # =========================================================================
    with tab1:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_stunting = df['persen_stunting'].mean()
            st.metric("Rata-rata Stunting", f"{avg_stunting:.1f}%", delta=f"{avg_stunting-14:.1f}% dari target")
        
        with col2:
            high_risk = (df['risk_level'].isin(['Tinggi', 'Sangat Tinggi'])).sum()
            st.metric("Wilayah Risiko Tinggi", f"{high_risk}", delta=None)
        
        with col3:
            medium_risk = (df['risk_level'] == 'Sedang').sum()
            st.metric("Wilayah Risiko Sedang", f"{medium_risk}")
        
        with col4:
            low_risk = (df['risk_level'].isin(['Rendah', 'Sangat Rendah'])).sum()
            st.metric("Wilayah Risiko Rendah", f"{low_risk}")
        
        st.subheader(f"Peta {selected_var_label}")
        
        # Prepare data for choropleth
        df_map = df.copy()
        df_map['kode_kabkota'] = df_map['kode_kabkota'].astype(str)
        
        # Create choropleth using px.choropleth (faster than choropleth_map)
        with st.container(border=True):
            fig = px.choropleth(
                df_map,
                geojson=geojson_data,
                locations='kode_kabkota',
                featureidkey='properties.kode_kabkota',
                color=selected_var,
                hover_name='nama_kabkota',
                hover_data={
                    'kode_kabkota': False,
                    'persen_stunting': ':.1f',
                    'risk_level': True,
                    selected_var: ':.2f'
                },
                color_continuous_scale=selected_color,
                labels={selected_var: selected_var_label}
            )
            
            fig.update_geos(
                fitbounds="locations",
                visible=False,
                bgcolor='rgba(0,0,0,0)'
            )
            
            fig.update_layout(
                height=550,
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                paper_bgcolor='rgba(0,0,0,0)',
                geo=dict(bgcolor='rgba(0,0,0,0)')
            )
            
            st.plotly_chart(fig, use_container_width=True, key='main_map')
        
        st.info("💡 **Tips:** Arahkan kursor ke wilayah untuk melihat detail. Zoom dengan scroll mouse.")
    
    # =========================================================================
    # TAB 2: PROFIL WILAYAH
    # =========================================================================
    with tab2:
        selected_kabkota = st.selectbox(
            "Pilih Kabupaten/Kota:",
            options=sorted(df['nama_kabkota'].unique())
        )
        
        kabkota_data = df[df['nama_kabkota'] == selected_kabkota].iloc[0]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📍 Profil Risiko")
            
            risk_level = kabkota_data['risk_level']
            risk_color = get_risk_color(risk_level)
            
            st.markdown(f"""
            <div style="background-color: {risk_color}; padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h2 style="margin: 0; color: white;">{selected_kabkota}</h2>
                <h3 style="margin: 10px 0 0 0; color: white;">Risiko {risk_level}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            
            # Key metrics
            metrics_col1, metrics_col2 = st.columns(2)
            with metrics_col1:
                st.metric("Prevalensi Stunting", f"{kabkota_data['persen_stunting']:.1f}%")
                st.metric("Kepadatan Penduduk", f"{kabkota_data['kepadatan_penduduk']:,.0f} jiwa/km²")
            with metrics_col2:
                st.metric("Air Minum Layak", f"{kabkota_data['persen_air_minum_layak']:.1f}%")
                st.metric("Penduduk Miskin", f"{kabkota_data['persen_miskin']:.2f}%")
            
            st.metric("Rumah Layak Huni", f"{kabkota_data['persen_rumah_layak_huni']:.1f}%")
        
        with col2:
            st.subheader("🗺️ Lokasi")
            
            # Highlight selected kabkota on map
            df_highlight = df.copy()
            df_highlight['kode_kabkota'] = df_highlight['kode_kabkota'].astype(str)
            df_highlight['highlight'] = df_highlight['nama_kabkota'].apply(
                lambda x: 'Terpilih' if x == selected_kabkota else 'Lainnya'
            )
            
            fig_loc = px.choropleth(
                df_highlight,
                geojson=geojson_data,
                locations='kode_kabkota',
                featureidkey='properties.kode_kabkota',
                color='highlight',
                hover_name='nama_kabkota',
                color_discrete_map={'Terpilih': '#2196F3', 'Lainnya': '#E0E0E0'}
            )
            
            fig_loc.update_geos(fitbounds="locations", visible=False)
            fig_loc.update_layout(
                height=350,
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                showlegend=False
            )
            
            st.plotly_chart(fig_loc, use_container_width=True, key='profile_map')
        
        # Comparison chart
        st.subheader("📊 Perbandingan dengan Wilayah Lain")
        
        df_compare = df.sort_values('persen_stunting', ascending=True).copy()
        df_compare['is_selected'] = df_compare['nama_kabkota'] == selected_kabkota
        
        fig_compare = px.bar(
            df_compare,
            x='persen_stunting',
            y='nama_kabkota',
            orientation='h',
            color='is_selected',
            color_discrete_map={True: '#2196F3', False: '#E0E0E0'},
            labels={'persen_stunting': 'Prevalensi Stunting (%)', 'nama_kabkota': ''}
        )
        
        fig_compare.update_layout(
            height=600,
            showlegend=False,
            xaxis_title='Prevalensi Stunting (%)',
            yaxis_title=''
        )
        
        st.plotly_chart(fig_compare, use_container_width=True, key='compare_bar')
    
    # =========================================================================
    # TAB 3: POLA RISIKO
    # =========================================================================
    with tab3:
        st.subheader("📊 Distribusi Kategori Risiko")
        
        st.write("""
        Analisis ini mengkategorikan kabupaten/kota berdasarkan prevalensi stunting
        untuk mengidentifikasi wilayah prioritas intervensi.
        """)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Risk distribution pie chart
            risk_counts = df['risk_level'].value_counts()
            
            fig_pie = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                color=risk_counts.index,
                color_discrete_map={
                    'Sangat Tinggi': '#dc2626',
                    'Tinggi': '#ea580c',
                    'Sedang': '#d97706',
                    'Rendah': '#16a34a',
                    'Sangat Rendah': '#15803d'
                },
                hole=0.4
            )
            
            fig_pie.update_layout(
                height=400,
                legend=dict(orientation='h', yanchor='bottom', y=-0.2)
            )
            
            st.plotly_chart(fig_pie, use_container_width=True, key='risk_pie')
        
        with col2:
            # Risk by category bar
            fig_bar = px.bar(
                x=risk_counts.index,
                y=risk_counts.values,
                color=risk_counts.index,
                color_discrete_map={
                    'Sangat Tinggi': '#dc2626',
                    'Tinggi': '#ea580c',
                    'Sedang': '#d97706',
                    'Rendah': '#16a34a',
                    'Sangat Rendah': '#15803d'
                },
                labels={'x': 'Kategori Risiko', 'y': 'Jumlah Wilayah'}
            )
            
            fig_bar.update_layout(
                height=400,
                showlegend=False,
                xaxis_title='Kategori Risiko',
                yaxis_title='Jumlah Wilayah'
            )
            
            st.plotly_chart(fig_bar, use_container_width=True, key='risk_bar')
        
        # Map by risk level
        st.subheader("🗺️ Peta Kategori Risiko")
        
        df_risk = df.copy()
        df_risk['kode_kabkota'] = df_risk['kode_kabkota'].astype(str)
        
        with st.container(border=True):
            fig_risk_map = px.choropleth(
                df_risk,
                geojson=geojson_data,
                locations='kode_kabkota',
                featureidkey='properties.kode_kabkota',
                color='risk_level',
                hover_name='nama_kabkota',
                hover_data={'persen_stunting': ':.1f', 'kode_kabkota': False},
                color_discrete_map={
                    'Sangat Tinggi': '#dc2626',
                    'Tinggi': '#ea580c',
                    'Sedang': '#d97706',
                    'Rendah': '#16a34a',
                    'Sangat Rendah': '#15803d'
                },
                category_orders={'risk_level': ['Sangat Rendah', 'Rendah', 'Sedang', 'Tinggi', 'Sangat Tinggi']}
            )
            
            fig_risk_map.update_geos(fitbounds="locations", visible=False)
            fig_risk_map.update_layout(
                height=500,
                margin={"r": 0, "t": 0, "l": 0, "b": 0}
            )
            
            st.plotly_chart(fig_risk_map, use_container_width=True, key='risk_map')
        
        # Top/Bottom 5
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔴 5 Wilayah Tertinggi")
            top5 = df.nlargest(5, 'persen_stunting')[['nama_kabkota', 'persen_stunting', 'risk_level']]
            for _, row in top5.iterrows():
                st.markdown(f"**{row['nama_kabkota']}**: {row['persen_stunting']:.1f}% ({row['risk_level']})")
        
        with col2:
            st.markdown("### 🟢 5 Wilayah Terendah")
            bottom5 = df.nsmallest(5, 'persen_stunting')[['nama_kabkota', 'persen_stunting', 'risk_level']]
            for _, row in bottom5.iterrows():
                st.markdown(f"**{row['nama_kabkota']}**: {row['persen_stunting']:.1f}% ({row['risk_level']})")
    
    # =========================================================================
    # TAB 4: MODEL STATISTIK
    # =========================================================================
    with tab4:
        st.subheader("📈 Analisis Regresi Linear Berganda")
        
        st.write("""
        Model ini menganalisis hubungan antara faktor-faktor sosial ekonomi dengan prevalensi stunting.
        Variabel independen: Kepadatan Penduduk, Air Minum Layak, Kemiskinan, Rumah Layak Huni.
        """)
        
        # Model summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Ringkasan Model")
            with st.container(border=True):
                st.metric("R-squared", "0.074 (7.4%)")
                st.metric("Adjusted R²", "-0.095")
                st.metric("F-statistic", "0.437")
                st.metric("Prob (F-stat)", "0.780")
                st.metric("Observasi", "27")
        
        with col2:
            st.markdown("### ⚠️ Interpretasi")
            st.warning("""
            **Model Tidak Signifikan (p = 0.780)**
            
            - Faktor sosial ekonomi agregat hanya menjelaskan **7.4%** variasi stunting
            - Tidak ada variabel yang signifikan pada α = 0.05
            - Diperlukan data individu dan variabel tambahan (ASI, MP-ASI, layanan kesehatan)
            """)
        
        # Coefficients table
        st.markdown("### 📋 Koefisien Regresi")
        
        coef_data = pd.DataFrame({
            'Variabel': ['Konstanta', 'Kepadatan Penduduk', 'Air Minum Layak', 'Kemiskinan', 'Rumah Layak Huni'],
            'Koefisien': [2.028, -0.00009, 0.230, 0.037, -0.102],
            'Std. Error': [36.088, 0.0004, 0.414, 0.521, 0.087],
            't-value': [0.056, -0.243, 0.556, 0.071, -1.171],
            'p-value': [0.956, 0.811, 0.584, 0.944, 0.254],
            'Signifikan': ['❌', '❌', '❌', '❌', '❌']
        })
        
        st.dataframe(coef_data, hide_index=True)
        
        # Correlation heatmap
        st.markdown("### 🔗 Matriks Korelasi")
        
        corr_vars = ['persen_stunting', 'kepadatan_penduduk', 'persen_air_minum_layak', 
                     'persen_miskin', 'persen_rumah_layak_huni']
        corr_labels = ['Stunting', 'Kepadatan', 'Air Minum', 'Kemiskinan', 'Rumah Layak']
        
        corr_matrix = df[corr_vars].corr()
        
        with st.container(border=True):
            fig_corr = px.imshow(
                corr_matrix.values,
                x=corr_labels,
                y=corr_labels,
                color_continuous_scale='RdBu_r',
                zmin=-1, zmax=1,
                text_auto='.2f',
                aspect='auto'
            )
            
            fig_corr.update_layout(
                height=450,
                title="Korelasi Pearson antar Variabel"
            )
            
            st.plotly_chart(fig_corr, use_container_width=True, key='corr_heatmap')
        
        # Scatter plots
        st.markdown("### 📈 Scatter Plot dengan Garis Regresi")
        
        scatter_col1, scatter_col2 = st.columns(2)
        
        with scatter_col1:
            fig_s1 = px.scatter(
                df, x='persen_rumah_layak_huni', y='persen_stunting',
                hover_name='nama_kabkota',
                trendline='ols',
                labels={'persen_rumah_layak_huni': 'Rumah Layak Huni (%)', 
                        'persen_stunting': 'Prevalensi Stunting (%)'}
            )
            fig_s1.update_layout(height=350, title="Stunting vs Rumah Layak Huni")
            st.plotly_chart(fig_s1, use_container_width=True, key='scatter1')
        
        with scatter_col2:
            fig_s2 = px.scatter(
                df, x='persen_miskin', y='persen_stunting',
                hover_name='nama_kabkota',
                trendline='ols',
                labels={'persen_miskin': 'Penduduk Miskin (%)', 
                        'persen_stunting': 'Prevalensi Stunting (%)'}
            )
            fig_s2.update_layout(height=350, title="Stunting vs Kemiskinan")
            st.plotly_chart(fig_s2, use_container_width=True, key='scatter2')
    
    # =========================================================================
    # TAB 5: RINGKASAN DATA
    # =========================================================================
    with tab5:
        st.subheader("📋 Statistik Deskriptif")
        
        # Summary statistics
        summary_vars = ['persen_stunting', 'kepadatan_penduduk', 'persen_air_minum_layak', 
                        'persen_miskin', 'persen_rumah_layak_huni']
        summary_stats = df[summary_vars].describe().T
        summary_stats.index = ['Stunting (%)', 'Kepadatan (jiwa/km²)', 'Air Minum (%)', 
                               'Miskin (%)', 'Rumah Layak (%)']
        
        st.dataframe(summary_stats.round(2))
        
        st.subheader("📋 Data Lengkap")
        
        # Search
        search = st.text_input("🔍 Cari Kabupaten/Kota:", placeholder="Ketik nama...")
        
        df_display = df.copy()
        if search:
            df_display = df_display[df_display['nama_kabkota'].str.contains(search, case=False)]
        
        # Sort option
        sort_col = st.selectbox("Urutkan berdasarkan:", list(variable_options.keys()))
        df_display = df_display.sort_values(variable_options[sort_col], ascending=False)
        
        # Display columns
        display_cols = ['nama_kabkota', 'persen_stunting', 'risk_level', 
                        'kepadatan_penduduk', 'persen_air_minum_layak', 
                        'persen_miskin', 'persen_rumah_layak_huni']
        
        df_show = df_display[display_cols].copy()
        df_show.columns = ['Kabupaten/Kota', 'Stunting (%)', 'Kategori', 
                           'Kepadatan', 'Air Minum (%)', 'Miskin (%)', 'Rumah Layak (%)']
        
        st.dataframe(df_show, hide_index=True, height=400)
        
        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data (CSV)",
            data=csv,
            file_name="data_stunting_jabar_2024.csv",
            mime="text/csv"
        )
    
    # =========================================================================
    # TAB 6: PANDUAN
    # =========================================================================
    with tab6:
        st.subheader("📖 Panduan Penggunaan Dashboard")
        
        st.markdown("""
        ### 1. 🗺️ Tab Peta Interaktif
        - Lihat distribusi stunting di seluruh kabupaten/kota Jawa Barat
        - Pilih variabel yang ingin divisualisasikan di sidebar
        - Arahkan kursor ke wilayah untuk melihat detail
        - Warna semakin gelap = nilai semakin tinggi
        
        ### 2. 🔍 Tab Profil Wilayah
        - Pilih kabupaten/kota untuk melihat profil detail
        - Bandingkan dengan wilayah lain melalui bar chart
        - Lihat lokasi wilayah pada peta
        
        ### 3. 📊 Tab Pola Risiko
        - Lihat distribusi kategori risiko stunting
        - Identifikasi wilayah prioritas (risiko tinggi)
        - Lihat top 5 tertinggi dan terendah
        
        ### 4. 📈 Tab Model Statistik
        - Hasil analisis regresi linear berganda
        - Matriks korelasi antar variabel
        - Scatter plot dengan trendline
        
        ### 5. 📋 Tab Ringkasan Data
        - Statistik deskriptif semua variabel
        - Pencarian dan filter data
        - Download data dalam format CSV
        
        ---
        
        ### 🎨 Keterangan Warna Kategori Risiko
        
        | Kategori | Prevalensi | Warna |
        |----------|------------|-------|
        | Sangat Tinggi | ≥25% | 🔴 Merah Tua |
        | Tinggi | 20-24.9% | 🟠 Oranye |
        | Sedang | 15-19.9% | 🟡 Kuning |
        | Rendah | 10-14.9% | 🟢 Hijau |
        | Sangat Rendah | <10% | 🟢 Hijau Tua |
        
        ---
        
        ### 📊 Tentang Data
        
        - **Sumber:** BPS & Dinas Kesehatan Provinsi Jawa Barat
        - **Tahun Data:** 2024
        - **Unit Analisis:** 27 Kabupaten/Kota
        - **Variabel:** Prevalensi Stunting, Kepadatan Penduduk, Akses Air Minum, 
          Kemiskinan, Rumah Layak Huni
        """)

# ============================================================================
# RUN APPLICATION
# ============================================================================
if __name__ == "__main__":
    main()
