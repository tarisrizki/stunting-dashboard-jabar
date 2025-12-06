"""
============================================================================
DASHBOARD ANALISIS SPASIAL STUNTING JAWA BARAT 2024
Inspired by: Indonesia Disease Risk Explorer (faradra)
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

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Stunting Risk Explorer - Jawa Barat 2024",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp { font-family: 'Inter', sans-serif; }
    
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
    
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    div[data-testid="stMetric"] label {
        color: #6b7280 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #111827 !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING FUNCTIONS - CACHED
# ============================================================================
@st.cache_data
def load_csv_data():
    """Load and preprocess CSV data"""
    df = pd.read_csv("df_analisis_stunting_jabar_2024.csv")
    
    # Rename columns - SESUAI DATASET ASLI
    df = df.rename(columns={
        'prevalensi_stunting': 'persen_stunting',
        'persen_rumah_layak': 'persen_rumah_layak_huni'
    })
    
    # Pastikan tipe data benar
    df['kode_kabkota'] = df['kode_kabkota'].astype(str)
    
    # Calculate risk levels based on quartiles (seperti referensi)
    q1 = df['persen_stunting'].quantile(0.25)
    q2 = df['persen_stunting'].quantile(0.50)
    q3 = df['persen_stunting'].quantile(0.75)
    
    def get_risk_level(value):
        if pd.isna(value):
            return "No Data"
        elif value >= q3:
            return "Very High Risk"
        elif value >= q2:
            return "High Risk"
        elif value >= q1:
            return "Medium Risk"
        else:
            return "Low Risk"
    
    df['risk_level'] = df['persen_stunting'].apply(get_risk_level)
    
    return df

@st.cache_data
def load_geojson_data():
    """Load simplified GeoJSON"""
    with open("gdf_stunting_simplified.geojson", 'r') as f:
        geojson = json.load(f)
    return geojson

@st.cache_data
def load_geodataframe():
    """Load as GeoDataFrame for spatial analysis"""
    gdf = gpd.read_file("gdf_stunting_simplified.geojson")
    return gdf

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
RISK_COLORS = {
    "Low Risk": "#F6D746",
    "Medium Risk": "#E55C30",
    "High Risk": "#84206B",
    "Very High Risk": "#140B34",
    "No Data": "#9E9E9E"
}

def get_risk_color(risk_level):
    """Get color for risk level"""
    return RISK_COLORS.get(risk_level, "#9E9E9E")

# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    st.title("📊 Stunting Risk Explorer - Jawa Barat 2024")
    
    # =========================================================================
    # SIDEBAR
    # =========================================================================
    st.sidebar.header("⚙️ Pengaturan")
    
    # Variable selection - SESUAI KOLOM DATASET
    var_options = {
        'persen_stunting': '📊 Prevalensi Stunting (%)',
        'kepadatan_penduduk': '👥 Kepadatan Penduduk (jiwa/km²)',
        'persen_air_minum_layak': '💧 Akses Air Minum Layak (%)',
        'persen_miskin': '💰 Penduduk Miskin (%)',
        'persen_rumah_layak_huni': '🏠 Rumah Layak Huni (%)',
        'persen_sanitasi_layak': '🚽 Sanitasi Layak (%)'
    }
    
    selected_var = st.sidebar.selectbox(
        "Pilih Variabel:",
        options=list(var_options.keys()),
        format_func=lambda x: var_options[x]
    )
    
    # Risk factors selection
    risk_factors = {
        'kepadatan_penduduk': 'Kepadatan Penduduk',
        'persen_air_minum_layak': 'Akses Air Minum',
        'persen_miskin': 'Kemiskinan',
        'persen_rumah_layak_huni': 'Rumah Layak Huni',
        'persen_sanitasi_layak': 'Sanitasi Layak'
    }
    
    selected_factors = st.sidebar.multiselect(
        "Faktor Risiko:",
        options=list(risk_factors.keys()),
        default=['persen_miskin', 'persen_air_minum_layak'],
        format_func=lambda x: risk_factors[x]
    )
    
    st.sidebar.divider()
    st.sidebar.caption("📅 Data: 2024")
    st.sidebar.caption("📍 Sumber: BPS & Dinkes Jabar")
    
    # =========================================================================
    # LOAD DATA
    # =========================================================================
    with st.spinner("Memuat data..."):
        df = load_csv_data()
        geojson = load_geojson_data()
        gdf = load_geodataframe()
    
    if df is None:
        st.error("Gagal memuat data!")
        return
    
    # =========================================================================
    # TABS - 6 TABS SEPERTI REFERENSI
    # =========================================================================
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
        # METRICS DINAMIS - berubah sesuai variabel
        col1, col2, col3, col4 = st.columns(4)
        
        # Hitung statistik untuk variabel terpilih
        total_cases = df['jumlah_stunting'].sum() if 'jumlah_stunting' in df.columns else 0
        avg_val = df[selected_var].mean()
        max_val = df[selected_var].max()
        min_val = df[selected_var].min()
        max_kab = df.loc[df[selected_var].idxmax(), 'nama_kabkota']
        min_kab = df.loc[df[selected_var].idxmin(), 'nama_kabkota']
        
        # Risk counts
        high_risk_count = (df['risk_level'].isin(['High Risk', 'Very High Risk'])).sum()
        medium_risk_count = (df['risk_level'] == 'Medium Risk').sum()
        low_risk_count = (df['risk_level'] == 'Low Risk').sum()
        
        with col1:
            if selected_var == 'persen_stunting':
                st.metric(
                    "Total Kasus Stunting", 
                    f"{int(total_cases):,}",
                    delta=f"dari {len(df)} wilayah",
                    delta_color="off"
                )
            else:
                st.metric(
                    f"Rata-rata {var_options[selected_var].split(' ')[1]}", 
                    f"{avg_val:,.1f}",
                    delta=f"Std: {df[selected_var].std():,.1f}",
                    delta_color="off"
                )
        
        with col2:
            st.metric(
                "Wilayah Risiko Tinggi", 
                f"{high_risk_count}",
                delta=f"{high_risk_count/len(df)*100:.0f}% wilayah",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                "Wilayah Risiko Sedang", 
                f"{medium_risk_count}",
                delta=f"{medium_risk_count/len(df)*100:.0f}% wilayah",
                delta_color="off"
            )
        
        with col4:
            st.metric(
                "Wilayah Risiko Rendah", 
                f"{low_risk_count}",
                delta=f"{low_risk_count/len(df)*100:.0f}% wilayah",
                delta_color="normal"
            )
        
        # MAP
        st.subheader(f"Peta {var_options[selected_var]}")
        
        with st.container(border=True):
            # Choropleth dengan risk level (seperti referensi)
            fig = px.choropleth(
                df,
                geojson=geojson,
                locations='kode_kabkota',
                featureidkey='properties.kode_kabkota',
                color='risk_level',
                hover_name='nama_kabkota',
                hover_data={
                    'kode_kabkota': False,
                    'persen_stunting': ':.1f',
                    'jumlah_stunting': ':,.0f',
                    'risk_level': True
                },
                color_discrete_map=RISK_COLORS,
                category_orders={'risk_level': ['Low Risk', 'Medium Risk', 'High Risk', 'Very High Risk']}
            )
            
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(
                height=550,
                margin={"r":0,"t":0,"l":0,"b":0},
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.1,
                    xanchor="center",
                    x=0.5
                )
            )
            
            st.plotly_chart(fig, key="main_map")
        
        st.info("💡 **Tips:** Kuning Muda = Risiko Rendah, Kuning-Oranye = Sedang, Oranye = Tinggi, Merah = Sangat Tinggi")
    
    # =========================================================================
    # TAB 2: PROFIL WILAYAH (Province Explorer)
    # =========================================================================
    with tab2:
        selected_kabkota = st.selectbox(
            "Pilih Kabupaten/Kota:",
            options=sorted(df['nama_kabkota'].unique())
        )
        
        kab_data = df[df['nama_kabkota'] == selected_kabkota].iloc[0]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📍 Profil Risiko")
            
            risk_level = kab_data['risk_level']
            risk_color = get_risk_color(risk_level)
            # Text color: dark for light backgrounds, white for dark backgrounds
            text_color = "#333333" if risk_level in ["Low Risk", "Medium Risk"] else "#ffffff"
            
            st.markdown(f"""
            <div style="background-color: {risk_color}; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid rgba(0,0,0,0.1);">
                <h2 style="margin: 0; color: {text_color};">{selected_kabkota}</h2>
                <h3 style="margin: 10px 0 0 0; color: {text_color};">{risk_level}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            st.write(f"**Prevalensi Stunting:** {kab_data['persen_stunting']:.1f}%")
            st.write(f"**Jumlah Balita Stunting:** {int(kab_data['jumlah_stunting']):,}")
            st.write(f"**Kepadatan Penduduk:** {kab_data['kepadatan_penduduk']:,.0f} jiwa/km²")
            st.write("")
            st.write(f"**Akses Air Minum Layak:** {kab_data['persen_air_minum_layak']:.1f}%")
            st.write(f"**Sanitasi Layak:** {kab_data['persen_sanitasi_layak']:.1f}%")
            st.write(f"**Rumah Layak Huni:** {kab_data['persen_rumah_layak_huni']:.1f}%")
            st.write(f"**Penduduk Miskin:** {kab_data['persen_miskin']:.2f}%")
        
        with col2:
            st.subheader("🗺️ Lokasi")
            
            # Highlight selected kabkota
            df_map = df.copy()
            df_map['map_category'] = df_map.apply(
                lambda x: 'Terpilih' if x['nama_kabkota'] == selected_kabkota else x['risk_level'],
                axis=1
            )
            
            # Updated color map with professional palette
            color_map = {
                'Terpilih': '#3182bd',        # Blue for selected
                'Low Risk': '#ffffb2',         # Light yellow
                'Medium Risk': '#fecc5c',      # Yellow-orange
                'High Risk': '#fd8d3c',        # Orange
                'Very High Risk': '#e31a1c'    # Red
            }
            
            fig_loc = px.choropleth(
                df_map,
                geojson=geojson,
                locations='kode_kabkota',
                featureidkey='properties.kode_kabkota',
                color='map_category',
                hover_name='nama_kabkota',
                hover_data={'kode_kabkota': False, 'persen_stunting': ':.1f'},
                color_discrete_map=color_map
            )
            
            fig_loc.update_geos(fitbounds="locations", visible=False)
            fig_loc.update_layout(
                height=350,
                margin={"r":0,"t":0,"l":0,"b":0},
                showlegend=False
            )
            
            st.plotly_chart(fig_loc, key="loc_map")
        
        # Comparison bar chart
        st.subheader("📊 Perbandingan dengan Wilayah Lain")
        
        df_sorted = df.sort_values('persen_stunting', ascending=True)
        
        fig_bar = px.bar(
            df_sorted,
            x='persen_stunting',
            y='nama_kabkota',
            orientation='h',
            color='risk_level',
            color_discrete_map=RISK_COLORS,
            category_orders={'risk_level': ['Low Risk', 'Medium Risk', 'High Risk', 'Very High Risk']},
            hover_data={'persen_stunting': ':.1f', 'risk_level': True}
        )
        
        # Highlight selected kabkota with marker
        selected_idx = df_sorted[df_sorted['nama_kabkota'] == selected_kabkota].index[0]
        fig_bar.add_annotation(
            x=df_sorted.loc[selected_idx, 'persen_stunting'] + 1,
            y=selected_kabkota,
            text="◀ Terpilih",
            showarrow=False,
            font=dict(size=12, color="#3182bd")
        )
        
        fig_bar.update_layout(
            height=650,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_title="Prevalensi Stunting (%)",
            yaxis_title=""
        )
        
        st.plotly_chart(fig_bar, key="compare_bar")
    
    # =========================================================================
    # TAB 3: POLA RISIKO
    # =========================================================================
    with tab3:
        st.subheader("📊 Analisis Distribusi Risiko Stunting")
        
        st.write("""
        Analisis ini menunjukkan distribusi kabupaten/kota berdasarkan tingkat risiko stunting
        untuk mengidentifikasi wilayah prioritas intervensi.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            risk_counts = df['risk_level'].value_counts()
            
            fig_pie = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                color=risk_counts.index,
                color_discrete_map=RISK_COLORS,
                hole=0.4,
                title="Distribusi Kategori Risiko"
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, key="risk_pie")
        
        with col2:
            # Bar chart
            fig_bar_risk = px.bar(
                x=risk_counts.index,
                y=risk_counts.values,
                color=risk_counts.index,
                color_discrete_map=RISK_COLORS,
                title="Jumlah Wilayah per Kategori",
                labels={'x': 'Kategori Risiko', 'y': 'Jumlah Wilayah'}
            )
            fig_bar_risk.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_bar_risk, key="risk_bar")
        
        # Top/Bottom 5
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔴 5 Wilayah Prevalensi Tertinggi")
            top5 = df.nlargest(5, 'persen_stunting')[['nama_kabkota', 'persen_stunting', 'risk_level', 'jumlah_stunting']]
            for i, (_, row) in enumerate(top5.iterrows(), 1):
                color = get_risk_color(row['risk_level'])
                text_color = "#333333" if row['risk_level'] in ["Low Risk", "Medium Risk"] else "#ffffff"
                st.markdown(f"""
                <div style="background-color: {color}; padding: 12px 15px; border-radius: 8px; margin: 5px 0; border: 1px solid rgba(0,0,0,0.1);">
                    <strong style="color: {text_color};">{i}. {row['nama_kabkota']}</strong><br>
                    <span style="color: {text_color};">{row['persen_stunting']:.1f}% ({int(row['jumlah_stunting']):,} balita)</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 🟢 5 Wilayah Prevalensi Terendah")
            bottom5 = df.nsmallest(5, 'persen_stunting')[['nama_kabkota', 'persen_stunting', 'risk_level', 'jumlah_stunting']]
            for i, (_, row) in enumerate(bottom5.iterrows(), 1):
                color = get_risk_color(row['risk_level'])
                text_color = "#333333" if row['risk_level'] in ["Low Risk", "Medium Risk"] else "#ffffff"
                st.markdown(f"""
                <div style="background-color: {color}; padding: 12px 15px; border-radius: 8px; margin: 5px 0; border: 1px solid rgba(0,0,0,0.1);">
                    <strong style="color: {text_color};">{i}. {row['nama_kabkota']}</strong><br>
                    <span style="color: {text_color};">{row['persen_stunting']:.1f}% ({int(row['jumlah_stunting']):,} balita)</span>
                </div>
                """, unsafe_allow_html=True)
        
        # Interpretasi
        if high_risk_count > len(df) * 0.3:
            st.error(f"""
            🔥 **Perhatian!** {high_risk_count} dari {len(df)} wilayah ({high_risk_count/len(df)*100:.0f}%) 
            berada dalam kategori risiko tinggi/sangat tinggi.
            
            **Rekomendasi:** Prioritaskan intervensi pada wilayah dengan prevalensi tertinggi.
            """)
        else:
            st.success(f"""
            ✅ Sebagian besar wilayah ({low_risk_count + medium_risk_count} dari {len(df)}) 
            berada dalam kategori risiko rendah-sedang.
            """)
    
    # =========================================================================
    # TAB 4: MODEL STATISTIK
    # =========================================================================
    with tab4:
        st.subheader("📈 Faktor yang Mempengaruhi Stunting")
        
        st.write("""
        Analisis ini menggunakan regresi untuk memahami hubungan antara faktor sosial ekonomi
        dengan prevalensi stunting di Jawa Barat.
        """)
        
        if len(selected_factors) > 0:
            # Show selected factors info
            st.info(f"📌 **Faktor yang dianalisis:** {', '.join([risk_factors[f] for f in selected_factors])}")
            
            # Correlation matrix
            st.subheader("🔗 Hubungan Antar Variabel")
            
            corr_vars = ['persen_stunting'] + selected_factors
            corr_matrix = df[corr_vars].corr()
            
            # Rename for display
            rename_dict = {'persen_stunting': 'Stunting'}
            rename_dict.update({k: risk_factors[k] for k in selected_factors})
            corr_display = corr_matrix.rename(columns=rename_dict, index=rename_dict)
            
            with st.container(border=True):
                fig_corr = px.imshow(
                    corr_display.values,
                    x=corr_display.columns,
                    y=corr_display.index,
                    color_continuous_scale='RdBu_r',
                    zmin=-1, zmax=1,
                    text_auto='.2f',
                    aspect='auto'
                )
                fig_corr.update_layout(height=450, title="Matriks Korelasi")
                st.plotly_chart(fig_corr, key="corr_matrix")
            
            # Dynamic correlation interpretation
            st.subheader("📊 Interpretasi Korelasi")
            
            corr_with_stunting = corr_matrix['persen_stunting'].drop('persen_stunting')
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Korelasi dengan Stunting:**")
                for factor in selected_factors:
                    corr_val = corr_with_stunting[factor]
                    direction = "↑ Positif" if corr_val > 0 else "↓ Negatif"
                    strength = "Kuat" if abs(corr_val) > 0.5 else "Sedang" if abs(corr_val) > 0.3 else "Lemah"
                    color = "#e31a1c" if corr_val > 0.3 else "#fd8d3c" if corr_val > 0 else "#3182bd"
                    st.markdown(f"- **{risk_factors[factor]}**: `{corr_val:.3f}` ({direction}, {strength})")
            
            with col2:
                # Find strongest correlation
                strongest = corr_with_stunting.abs().idxmax()
                strongest_val = corr_with_stunting[strongest]
                st.metric(
                    "Faktor Paling Berkorelasi",
                    risk_factors[strongest],
                    delta=f"r = {strongest_val:.3f}",
                    delta_color="off"
                )
            
            # Model results - NOW DYNAMIC based on selected factors
            st.subheader("📊 Hasil Model Regresi OLS")
            
            # Calculate OLS dynamically
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score
            
            X = df[selected_factors].values
            y = df['persen_stunting'].values
            
            model = LinearRegression()
            model.fit(X, y)
            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("R-squared", f"{r2:.3f} ({r2*100:.1f}%)")
                st.metric("Jumlah Faktor", f"{len(selected_factors)}")
            
            with col2:
                st.metric("Observasi", f"{len(df)}")
                adj_r2 = 1 - (1-r2)*(len(df)-1)/(len(df)-len(selected_factors)-1)
                st.metric("Adjusted R²", f"{adj_r2:.3f}")
            
            # Coefficients table
            coef_df = pd.DataFrame({
                'Faktor': [risk_factors[f] for f in selected_factors],
                'Koefisien': model.coef_,
                'Arah': ['↑ Meningkatkan' if c > 0 else '↓ Menurunkan' for c in model.coef_]
            })
            st.dataframe(coef_df, hide_index=True)
            
            # Interpretation
            if r2 < 0.1:
                st.warning(f"""
                ⚠️ **Model Lemah** (R² = {r2:.1%})
                
                Faktor yang dipilih ({', '.join([risk_factors[f] for f in selected_factors])}) 
                hanya menjelaskan **{r2:.1%}** variasi stunting.
                """)
            elif r2 < 0.3:
                st.info(f"""
                📊 **Model Moderat** (R² = {r2:.1%})
                
                Faktor yang dipilih menjelaskan **{r2:.1%}** variasi stunting.
                """)
            else:
                st.success(f"""
                ✅ **Model Cukup Baik** (R² = {r2:.1%})
                
                Faktor yang dipilih menjelaskan **{r2:.1%}** variasi stunting.
                """)
            
            # Scatter plots
            st.subheader("📈 Scatter Plot")
            
            scatter_cols = st.columns(2)
            
            for i, factor in enumerate(selected_factors[:4]):
                with scatter_cols[i % 2]:
                    fig_scatter = px.scatter(
                        df,
                        x=factor,
                        y='persen_stunting',
                        hover_name='nama_kabkota',
                        trendline='ols',
                        color='risk_level',
                        color_discrete_map=RISK_COLORS,
                        labels={
                            factor: risk_factors[factor],
                            'persen_stunting': 'Prevalensi Stunting (%)'
                        },
                        title=f"Stunting vs {risk_factors[factor]}"
                    )
                    fig_scatter.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_scatter, key=f"scatter_{factor}")
        else:
            st.warning("Pilih minimal satu faktor risiko di sidebar untuk melihat analisis.")
    
    # =========================================================================
    # TAB 5: RINGKASAN DATA
    # =========================================================================
    with tab5:
        st.subheader("📋 Statistik Deskriptif")
        
        # Summary stats
        summary_vars = ['persen_stunting', 'jumlah_stunting', 'kepadatan_penduduk', 
                        'persen_air_minum_layak', 'persen_miskin', 'persen_rumah_layak_huni']
        summary_stats = df[summary_vars].describe().T
        summary_stats.index = ['Stunting (%)', 'Jumlah Stunting', 'Kepadatan', 
                               'Air Minum (%)', 'Miskin (%)', 'Rumah Layak (%)']
        
        st.dataframe(summary_stats.round(2))
        
        # Full dataset
        st.subheader("📋 Data Lengkap")
        
        # Search
        search = st.text_input("🔍 Cari kabupaten/kota:", placeholder="Ketik nama...")
        
        df_display = df.copy()
        if search:
            df_display = df_display[df_display['nama_kabkota'].str.contains(search, case=False)]
        
        # Display
        display_cols = ['nama_kabkota', 'persen_stunting', 'jumlah_stunting', 'risk_level',
                        'kepadatan_penduduk', 'persen_air_minum_layak', 'persen_miskin', 
                        'persen_rumah_layak_huni']
        
        df_show = df_display[display_cols].sort_values('persen_stunting', ascending=False)
        df_show.columns = ['Kab/Kota', 'Stunting (%)', 'Jml Stunting', 'Risiko',
                           'Kepadatan', 'Air Minum (%)', 'Miskin (%)', 'Rumah Layak (%)']
        
        st.dataframe(df_show, hide_index=True, height=450)
        
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
        
        st.write("""
        ### 1. 🗺️ Tab Peta Interaktif
        - Lihat distribusi risiko stunting di seluruh kabupaten/kota Jawa Barat
        - **Kuning** = Risiko Rendah, **Oranye** = Sedang, **Merah** = Tinggi, **Ungu Gelap** = Sangat Tinggi
        - Arahkan kursor ke wilayah untuk melihat detail
        
        ### 2. 🔍 Tab Profil Wilayah
        - Pilih kabupaten/kota untuk melihat profil lengkap
        - Lihat perbandingan dengan wilayah lain
        - Warna biru menandakan wilayah yang sedang dipilih
        
        ### 3. 📊 Tab Pola Risiko
        - Lihat distribusi kategori risiko
        - Identifikasi 5 wilayah tertinggi dan terendah
        - Dapatkan rekomendasi intervensi
        
        ### 4. 📈 Tab Model Statistik
        - Analisis korelasi antar variabel
        - Hasil model regresi OLS
        - Scatter plot dengan trendline
        
        ### 5. 📋 Tab Ringkasan Data
        - Statistik deskriptif semua variabel
        - Pencarian dan filter data
        - Download data dalam format CSV
        
        ---
        
        ### 🎨 Keterangan Warna Risiko (ColorBrewer YlOrRd)
        
        Palette warna menggunakan **ColorBrewer YlOrRd** yang merupakan standar 
        visualisasi data kesehatan dan epidemiologi.
        
        | Kategori | Kriteria | Warna | Hex Code |
        |----------|----------|-------|----------|
        | Low Risk | < Kuartil 1 | 🟨 Kuning Muda | `#ffffb2` |
        | Medium Risk | Q1 - Median | 🟡 Kuning-Oranye | `#fecc5c` |
        | High Risk | Median - Q3 | 🟠 Oranye | `#fd8d3c` |
        | Very High Risk | > Kuartil 3 | 🔴 Merah | `#e31a1c` |
        
        ---
        
        ### 📊 Tentang Data
        
        - **Sumber:** BPS & Dinas Kesehatan Provinsi Jawa Barat
        - **Tahun:** 2024
        - **Unit Analisis:** 27 Kabupaten/Kota
        - **Variabel:**
          - Prevalensi Stunting (%)
          - Jumlah Balita Stunting
          - Kepadatan Penduduk (jiwa/km²)
          - Akses Air Minum Layak (%)
          - Sanitasi Layak (%)
          - Penduduk Miskin (%)
          - Rumah Layak Huni (%)
        """)

# ============================================================================
# RUN APPLICATION
# ============================================================================
if __name__ == "__main__":
    main()
