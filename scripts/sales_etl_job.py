import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

# ---------------------------------------------
# 1️ Inicializar contexto e obter parâmetros
# ---------------------------------------------
try:
    # Obter argumentos do job
    args = getResolvedOptions(sys.argv, ['JOB_NAME'])
    
    # Inicializar contexto do Glue
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'])
    
    print("Glue context initialized successfully")
    
except Exception as e:
    print(f"Error initializing Glue context: {str(e)}")
    raise

# ---------------------------------------------
# 2️ Ler dados do Data Catalog
# ---------------------------------------------
try:
    print("Reading data from AWS Glue Data Catalog...")
    sales_data = glueContext.create_dynamic_frame.from_catalog(
        database="sales_database",
        table_name="sales_data"
    )
    
    print(f"Successfully read data from catalog. Count: {sales_data.count()}")
    
except Exception as e:
    print(f"Error reading from Data Catalog: {str(e)}")
    raise

# ---------------------------------------------
# 3️ Transformações dos dados
# ---------------------------------------------
try:
    # Converter para DataFrame do Spark para transformações
    sales_df = sales_data.toDF()
    
    # Mostrar schema original
    print("Original schema:")
    sales_df.printSchema()
    
    # Transformação 1: Filtrar registros com preço nulo
    print("Filtering records with null prices...")
    initial_count = sales_df.count()
    sales_df = sales_df.filter(sales_df.price.isNotNull())
    filtered_count = sales_df.count()
    print(f"Filtered out {initial_count - filtered_count} records with null prices")
    
    # Transformação 2: Converter coluna price para float
    print("Converting price column to float...")
    sales_df = sales_df.withColumn("price", sales_df["price"].cast("float"))
    
    # Transformação 3: Adicionar coluna total_value
    print("Calculating total_value column...")
    sales_df = sales_df.withColumn("total_value", sales_df["quantity"] * sales_df["price"])
    
    # Mostrar schema após transformações
    print("Schema after transformations:")
    sales_df.printSchema()
    
    # Mostrar estatísticas básicas
    print(f"Total records after processing: {sales_df.count()}")
    
except Exception as e:
    print(f"Error during data transformations: {str(e)}")
    raise

# ---------------------------------------------
# 4️ Salvar dados processados no S3
# ---------------------------------------------
try:
    # Converter de volta para DynamicFrame
    output_dynamic_frame = DynamicFrame.fromDF(sales_df, glueContext, "output_dynamic_frame")
    
    # Salvar os dados processados no S3 em formato Parquet
    output_path = "s3://processed-sales-data-neto/processed_sales/"
    print(f"Writing processed data to: {output_path}")
    
    glueContext.write_dynamic_frame.from_options(
        frame=output_dynamic_frame,
        connection_type="s3",
        connection_options={"path": output_path},
        format="parquet"
    )
    
    print("Data successfully written to S3")
    
except Exception as e:
    print(f"Error writing to S3: {str(e)}")
    raise

# ---------------------------------------------
# 5️ Finalizar o job
# ---------------------------------------------
try:
    job.commit()
    print("Job completed successfully!")
    
except Exception as e:
    print(f"Error committing job: {str(e)}")
    raise
