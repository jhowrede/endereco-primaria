import streamlit as st
import pandas as pd
import os
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Configuração da página
st.set_page_config(page_title="Buscar Endereço", layout="centered")
st.title("🔍 Buscar Endereço")

# Caminho do arquivo Excel
excel_path = "ENDEREÇO CTOP FINAL Atualizado.xlsx"

# Verifica se o arquivo existe
if not os.path.exists(excel_path):
    st.error(f"Arquivo '{excel_path}' não encontrado no diretório.")
    st.stop()

# Carregar os dados
@st.cache_data
def carregar_dados():
    return pd.read_excel(excel_path)

df = carregar_dados()

# === Função de geocodificação aprimorada ===
@st.cache_data
def geocodificar_enderecos(df, cidade):
    if {"LAT", "LON"}.issubset(df.columns):
        return df  # já tem coordenadas salvas
    
    geolocator = Nominatim(user_agent="streamlit_app")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    latitudes = []
    longitudes = []

    for _, row in df.iterrows():
        endereco = str(row.get("Endereço", "")).strip()
        bairro = str(row.get("BAIRRO", "")).strip()
        at = str(row.get("AT", "")).strip()

        # Monta uma query mais completa
        query = f"{endereco}, {bairro}, {cidade}, {at}, Brasil"

        try:
            location = geocode(query)
            if location:
                latitudes.append(location.latitude)
                longitudes.append(location.longitude)
            else:
                # Se não achou, tenta com menos informações
                query_alt = f"{endereco}, {cidade}, Brasil"
                location = geocode(query_alt)
                if location:
                    latitudes.append(location.latitude)
                    longitudes.append(location.longitude)
                else:
                    latitudes.append(None)
                    longitudes.append(None)
        except Exception:
            latitudes.append(None)
            longitudes.append(None)

    df["LAT"] = latitudes
    df["LON"] = longitudes
    return df

# Filtro por CIDADE
cidade_escolhida = st.selectbox("Selecione a cidade:", sorted(df["CIDADE"].dropna().unique()))
df_filtrado = df[df["CIDADE"] == cidade_escolhida]

# Filtro por AT
ats_disponiveis = df_filtrado["AT"].dropna().unique()
if len(ats_disponiveis) > 0:
    at_escolhida = st.selectbox("Filtrar por AT:", ["Todas"] + sorted(ats_disponiveis.tolist()))
    if at_escolhida != "Todas":
        df_filtrado = df_filtrado[df_filtrado["AT"] == at_escolhida]

# Filtro por FAC
fac_unicas = df_filtrado["FAC"].dropna().unique()
if len(fac_unicas) > 0:
    fac_escolhida = st.selectbox("Filtrar por FAC:", ["Todas"] + sorted(fac_unicas.tolist()))
    if fac_escolhida != "Todas":
        df_filtrado = df_filtrado[df_filtrado["FAC"] == fac_escolhida]

# Exibir resultados e botão de download
if not df_filtrado.empty:
    st.markdown(f"### ✅ Resultados encontrados: {len(df_filtrado)}")
    colunas_exibidas = ["ID", "Endereço", "BAIRRO", "CIDADE", "AT", "CTO", "FAC"]
    colunas_disponiveis = [col for col in colunas_exibidas if col in df_filtrado.columns]
    df_final = df_filtrado[colunas_disponiveis].reset_index(drop=True)
    st.dataframe(df_final, use_container_width=True)

    # Botão de download CSV
    csv = df_final.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Baixar resultados como CSV",
        data=csv,
        file_name="resultados_filtrados.csv",
        mime="text/csv"
    )

    # === Exibir no mapa ===
    st.markdown("### 🗺️ Mapa dos endereços filtrados")
    df_mapa = geocodificar_enderecos(df_filtrado, cidade_escolhida)
    df_mapa = df_mapa.dropna(subset=["LAT", "LON"])  # remove os que não foram encontrados
    if not df_mapa.empty:
        st.map(df_mapa[["LAT", "LON"]])
    else:
        st.warning("⚠️ Nenhum endereço pôde ser localizado no mapa.")
else:
    st.warning("Nenhum resultado encontrado para os filtros aplicados.")
