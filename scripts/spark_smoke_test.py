"""Original Day 1 Spark smoke test, now reusing the shared environment helper."""

import sys
from pathlib import Path

# Allow running this script directly from the repository root.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from university_knowledge_assistant.utils import prepare_spark_environment


def main():
    prepare_spark_environment()

    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col

    # 1. Start a local Spark application
    spark = (
        SparkSession.builder
        .appName("UniversityKnowledgeAssistant")
        .master("local[2]")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")

    try:
        # 2. Create sample university document records
        documents = [
            ("deep_learning.pdf", "Deep Learning", 45),
            ("big_data.pdf", "Big Data", 32),
            ("statistics.pdf", "Statistics", 28),
            ("nlp.pdf", "Natural Language Processing", 60),
        ]

        columns = ["filename", "subject", "pages"]

        df = spark.createDataFrame(documents, columns)

        print("\n--- ORIGINAL DOCUMENTS ---")
        df.show()

        # 3. Transformation: filter documents
        large_documents = df.filter(col("pages") > 30)

        print("\n--- DOCUMENTS WITH MORE THAN 30 PAGES ---")
        large_documents.show()

        # 4. Action: count the filtered documents
        total = large_documents.count()

        print(f"\nNumber of documents with more than 30 pages: {total}")

        # 5. Calculate total pages
        print("\n--- TOTAL NUMBER OF PAGES ---")
        df.selectExpr("sum(pages) AS total_pages").show()

    finally:
        # 6. Stop Spark
        spark.stop()


if __name__ == "__main__":
    main()
