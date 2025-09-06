# Projeto: Pipeline ETL Completo com AWS Glue, S3 e Redshift

## Visão Geral do Projeto

Este projeto demonstra a construção de um pipeline de Extração, Transformação e Carga (ETL) robusto e escalável utilizando serviços da Amazon Web Services (AWS).
O objetivo principal é processar dados brutos recebidos de um produtor de arquivos CSV, ingeridos via AWS Lambda e armazenados no Amazon S3.
Em seguida, os dados são catalogados e transformados pelo AWS Glue, armazenados no formato Parquet e, finalmente, disponibilizados para análise no Amazon Redshift.
Além disso, consultas interativas podem ser feitas diretamente no S3 utilizando Amazon Athena ou Redshift Spectrum.

## Arquitetura do Projeto

O fluxo segue conforme o diagrama:

**Produtor → CSV**: Fonte de dados externa que gera arquivos CSV.

**AWS Lambda (Consumidor)**: Função responsável por ingerir e depositar os arquivos no bucket de dados brutos no S3.

**Amazon S3 (Dados Brutos – CSV)**: Camada de armazenamento inicial dos dados recebidos.

**AWS Glue Crawler**: Descobre o esquema dos dados brutos e registra no Glue Data Catalog.

**AWS Glue ETL Job (PySpark)**: Transforma os dados brutos em dados estruturados, convertendo para Parquet.

**Amazon S3 (Dados Estruturados – Parquet)**: Camada de dados processados.

**Glue Data Catalog**: Repositório de metadados, utilizado por Glue, Athena e Redshift Spectrum.

**Amazon Athena**: Permite consultas interativas diretamente sobre os dados processados no S3, sem necessidade de carga no Redshift.

**Amazon Redshift Spectrum**: Habilita consultas sobre os dados processados no S3, integrando-os ao Redshift.

**Amazon Redshift**: Data warehouse final para análises avançadas e relatórios agregados.

## Ferramentas e Tecnologias Envolvidas

Ferramentas e Tecnologias Envolvidas

*   **AWS Lambda** → para ingestão automatizada de arquivos CSV no bucket raw do S3.
*   **Amazon S3** → armazenamento de dados brutos e processados.
*   **AWS Glue (Crawler, Catalog e ETL Jobs)** → catalogação, transformação e integração.
*   **Amazon Athena** → consultas SQL interativas diretamente sobre os dados no S3.
*   **Amazon Redshift Spectrum** → consulta federada entre S3 e Redshift.
*   **Amazon Redshift** → armazenamento final para análise de larga escala.
*   **PySpark** → transformação de dados dentro do Glue ETL.

## Pré-requisitos

Para replicar e executar este projeto, você precisará:

*   Uma conta AWS ativa.
*   Acesso ao console da AWS com permissões adequadas para S3, Glue e Redshift.
*   Conhecimento básico de SQL e Python.
*   (Opcional, mas recomendado) AWS CLI configurada em sua máquina local.

## Passo a Passo para Implementação

### 1. Criar Bucket S3 para Dados Brutos

O primeiro passo é criar um bucket no Amazon S3 para armazenar os dados brutos que serão processados pelo pipeline.

1.  Acesse o console da AWS e procure por "S3".
2.  Clique em "Criar bucket".
3.  **Nome do bucket**: `raw-sales-data-neto` (ou um nome único de sua preferência, seguindo as convenções de nomenclatura do S3).
4.  **Região da AWS**: Escolha a região mais próxima de você.
5.  Mantenha as outras configurações padrão e clique em "Criar bucket".

### 2. Upload de um CSV de Exemplo

Para testar o pipeline, você precisará de um arquivo CSV de exemplo. Crie um arquivo chamado `sales_data.csv` com o seguinte conteúdo:

```csv
id,product,quantity,price,date
1,Laptop,1,1200.00,2024-01-01
2,Mouse,2,25.00,2024-01-01
3,Keyboard,1,75.00,2024-01-02
4,Monitor,1,300.00,2024-01-02
5,Laptop,1,1250.00,2024-01-03
6,Mouse,3,20.00,2024-01-03
7,Webcam,1,50.00,2024-01-04
8,Headphones,1,100.00,2024-01-04
9,Keyboard,2,70.00,2024-01-05
10,Monitor,1,320.00,2024-01-05
```

Faça o upload deste arquivo para o bucket `raw-sales-data-neto`:

1.  No console do S3, clique no bucket `raw-sales-data-neto`.
2.  Clique em "Fazer upload".
3.  Arraste e solte o arquivo `sales_data.csv` ou clique em "Adicionar arquivos" e selecione-o.
4.  Clique em "Fazer upload".

### 3. Criar Glue Crawler

O AWS Glue Crawler irá escanear o bucket S3, inferir o esquema dos dados e criar uma tabela no AWS Glue Data Catalog.

1.  Acesse o console da AWS e procure por "Glue".
2.  No painel de navegação esquerdo, em "Data Catalog", clique em "Crawlers".
3.  Clique em "Criar crawler".
4.  **Nome do crawler**: `sales_data_crawler`.
5.  Clique em "Próximo".
6.  **Tipo de fonte de dados**: "Data stores".
7.  **Conexão**: "S3".
8.  **Caminho de inclusão**: Navegue até o bucket `raw-sales-data-neto` e selecione-o. O caminho deve ser `s3://raw-sales-data-neto/`.
9.  Clique em "Próximo".
10. **Adicionar outro armazenamento de dados**: "Não". Clique em "Próximo".
11. **Função do IAM**: Clique em "Criar nova função do IAM". Uma nova janela será aberta. O nome da função será preenchido automaticamente (ex: `AWSGlueServiceRole-sales_data_crawler`). Clique em "Criar função". Feche a janela e selecione a função recém-criada na lista.
12. Clique em "Próximo".
13. **Frequência**: "Sob demanda" (para este projeto, executaremos manualmente).
14. Clique em "Próximo".
15. **Configurar saída do crawler**: Em "Banco de dados", clique em "Adicionar banco de dados".
    *   **Nome do banco de dados**: `sales_database`.
    *   Clique em "Criar".
    *   Selecione `sales_database` na lista.
16. Clique em "Próximo".
17. Revise as configurações e clique em "Criar crawler".
18. Selecione o crawler `sales_data_crawler` e clique em "Executar crawler". Aguarde até que o status mude para "Pronto" e o crawler tenha concluído a execução.
19. Após a execução, no painel de navegação esquerdo, em "Data Catalog", clique em "Tabelas". Você deverá ver uma nova tabela (provavelmente com o nome `sales_data`) criada no banco de dados `sales_database`.

### 4. Criar Glue Job (ETL) com PySpark

Este job lerá os dados da tabela catalogada, fará algumas transformações e salvará os dados processados em um novo bucket S3 no formato Parquet.

1.  Crie um novo bucket S3 para os dados processados. Repita o passo 1, mas nomeie o bucket como `processed-sales-data-neto`.
2.  No console do Glue, no painel de navegação esquerdo, em "ETL", clique em "Jobs".
3.  Clique em "Criar job".
4.  **Nome do job**: `sales_etl_job`.
5.  **Função do IAM**: Selecione a mesma função do IAM que você criou para o crawler (`AWSGlueServiceRole-sales_data_crawler`).
6.  **Tipo de job**: "Spark".
7.  **Versão do Glue**: Selecione a versão mais recente (ex: Glue 4.0 ou Glue 3.0).
8.  **Linguagem**: "Python".
9.  **Tipo de script**: "Um novo script a ser criado por você".
10. **Caminho do script S3**: Especifique um caminho no seu bucket de dados processados, por exemplo, `s3://processed-sales-data-neto/scripts/sales_etl_job.py`.
11. Mantenha os parâmetros de segurança, script, monitoramento e agendamento padrão.
12. Clique em "Próximo".
13. Mantenha as propriedades do job padrão.
14. Clique em "Salvar job e editar script".

Agora, você será redirecionado para o editor de script do Glue. Substitua o conteúdo existente pelo seguinte código PySpark:

```python
import sys
from awsglue.transforms import *
from awsglue.utils import *
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

# Inicializar o contexto do Glue
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(sys.argv[1])

# Ler os dados do Data Catalog
sales_data = glueContext.create_dynamic_frame.from_catalog(database="sales_database",
table_name="sales_data")

# Converter para DataFrame do Spark para transformações
sales_df = sales_data.toDF()

# Exemplo de transformação: Limpar campos nulos na coluna 'price' e converter para float
sales_df = sales_df.filter(sales_df.price.isNotNull())
sales_df = sales_df.withColumn("price", sales_df["price"].cast("float"))

# Exemplo de transformação: Adicionar uma coluna 'total_value'
sales_df = sales_df.withColumn("total_value", sales_df["quantity"] * sales_df["price"])

# Converter de volta para DynamicFrame para escrita no S3
output_dynamic_frame = DynamicFrame.fromDF(sales_df, glueContext, "output_dynamic_frame")

# Salvar os dados processados no S3 em formato Parquet
output_path = "s3://processed-sales-data-neto/processed_sales/"
glueContext.write_dynamic_frame.from_options(
frame=output_dynamic_frame,
connection_type="s3",
connection_options={"path": output_path},
format="parquet",
transformation_ctx="datasink"
)

job.commit()
```

1.  Clique em "Salvar" no editor de script.
2.  Clique em "Executar" para iniciar o job. Você pode monitorar o status do job na aba "Execuções" do job. Aguarde até que o job seja concluído com sucesso.
3.  Após a conclusão, verifique o bucket `processed-sales-data-neto`. Você deverá ver uma nova pasta `processed_sales/` contendo arquivos Parquet.

### 5. Criar Cluster Redshift

Agora, vamos provisionar um cluster Amazon Redshift para armazenar os dados processados.

1.  Acesse o console da AWS e procure por "Redshift".
2.  No painel de navegação esquerdo, clique em "Clusters".
3.  Clique em "Criar cluster".
4.  **Identificador do cluster**: `sales-data-warehouse`.
5.  **Tipo de nó**: Selecione um tipo de nó pequeno para fins de teste (ex: `dc2.large` ou `ra3.xlplus`).
6.  **Número de nós**: `1` (para começar).
7.  **Credenciais do banco de dados**: Defina um nome de usuário (ex: `awsuser`) e uma senha forte.
8.  **Configurações de rede**: Mantenha as configurações padrão ou selecione uma VPC e sub-rede de sua preferência. Certifique-se de que o grupo de segurança permita o tráfego de entrada na porta do Redshift (padrão: `5439`) do seu IP ou da rede do Glue.
9.  Mantenha as outras configurações padrão e clique em "Criar cluster".
10. Aguarde até que o status do cluster mude para "Disponível". Isso pode levar alguns minutos.

### 6. Criar Schema e Tabela no Redshift

Uma vez que o cluster Redshift esteja disponível, você pode se conectar a ele e criar o esquema e a tabela para os dados processados. Você pode usar o Editor de Consultas v2 do Redshift no console da AWS.

1.  No console do Redshift, selecione seu cluster `sales-data-warehouse`.
2.  Na aba "Editor de Consultas v2", clique em "Conectar ao banco de dados".
3.  Insira as credenciais que você definiu ao criar o cluster.
4.  Execute as seguintes instruções SQL para criar o esquema e a tabela:

```sql
CREATE SCHEMA IF NOT EXISTS sales_schema;
CREATE TABLE IF NOT EXISTS sales_schema.processed_sales (
    id INT,
    product VARCHAR(256),
    quantity INT,
    price FLOAT,
    date DATE,
    total_value FLOAT
);
```

### 7. Criar Glue Job de Load (S3 para Redshift)

Este job será responsável por carregar os dados do formato Parquet no S3 para a tabela recém-criada no Redshift.

1.  No console do Glue, em "ETL", clique em "Jobs".
2.  Clique em "Criar job".
3.  **Nome do job**: `sales_load_to_redshift_job`.
4.  **Função do IAM**: Selecione a mesma função do IAM. Certifique-se de que esta função tenha permissões para acessar o Redshift (ex: `AmazonRedshiftFullAccess` ou uma política mais restritiva).
5.  **Tipo de job**: "Spark".
6.  **Versão do Glue**: Selecione a versão mais recente.
7.  **Linguagem**: "Python".
8.  **Tipo de script**: "Um novo script a ser criado por você".
9.  **Caminho do script S3**: Especifique um caminho, por exemplo, `s3://processed-sales-data-neto/scripts/sales_load_to_redshift_job.py`.
10. Clique em "Salvar job e editar script".

Substitua o conteúdo existente pelo seguinte código PySpark:

```python
import sys
from awsglue.transforms import *
from awsglue.utils import *
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

# Inicializar o contexto do Glue
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(sys.argv[1])

# Caminho para os dados Parquet processados no S3
input_path = "s3://processed-sales-data-neto/processed_sales/"

# Ler os dados Parquet do S3
processed_sales_df = spark.read.parquet(input_path)

# Configurações de conexão com o Redshift
redshift_url = "jdbc:redshift://<SEU_ENDPOINT_REDSHIFT>:5439/dev"
redshift_user = "<SEU_USUARIO_REDSHIFT>"
redshift_password = "<SUA_SENHA_REDSHIFT>"
redshift_table = "sales_schema.processed_sales"

# Substitua <SEU_ENDPOINT_REDSHIFT>, <SEU_USUARIO_REDSHIFT> e <SUA_SENHA_REDSHIFT>
# pelo endpoint do seu cluster Redshift (disponível no console do Redshift, na aba 'Propriedades'),
# seu nome de usuário e sua senha.

# Escrever os dados no Redshift
processed_sales_df.write \
.format("jdbc") \
.option("url", redshift_url) \
.option("dbtable", redshift_table) \
.option("user", redshift_user) \
.option("password", redshift_password) \
.option("aws_iam_role", "arn:aws:iam::<SUA_CONTA_AWS_ID>:role/AWSGlueServiceRole-sales_data_crawler") \
.option("tempdir", "s3://processed-sales-data-neto/temp_redshift/") \
.mode("append") \
.save()

job.commit()
```

**Atenção**: Substitua os placeholders `<SEU_ENDPOINT_REDSHIFT>`, `<SEU_USUARIO_REDSHIFT>`, `<SUA_SENHA_REDSHIFT>` e `<SUA_CONTA_AWS_ID>` com as informações reais do seu ambiente AWS. O `aws_iam_role` deve ser o ARN completo da função IAM que o Glue está usando, que deve ter permissões para acessar o S3 e o Redshift.

1.  Clique em "Salvar" no editor de script.
2.  Clique em "Executar" para iniciar o job. Monitore o status até que seja concluído com sucesso.

### 8. Consulta de Validação no Redshift

Após a conclusão do job de carga, você pode validar se os dados foram carregados corretamente no Redshift.

1.  No Editor de Consultas v2 do Redshift, execute a seguinte consulta:

```sql
SELECT * FROM sales_schema.processed_sales;
```

Você deverá ver os dados do seu arquivo CSV original, com as novas colunas e transformações aplicadas.

Para uma análise mais aprofundada, você pode executar a seguinte consulta:

```sql
SELECT
    product,
    SUM(total_value) AS total_sales
FROM
    sales_schema.processed_sales
GROUP BY
    product
ORDER BY
    total_sales DESC;
```

Esta consulta agregará o valor total de vendas por produto, demonstrando a capacidade analítica do Redshift.

## Estrutura do Projeto

**Ingestão**

Produtor gera CSV → Lambda → S3 (raw).

**Descoberta e Catalogação**

Glue Crawler varre o S3 (raw).

Glue Data Catalog registra metadados.

**Transformação**

Glue ETL Job converte CSV para Parquet, cria coluna total_value, remove nulos.

Dados processados são armazenados em S3 (processed).

**Consumo dos Dados**

Athena → consultas ad hoc diretamente no S3 (processed).

Redshift Spectrum → acesso híbrido (S3 + Redshift).

Redshift → carga final via Glue Job para análises estruturadas.

## Próximos Passos e Melhorias

*   **Automação**: Configure triggers no AWS Glue para automatizar a execução dos jobs ETL e de carga em intervalos regulares ou em resposta a eventos (ex: chegada de novos arquivos no S3).
*   **Monitoramento e Alertas**: Implemente monitoramento com AWS CloudWatch para acompanhar a execução dos jobs e configurar alertas para falhas ou anomalias.
*   **Otimização de Custos**: Explore opções de otimização de custos para o Redshift (ex: nós reservados) e o Glue (ex: ajuste do número de DPUs).
*   **Segurança**: Refine as políticas de IAM para conceder apenas as permissões mínimas necessárias (princípio do menor privilégio).
*   **Visualização de Dados**: Conecte o Redshift a ferramentas de Business Intelligence (BI) como Amazon QuickSight, Tableau ou Power BI para criar dashboards e relatórios interativos.
*   **Dados Reais**: Substitua os dados de exemplo por dados reais e de maior volume para testar a escalabilidade do pipeline.
