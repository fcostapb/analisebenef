from textwrap import wrap

import matplotlib.pyplot as plt
import pandas as pd
import pymysql
import seaborn as sns

import locale

locale.setlocale(locale.LC_ALL,"pt_BR.UTF-8")

# Dados de conexão ao banco de dados
db_name = "db_demo"
db_host = "localhost"
db_user = "grauzy_user"
db_pass = "@K41sal1s"

query = """
        SELECT
            CASE 
                WHEN b.NM_BAIRRO = 'ESTADOS' THEN REPLACE(b.NM_BAIRRO,'ESTADOS','BAIRRO DOS ESTADOS')
                WHEN b.NM_BAIRRO = 'DOS ESTADOS' THEN REPLACE(b.NM_BAIRRO,'DOS ESTADOS', 'BAIRRO DOS ESTADOS')
                WHEN b.NM_BAIRRO = 'JARDIM CIDADE UNIVERSITAR' THEN REPLACE(b.NM_BAIRRO,'JARDIM CIDADE UNIVERSITAR', 'JARDIM CIDADE UNIVERSITARIA')
                WHEN b.NM_BAIRRO = 'JD CIDADE UNIVERSITARIA' THEN REPLACE(b.NM_BAIRRO,'JD CIDADE UNIVERSITARIA', 'JARDIM CIDADE UNIVERSITARIA')
                WHEN b.NM_BAIRRO = 'TAMABUZINHO' THEN REPLACE(b.NM_BAIRRO,'TAMABUZINHO', 'TAMBAUZINHO')
                WHEN b.NM_BAIRRO = 'VALENTINA FIGUEIREDO' THEN REPLACE(b.NM_BAIRRO,'VALENTINA FIGUEIREDO', 'VALENTINA DE FIGUEIREDO')
                ELSE b.NM_BAIRRO
            END AS BAIRRO,
            YEAR(CURDATE()) - YEAR(b.DT_NASCIMENTO) -(DATE_FORMAT(CURDATE(), "%m%d") < DATE_FORMAT(b.DT_NASCIMENTO, "%m%d")) AS IDADE
        FROM
            db_demo.tb_beneficiario AS b
        WHERE
            b.CD_EMPRESA_CONVENIADA = 10
            AND b.NM_CIDADE = 'João Pessoa'
        GROUP BY
            BAIRRO, IDADE
        ORDER BY BAIRRO ASC
        """

try:

    # Conexão
    conn = pymysql.connect(
        host=db_host,
        port=int(3306),
        user=db_user,
        password=db_pass,
        db=db_name
    )
    # Carregando os dados em um DataFrame
    df = pd.read_sql(query, conn)

    print("Dados carregados com sucesso!")
    print(df.head())
    print("\n")
    print(f"Total de registros: {len(df)}")
    print(f"Qtd. Bairros: {df['BAIRRO'].nunique()}")

    # Análise descritiva
    print("\nEstatísticas descritivas das idades:")
    print(df['IDADE'].describe().round(1))

    # Criando faixas etárias
    bins = [0, 18, 23, 28, 33, 38, 43, 48, 53, 58, 100]
    labels = ['0-18', '19-23', '24-28', '29-33', '34-38', '39-43', '44-48', '49-53', '54-58', '59+']
    df['FAIXA_ETARIA'] = pd.cut(df['IDADE'], bins=bins, labels=labels)

    # Configuração de estilo
    #plt.style.use('seaborn') # REMOVA ESTA LINHA
    sns.set_palette("husl")

    # 1. Distribuição etária geral com rótulos
    plt.figure(figsize=(14, 7))
    ax = sns.histplot(data=df, x='IDADE', bins=30, kde=True)

    # Adicionando rótulos de dados
    for p in ax.patches:
        if p.get_height() > 0:
            ax.annotate(f"{int(p.get_height())}",
                        (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='center',
                        xytext=(0, 5),
                        textcoords='offset points')

    plt.title('Distribuição de Idade dos Beneficiários em João Pessoa', fontsize=16, pad=20)
    plt.xlabel('Idade', fontsize=12)
    plt.ylabel('Quantidade de Beneficiários', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    # 2. Top 10 bairros com mais beneficiários - Gráfico de barras
    top_bairros = df['BAIRRO'].value_counts().nlargest(10)

    plt.figure(figsize=(14, 7))
    ax = sns.barplot(x=top_bairros.index, y=top_bairros.values)

    # Adicionando rótulos
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height())}",
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center',
                    xytext=(0, 5),
                    textcoords='offset points',
                    fontsize=10)

    plt.title('Top 10 Bairros com Mais Beneficiários', fontsize=16, pad=20)
    plt.xlabel('Bairro', fontsize=12)
    plt.ylabel('Quantidade de Beneficiários', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()

    # 3. Boxplot de idade por bairro (top 10)
    df_top = df[df['BAIRRO'].isin(top_bairros.index)]

    plt.figure(figsize=(14, 7))
    ax = sns.boxplot(data=df_top, x='BAIRRO', y='IDADE')

    # Adicionando número de observações
    medians = df_top.groupby('BAIRRO')['IDADE'].median().values
    nobs = df_top['BAIRRO'].value_counts().values
    nobs = [str(x) for x in nobs]

    pos = range(len(nobs))
    for tick, label in zip(pos, ax.get_xticklabels()):
        ax.text(pos[tick], medians[tick] + 0.5, nobs[tick],
                horizontalalignment='center',
                size='small',
                color='black',
                weight='semibold')

    plt.title('Distribuição de Idade nos 10 Bairros com Mais Beneficiários', fontsize=16, pad=20)
    plt.xlabel('Bairro', fontsize=12)
    plt.ylabel('Idade', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()

    # 4. Heatmap de faixas etárias por bairro (top 15)
    top_15_bairros = df['BAIRRO'].value_counts().nlargest(15).index
    df_top_15 = df[df['BAIRRO'].isin(top_15_bairros)]

    cross_tab = pd.crosstab(df_top_15['BAIRRO'], df_top_15['FAIXA_ETARIA'])
    cross_tab = cross_tab[labels]  # Ordem correta das faixas

    plt.figure(figsize=(16, 9))
    ax = sns.heatmap(cross_tab, annot=True, fmt='d', cmap='YlOrRd', linewidths=.5,
                     annot_kws={"size": 10, "color": "black"})

    # Ajustando rótulos
    ax.set_yticklabels(["\n".join(wrap(label.get_text(), 15)) for label in ax.get_yticklabels()])

    plt.title('Mapa de calor - Distribuição de Faixas Etárias por Bairro (Top 15)', fontsize=16, pad=20)
    plt.xlabel('Faixa Etária', fontsize=12)
    plt.ylabel('Bairro', fontsize=12)
    plt.tight_layout()
    plt.show()

    # 5. Média de idade por bairro (top 20)
    media_idade = df.groupby('BAIRRO')['IDADE'].mean().sort_values(ascending=False).head(20)

    plt.figure(figsize=(14, 7))
    ax = sns.barplot(x=media_idade.index, y=media_idade.values)

    # Adicionando rótulos
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.1f} anos",
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center',
                    xytext=(0, 5),
                    textcoords='offset points',
                    fontsize=10)

    plt.title('Top 20 Bairros com Maior Média de Idade', fontsize=16, pad=20)
    plt.xlabel('Bairro', fontsize=12)
    plt.ylabel('Média de Idade', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()

    # 6. Distribuição percentual por faixa etária
    faixa_dist = df['FAIXA_ETARIA'].value_counts(normalize=True).sort_index() * 100

    plt.figure(figsize=(12, 6))
    ax = sns.barplot(x=faixa_dist.index, y=faixa_dist.values)

    # Adicionando rótulos percentuais
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.1f}%",
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center',
                    xytext=(0, 5),
                    textcoords='offset points',
                    fontsize=10)

    plt.title('Distribuição Percentual por Faixa Etária', fontsize=16, pad=20)
    plt.xlabel('Faixa Etária', fontsize=12)
    plt.ylabel('Percentual (%)', fontsize=12)
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"Erro: {e}")
finally:
    if conn:
        conn.close()
