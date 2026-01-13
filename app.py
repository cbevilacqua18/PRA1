# streamlit_app_final.py
import streamlit as st
import pandas as pd
import plotly.express as px
import json

# =========================
# Configuració inicial
# =========================
st.set_page_config(page_title="Criminalitat a Suïssa (2010-2022)", layout="wide")
st.title("Criminalitat a Suïssa (2010–2022)")
st.markdown("""
Autor: Christian Bevilacqua i Aregall
""")
st.markdown("""
Explora l'evolució de delictes a Suïssa, comparatives entre cantons i relació amb variables socioeconòmiques.
Filtra per cantó, any i tipus de delicte per obtenir informació detallada.
""")

# =========================
# Carregar dataset
# =========================
@st.cache_data
def load_data():
    df  = pd.read_csv("df_final_compressed.csv.gz", sep=';', decimal='.', encoding='utf-8', compression='gzip')

  # utilitza el teu fitxer
    return df

df = load_data()

# =========================
# Carregar GeoJSON de cantons suïssos
# =========================
@st.cache_data
def load_geojson():
    with open("switzerland.geojson", "r") as f: 
        geojson = json.load(f)
    return geojson

geojson = load_geojson()

# =========================
# Sidebar - filtres
# =========================
st.sidebar.header("Filtres")
selected_year = st.sidebar.slider("Any", int(df['Any'].min()), int(df['Any'].max()), (int(df['Any'].min()), int(df['Any'].max())))
selected_canton = st.sidebar.selectbox("Cantó", options=["Tots"] + sorted(df['Canto_norm'].unique()))
selected_offence = st.sidebar.multiselect("Tipus de delicte", options=df['Tipus_de_Delicte'].unique(), default=df['Tipus_de_Delicte'].unique())

# =========================
# Aplicar filtres
# =========================
df_filtered = df[df['Any'].between(selected_year[0], selected_year[1])]
if selected_canton != "Tots":
    df_filtered = df_filtered[df_filtered['Canto_norm'] == selected_canton]
df_filtered = df_filtered[df_filtered['Tipus_de_Delicte'].isin(selected_offence)]

# =========================
# Secció 1: KPI metrics
# =========================
st.subheader("Indicadors generals")
total_crimes = df_filtered['Nombre_de_Delictes'].sum()
avg_crime_rate = df_filtered['Taxa_Criminalitat_per_1000'].mean()
avg_resolution = df_filtered['Percentatge_Casos_Resolts'].mean()
col1, col2, col3 = st.columns(3)
col1.metric("Total de delictes", f"{int(total_crimes):,}")
col2.metric("Taxa de crim mitjana (per 1000 habitants)", f"{avg_crime_rate:.2f}")
col3.metric("Percentatge mitjà de casos resolts", f"{avg_resolution:.2f}%")

st.markdown("---")


# =========================
# Secció 2: Mapes per cantó
# =========================
st.subheader("Mapa de criminalitat per cantó")
map_data = df_filtered.groupby(['Canto_norm', 'Any']).agg({
    'Taxa_Criminalitat_per_1000': 'mean',
    'Nombre_de_Delictes': 'sum'
}).reset_index()

selected_metric = st.selectbox("Mètrica del mapa", ["Taxa_Criminalitat_per_1000", "Nombre_de_Delictes"])
map_fig = px.choropleth(
    map_data[map_data['Any'] == selected_year[1]],
    geojson=geojson,
    locations='Canto_norm',
    featureidkey="properties.name",
    color=selected_metric,
    color_continuous_scale="Reds",
    hover_name='Canto_norm',
    hover_data={selected_metric: True, 'Any': True},
    labels={selected_metric: "Crims" if selected_metric=="Nombre_de_Delictes" else "Crims per 1000 habitants"}
)
map_fig.update_geos(fitbounds="locations", visible=False)
map_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(map_fig, use_container_width=True)

st.markdown(""" La criminalitat es concentra principalment als cantons urbans i densament poblats, mentre que els cantons rurals mantenen nivells clarament inferiors tant en volum com en taxa.""")
# =========================
# Secció 3: Evolució temporal per cantó
# =========================
st.subheader("Evolució temporal dels delictes per cantó")
line_fig = px.line(
    map_data,
    x='Any',
    y=selected_metric,
    color='Canto_norm',
    markers=True,
    labels={"Canto_norm": "Cantó", selected_metric: "Crims" if selected_metric=="Nombre_de_Delictes" else "Crims per 1000 habitants"}
)
st.plotly_chart(line_fig, use_container_width=True)

st.markdown("""
Tots els cantons segueixen una evolució temporal similar, amb una davallada general fins al 2020 i un lleuger repunt recent, però amb diferències estructurals persistents entre territoris urbans i rurals.""")

# =========================
# Secció 4: Relació amb variables socioeconòmiques
# =========================

st.subheader("Relació entre PIB, % d'estrangers i taxa de crim")

# 1️⃣ Treballem només amb "Total de casos" (una observació per cantó-any)
df_scatter = df_filtered[
    df_filtered['Nivell_de_Resolucio'] == 'Total de casos'
]

# 2️⃣ Agregació explícita (evita errors i és semànticament correcta)
scatter_data = (
    df_scatter
    .groupby(['Canto_norm', 'Any'], as_index=False)
    .agg(
        Taxa_Criminalitat_per_1000=('Taxa_Criminalitat_per_1000', 'mean'),
        PIB_per_Capita=('PIB_per_Capita', 'first'),
        Percentatge_Estrangers=('Percentatge_Estrangers', 'first'),
        Poblacio_Total=('Poblacio_Total', 'first')
    )
)

# 3️⃣ Scatter plot
scatter_fig = px.scatter(
    scatter_data,
    x='PIB_per_Capita',
    y='Taxa_Criminalitat_per_1000',
    size='Poblacio_Total',
    color='Percentatge_Estrangers',
    hover_name='Canto_norm',
    animation_frame='Any',   # 🔥 molt potent per storytelling
    size_max=50,
    labels={
        "PIB_per_Capita": "PIB per càpita (CHF)",
        "Taxa_Criminalitat_per_1000": "Crims per 1.000 habitants",
        "Percentatge_Estrangers": "% població estrangera",
        "Any": "Any"
    },
    color_continuous_scale='Viridis'
)

st.plotly_chart(scatter_fig, use_container_width=True)

st.markdown("""

Tots els cantons segueixen una evolució temporal similar, amb una davallada general fins al 2020 i un lleuger repunt recent, però amb diferències estructurals persistents entre territoris urbans i rurals.""")

# =========================
# Secció 4: Resolució de casos
# =========================
st.subheader("Resolució de casos per tipus de delicte")
stacked_data = df_filtered.groupby(['Tipus_de_Delicte', 'Nivell_de_Resolucio'])['Nombre_de_Delictes'].sum().reset_index()

top_n = 20
top_delictes = (
    df_filtered.groupby('Tipus_de_Delicte')['Nombre_de_Delictes'].sum()
    .sort_values(ascending=False)
    .head(top_n)
    .index
)

def categoritza_delicte(d):
    d_lower = d.lower()
    if 'vol' in d_lower or 'détournement' in d_lower or 'dommages' in d_lower:
        return 'Robatoris / Détournements / Danys'  # Vols / Détournements / Dommages
    elif 'violence' in d_lower or 'lésions' in d_lower or 'meurtre' in d_lower:
        return 'Violència / Homicidi'  # Violence / Homicide
    elif 'fraude' in d_lower or 'escroquerie' in d_lower or 'corruption' in d_lower:
        return 'Frau / Corrupció'  # Fraude / Corruption
    elif 'sexuel' in d_lower or 'inceste' in d_lower or 'prostitution' in d_lower:
        return 'Infraccions sexuals'  # Infractions sexuelles
    else:
        return 'Altres'  # Autres


stacked_data['Categorie'] = stacked_data['Tipus_de_Delicte'].apply(categoritza_delicte)
stacked_data_cat = stacked_data.groupby(['Categorie', 'Nivell_de_Resolucio'])['Nombre_de_Delictes'].sum().reset_index()




stacked_data['Categorie'] = stacked_data['Tipus_de_Delicte'].apply(categoritza_delicte)

# Agrupem per categoria i nivell de resolució
stacked_data_cat = stacked_data.groupby(
    ['Categorie', 'Nivell_de_Resolucio']
)['Nombre_de_Delictes'].sum().reset_index()

# Calculem percentatge dins de cada categoria
stacked_data_cat['Percentatge'] = stacked_data_cat.groupby('Categorie')['Nombre_de_Delictes'].transform(lambda x: 100 * x / x.sum())

# Eliminem 'Total de casos'
stacked_data_cat = stacked_data_cat[
    stacked_data_cat['Nivell_de_Resolucio'] != 'Total de casos'
]

stacked_fig = px.bar(
    stacked_data_cat,
    x='Categorie',
    y='Percentatge',
    color='Nivell_de_Resolucio',
    text=stacked_data_cat['Percentatge'].apply(lambda x: f"{x:.1f}%"),
    labels={"Percentatge": "Percentatge de delictes (%)"}
)

stacked_fig.update_layout(
    barmode='stack',
    xaxis_tickangle=-45,
    yaxis=dict(ticksuffix="%")
)

st.plotly_chart(stacked_fig, use_container_width=True)

st.markdown("""
Tots els cantons segueixen una evolució temporal similar, amb una davallada general fins al 2020 i un lleuger repunt recent, però amb diferències estructurals persistents entre territoris urbans i rurals.""")

# =========================
# Secció 5: Evolució temporal per categoria de delicte
# =========================
st.subheader("Evolució temporal per categoria de delicte (2010–2022)")

def categoritza_delicte(d):
    d_lower = d.lower()
    if 'vol' in d_lower or 'détournement' in d_lower or 'dommages' in d_lower:
        return 'Robatoris / Détournements / Danys'  # Vols / Détournements / Dommages
    elif 'violence' in d_lower or 'lésions' in d_lower or 'meurtre' in d_lower:
        return 'Violència / Homicidi'  # Violence / Homicide
    elif 'fraude' in d_lower or 'escroquerie' in d_lower or 'corruption' in d_lower:
        return 'Frau / Corrupció'  # Fraude / Corruption
    elif 'sexuel' in d_lower or 'inceste' in d_lower or 'prostitution' in d_lower:
        return 'Infraccions sexuals'  # Infractions sexuelles
    else:
        return 'Altres'  # Autres


df_filtered['Categorie'] = df_filtered['Tipus_de_Delicte'].apply(categoritza_delicte)

temporal_data = df_filtered.groupby(['Any', 'Categorie'])['Nombre_de_Delictes'].sum().reset_index()
line_cat_fig = px.line(
    temporal_data,
    x='Any',
    y='Nombre_de_Delictes',
    color='Categorie',
    markers=True,
    labels={"Nombre_de_Delictes": "Nombre de delictes"}
)
st.plotly_chart(line_cat_fig, use_container_width=True)

st.markdown("""
Les categories més freqüents disminueixen amb el temps, mentre que delictes més complexos com el frau mostren una tendència creixent.""")

# =========================
# Secció 7: Evolució temporal de la resolució per categoria
# =========================
st.subheader("Taxa de resolució per categoria al llarg dels anys")

resolution_data = df_filtered[df_filtered['Nivell_de_Resolucio'] != 'Total de casos']
resolution_pct = resolution_data.groupby(['Any','Categorie','Nivell_de_Resolucio'])['Nombre_de_Delictes'].sum().reset_index()
resolution_pct['Percentatge'] = resolution_pct.groupby(['Any','Categorie'])['Nombre_de_Delictes'].transform(lambda x: 100*x/x.sum())

line_res_fig = px.line(
    resolution_pct[resolution_pct['Nivell_de_Resolucio']=='Resolts'],
    x='Any',
    y='Percentatge',
    color='Categorie',
    markers=True,
    labels={"Percentatge": "% casos resolts"}
)
st.plotly_chart(line_res_fig, use_container_width=True)

st.markdown("""
Els cantons grans concentren la major part dels delictes en totes les categories, confirmant el paper clau de la població i la urbanització en el volum criminal.""")



# =========================
# Secció 8: Diferències entre cantons per categoria
# =========================
st.subheader("Distribució de delictes per cantó i categoria")
cantons_cat = df_filtered[df_filtered['Canto_norm'] != 'Switzerland'] \
    .groupby(['Canto_norm', 'Categorie'])['Nombre_de_Delictes'].sum().reset_index()
bar_canton_fig = px.bar(
    cantons_cat,
    x='Canto_norm',
    y='Nombre_de_Delictes',
    color='Categorie',
    text='Nombre_de_Delictes'
)
bar_canton_fig.update_layout(barmode='stack', xaxis_tickangle=-45)
st.plotly_chart(bar_canton_fig, use_container_width=True)
st.markdown("""
El gràfic de barres apilat mostra com es distribueixen els delictes entre els diferents cantons segons la seva categoria.

S’observa que els cantons més grans i urbans com **Zuric, Vaud, Ginebra i Bern** presenten el nombre absolut més elevat de delictes, amb especial concentració en la categoria de **Robatoris / Détournements / Danys** i **Altres**. Això reflecteix tant la major població com la concentració d’activitat econòmica i social en aquests territoris.

Els cantons més petits i rurals, com **Uri, Glarus o Nidwalden**, mostren un volum molt menor de delictes en totes les categories, destacant la influència de la dimensió poblacional i de la densitat urbana en la incidència criminal.

Pel que fa a les categories específiques, **Violència / Homicidi** i **Infraccions sexuals** mantenen valors més baixos en tots els cantons, indicant que aquests delictes, tot i la gravetat, són menys freqüents. **Frau / Corrupció** és moderada en tots els cantons, amb punts més destacats en zones amb activitat econòmica significativa.

En conjunt, el gràfic evidencia que hi ha **diferències clares entre cantons** pel que fa al tipus i nombre de delictes, amb factors com la població, urbanització i activitat econòmica com a principals determinants dels volums observats.
""")
# =========================
# Secció 9: Correlació socioeconòmica
# =========================
st.subheader("Correlació entre característiques socioeconòmiques i delictes")
corr_df = df_filtered.groupby('Canto_norm').agg({
    'Nombre_de_Delictes':'sum',
    'PIB_per_Capita':'mean',
    'Percentatge_Estrangers':'mean',
    'Poblacio_Total':'mean'
}).corr()
# Convertim a format apt per a heatmap
corr_matrix = corr_df.reset_index().melt(id_vars='index')
corr_matrix.columns = ['Variable1', 'Variable2', 'Correlacio']

# Creem el heatmap
heatmap_fig = px.imshow(
    corr_df,
    text_auto=True,
    color_continuous_scale='RdBu_r',
    zmin=-1, zmax=1,
    labels=dict(x="Variable", y="Variable", color="Correlació"),
)

# Mostrem al Streamlit amb un key únic
st.plotly_chart(heatmap_fig, use_container_width=True, key="heatmap_corr")
st.markdown("""
La població del cantó explica gairebé tot el volum de delictes, mentre que el PIB i el percentatge d’estrangers tenen una influència molt més limitada.""")

# =========================
# Secció 10: Impacte de característiques socioeconòmiques en tendències per categoria
# =========================
st.subheader("Impacte de característiques socioeconòmiques en tendències de delictes per categoria")
bubble_data = df_filtered.groupby(['Any','Categorie','Canto_norm']).agg({
    'Nombre_de_Delictes':'sum',
    'PIB_per_Capita':'first',
    'Percentatge_Estrangers':'first',
    'Poblacio_Total':'first'
}).reset_index()

bubble_fig = px.scatter(
    bubble_data,
    x='PIB_per_Capita',
    y='Nombre_de_Delictes',
    size='Poblacio_Total',
    color='Percentatge_Estrangers',
    animation_frame='Any',
    hover_name='Canto_norm',
    facet_col='Categorie',
    size_max=40,
    color_continuous_scale='Viridis',
    labels={'Nombre_de_Delictes':'Delictes','Percentatge_Estrangers':'% estrangers','PIB_per_Capita':'PIB per càpita'}
)

bubble_fig = px.scatter(
    bubble_data,
    x='PIB_per_Capita',
    y='Nombre_de_Delictes',
    size='Poblacio_Total',
    color='Categorie',   # 👈 color discret
    animation_frame='Any',
    hover_name='Canto_norm',
    facet_col='Categorie',
    size_max=40,
    labels={
        'Nombre_de_Delictes':'Delictes',
        'PIB_per_Capita':'PIB per càpita'
    }
)

st.plotly_chart(bubble_fig, use_container_width=True)

st.markdown("""
EEl volum de delictes per categoria està principalment determinat per la població del cantó, amb efectes socioeconòmics moderats i específics segons el tipus de delicte.""")

st.markdown("---")

st.markdown("""## Conclusions

L’anàlisi de la criminalitat a Suïssa mitjançant l’enriquiment del *Swiss National Crime Dataset* amb dades demogràfiques i socioeconòmiques permet extreure diverses conclusions rellevants a nivell temporal, territorial i estructural.

### 1. Evolució temporal dels delictes
Entre 2008 i 2022 s’observa una **tendència general de descens dels delictes més abundants**, especialment *Robatoris / Détournements / Danys* i *Altres*, amb una lleugera recuperació en els darrers anys. En canvi, *Frau / Corrupció* mostra un **increment progressiu**, mentre que els delictes violents i les infraccions sexuals es mantenen relativament estables.

### 2. Diferències entre cantons
Existeixen **diferències territorials clares** en el nombre i el tipus de delictes. Els cantons urbans i densament poblats (Zuric, Vaud, Ginebra, Basel-Stadt) concentren més delictes, tant en termes absoluts com, en alguns casos, en taxa per 1.000 habitants, mentre que els cantons rurals presenten nivells significativament inferiors.

### 3. Taxa de resolució dels delictes
La **taxa de resolució depèn fortament del tipus de delicte**. Els delictes greus i específics (*Violència / Homicidi*, *Infraccions sexuals*) mostren taxes elevades i estables, mentre que els delictes més comuns (*Robatoris / Danys*) tenen una resolució baixa. *Frau / Corrupció* combina un augment de casos amb una disminució progressiva de la taxa de resolució.

### 4. Relació amb factors socioeconòmics
La **població total del cantó és el factor més determinant** del nombre de delictes. El PIB per càpita no mostra una relació clara amb la incidència criminal, mentre que el percentatge de població estrangera presenta una associació moderada, especialment en contextos urbans, sense evidència de causalitat directa.

### 5. Impacte regional i estructural
Les tendències criminals responen a la **interacció entre factors demogràfics, socioeconòmics i territorials**. Les diferències entre cantons són persistents al llarg del temps, indicant una estructura criminal relativament estable que requereix **estratègies de prevenció i investigació adaptades al context regional i al tipus de delicte**.

**En síntesi**, l’enfocament multidimensional (fet–dimensió) permet una comprensió més profunda de la criminalitat a Suïssa i aporta informació clau per a la planificació de polítiques públiques basades en evidència.""")
