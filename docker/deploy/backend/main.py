import logging
import os
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from retriever import search

load_dotenv()

logger = logging.getLogger("uvicorn.error")


def connect_db():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                text TEXT NOT NULL
            )
        """)
    yield


app = FastAPI(title="Docker Practice", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class NoteInput(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class SearchInput(BaseModel):
    model_config = {"str_strip_whitespace": True}
    query: str = Field(min_length=1, max_length=1000)


def save_note(text: str):
    with connect_db() as conn:
        return conn.execute(
            "INSERT INTO notes (text) VALUES (%s) RETURNING id, text",
            (text,),
        ).fetchone()


@app.get("/health")
def health():
    with connect_db() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.post("/notes", status_code=201)
def create_note(body: NoteInput):
    return save_note(body.text)


@app.get("/notes")
def list_notes():
    with connect_db() as conn:
        return conn.execute(
            "SELECT id, text FROM notes ORDER BY id DESC LIMIT 20"
        ).fetchall()


@app.post("/search")
def search_documents(body: SearchInput):
    try:
        documents = search(body.query)
    except LookupError:
        raise HTTPException(503, "먼저 ingest.py로 검색할 텍스트를 등록해 주세요.") from None
    except Exception:
        logger.exception("벡터 검색 실패")
        raise HTTPException(502, "검색에 실패했습니다. 백엔드 로그를 확인해 주세요.") from None
    return {
        "documents": [
            {"id": document.id, "text": document.page_content}
            for document in documents
        ]
    }
