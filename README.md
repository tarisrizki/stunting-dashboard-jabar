# 📊 Dashboard Analisis Spasial Stunting - Jawa Barat 2024

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://stunting-jabar.streamlit.app)

Dashboard interaktif untuk analisis spasial prevalensi stunting balita di Provinsi Jawa Barat tahun 2024.

## 🎯 Fitur

- **Peta Interaktif**: Visualisasi koroplet prevalensi stunting per kabupaten/kota
- **Profil Wilayah**: Detail statistik per wilayah dengan perbandingan
- **Pola Risiko**: Analisis faktor-faktor risiko stunting
- **Model Statistik**: Regresi dan korelasi dinamis
- **Ringkasan Data**: Tabel lengkap dengan export
- **Panduan**: Dokumentasi metodologi

## 📈 Statistik Utama

| Metrik | Nilai |
|--------|-------|
| Wilayah | 27 Kab/Kota |
| Median Stunting | 18% |
| Tertinggi | Bandung Barat (30.8%) |
| Terendah | Cianjur (7.2%) |

## 🛠️ Teknologi

- Python 3.10+
- Streamlit
- Plotly
- GeoPandas
- Statsmodels

## 🚀 Menjalankan Lokal

```bash
pip install -r requirements.txt
streamlit run dashboard_stunting_final.py
```

## 📁 Struktur File

```
├── dashboard_stunting_final.py   # Dashboard utama
├── df_analisis_stunting_jabar_2024.csv
├── gdf_stunting_simplified.geojson
├── requirements.txt
└── .streamlit/config.toml
```

## 👤 Author

Tim Epidemiologi - Analisis Stunting Jawa Barat 2024

## 📄 License

MIT License
