import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

# ---------------------------------------------
# 1️ Inicializar contexto do Glue
# ---------------------------------------------
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Obter argumentos passados para o job (nome do job)
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# ---------------------------------------------
# 2️ Caminho para os dados processados no S3
# ---------------------------------------------
input_path = "s3://processed-sales-data-neto/processed_sales/"

# Ler os dados Parquet do S3
processed_sales_df = spark.read.parquet(input_path)

# ---------------------------------------------
# 3️ Configurações de conexão com o Redshift
# ---------------------------------------------
redshift_url = "jdbc:redshift://<SEU_ENDPOINT_REDSHIFT>:5439/dev"
redshift_user = "<SEU_USUARIO_REDSHIFT>"
redshift_password = "<SUA_SENHA_REDSHIFT>"
redshift_table = "sales_schema.processed_sales"

# Role do Glue com permissões de leitura no S3 e escrita no Redshift
aws_iam_role = "arn:aws:iam::<SUA_CONTA_AWS_ID>:role/AWSGlueServiceRole-sales_data_crawler"

# Diretório temporário no S3 para staging
temp_dir = "s3://processed-sales-data-neto/temp_redshift/"

# ---------------------------------------------
# 4️ Escrever dados no Redshift
# ---------------------------------------------
processed_sales_df.write \
    .format("jdbc") \
    .option("url", redshift_url) \
    .option("dbtable", redshift_table) \
    .option("user", redshift_user) \
    .option("password", redshift_password) \
    .option("aws_iam_role", aws_iam_role) \
    .option("tempdir", temp_dir) \
    .mode("append") \   # Use "overwrite" se quiser substituir a tabela
    .save()

# ---------------------------------------------
# 5️ Finalizar o job
# ---------------------------------------------
job.commit()
