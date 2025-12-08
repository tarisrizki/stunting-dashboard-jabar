"""
============================================================================
DASHBOARD ANALISIS SPASIAL STUNTING JAWA BARAT 2024
============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Stunting Risk Explorer - Jawa Barat 2024",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS - MINIMALIS
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #475569;
    }
    
    div[data-testid="stMetric"] label { color: #94a3b8 !important; font-size: 0.85rem !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #f1f5f9 !important; font-size: 1.3rem !important; font-weight: 600 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; }
    
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING - CACHED
# ============================================================================
@st.cache_data
def load_data():
    """Load and preprocess data with proper NaN handling"""
    try:
        df = pd.read_csv('df_analisis_stunting_jabar_2024.csv')
        
        # Validate required columns
        required_cols = ['prevalensi_stunting', 'jumlah_stunting', 'kepadatan_penduduk', 
                        'persen_air_minum_layak', 'persen_miskin', 'persen_rumah_layak']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Kolom yang diperlukan tidak ditemukan: {missing_cols}")
        
        # Rename columns
        df = df.rename(columns={
            'prevalensi_stunting': 'persen_stunting',
            'persen_rumah_layak': 'persen_rumah_layak_huni'
        })
        
        # Data validation
        if len(df) == 0:
            raise ValueError("Dataset kosong")
        
        # Validate numeric columns
        numeric_cols = ['persen_stunting', 'jumlah_stunting', 'kepadatan_penduduk', 
                       'persen_air_minum_layak', 'persen_miskin', 'persen_rumah_layak_huni']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['kode_kabkota'] = df['kode_kabkota'].astype(str)
    
    except Exception as e:
        raise ValueError(f"Error memuat data: {str(e)}")
    
    # Klasifikasi WHO (1995) Technical Report Series No. 854, Table 39
    # Low (<20%), Medium (20-29%), High (30-39%), Very High (>=40%)
    def get_risk_level(val):
        if pd.isna(val): 
            return "No Data"
        elif val < 20: 
            return "Rendah"       # Low
        elif val < 30: 
            return "Sedang"       # Medium
        elif val < 40: 
            return "Tinggi"       # High
        else: 
            return "Sangat Tinggi"         # Very High
    
    df['risk_level'] = df['persen_stunting'].apply(get_risk_level)
    
    return df

@st.cache_data
def load_geojson():
    """Load GeoJSON"""
    try:
        with open("gdf_stunting_simplified.geojson", 'r') as f:
            geojson = json.load(f)
        
        # Validate GeoJSON structure
        if 'features' not in geojson:
            raise ValueError("GeoJSON tidak valid: missing 'features' key")
        
        return geojson
    except FileNotFoundError:
        raise FileNotFoundError("File gdf_stunting_simplified.geojson tidak ditemukan")
    except json.JSONDecodeError:
        raise ValueError("File GeoJSON tidak valid (corrupted)")

# ============================================================================
# VARIABEL PREDIKTOR - BERBASIS REFERENSI PENELITIAN
# ============================================================================
# Referensi: UNICEF Framework, de Onis & Branca (2016), Victora et al. (2008)

PREDICTORS = {
    'persen_miskin': {
        'label': 'Kemiskinan (%)',
        'expected_direction': 'positif',
        'reference': 'UNICEF (2013). Improving Child Nutrition: The achievable imperative for global progress. New York: UNICEF.',
        'hypothesis': 'Semakin tinggi kemiskinan, semakin tinggi prevalensi stunting'
    },
    'persen_air_minum_layak': {
        'label': 'Akses Air Minum Layak (%)',
        'expected_direction': 'negatif',
        'reference': 'WHO (2014). Global Nutrition Targets 2025: Stunting Policy Brief. Geneva: WHO.',
        'hypothesis': 'Semakin tinggi akses air minum layak, semakin rendah prevalensi stunting'
    },
    'persen_rumah_layak_huni': {
        'label': 'Rumah Layak Huni (%)',
        'expected_direction': 'negatif',
        'reference': 'Victora, C.G. et al. (2008). Maternal and child undernutrition. The Lancet, 371(9609), 340-357.',
        'hypothesis': 'Semakin tinggi persentase rumah layak huni, semakin rendah prevalensi stunting'
    },
    'kepadatan_penduduk': {
        'label': 'Kepadatan Penduduk (jiwa/km2)',
        'expected_direction': 'tidak pasti',
        'reference': 'Smith, L.C. & Ruel, M.T. (2005). Why Is Child Malnutrition Lower in Urban Than in Rural Areas? World Development, 33(8), 1285-1305.',
        'hypothesis': 'Hubungan tidak pasti: dapat negatif (akses layanan lebih baik) atau positif (kemiskinan urban)'
    }
}

# Warna berdasarkan klasifikasi WHO (1995)
# Ref: Physical Status: The use and interpretation of anthropometry. WHO TRS 854
RISK_COLORS = {
    "Rendah": "#91cf60",         # Low (<20%) - hijau
    "Sedang": "#fee08b",         # Medium (20-29%) - kuning
    "Tinggi": "#fc8d59",         # High (30-39%) - oranye
    "Sangat Tinggi": "#d73027",  # Very High (>=40%) - merah
    "No Data": "#9E9E9E"
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def format_value(val, decimal=1):
    """Format value, handle NaN"""
    if pd.isna(val):
        return "N/A"
    return f"{val:,.{decimal}f}"

def get_text_color(risk_level):
    """Get appropriate text color for background"""
    if risk_level in ["Rendah", "Sedang"]:
        return "#1f2937"
    return "#ffffff"

def calculate_correlation(df, x_var, y_var='persen_stunting'):
    """Calculate correlation with p-value, handle NaN"""
    valid = df[[x_var, y_var]].dropna()
    if len(valid) < 3:
        return np.nan, np.nan
    r, p = stats.pearsonr(valid[x_var], valid[y_var])
    return r, p

def calculate_vif(df, predictors):
    """Calculate Variance Inflation Factor for multicollinearity check"""
    from sklearn.linear_model import LinearRegression
    
    vif_data = []
    for pred in predictors:
        X = [p for p in predictors if p != pred]
        if len(X) == 0:
            vif = 1.0
        else:
            valid_df = df[[pred] + X].dropna()
            if len(valid_df) < 3:
                vif = np.nan
            else:
                X_vals = valid_df[X].values
                y_vals = valid_df[pred].values
                model = LinearRegression().fit(X_vals, y_vals)
                r2 = model.score(X_vals, y_vals)
                vif = 1 / (1 - r2) if r2 < 0.99 else np.nan
        
        vif_data.append({'Variabel': PREDICTORS[pred]['label'], 'VIF': vif})
    
    return pd.DataFrame(vif_data)

def run_ols_model(df, predictors, y_var='persen_stunting'):
    """Run OLS regression with multiple predictors"""
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score, mean_squared_error
    
    # Drop rows with NaN in any predictor or y
    valid_df = df[[y_var] + predictors].dropna()
    
    if len(valid_df) < len(predictors) + 2:
        return None
    
    X = valid_df[predictors].values
    y = valid_df[y_var].values
    
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    
    r2 = r2_score(y, y_pred)
    adj_r2 = 1 - (1-r2)*(len(y)-1)/(len(y)-len(predictors)-1)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    
    return {
        'model': model,
        'r2': r2,
        'adj_r2': adj_r2,
        'rmse': rmse,
        'n': len(valid_df),
        'coef': dict(zip(predictors, model.coef_)),
        'intercept': model.intercept_
    }

# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    st.title("Stunting Risk Explorer - Jawa Barat 2024")
    st.caption("Dashboard Analisis Spasial Prevalensi Stunting Balita")
    
    # Load data with error handling
    try:
        df = load_data()
        geojson = load_geojson()
    except Exception as e:
        st.error(f"Error memuat data: {str(e)}")
        st.stop()
    
    # =========================================================================
    # SIDEBAR
    # =========================================================================
    st.sidebar.header("Pengaturan")
    
    # Predictor selection based on research
    st.sidebar.subheader("Faktor Prediktor")
    
    selected_predictors = st.sidebar.multiselect(
        "Pilih Prediktor:",
        options=list(PREDICTORS.keys()),
        default=['persen_miskin', 'persen_rumah_layak_huni'],
        format_func=lambda x: PREDICTORS[x]['label']
    )
    
    st.sidebar.divider()
    st.sidebar.caption("Data: BPS & Dinkes Jabar 2024")
    st.sidebar.caption(f"Unit: {len(df)} Kabupaten/Kota")
    
    # =========================================================================
    # TABS
    # =========================================================================
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Peta", "Profil Wilayah", "Distribusi Risiko", 
        "Model Statistik", "Data", "Metodologi"
    ])
    
    # =========================================================================
    # TAB 1: PETA
    # =========================================================================
    with tab1:
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_stunting = df['jumlah_stunting'].sum()
        mean_prev = df['persen_stunting'].mean()
        high_risk = df[df['risk_level'].isin(['Tinggi', 'Sangat Tinggi'])].shape[0]
        low_risk = df[df['risk_level'] == 'Rendah'].shape[0]
        
        with col1:
            st.metric("Total Kasus", f"{int(total_stunting):,}")
        with col2:
            st.metric("Rata-rata Prevalensi", f"{mean_prev:.1f}%")
        with col3:
            st.metric("Risiko Tinggi", f"{high_risk} wilayah")
        with col4:
            st.metric("Risiko Rendah", f"{low_risk} wilayah")
        
        st.subheader("Peta Distribusi Risiko Stunting")
        
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
                'jumlah_stunting': ':,.0f'
            },
            color_discrete_map=RISK_COLORS,
            category_orders={'risk_level': ['Rendah', 'Sedang', 'Tinggi', 'Sangat Tinggi']}
        )
        
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            height=500,
            margin={"r":0,"t":0,"l":0,"b":0},
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption("Kategori: Rendah (<20%), Sedang (20-29%), Tinggi (30-39%), Sangat Tinggi (≥40%)")
    
    # =========================================================================
    # TAB 2: PROFIL WILAYAH
    # =========================================================================
    with tab2:
        selected_kab = st.selectbox("Pilih Kabupaten/Kota:", sorted(df['nama_kabkota'].unique()))
        kab_data = df[df['nama_kabkota'] == selected_kab].iloc[0]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Profil Risiko")
            
            risk = kab_data['risk_level']
            color = RISK_COLORS.get(risk, "#9E9E9E")
            text_color = get_text_color(risk)
            
            st.markdown(f"""
            <div style="background-color: {color}; padding: 20px; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0; color: {text_color};">{selected_kab}</h3>
                <p style="margin: 5px 0 0 0; color: {text_color}; font-size: 1.2em;">{risk}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            
            # Data table
            data_rows = [
                ("Prevalensi Stunting", f"{format_value(kab_data['persen_stunting'])}%"),
                ("Jumlah Balita Stunting", f"{int(kab_data['jumlah_stunting']):,}"),
                ("Kepadatan Penduduk", f"{format_value(kab_data['kepadatan_penduduk'], 0)} jiwa/km2"),
                ("Akses Air Minum Layak", f"{format_value(kab_data['persen_air_minum_layak'])}%"),
                ("Rumah Layak Huni", f"{format_value(kab_data['persen_rumah_layak_huni'])}%"),
                ("Penduduk Miskin", f"{format_value(kab_data['persen_miskin'])}%"),
            ]
            
            for label, value in data_rows:
                st.markdown(f"**{label}:** {value}")
        
        with col2:
            st.subheader("Lokasi")
            
            df_map = df.copy()
            df_map['highlight'] = df_map['nama_kabkota'].apply(
                lambda x: 'Terpilih' if x == selected_kab else 'Lainnya'
            )
            
            fig_loc = px.choropleth(
                df_map,
                geojson=geojson,
                locations='kode_kabkota',
                featureidkey='properties.kode_kabkota',
                color='highlight',
                hover_name='nama_kabkota',
                color_discrete_map={'Terpilih': '#2563eb', 'Lainnya': '#e2e8f0'}
            )
            
            fig_loc.update_geos(fitbounds="locations", visible=False)
            fig_loc.update_layout(height=300, margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False)
            
            st.plotly_chart(fig_loc, use_container_width=True)
        
        # Ranking
        st.subheader("Perbandingan Ranking")
        
        df_rank = df.sort_values('persen_stunting', ascending=True).reset_index(drop=True)
        df_rank['rank'] = range(1, len(df_rank) + 1)
        
        fig_bar = px.bar(
            df_rank,
            x='persen_stunting',
            y='nama_kabkota',
            orientation='h',
            color='risk_level',
            color_discrete_map=RISK_COLORS,
            category_orders={'risk_level': ['Rendah', 'Sedang', 'Tinggi', 'Sangat Tinggi']}
        )
        
        # Highlight selected
        selected_rank = df_rank[df_rank['nama_kabkota'] == selected_kab]['rank'].values[0]
        fig_bar.add_annotation(
            x=kab_data['persen_stunting'] + 1,
            y=selected_kab,
            text=f"#{selected_rank}",
            showarrow=False,
            font=dict(size=11, color="#2563eb", weight="bold")
        )
        
        fig_bar.update_layout(
            height=600,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_title="Prevalensi Stunting (%)",
            yaxis_title=""
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # =========================================================================
    # TAB 3: DISTRIBUSI RISIKO
    # =========================================================================
    with tab3:
        st.subheader("Distribusi Kategori Risiko")
        
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
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = px.bar(
                x=risk_counts.index,
                y=risk_counts.values,
                color=risk_counts.index,
                color_discrete_map=RISK_COLORS,
                labels={'x': 'Kategori', 'y': 'Jumlah'}
            )
            fig_bar.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Top/Bottom
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**5 Prevalensi Tertinggi**")
            top5 = df.nlargest(5, 'persen_stunting')[['nama_kabkota', 'persen_stunting', 'risk_level']]
            for i, (_, row) in enumerate(top5.iterrows(), 1):
                color = RISK_COLORS.get(row['risk_level'], "#9E9E9E")
                text_col = get_text_color(row['risk_level'])
                st.markdown(f"""
                <div style="background: {color}; padding: 10px; border-radius: 6px; margin: 4px 0;">
                    <span style="color: {text_col};">{i}. {row['nama_kabkota']} - {row['persen_stunting']:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("**5 Prevalensi Terendah**")
            bottom5 = df.nsmallest(5, 'persen_stunting')[['nama_kabkota', 'persen_stunting', 'risk_level']]
            for i, (_, row) in enumerate(bottom5.iterrows(), 1):
                color = RISK_COLORS.get(row['risk_level'], "#9E9E9E")
                text_col = get_text_color(row['risk_level'])
                st.markdown(f"""
                <div style="background: {color}; padding: 10px; border-radius: 6px; margin: 4px 0;">
                    <span style="color: {text_col};">{i}. {row['nama_kabkota']} - {row['persen_stunting']:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 4: MODEL STATISTIK
    # =========================================================================
    with tab4:
        st.subheader("Analisis Faktor Determinan Stunting")
        
        st.markdown("""
        Pemilihan variabel prediktor didasarkan pada kerangka konseptual **UNICEF (2013)** 
        yang mengidentifikasi determinan stunting pada tiga level: penyebab langsung (immediate), 
        tidak langsung (underlying), dan dasar (basic).
        """)
        
        # Show predictor references
        with st.expander("Dasar Pemilihan Variabel Prediktor"):
            for var, info in PREDICTORS.items():
                st.markdown(f"""
                **{info['label']}**
                - Arah hubungan yang diharapkan: {info['expected_direction']}
                - Hipotesis: {info['hypothesis']}
                - Referensi: {info['reference']}
                """)
        
        if len(selected_predictors) == 0:
            st.warning("Pilih minimal satu prediktor di sidebar untuk melihat analisis.")
            st.info("**Tip:** Pilih 'Kemiskinan (%)' dan 'Rumah Layak Huni (%)' untuk analisis awal yang komprehensif.")
            return
        
        # Multicollinearity Check
        if len(selected_predictors) > 1:
            st.subheader("Pemeriksaan Multikolinearitas (VIF)")
            vif_df = calculate_vif(df, selected_predictors)
            
            # Add interpretation
            def interpret_vif(vif):
                if pd.isna(vif):
                    return "Tidak dapat dihitung"
                elif vif < 5:
                    return "Rendah"
                elif vif < 10:
                    return "Sedang"
                else:
                    return "Tinggi"
            
            vif_df['Interpretasi'] = vif_df['VIF'].apply(interpret_vif)
            st.dataframe(vif_df.style.format({'VIF': '{:.2f}'}), hide_index=True)
            
            st.caption("VIF < 5: Rendah, 5-10: Sedang, >10: Tinggi (multikolinearitas bermasalah)")
            
            if vif_df['VIF'].max() > 10:
                st.warning("Terdapat multikolinearitas tinggi. Pertimbangkan menghapus salah satu variabel.")
        
        # Correlation Analysis
        st.subheader("Analisis Korelasi Bivariat")
        
        corr_results = []
        for pred in selected_predictors:
            r, p = calculate_correlation(df, pred)
            expected = PREDICTORS[pred]['expected_direction']
            actual = 'positif' if r > 0 else 'negatif' if r < 0 else 'tidak ada'
            match = 'Sesuai' if (expected == actual or expected == 'tidak pasti') else 'Tidak sesuai'
            
            corr_results.append({
                'Variabel': PREDICTORS[pred]['label'],
                'r': r,
                'p-value': p,
                'Signifikan (a=0.05)': 'Ya' if p < 0.05 else 'Tidak',
                'Arah Diharapkan': expected,
                'Arah Aktual': actual,
                'Kesesuaian': match
            })
        
        corr_df = pd.DataFrame(corr_results)
        st.dataframe(corr_df.style.format({'r': '{:.3f}', 'p-value': '{:.3f}'}), hide_index=True)
        
        # Correlation Matrix
        st.subheader("Matriks Korelasi")
        
        corr_vars = ['persen_stunting'] + selected_predictors
        corr_matrix = df[corr_vars].corr()
        
        labels = ['Stunting'] + [PREDICTORS[p]['label'].split(' (')[0] for p in selected_predictors]
        
        fig_corr = px.imshow(
            corr_matrix.values,
            x=labels,
            y=labels,
            color_continuous_scale='RdBu_r',
            zmin=-1, zmax=1,
            text_auto='.2f'
        )
        fig_corr.update_layout(height=400)
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Model Comparison
        st.subheader("Perbandingan Model Regresi")
        
        st.markdown("""
        Membandingkan beberapa spesifikasi model untuk mengevaluasi kontribusi 
        masing-masing prediktor terhadap variasi stunting.
        """)
        
        model_results = []
        
        # Model 1: Each predictor alone
        for pred in selected_predictors:
            result = run_ols_model(df, [pred])
            if result:
                model_results.append({
                    'Model': f"Univariat: {PREDICTORS[pred]['label'].split(' (')[0]}",
                    'Prediktor': 1,
                    'R2': result['r2'],
                    'Adj R2': result['adj_r2'],
                    'RMSE': result['rmse'],
                    'n': result['n']
                })
        
        # Model Full: All predictors
        if len(selected_predictors) > 1:
            result_full = run_ols_model(df, selected_predictors)
            if result_full:
                model_results.append({
                    'Model': 'Multivariat (semua prediktor)',
                    'Prediktor': len(selected_predictors),
                    'R2': result_full['r2'],
                    'Adj R2': result_full['adj_r2'],
                    'RMSE': result_full['rmse'],
                    'n': result_full['n']
                })
        
        if model_results:
            model_df = pd.DataFrame(model_results)
            model_df = model_df.sort_values('R2', ascending=False)
            
            st.dataframe(
                model_df.style.format({'R2': '{:.3f}', 'Adj R2': '{:.3f}', 'RMSE': '{:.2f}'}),
                hide_index=True
            )
            
            # Best model interpretation
            best_model = model_df.iloc[0]
            st.info(f"""
            **Model Terbaik:** {best_model['Model']}
            - R2 = {best_model['R2']:.3f} ({best_model['R2']*100:.1f}% variasi stunting dapat dijelaskan)
            - Adjusted R2 = {best_model['Adj R2']:.3f}
            - RMSE = {best_model['RMSE']:.2f}
            """)
            
            # Full model coefficients
            if len(selected_predictors) > 1 and result_full:
                st.subheader("Koefisien Model Multivariat")
                
                coef_data = []
                for pred in selected_predictors:
                    coef = result_full['coef'][pred]
                    direction = 'Meningkatkan' if coef > 0 else 'Menurunkan'
                    coef_data.append({
                        'Variabel': PREDICTORS[pred]['label'],
                        'Koefisien (B)': coef,
                        'Interpretasi': f"{direction} stunting sebesar {abs(coef):.3f}% per unit"
                    })
                
                coef_df = pd.DataFrame(coef_data)
                st.dataframe(coef_df.style.format({'Koefisien (B)': '{:.4f}'}), hide_index=True)
        
        # Scatter plots
        st.subheader("Scatter Plot dengan Garis Regresi")
        
        cols = st.columns(2)
        for i, pred in enumerate(selected_predictors[:4]):
            with cols[i % 2]:
                # Filter valid data
                plot_df = df[[pred, 'persen_stunting', 'nama_kabkota', 'risk_level']].dropna()
                
                if len(plot_df) > 2:
                    fig = px.scatter(
                        plot_df,
                        x=pred,
                        y='persen_stunting',
                        hover_name='nama_kabkota',
                        trendline='ols',
                        color='risk_level',
                        color_discrete_map=RISK_COLORS,
                        labels={pred: PREDICTORS[pred]['label'], 'persen_stunting': 'Stunting (%)'}
                    )
                    fig.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show correlation
                    r, p = calculate_correlation(df, pred)
                    st.caption(f"r = {r:.3f}, p = {p:.3f}")
    
    # =========================================================================
    # TAB 5: DATA
    # =========================================================================
    with tab5:
        st.subheader("Statistik Deskriptif")
        
        desc_vars = ['persen_stunting', 'jumlah_stunting', 'kepadatan_penduduk', 
                     'persen_air_minum_layak', 'persen_miskin', 'persen_rumah_layak_huni']
        
        desc_stats = df[desc_vars].describe().T
        desc_stats.index = ['Stunting (%)', 'Jml Stunting', 'Kepadatan', 
                            'Air Minum (%)', 'Miskin (%)', 'Rumah Layak (%)']
        
        st.dataframe(desc_stats.round(2))
        
        st.subheader("Data Lengkap")
        
        search = st.text_input("Cari kabupaten/kota:", placeholder="Ketik nama...")
        
        df_display = df.copy()
        if search:
            df_display = df_display[df_display['nama_kabkota'].str.contains(search, case=False)]
        
        cols_show = ['nama_kabkota', 'persen_stunting', 'jumlah_stunting', 'risk_level',
                     'kepadatan_penduduk', 'persen_air_minum_layak', 'persen_miskin', 
                     'persen_rumah_layak_huni']
        
        df_show = df_display[cols_show].sort_values('persen_stunting', ascending=False)
        df_show.columns = ['Kab/Kota', 'Stunting (%)', 'Jml Stunting', 'Risiko',
                           'Kepadatan', 'Air Minum (%)', 'Miskin (%)', 'Rumah Layak (%)']
        
        st.dataframe(df_show, hide_index=True, height=400)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "data_stunting_jabar_2024.csv", "text/csv")
    
    # =========================================================================
    # TAB 6: METODOLOGI
    # =========================================================================
    with tab6:
        st.subheader("Metodologi Analisis")
        
        st.markdown("""
        ### Kerangka Konseptual
        
        Analisis ini menggunakan kerangka konseptual **UNICEF (2013)** yang mengidentifikasi 
        determinan stunting pada tiga level:
        
        1. **Penyebab Langsung (Immediate):** Asupan gizi tidak adekuat, penyakit infeksi
        2. **Penyebab Tidak Langsung (Underlying):** Ketersediaan pangan, pola asuh, akses air bersih dan sanitasi
        3. **Penyebab Dasar (Basic):** Kemiskinan, ketimpangan, pendidikan
        
        ### Variabel dalam Analisis
        
        | Variabel | Level UNICEF | Referensi |
        |----------|--------------|-----------|
        | Kemiskinan | Basic cause | UNICEF (2013) |
        | Akses air minum layak | Underlying cause | WHO (2014) |
        | Rumah layak huni | Underlying cause | Victora et al. (2008) |
        | Kepadatan penduduk | Kontekstual | Smith & Ruel (2005) |
        
        ### Kategori Risiko
        
        Kategorisasi risiko mengacu pada **WHO (1995) Technical Report Series No. 854**:
        
        | Kategori | Prevalensi | Keterangan |
        |----------|------------|------------|
        | Rendah | <20% | Low prevalence |
        | Sedang | 20-29% | Medium prevalence |
        | Tinggi | 30-39% | High prevalence |
        | Sangat Tinggi | >=40% | Very high prevalence |
        """)
        
        st.markdown(f"""
        ### Keterbatasan
        
        1. **Ecological fallacy:** Hubungan pada level agregat tidak dapat diinterpretasikan pada level individu
        2. **Cross-sectional:** Tidak dapat menetapkan hubungan kausal
        3. **Ukuran sampel:** n={len(df)} membatasi power statistik
        4. **Missing data:** Beberapa variabel tidak tersedia lengkap
        
        ### Referensi
        
        - WHO. (1995). *Physical Status: The Use and Interpretation of Anthropometry*. Technical Report Series No. 854. Geneva: WHO.
        - UNICEF. (2013). *Improving Child Nutrition: The achievable imperative for global progress*. New York: UNICEF.
        - de Onis, M., & Branca, F. (2016). Childhood stunting: a global perspective. *Maternal & Child Nutrition*, 12(S1), 12-26.
        - WHO. (2014). *Global Nutrition Targets 2025: Stunting Policy Brief*. Geneva: WHO.
        - Victora, C.G., et al. (2008). Maternal and child undernutrition. *The Lancet*, 371(9609), 340-357.
        - Smith, L.C. & Ruel, M.T. (2005). Why Is Child Malnutrition Lower in Urban Than in Rural Areas? *World Development*, 33(8), 1285-1305.
        """)

# ============================================================================
# RUN
# ============================================================================
if __name__ == "__main__":
    main()
