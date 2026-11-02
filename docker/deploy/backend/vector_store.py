import asyncio
import os
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import Column, PGEngine, PGVectorStore

TABLE_NAME = "practice_texts_embedding2"
VECTOR_SIZE = 768


@contextmanager
def open_vector_store(*, initialize=False):
    load_dotenv()
    connection_string = os.environ["DATABASE_URL"].replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
    engine = PGEngine.from_connection_string(url=connection_string)
    embeddings = None
    try:
        with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
            table = conn.execute(
                "SELECT to_regclass(%s)", (f"public.{TABLE_NAME}",)
            ).fetchone()[0]
        if table is None:
            if not initialize:
                raise LookupError("먼저 ingest.py로 검색할 텍스트를 등록해 주세요.")
            engine.init_vectorstore_table(
                table_name=TABLE_NAME,
                vector_size=VECTOR_SIZE,
                id_column=Column("id", "TEXT"),
            )

        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-2",
            api_key=os.environ["GEMINI_API_KEY"],
            output_dimensionality=VECTOR_SIZE,
            vertexai=False,
        )
        yield PGVectorStore.create_sync(
            engine=engine,
            table_name=TABLE_NAME,
            id_column="id",
            embedding_service=embeddings,
        )
    finally:
        if embeddings is not None:
            embeddings.client.close()
        asyncio.run(engine.close())
