import requests
import pandas as pd
import time
import streamlit as st
import pydeck as pdk
import json
from collections import defaultdict
import pyarrow.parquet as pq
import pyarrow as pa
import numpy as np
import plotly.express as px

## Título da página,layout
st.set_page_config(page_title="GPS Rio Ônibus")

@st.cache_data(ttl=14)
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
        st.warning("Sem conexão com a API. Tentando novamente em breve.")
        return None

    except requests.exceptions.Timeout:
        st.warning("Tempo excessivo para resposta da API.")
        return None

    except requests.exceptions.HTTPError as e:
        st.warning(f"Erro HTTP: {e}")
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

    df = (df.sort_values(by=['ordem','datahora'], ascending=[True,False]).drop_duplicates(subset='ordem', keep='first'))

    return df

@st.cache_data
def carrega_itinerario(path, servico):
    with open(path) as f:
        geojson = json.load(f)
    geojson_filtrado = {
        "type": "FeatureCollection",
        "features": [
            f for f in geojson['features']
            if str(f['properties'].get('servico', '')).strip() == str(servico)
        ]
    }

    destinos = defaultdict(list)
    for f in geojson_filtrado['features']:
        servico_key = str(f['properties']['servico']).strip()
        destinos[servico_key].append({
            'destino': f['properties'].get('destino', ''),
            'extensao': f['properties'].get('SHAPE__Length', 0)
        })

    return geojson_filtrado, destinos

@st.cache_data
def tempo_medio_viagem(df,linha,tipo_dia,sentido):
    bins=np.linspace(0,24,25)
    labels=['0h-1h','1h-2h','2h-3h','3h-4h','4h-5h','5h-6h','6h-7h','7h-8h','8h-9h','9h-10h','10h-11h','11h-12h','12h-13h','13h-14h','14h-15h','15h-16h',
    '16h-17h','17h-18h','18h-19h','19h-20h','20h-21h','21h-22h','22h-23h','23h-24h']
    viagem_linha = df[(df['servico'] == linha) & (df['tipo_dia'] == tipo_dia) & (df['sentido'] == sentido)]

    viagem_linha['faixa_horaria'] = pd.cut(
    viagem_linha['datetime_partida'].dt.hour,
    bins=bins,
    labels=labels,
    right=False 
    )

    resultado = viagem_linha.groupby('faixa_horaria', observed=False, sort=True)['tempo_viagem'].median().reset_index(name='mediana_tempo_viagem')

    resultado['faixa_horaria'] = pd.Categorical(resultado['faixa_horaria'], categories=labels, ordered=True)
    resultado = resultado.sort_values('faixa_horaria')
    resultado['faixa_horaria'] = resultado['faixa_horaria'].astype(str)


    resultado['tempo_formatado'] = resultado['mediana_tempo_viagem'].apply(
    lambda s: f"{int(s // 60):02d}:{int(s % 60):02d}" if pd.notna(s) else '')

    return resultado, labels

#Leitura de parquet com dados de todas as viagens entre 01/01/2026 e 18/05/2026
tabela = pq.read_table('viagem_onibus.parquet')
tabela = tabela.replace_schema_metadata({})  
df_dados_viagens = tabela.to_pandas(date_as_object=True)

def main():
    
    linha = st.text_input('Busque a linha')
    st.write('## Monitoramento de linhas de ônibus municipais do Rio de Janeiro')

    if linha == '':
        st.info('Digite o número de uma linha para visualizar detalhes e a posição de seus carros em tempo real')

    else:
        df = localiza_linha(linha)
        geojson_filtrado, destinos = carrega_itinerario("itinerarios.geojson", linha)

        destino_str = ' / '.join(item['destino'] for item in destinos.get(str(linha).strip(), []))

        if df is None or df.empty:
            st.warning("Não foi possível coletar dados. Pode ter ocorrido alguma das situações a seguir:\n 1. Digitação incorreta do número da linha\n2. A linha não se encontra em operação no horário\n3. Falha ao acessar os dados")
        
        else:

            df['velocidade'] = pd.to_numeric(df['velocidade'], errors='coerce').fillna(0)
            veiculos_ativos = len(df[df['velocidade'] != 0])

            with st.container(border=True):
                st.markdown(
                """
                <style>
                .centered-text {
                    text-align: center;
                    font-size: 28px;
                }
                </style>
                <div class="centered-text">
                    Informações da linha<br>
                </div>
                """,
                unsafe_allow_html=True
                )

                st.write(f'Linha: {linha}')
                st.write(f'Trecho: {destino_str}')
                st.write(f'Extensão do trajeto com destino a {destinos[linha][0]["destino"]}: {round(float(destinos[linha][0]["extensao"])/1000,2)} km')
                st.write(f'Extensão do trajeto com destino a {destinos[linha][1]["destino"]}: {round(float(destinos[linha][1]["extensao"])/1000,2)} km')
                st.write(f'Veículos em circulação neste momento: {veiculos_ativos}')

            with st.container(border=True):

                st.markdown(
                """
                <style>
                .centered-text {
                    text-align: center;
                    font-size: 28px;
                }
                </style>
                <div class="centered-text">
                    Monitoramento em tempo real<br>
                </div>
                """,
                unsafe_allow_html=True
                )

                status = st.empty()
                map_placeholder = st.empty()

                linha1 = {k: v for k, v in geojson_filtrado.items()}
                linha1["features"] = [geojson_filtrado["features"][0]]

                linha2 = {k: v for k, v in geojson_filtrado.items()}
                linha2["features"] = [geojson_filtrado["features"][1]]

                layerlinha1 = pdk.Layer(
                    "GeoJsonLayer",
                    data=linha1,
                    get_line_color=[0, 120, 255, 150],
                    get_line_width=30,
                    line_width_min_pixels=2,
                    pickable=True,
                )

                layerlinha2 = pdk.Layer(
                    "GeoJsonLayer",
                    data=linha2,
                    get_line_color=[255, 60, 0, 150],
                    get_line_width=30,
                    line_width_min_pixels=2,
                    pickable=True,
                )

                # Camada dos ônibus (círculo + rótulo)
                scatter_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=df,
                    get_position='[longitude, latitude]',
                    get_fill_color=[255, 60, 60, 220],
                    get_radius=40,
                    radius_min_pixels=10,
                    radius_max_pixels=10,
                    pickable=True,
                )

                text_layer = pdk.Layer(
                    "TextLayer",
                    data=df,
                    get_position='[longitude, latitude]',
                    get_text='ordem',
                    get_size=11,
                    get_color=[255, 255, 255, 255],
                    get_alignment_baseline="'center'",
                    get_text_anchor="'middle'",
                )

                coords = [c for f in geojson_filtrado['features'] for c in f['geometry']['coordinates']]
                view = pdk.ViewState(
                    latitude=sum(c[1] for c in coords) / len(coords),
                    longitude=sum(c[0] for c in coords) / len(coords),
                    zoom=11,
                )

                chart = pdk.Deck(
                    layers=[layerlinha1, layerlinha2, scatter_layer, text_layer],
                    initial_view_state=view,
                    tooltip={"text": "Identificador: {ordem}\Velocidade: {velocidade}km/h\nSentido: {destino}"},
                )      

                map_placeholder.pydeck_chart(chart)

            with st.container(border=True):

                st.markdown(
                """
                <style>
                .centered-text {
                    text-align: center;
                    font-size: 28px;
                }
                </style>
                <div class="centered-text">
                    Tempos esperados de viagens<br>
                </div>
                """,
                unsafe_allow_html=True
                )

                tipo_dia = st.selectbox(
                label='Tipo de dia',
                options=df_dados_viagens['tipo_dia'].unique(),
                index=None,
                placeholder='Opções'
                )
                resultado_ida, labels = tempo_medio_viagem(df_dados_viagens,linha,tipo_dia,'I')
                resultado_volta,_ = tempo_medio_viagem(df_dados_viagens,linha,tipo_dia,'V')

                print(resultado_ida['faixa_horaria'].dtype)
                print(resultado_ida)

                fig_ida = px.bar(
                    resultado_ida,
                    x='faixa_horaria',
                    y='mediana_tempo_viagem',
                    text='tempo_formatado',
                    barmode='group',
                    category_orders={'faixa_horaria': resultado_ida['faixa_horaria'].tolist()} 

                )
                fig_ida.update_layout(yaxis=dict(title='Tempo de viagem', showticklabels=False), xaxis=dict(title='Horário'), title_text=f'Tempo de viagem no sentido {destinos[linha][0]["destino"]}')

                fig_volta = px.bar(
                    resultado_volta,
                    x='faixa_horaria',
                    y='mediana_tempo_viagem',
                    text='tempo_formatado',
                    barmode='group',
                    category_orders={'faixa_horaria': resultado_ida['faixa_horaria'].tolist()}
                )
                fig_volta.update_layout(yaxis=dict(title='Tempo de viagem', showticklabels=False), xaxis=dict(title='Horário'), title_text=f'Tempo de viagem no sentido {destinos[linha][1]["destino"]}')

                st.plotly_chart(fig_ida)
                st.plotly_chart(fig_volta)



            time.sleep(30)
            st.rerun()

if __name__ == "__main__":
    main()
