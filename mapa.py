# import pandas as pd
# import json
# # import streamlit as st
# import pydeck as pdk

# with open("Limite_de_Bairros.geojson") as f:
#     geojson = json.load(f)

# st.title("🗺️ Bairros do Rio de Janeiro")

# layer = pdk.Layer(
#     "GeoJsonLayer",
#     data=geojson,
#     get_line_color=[0, 120, 255, 180],
#     get_line_width=20,
#     line_width_min_pixels=1,
#     pickable=True,
# )

# view = pdk.ViewState(
#     latitude=-22.9,
#     longitude=-43.2,
#     zoom=11,
# )

# chart = pdk.Deck(
#     layers=[layer],
#     initial_view_state=view,
#     tooltip={"text": " {nome}\n {regiao_adm}"}, 
# )

# st.pydeck_chart(chart)

import requests
import pandas as pd
import time
from collections import defaultdict

def localiza_linha(linha):
    url = "https://dados.mobilidade.rio/gps/sppo"
    
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={"Accept-Encoding": "gzip"},
        )
        response.raise_for_status()

    except requests.exceptions.ConnectionError:
        print("Sem conexão com a API. Tentando novamente em breve...")
        return None

    except requests.exceptions.Timeout:
        print("A API demorou demais para responder.")
        return None

    except requests.exceptions.HTTPError as e:
        print(f"⚠️ Erro HTTP: {e}")
        return None

    if response.status_code != 200:
        return None

    dados = [row for row in response.json() if str(row.get('linha', '')).strip() == str(linha)]

    if not dados:
        return None

    df = pd.DataFrame(dados, columns=['ordem','latitude','longitude','datahora','velocidade'])

    df['datahora'] = (
        pd.to_datetime(df['datahora'], unit="ms", utc=True)
        .dt.tz_convert("America/Sao_Paulo")
    )

    df['latitude'] = (
    df['latitude']
    .astype(str)
    .str.replace(',', '.', regex=False)
    .astype(float)
)

    df['longitude'] = (
        df['longitude']
        .astype(str)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )

    df = (df.sort_values(by=['ordem','datahora'], ascending=[True,False]))

    return df

while(1):
    print(localiza_linha(397))
