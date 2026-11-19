"""Local Spark DataFrame transformation over structured chunk records.

This is a deliberately small pipeline: its purpose is to show a real Spark
DataFrame transformation (filter, select, derived columns, distinct counts)
on our extracted records. The data is tiny and runs with ``local[2]``; this
is *not* a distributed production cluster.
"""

from dataclasses import dataclass
from typing import Any, Sequence

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from ..utils.spark_env import prepare_spark_environment

# Explicit schema: avoids type inference surprises when records are empty.
CHUNK_SCHEMA = StructType(
    [
        StructField("document_id", StringType(), nullable=False),
        StructField("filename", StringType(), nullable=False),
        StructField("page_number", IntegerType(), nullable=False),
        StructField("chunk_id", StringType(), nullable=False),
        StructField("chunk_index", IntegerType(), nullable=False),
        StructField("text", StringType(), nullable=True),
    ]
)


@dataclass
class ProcessingResult:
    """Output of the Spark stage, collected back to the driver for embedding."""

    records: list[dict[str, Any]]
    document_count: int
    page_count: int
    chunk_count: int


def build_chunk_dataframe(
    spark: SparkSession, chunks: Sequence[dict[str, Any]]
) -> DataFrame:
    """Create a Spark DataFrame from chunk records using the explicit schema."""
    rows = [
        (
            str(chunk["document_id"]),
            str(chunk["filename"]),
            int(chunk["page_number"]),
            str(chunk["chunk_id"]),
            int(chunk.get("chunk_index", 0)),
            str(chunk["text"]),
        )
        for chunk in chunks
    ]
    return spark.createDataFrame(rows, schema=CHUNK_SCHEMA)


def process_chunks(
    chunks: Sequence[dict[str, Any]],
    *,
    app_name: str = "UniversityKnowledgeAssistant",
    master: str = "local[2]",
) -> ProcessingResult:
    """Filter, transform and count chunk records with a local Spark session.

    The session is created and stopped here, so this function owns the Spark
    lifecycle. Returned records are plain dictionaries ready for embedding.
    """
    prepare_spark_environment()

    spark = SparkSession.builder.appName(app_name).master(master).getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    try:
        raw_df = build_chunk_dataframe(spark, chunks)

        # Real transformations: drop empty text, keep source columns and add
        # a simple derived column used later for logging/quality checks.
        non_empty_df = raw_df.filter(
            F.col("text").isNotNull() & (F.length(F.trim(F.col("text"))) > 0)
        )
        embedding_ready_df = non_empty_df.select(
            "document_id",
            "filename",
            "page_number",
            "chunk_id",
            "chunk_index",
            "text",
        ).withColumn("text_length", F.length(F.col("text")))

        # Actions: these actually trigger computation on the DataFrame.
        chunk_count = embedding_ready_df.count()
        document_count = embedding_ready_df.select("document_id").distinct().count()
        page_count = (
            embedding_ready_df.select("document_id", "page_number").distinct().count()
        )

        ordered_df = embedding_ready_df.orderBy(
            "document_id", "page_number", "chunk_index"
        )
        records = [row.asDict() for row in ordered_df.collect()]
    finally:
        spark.stop()

    return ProcessingResult(
        records=records,
        document_count=document_count,
        page_count=page_count,
        chunk_count=chunk_count,
    )
