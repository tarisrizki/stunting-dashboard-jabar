"""
============================================================================
DASHBOARD STUNTING JAWA BARAT 2024 - ULTRA FAST VERSION
============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

# ============================================================================
# PAGE CONFIG - MUST BE FIRST
# ============================================================================
st.set_page_config(
    page_title="Dashboard Stunting Jabar 2024",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS STYLING
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp { font-family: 'Inter', sans-serif; }
    
    .header-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .header-card h1 { color: white; margin: 0; font-size: 1.75rem; }
    .header-card p { color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; }
    
    .metric-box {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border-left: 4px solid #3b82f6;
    }
    
    .risk-very-high { background: #fef2f2; border-left-color: #dc2626; }
    .risk-high { background: #fff7ed; border-left-color: #ea580c; }
    .risk-medium { background: #fffbeb; border-left-color: #d97706; }
    .risk-low { background: #f0fdf4; border-left-color: #16a34a; }
    
    #MainMenu, footer, header { visibility: hidden; }
    
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    div[data-testid="stMetric"] label {
        color: #6b7280 !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #111827 !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING - ULTRA CACHED
# ============================================================================
@st.cache_data(ttl=3600)
def load_all_data():
    """Load all data at once - cached for 1 hour"""
    # Load CSV
    df = pd.read_csv("df_analisis_stunting_jabar_2024.csv")
    df = df.rename(columns={
        'prevalensi_stunting': 'persen_stunting',
        'persen_rumah_layak': 'persen_rumah_layak_huni'
    })
    
    # Calculate risk levels
    def get_risk(val):
        if val >= 25: return "Sangat Tinggi"
        elif val >= 20: return "Tinggi"
        elif val >= 15: return "Sedang"
        elif val >= 10: return "Rendah"
        return "Sangat Rendah"
    
    df['risk_level'] = df['persen_stunting'].apply(get_risk)
    df['kode_kabkota'] = df['kode_kabkota'].astype(str)
    
    # Load simplified GeoJSON
    with open("gdf_stunting_simplified.geojson", 'r') as f:
        geojson = json.load(f)
    
    return df, geojson

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
RISK_COLORS = {
    "Sangat Tinggi": "#dc2626",
    "Tinggi": "#ea580c", 
    "Sedang": "#d97706",
    "Rendah": "#16a34a",
    "Sangat Rendah": "#15803d"
}

def create_choropleth(df, geojson, color_col, color_scale, title=""):
    """Create optimized choropleth map"""
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations='kode_kabkota',
        featureidkey='properties.kode_kabkota',
        color=color_col,
        hover_name='nama_kabkota',
        hover_data={'kode_kabkota': False, color_col: ':.2f'},
        color_continuous_scale=color_scale
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        height=500,
        margin={"r":0,"t":30,"l":0,"b":0},
        title=title
    )
    return fig

def create_risk_map(df, geojson):
    """Create categorical risk map"""
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations='kode_kabkota',
        featureidkey='properties.kode_kabkota',
        color='risk_level',
        hover_name='nama_kabkota',
        hover_data={'persen_stunting': ':.1f', 'kode_kabkota': False},
        color_discrete_map=RISK_COLORS,
        category_orders={'risk_level': ['Sangat Rendah','Rendah','Sedang','Tinggi','Sangat Tinggi']}
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=500, margin={"r":0,"t":0,"l":0,"b":0})
    return fig

# ============================================================================
# MAIN APP
# ============================================================================
def main():
    # Header
    st.markdown("""
    <div class="header-card">
        <h1>📊 Dashboard Stunting Jawa Barat 2024</h1>
        <p>Analisis Spasial Prevalensi Stunting Tingkat Kabupaten/Kota</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data once
    df, geojson = load_all_data()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Pengaturan")
        
        var_options = {
            'Prevalensi Stunting (%)': 'persen_stunting',
            'Kepadatan Penduduk': 'kepadatan_penduduk',
            'Air Minum Layak (%)': 'persen_air_minum_layak',
            'Penduduk Miskin (%)': 'persen_miskin',
            'Rumah Layak Huni (%)': 'persen_rumah_layak_huni'
        }
        selected_label = st.selectbox("📌 Variabel Peta:", list(var_options.keys()))
        selected_var = var_options[selected_label]
        
        color_opt = st.selectbox("🎨 Skema Warna:", ['Reds','Blues','Greens','Viridis','YlOrRd'])
        
        st.divider()
        st.caption("Data: BPS & Dinkes Jabar 2024")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Peta", "📊 Risiko", "🔍 Profil", "📈 Statistik", "📋 Data"
    ])
    
    # =========================================================================
    # TAB 1: PETA
    # =========================================================================
    with tab1:
        # Dynamic Metrics based on selected variable
        avg_val = df[selected_var].mean()
        max_val = df[selected_var].max()
        min_val = df[selected_var].min()
        std_val = df[selected_var].std()
        
        # Get max/min kabkota names
        max_kab = df.loc[df[selected_var].idxmax(), 'nama_kabkota']
        min_kab = df.loc[df[selected_var].idxmin(), 'nama_kabkota']
        
        # Risk counts for stunting
        high_risk = (df['risk_level'].isin(['Tinggi', 'Sangat Tinggi'])).sum()
        low_risk = (df['risk_level'].isin(['Rendah', 'Sangat Rendah'])).sum()
        
        # Target nasional stunting = 14%
        target_nasional = 14.0
        delta_target = avg_val - target_nasional if selected_var == 'persen_stunting' else None
        
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            if selected_var == 'persen_stunting':
                st.metric(
                    "📊 Rata-rata Stunting", 
                    f"{avg_val:.1f}%",
                    delta=f"{delta_target:+.1f}% dari target 14%",
                    delta_color="inverse"
                )
            else:
                st.metric(f"📊 Rata-rata", f"{avg_val:,.1f}")
        
        with c2:
            st.metric(
                "🔴 Tertinggi", 
                f"{max_val:,.1f}{'%' if 'persen' in selected_var else ''}",
                delta=f"{max_kab}",
                delta_color="off"
            )
        
        with c3:
            st.metric(
                "🟢 Terendah", 
                f"{min_val:,.1f}{'%' if 'persen' in selected_var else ''}",
                delta=f"{min_kab}",
                delta_color="off"
            )
        
        with c4:
            if selected_var == 'persen_stunting':
                st.metric(
                    "⚠️ Wilayah Risiko Tinggi", 
                    f"{high_risk} dari {len(df)}",
                    delta=f"{high_risk/len(df)*100:.0f}% wilayah",
                    delta_color="inverse"
                )
            else:
                st.metric(
                    "📍 Total Wilayah", 
                    f"{len(df)}",
                    delta=f"Std: {std_val:,.1f}",
                    delta_color="off"
                )
        
        st.subheader(f"🗺️ {selected_label}")
        fig = create_choropleth(df, geojson, selected_var, color_opt)
        st.plotly_chart(fig, key="map1")
    
    # =========================================================================
    # TAB 2: RISIKO
    # =========================================================================
    with tab2:
        st.subheader("📊 Kategori Risiko Stunting")
        
        col1, col2 = st.columns(2)
        
        with col1:
            risk_counts = df['risk_level'].value_counts()
            fig_pie = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                color=risk_counts.index,
                color_discrete_map=RISK_COLORS,
                hole=0.4
            )
            fig_pie.update_layout(height=350)
            st.plotly_chart(fig_pie, key="pie1")
        
        with col2:
            fig_bar = px.bar(
                x=risk_counts.index,
                y=risk_counts.values,
                color=risk_counts.index,
                color_discrete_map=RISK_COLORS
            )
            fig_bar.update_layout(height=350, showlegend=False,
                                  xaxis_title="Kategori", yaxis_title="Jumlah")
            st.plotly_chart(fig_bar, key="bar1")
        
        st.subheader("🗺️ Peta Risiko")
        fig_risk = create_risk_map(df, geojson)
        st.plotly_chart(fig_risk, key="risk_map")
        
        # Top/Bottom
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🔴 Top 5 Tertinggi")
            for _, r in df.nlargest(5, 'persen_stunting').iterrows():
                st.write(f"**{r['nama_kabkota']}**: {r['persen_stunting']:.1f}%")
        with col2:
            st.markdown("### 🟢 Top 5 Terendah")
            for _, r in df.nsmallest(5, 'persen_stunting').iterrows():
                st.write(f"**{r['nama_kabkota']}**: {r['persen_stunting']:.1f}%")
    
    # =========================================================================
    # TAB 3: PROFIL WILAYAH
    # =========================================================================
    with tab3:
        st.subheader("🔍 Profil Wilayah")
        
        selected = st.selectbox("Pilih Kabupaten/Kota:", sorted(df['nama_kabkota'].unique()))
        data = df[df['nama_kabkota'] == selected].iloc[0]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            risk = data['risk_level']
            color = RISK_COLORS[risk]
            st.markdown(f"""
            <div style="background:{color}; padding:20px; border-radius:10px; color:white; text-align:center;">
                <h2 style="margin:0; color:white;">{selected}</h2>
                <h3 style="margin:10px 0 0 0; color:white;">Risiko {risk}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            m1, m2 = st.columns(2)
            m1.metric("Stunting", f"{data['persen_stunting']:.1f}%")
            m2.metric("Kepadatan", f"{data['kepadatan_penduduk']:,.0f}")
            m1.metric("Air Minum", f"{data['persen_air_minum_layak']:.1f}%")
            m2.metric("Miskin", f"{data['persen_miskin']:.2f}%")
        
        with col2:
            # Highlight map
            df_hl = df.copy()
            df_hl['highlight'] = df_hl['nama_kabkota'].apply(
                lambda x: 'Terpilih' if x == selected else 'Lainnya'
            )
            fig_loc = px.choropleth(
                df_hl, geojson=geojson,
                locations='kode_kabkota',
                featureidkey='properties.kode_kabkota',
                color='highlight',
                hover_name='nama_kabkota',
                color_discrete_map={'Terpilih': '#2196F3', 'Lainnya': '#E0E0E0'}
            )
            fig_loc.update_geos(fitbounds="locations", visible=False)
            fig_loc.update_layout(height=300, margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False)
            st.plotly_chart(fig_loc, key="loc_map")
        
        # Comparison bar
        st.subheader("📊 Perbandingan")
        df_sort = df.sort_values('persen_stunting')
        df_sort['is_sel'] = df_sort['nama_kabkota'] == selected
        fig_cmp = px.bar(
            df_sort, x='persen_stunting', y='nama_kabkota', orientation='h',
            color='is_sel', color_discrete_map={True:'#2196F3', False:'#E0E0E0'}
        )
        fig_cmp.update_layout(height=600, showlegend=False, xaxis_title="Stunting (%)", yaxis_title="")
        st.plotly_chart(fig_cmp, key="cmp_bar")
    
    # =========================================================================
    # TAB 4: STATISTIK
    # =========================================================================
    with tab4:
        st.subheader("📈 Analisis Statistik")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Model Regresi OLS")
            st.info("""
            **R² = 0.074 (7.4%)** - Model tidak signifikan (p=0.780)
            
            Faktor sosial ekonomi agregat tidak cukup menjelaskan variasi stunting.
            Diperlukan data level individu (ASI, MP-ASI, layanan kesehatan).
            """)
            
            coef = pd.DataFrame({
                'Variabel': ['Kepadatan', 'Air Minum', 'Kemiskinan', 'Rumah Layak'],
                'Koef': [-0.0001, 0.230, 0.037, -0.102],
                'p-value': [0.811, 0.584, 0.944, 0.254]
            })
            st.dataframe(coef, hide_index=True)
        
        with col2:
            st.markdown("### Korelasi")
            corr_vars = ['persen_stunting', 'kepadatan_penduduk', 
                        'persen_air_minum_layak', 'persen_miskin', 'persen_rumah_layak_huni']
            labels = ['Stunting', 'Kepadatan', 'Air Minum', 'Miskin', 'Rumah Layak']
            corr = df[corr_vars].corr()
            
            fig_corr = px.imshow(
                corr.values, x=labels, y=labels,
                color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
                text_auto='.2f'
            )
            fig_corr.update_layout(height=400)
            st.plotly_chart(fig_corr, key="corr")
        
        # Scatter
        st.markdown("### Scatter Plots")
        sc1, sc2 = st.columns(2)
        with sc1:
            fig_s1 = px.scatter(df, x='persen_rumah_layak_huni', y='persen_stunting',
                               hover_name='nama_kabkota', trendline='ols')
            fig_s1.update_layout(height=300, title="Stunting vs Rumah Layak")
            st.plotly_chart(fig_s1, key="sc1")
        with sc2:
            fig_s2 = px.scatter(df, x='persen_miskin', y='persen_stunting',
                               hover_name='nama_kabkota', trendline='ols')
            fig_s2.update_layout(height=300, title="Stunting vs Kemiskinan")
            st.plotly_chart(fig_s2, key="sc2")
    
    # =========================================================================
    # TAB 5: DATA
    # =========================================================================
    with tab5:
        st.subheader("📋 Data Lengkap")
        
        # Stats
        st.markdown("### Statistik Deskriptif")
        stats_cols = ['persen_stunting', 'kepadatan_penduduk', 'persen_air_minum_layak', 
                      'persen_miskin', 'persen_rumah_layak_huni']
        st.dataframe(df[stats_cols].describe().T.round(2))
        
        # Search & Display
        st.markdown("### Tabel Data")
        search = st.text_input("🔍 Cari:", placeholder="Nama kabupaten/kota...")
        
        df_show = df.copy()
        if search:
            df_show = df_show[df_show['nama_kabkota'].str.contains(search, case=False)]
        
        display_cols = ['nama_kabkota', 'persen_stunting', 'risk_level',
                        'kepadatan_penduduk', 'persen_air_minum_layak', 
                        'persen_miskin', 'persen_rumah_layak_huni']
        
        st.dataframe(df_show[display_cols].sort_values('persen_stunting', ascending=False), 
                     hide_index=True, height=400)
        
        # Download
        st.download_button(
            "📥 Download CSV",
            df.to_csv(index=False).encode('utf-8'),
            "stunting_jabar_2024.csv",
            "text/csv"
        )

# ============================================================================
# RUN
# ============================================================================
if __name__ == "__main__":
    main()
