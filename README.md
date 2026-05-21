# 📄 Monitoramento de linhas de ônibus municipais do Rio de Janeiro


## Introdução

Este documento introduz  as funcionalidades encontradas no **Painel de Monitoramento de linhas de ônibus municipais do Rio de Janeiro**. Este projeto propõe um painel que pode ser utilizado como aplicativo centralizardor de informações úteis sobre a operação deste modal na cidade, especialmente do ponto de vista do usuário. Todas as informações tratadas e exibidas na página são públicas, obtidas através da página [DATA.RIO](https://data.rio).

## Metodologia

A manipulação dos dados é realizada integralmente por meio de um subrotinas escritas na linguagem Python, sendo destacado o uso da biblioteca **Pandas** para manipulação dos dados e da biblioteca **Streamlit** para elaboração do painel de visualização.

## Acesso ao painel e base de dados

O painel para visualização dos dados e aplicação pode ser acessado diretamente através [deste link](https://gpsrioonibus.streamlit.app/).

Alternativamente, o repositório pode ser clonado para que as subrotinas sejam executadas localmente em um interpretador Python. Seguem as etapas:

```
git clone https://github.com/henriquecuryboaro/Onibus_RJ

```
Com o diretório clonado, instalam-se os pacotes necessários à execução do painel ao se executar o seguinte código no diretório em que os arquivos do projeto se encontram:

```
pip install -r requirements.txt
```

É recomendado o isolamento do ambiente em que o projeto será executado por meio da criação de ambiente virtual.

## Conteúdo do painel

O conteúdo do painel é exibido em uma página única, com a visualização dos dados ocorrendo em três blocos:

* **Informações da linha**: informações gerais da linha, com distâncias percorridas e quantitativo de veículos em movimento no instante da consulta
* **Monitoramento em tempo real**: exibição da posição dos veículos da linha em tempo real, com atualização a cada 30 segundos
* **Tempos esperados de viagens**: tempos esperados de viagem no trecho completo da linha, separados por classificações de dias e horários da operação


### Imagens

![Visualização de dados no painel](/Figura1.jpeg "Informações do painel de natureza operacional")

![Visualização de dados no painel](/Figura2.jpeg "Informações do painel de natureza operacional")




