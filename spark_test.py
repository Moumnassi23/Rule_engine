"""Test PySpark : créer un DataFrame via un fichier (contourne le bug cloudpickle)."""
import os

os.environ["JAVA_TOOL_OPTIONS"] = (
    "--add-opens=java.base/java.lang=ALL-UNNAMED "
    "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED "
    "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED "
    "--add-opens=java.base/java.io=ALL-UNNAMED "
    "--add-opens=java.base/java.net=ALL-UNNAMED "
    "--add-opens=java.base/java.nio=ALL-UNNAMED "
    "--add-opens=java.base/java.util=ALL-UNNAMED "
    "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED "
    "--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED "
    "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED "
    "--add-opens=java.base/sun.nio.cs=ALL-UNNAMED "
    "--add-opens=java.base/sun.security.action=ALL-UNNAMED "
    "--add-opens=java.base/sun.util.calendar=ALL-UNNAMED"
)

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


spark = (
    SparkSession.builder
    .appName("rule-engine-dev")
    .master("local[*]")
    .config("spark.driver.memory", "2g")
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

print(f"\n=== Spark démarré ===")
print(f"Version : {spark.version}\n")

# Créer un CSV temporaire (contourne le bug cloudpickle/Python 3.11)
csv_path = "test_data.csv"
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("compte_id,etat,solde\n")
    f.write("C1,VALIDE,1000\n")
    f.write("C2,CLOTURE,500\n")
    f.write("C3,VALIDE,2000\n")

# Lire le CSV avec Spark (pas de sérialisation de RDD Python)
df = spark.read.csv(csv_path, header=True, inferSchema=True)

print("=== DataFrame de test ===")
df.show()

print("=== Filtre des comptes valides ===")
df.filter(F.col("etat") == "VALIDE").show()

print("=== Somme des soldes valides ===")
df.filter(F.col("etat") == "VALIDE").select(F.sum("solde").alias("total")).show()

spark.stop()
os.remove(csv_path)
print("=== Spark arrêté ===")