import pandas as pd
import pymysql
import folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Configuração do locale
try:
    import locale

    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
except:
    print("Locale pt_BR.UTF-8 não disponível. Continuando com locale padrão.")

# Conectando ao banco de dados MySQL
db_name = "db_demo"
db_host = "localhost"
db_user = "grauzy_user"
db_pass = "@K41sal1s"

try:
    conn = pymysql.connect(
        host=db_host,
        port=int(3306),
        user=db_user,
        password=db_pass,
        db=db_name
    )
    print("Conexão realizada com sucesso")
except Exception as e:
    print(f"Erro na conexão: {e}")
    exit(1)  # Encerra o script com código de erro

# Verificar se a conexão foi estabelecida
if 'conn' not in locals():
    print("Conexão com o banco de dados não foi estabelecida.")
    exit(1)

# Carregando os dados da tabela tb_lancamentos_prod_recebida
query = """
    SELECT
        CASE
            WHEN b.NM_BAIRRO = 'ESTADOS' THEN REPLACE(b.NM_BAIRRO, 'ESTADOS', 'BAIRRO DOS ESTADOS')
            WHEN b.NM_BAIRRO = 'DOS ESTADOS' THEN REPLACE(b.NM_BAIRRO, 'DOS ESTADOS', 'BAIRRO DOS ESTADOS')
            WHEN b.NM_BAIRRO = 'JARDIM CIDADE UNIVERSITAR' THEN REPLACE(b.NM_BAIRRO, 'JARDIM CIDADE UNIVERSITAR', 'JARDIM CIDADE UNIVERSITARIA')
            WHEN b.NM_BAIRRO = 'JD CIDADE UNIVERSITARIA' THEN REPLACE(b.NM_BAIRRO, 'JD CIDADE UNIVERSITARIA', 'JARDIM CIDADE UNIVERSITARIA')
            WHEN b.NM_BAIRRO = 'TAMABUZINHO' THEN REPLACE(b.NM_BAIRRO, 'TAMABUZINHO', 'TAMBAUZINHO')
            WHEN b.NM_BAIRRO = 'VALENTINA FIGUEIREDO' THEN REPLACE(b.NM_BAIRRO, 'VALENTINA FIGUEIREDO', 'VALENTINA DE FIGUEIREDO')
            WHEN b.NM_BAIRRO = 'ALTIPLANO' THEN REPLACE(b.NM_BAIRRO, 'ALTIPLANO', 'ALTIPLANO CABO BRANCO')
            ELSE b.NM_BAIRRO
        END AS BAIRRO,
        COUNT(*) AS QUANTIDADE
    FROM
        db_demo.tb_beneficiario AS b
    WHERE
        b.CD_EMPRESA_CONVENIADA = 10
        AND YEAR(CURDATE()) - YEAR(b.DT_NASCIMENTO) -(DATE_FORMAT(CURDATE(), "%m%d") < DATE_FORMAT(b.DT_NASCIMENTO, "%m%d")) >60
        AND b.NM_CIDADE = 'João Pessoa'
    GROUP BY
        BAIRRO
    ORDER BY
        QUANTIDADE DESC
"""
df = pd.read_sql(query, conn)

# Configurar o geocoder
geolocator = Nominatim(user_agent="beneficiarios_bairros_jp")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


# Função para obter coordenadas
def get_coordinates(bairro):
    try:
        location = geocode(f"{bairro}, João Pessoa, PB, Brasil")
        if location:
            return (location.latitude, location.longitude)
        else:
            print(f"Coordenadas não encontradas para: {bairro}")
            return None
    except Exception as e:
        print(f"Erro ao geocodificar {bairro}: {e}")
        return None


# Adicionar coordenadas ao DataFrame
df['COORDENADAS'] = df['BAIRRO'].apply(get_coordinates)

# Remover bairros sem coordenadas
df = df.dropna(subset=['COORDENADAS'])

# Criando o mapa centrado em João Pessoa
mapa = folium.Map(location=[-7.1195, -34.8450], zoom_start=12)

# Definindo tamanho máximo do raio para o maior bairro
max_radius = 50  # Ajuste conforme necessário

# definindo círculos proporcionais para cada bairro
for idx, row in df.iterrows():
    lat, lon = row['COORDENADAS']
    quantidade = row['QUANTIDADE']

    # Calcular raio proporcional
    radius = (quantidade / df['QUANTIDADE'].max()) * max_radius

    #Titulo do mapa
    #map_title = "Distribuição dos beneficiários > 60 anos por bairro"
    #title_html = f'<h1 style="position:absolute;z-index:100000;left:40vw" >{map_title}</h1>'

    folium.Circle(
        location=[lat, lon],
        radius=radius * 10,
        color='red',
        tooltip=f"<strong> {row['BAIRRO']}</strong> <br>Quantidade de beneficiários:<strong>{row['QUANTIDADE']} </strong>",
        fill=True,
        fill_color='red',
        fill_opacity=0.5
    ).add_to(mapa)

# Legenda no mapa
legend_html = '''
     <div style="position: fixed; 
                 bottom: 50px; left: 50px; width: 250px; height: 60px; 
                 border:2px solid grey; z-index:9999; font-size:12px;
                 background-color:white;
                 ">
         <b>Beneficiários > 60 anos por bairro</b><br>
         <div style="display: inline-block; 
                     width: 20px; height: 20px; 
                     background-color: blue; opacity: 0.6;
                     margin-right: 5px;">
         </div>
         * Tamanho proporcional à quantidade
     </div>
'''
mapa.get_root().html.add_child(folium.Element(legend_html))

# Salvar o mapa
mapa.save('beneficiarios_por_bairro.html')
print("Mapa salvo como 'beneficiarios_por_bairro.html'")

# Mostrar os dados que serão plotados
print("\nDados que serão plotados no mapa:")
print(df[['BAIRRO', 'QUANTIDADE']].sort_values('QUANTIDADE', ascending=False))

conn.close()