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
