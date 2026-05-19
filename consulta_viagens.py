import basedosdados as bd
import pandas as pd

query = """
    SELECT data, 
           tipo_dia, 
           servico,
           sentido,
           datetime_partida,
           tempo_viagem
    FROM `datario.transporte_rodoviario_municipal.viagem_onibus`
    WHERE data BETWEEN '2026-01-01' AND '2026-05-18'
"""

# df = bd.read_sql ( query,billing_project_id = "proven-mind-485116-i6" )
# print(df.head(50))

# df.to_parquet(
#     "viagem_onibus.parquet",
#     engine="pyarrow",  
#     compression="snappy",  
#     index=False
# )

df = pd.read_parquet('viagem_onibus.parquet')
viagens_397 = df[df['servico'] == '397']
util_397 = viagens_397[viagens_397['tipo_dia'] == 'Domingo']
print(util_397['tempo_viagem'].mean())
print(util_397['tempo_viagem'].median())