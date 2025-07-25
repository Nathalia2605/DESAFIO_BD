# Script de Análise de Dados de E-commerce Brasileiro
# Requisitos: pandas, matplotlib, seaborn

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch

# Configurações
sns.set(style="whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)

# Leitura dos dados
order_items = pd.read_csv("order_items.csv")
payments = pd.read_csv("pag_de_pedidos.csv")
orders = pd.read_csv("pedidos.csv")
product_category_translation = pd.read_csv("produto_categoria_traducao.csv")
products = pd.read_csv("produtos.csv")
reviews = pd.read_csv("analise.csv")
customers = pd.read_csv("clientes.csv")

# Tratamento de datas
orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
orders["order_approved_at"] = pd.to_datetime(orders["order_approved_at"])
orders["order_delivered_customer_date"] = pd.to_datetime(
    orders["order_delivered_customer_date"]
)
orders["order_estimated_delivery_date"] = pd.to_datetime(
    orders["order_estimated_delivery_date"]
)

# Mesclagem de dados
products_merged = products.merge(
    product_category_translation, how="left", on="product_category_name"
)
order_items_products = order_items.merge(products_merged, on="product_id", how="left")
order_items_orders = order_items_products.merge(orders, on="order_id", how="left")
order_full = order_items_orders.merge(
    reviews[["order_id", "review_score"]], on="order_id", how="left"
)
order_full = order_full.merge(
    payments[["order_id", "payment_value"]], on="order_id", how="left"
)
order_full["purchase_month"] = order_full["order_purchase_timestamp"].dt.to_period("M")

# 1.b - Sazonalidade nas vendas e identificação de períodos de maior volume
sales_by_month = (
    order_full.groupby("purchase_month").agg({"order_id": "nunique"}).reset_index()
)
sales_by_month.columns = ["Mês", "Pedidos"]
sales_by_month["Mês"] = sales_by_month["Mês"].astype(str)

# Estatísticas de sazonalidade
pedidos_medio = sales_by_month["Pedidos"].mean()
pedidos_max = sales_by_month["Pedidos"].max()
pedidos_min = sales_by_month["Pedidos"].min()
mes_maior_venda = sales_by_month.loc[sales_by_month["Pedidos"].idxmax(), "Mês"]
mes_menor_venda = sales_by_month.loc[sales_by_month["Pedidos"].idxmin(), "Mês"]


# Gráfico principal de sazonalidade
plt.figure(figsize=(15, 10))

# Gráfico 1: Sazonalidade geral com destaque dos picos
plt.subplot(2, 2, 1)
sns.lineplot(
    data=sales_by_month, x="Mês", y="Pedidos", marker="o", linewidth=2, markersize=8
)
plt.title("Sazonalidade nas Vendas - Padrões Mensais", fontsize=14, fontweight="bold")
plt.xlabel("Mês")
plt.ylabel("Número de Pedidos")
plt.xticks(rotation=45)

# Destacar picos e vales
pico_idx = sales_by_month["Pedidos"].idxmax()
vale_idx = sales_by_month["Pedidos"].idxmin()
plt.scatter(
    sales_by_month.loc[pico_idx, "Mês"],
    sales_by_month.loc[pico_idx, "Pedidos"],
    color="red",
    s=100,
    zorder=5,
    label=f"Pico: {pedidos_max:.0f} pedidos",
)
plt.scatter(
    sales_by_month.loc[vale_idx, "Mês"],
    sales_by_month.loc[vale_idx, "Pedidos"],
    color="blue",
    s=100,
    zorder=5,
    label=f"Vale: {pedidos_min:.0f} pedidos",
)
plt.axhline(
    y=pedidos_medio,
    color="green",
    linestyle="--",
    alpha=0.7,
    label=f"Média: {pedidos_medio:.0f}",
)
plt.legend()
plt.grid(True, alpha=0.3)

# Gráfico 2: Top categorias por mês (análise de sazonalidade por categoria)
plt.subplot(2, 2, 2)
vendas_categoria_mes = (
    order_full.groupby(["purchase_month", "product_category_name_english"])
    .agg({"order_id": "nunique"})
    .reset_index()
)
vendas_categoria_mes.columns = ["Mês", "Categoria", "Pedidos"]

# Top 5 categorias em volume total
top_categorias = (
    order_full.groupby("product_category_name_english")
    .agg({"order_id": "nunique"})
    .reset_index()
    .nlargest(5, "order_id")["product_category_name_english"]
    .tolist()
)

vendas_top_categorias = vendas_categoria_mes[
    vendas_categoria_mes["Categoria"].isin(top_categorias)
]

for categoria in top_categorias:
    dados_categoria = vendas_top_categorias[
        vendas_top_categorias["Categoria"] == categoria
    ]
    # Converter período para string para compatibilidade com matplotlib
    dados_categoria["Mês_str"] = dados_categoria["Mês"].astype(str)
    plt.plot(
        dados_categoria["Mês_str"],
        dados_categoria["Pedidos"],
        marker="o",
        label=categoria,
        linewidth=2,
    )

plt.title("Sazonalidade por Categoria (Top 5)", fontsize=14, fontweight="bold")
plt.xlabel("Mês")
plt.ylabel("Número de Pedidos")
plt.xticks(rotation=45)
plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
plt.grid(True, alpha=0.3)

# Gráfico 3: Análise de tendência e sazonalidade
plt.subplot(2, 2, 3)
sales_by_month["Mês_num"] = range(len(sales_by_month))
sales_by_month["Tendência"] = (
    sales_by_month["Pedidos"].rolling(window=3, center=True).mean()
)

plt.plot(
    sales_by_month["Mês"],
    sales_by_month["Pedidos"],
    marker="o",
    label="Vendas Reais",
    linewidth=2,
)
plt.plot(
    sales_by_month["Mês"],
    sales_by_month["Tendência"],
    color="red",
    linestyle="--",
    label="Tendência (média móvel)",
    linewidth=2,
)
plt.title("Tendência de Vendas ao Longo do Tempo", fontsize=14, fontweight="bold")
plt.xlabel("Mês")
plt.ylabel("Número de Pedidos")
plt.xticks(rotation=45)
plt.legend()
plt.grid(True, alpha=0.3)

# Gráfico 4: Distribuição de vendas por trimestre
plt.subplot(2, 2, 4)
sales_by_month["Mês"] = pd.to_datetime(sales_by_month["Mês"].astype(str) + "-01")
sales_by_month["Trimestre"] = sales_by_month["Mês"].dt.quarter
sales_by_month["Ano"] = sales_by_month["Mês"].dt.year

vendas_trimestre = (
    sales_by_month.groupby(["Ano", "Trimestre"]).agg({"Pedidos": "sum"}).reset_index()
)
vendas_trimestre["Período"] = (
    vendas_trimestre["Ano"].astype(str)
    + " Q"
    + vendas_trimestre["Trimestre"].astype(str)
)

sns.barplot(data=vendas_trimestre, x="Período", y="Pedidos")
plt.title("Volume de Vendas por Trimestre", fontsize=14, fontweight="bold")
plt.xlabel("Trimestre")
plt.ylabel("Total de Pedidos")
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("1b_sazonalidade_vendas.png", dpi=300, bbox_inches="tight")

# Salvar dados de análise de sazonalidade
analise_sazonalidade = sales_by_month.copy()
analise_sazonalidade["Mês"] = analise_sazonalidade["Mês"].astype(str)
analise_sazonalidade["Variação_vs_média"] = (
    (analise_sazonalidade["Pedidos"] - pedidos_medio) / pedidos_medio * 100
)
analise_sazonalidade.to_csv("1b_analise_sazonalidade.csv", index=False)

# 2.a - Prazos de entrega e fatores que influenciam atrasos
order_full["delivery_time"] = (
    order_full["order_delivered_customer_date"] - order_full["order_purchase_timestamp"]
).dt.days
order_full["atraso_entrega"] = (
    order_full["order_delivered_customer_date"]
    > order_full["order_estimated_delivery_date"]
)
order_full["dias_atraso"] = (
    order_full["order_delivered_customer_date"]
    - order_full["order_estimated_delivery_date"]
).dt.days

entregas_validas = order_full[order_full["delivery_time"].notnull()]

# Estatísticas gerais de entrega
tempo_medio_entrega = entregas_validas["delivery_time"].mean()
porcentagem_atrasos = (
    entregas_validas["atraso_entrega"].sum() / len(entregas_validas)
) * 100
atraso_medio = entregas_validas[entregas_validas["atraso_entrega"]][
    "dias_atraso"
].mean()


# Gráfico 1: Distribuição do tempo de entrega
plt.figure(figsize=(12, 8))

plt.subplot(2, 2, 1)
sns.histplot(entregas_validas["delivery_time"], bins=30, kde=True)
plt.title("Distribuição do Tempo de Entrega")
plt.xlabel("Dias")
plt.ylabel("Quantidade")
plt.axvline(
    tempo_medio_entrega,
    color="red",
    linestyle="--",
    label=f"Média: {tempo_medio_entrega:.1f} dias",
)
plt.legend()

# Gráfico 2: Atrasos por categoria de produto
plt.subplot(2, 2, 2)
atrasos_por_categoria = (
    entregas_validas.groupby("product_category_name_english")
    .agg(
        total_entregas=("order_id", "count"),
        atrasos=("atraso_entrega", "sum"),
        tempo_medio=("delivery_time", "mean"),
    )
    .reset_index()
)
atrasos_por_categoria["taxa_atraso"] = (
    atrasos_por_categoria["atrasos"] / atrasos_por_categoria["total_entregas"]
) * 100

top_categorias_atraso = atrasos_por_categoria.nlargest(10, "taxa_atraso")
sns.barplot(
    data=top_categorias_atraso, x="taxa_atraso", y="product_category_name_english"
)
plt.title("Top 10 Categorias com Maior Taxa de Atraso")
plt.xlabel("Taxa de Atraso (%)")

# Gráfico 3: Tempo de entrega vs Preço do frete
plt.subplot(2, 2, 3)
sns.scatterplot(data=entregas_validas, x="freight_value", y="delivery_time", alpha=0.5)
plt.title("Tempo de Entrega vs Valor do Frete")
plt.xlabel("Valor do Frete (R$)")
plt.ylabel("Tempo de Entrega (dias)")

# Gráfico 4: Atrasos por mês
plt.subplot(2, 2, 4)
entregas_validas["mes_compra"] = entregas_validas[
    "order_purchase_timestamp"
].dt.to_period("M")
atrasos_por_mes = (
    entregas_validas.groupby("mes_compra")
    .agg(total_entregas=("order_id", "count"), atrasos=("atraso_entrega", "sum"))
    .reset_index()
)
atrasos_por_mes["taxa_atraso"] = (
    atrasos_por_mes["atrasos"] / atrasos_por_mes["total_entregas"]
) * 100
atrasos_por_mes["mes_compra"] = atrasos_por_mes["mes_compra"].astype(str)

sns.lineplot(data=atrasos_por_mes, x="mes_compra", y="taxa_atraso", marker="o")
plt.title("Taxa de Atraso por Mês")
plt.xlabel("Mês")
plt.ylabel("Taxa de Atraso (%)")
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig("2a_prazo_entrega.png", dpi=300, bbox_inches="tight")

# Salvar dados de análise de atrasos
analise_atrasos = atrasos_por_categoria.sort_values("taxa_atraso", ascending=False)
analise_atrasos.to_csv("2a_analise_atrasos_categoria.csv", index=False)

# 3.a - Avaliação de produtos
avaliacoes_produto = (
    order_full.groupby("product_id")
    .agg(
        media_avaliacao=("review_score", "mean"),
        qtd_avaliacoes=("review_score", "count"),
    )
    .reset_index()
)
avaliacoes_produto = avaliacoes_produto.merge(
    products_merged[["product_id", "product_category_name_english"]],
    on="product_id",
    how="left",
)
avaliacoes_filtradas = avaliacoes_produto[avaliacoes_produto["qtd_avaliacoes"] >= 10]
top_10_melhores = avaliacoes_filtradas.sort_values(
    by="media_avaliacao", ascending=False
).head(10)
top_10_piores = avaliacoes_filtradas.sort_values(
    by="media_avaliacao", ascending=True
).head(10)
avaliacoes_resultado = pd.concat([top_10_melhores, top_10_piores])
avaliacoes_resultado.to_csv("3a_avaliacoes_produtos.csv", index=False)

# 4.a - Lucratividade por categoria
order_full["lucro_liquido"] = order_full["price"] - order_full["freight_value"]
# Cálculo da porcentagem de lucro (margem de lucro)
order_full["porcentagem_lucro"] = (
    order_full["lucro_liquido"] / order_full["price"]
) * 100

lucro_por_categoria = (
    order_full.groupby("product_category_name_english")
    .agg(
        lucro_total=("lucro_liquido", "sum"),
        vendas=("order_id", "count"),
        receita_total=("price", "sum"),
        porcentagem_lucro_media=("porcentagem_lucro", "mean"),
    )
    .reset_index()
)
lucro_por_categoria["lucro_medio"] = (
    lucro_por_categoria["lucro_total"] / lucro_por_categoria["vendas"]
)
top_lucratividade = lucro_por_categoria.sort_values(
    by="lucro_medio", ascending=False
).head(10)
top_lucratividade.to_csv("4a_lucratividade_categoria.csv", index=False)

# 5.b - Eficácia promocional com novos clientes e destaques
orders_customers = orders.merge(customers, on="customer_id", how="left")
first_orders = orders_customers.sort_values("order_purchase_timestamp").drop_duplicates(
    "customer_unique_id", keep="first"
)
first_orders["purchase_month"] = first_orders["order_purchase_timestamp"].dt.to_period(
    "M"
)
novos_clientes_por_mes = (
    first_orders.groupby("purchase_month").size().reset_index(name="novos_clientes")
)
novos_clientes_por_mes["purchase_month"] = novos_clientes_por_mes[
    "purchase_month"
].astype(str)

preco_mensal = (
    order_full.groupby(["purchase_month", "product_category_name_english"])
    .agg(preco_medio=("price", "mean"), vendas=("order_id", "count"))
    .reset_index()
)
categoria_destaque = (
    preco_mensal.groupby("product_category_name_english")["vendas"]
    .sum()
    .sort_values(ascending=False)
    .index[0]
)
preco_categoria = preco_mensal[
    preco_mensal["product_category_name_english"] == categoria_destaque
].copy()
preco_categoria["purchase_month"] = preco_categoria["purchase_month"].astype(str)
dados_marketing = preco_categoria.merge(
    novos_clientes_por_mes, on="purchase_month", how="left"
)
limiar_promocao = dados_marketing["preco_medio"].quantile(0.25)
dados_marketing["promocao"] = dados_marketing["preco_medio"] < limiar_promocao

# Gráfico final com destaque de marketing
fig, ax1 = plt.subplots(figsize=(14, 6))
sns.lineplot(
    data=dados_marketing,
    x="purchase_month",
    y="vendas",
    ax=ax1,
    color="tab:blue",
    marker="o",
)
ax1.set_xlabel("Mês")
ax1.set_ylabel("Vendas", color="tab:blue")
ax1.tick_params(axis="y", labelcolor="tab:blue")

ax2 = ax1.twinx()
ax2.tick_params(axis="y", labelcolor="tab:red")

ax1b = ax1.twinx()
ax1b.spines.right.set_position(("outward", 60))
sns.barplot(
    data=dados_marketing,
    x="purchase_month",
    y="novos_clientes",
    ax=ax1b,
    color="tab:green",
    alpha=0.3,
)
ax1b.set_ylabel("Novos Clientes", color="tab:green")
ax1b.tick_params(axis="y", labelcolor="tab:green")

for i, row in dados_marketing.iterrows():
    if row["promocao"]:
        ax1.axvspan(i - 0.4, i + 0.4, color="yellow", alpha=0.2)

legend_promo = Patch(
    facecolor="yellow",
    edgecolor="yellow",
    color="yellow",
    alpha=0.2,
    label="Atuação de Marketing (Promoções)",
)

sales_volume = Patch(
    facecolor="blue",
    edgecolor="blue",
    alpha=0.2,
    label="Volume de Vendas",
    capstyle="round",
)

plt.title(
    "Análise de Marketing - Eficácia de Campanhas Promocionais\nImpacto Visual do Marketing (Faixas Amarelas)"
)
ax1.set_xticklabels(dados_marketing["purchase_month"], rotation=45)
fig.tight_layout()
plt.grid(True)

lines_labels = [ax.get_legend_handles_labels() for ax in [ax1, ax2]]
lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
lines.append(sales_volume)
lines.append(legend_promo)
labels.append("Volume de Vendas")
labels.append("Atuação de Marketing (Promoções)")
fig.legend(lines, labels, loc="upper left", bbox_to_anchor=(0.06, 0.92))

plt.savefig("5b_eficacia_promocao_destaque_marketing.png")
