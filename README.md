# Dashboard Analisis Spasial Stunting - Jawa Barat 2024

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://stunting-jabar.streamlit.app)

Dashboard interaktif untuk analisis spasial prevalensi stunting balita di Provinsi Jawa Barat tahun 2024.

## Fitur

- **Peta Interaktif**: Visualisasi koroplet prevalensi stunting per kabupaten/kota
- **Profil Wilayah**: Detail statistik per wilayah dengan perbandingan
- **Distribusi Risiko**: Analisis kategori risiko berdasarkan WHO (1995)
- **Model Statistik**: Regresi dan korelasi dengan referensi UNICEF Framework
- **Data**: Tabel lengkap dengan export CSV
- **Metodologi**: Dokumentasi sumber data dan referensi

## Teknologi

- Python 3.10+
- Streamlit
- Plotly
- Scipy
- Scikit-learn

## Menjalankan Lokal

```bash
pip install -r requirements.txt
streamlit run dashboard_stunting_final.py
```

## Struktur File

```
├── dashboard_stunting_final.py   # Dashboard utama
├── df_analisis_stunting_jabar_2024.csv
├── gdf_stunting_simplified.geojson
├── requirements.txt
└── .streamlit/config.toml
```

## Referensi

- WHO (1995). Physical Status: The Use and Interpretation of Anthropometry. TRS 854
- UNICEF (2013). Improving Child Nutrition
- de Onis & Branca (2016). Childhood stunting: a global perspective

## License

MIT License
