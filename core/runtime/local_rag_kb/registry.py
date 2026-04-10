from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .models import ChunkRecord, DocumentRow


class Registry:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(db_path))
        self.connection.row_factory = sqlite3.Row
        self._initialize()

    def close(self) -> None:
        self.connection.close()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                kb_name TEXT NOT NULL,
                source_rel_path TEXT NOT NULL,
                source_type TEXT NOT NULL,
                parser TEXT NOT NULL,
                title TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                chunk_count INTEGER NOT NULL,
                cache_path TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_documents_kb_path
            ON documents (kb_name, source_rel_path, status);

            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                char_start INTEGER NOT NULL,
                char_end INTEGER NOT NULL,
                FOREIGN KEY(doc_id) REFERENCES documents(doc_id)
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_doc
            ON chunks (doc_id, chunk_index);
            """
        )
        self.connection.commit()

    def get_active_document(self, kb_name: str, source_rel_path: str) -> Optional[DocumentRow]:
        row = self.connection.execute(
            """
            SELECT * FROM documents
            WHERE kb_name = ? AND source_rel_path = ? AND status = 'active'
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (kb_name, source_rel_path),
        ).fetchone()
        return self._row_to_document(row) if row else None

    def list_active_documents(self, kb_name: str) -> List[DocumentRow]:
        rows = self.connection.execute(
            """
            SELECT * FROM documents
            WHERE kb_name = ? AND status = 'active'
            ORDER BY source_rel_path ASC
            """,
            (kb_name,),
        ).fetchall()
        return [self._row_to_document(row) for row in rows]

    def insert_document(self, document: DocumentRow, chunks: Iterable[ChunkRecord]) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO documents (
                doc_id, kb_name, source_rel_path, source_type, parser, title,
                content_hash, status, chunk_count, cache_path, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document.doc_id,
                document.kb_name,
                document.source_rel_path,
                document.source_type,
                document.parser,
                document.title,
                document.content_hash,
                document.status,
                document.chunk_count,
                document.cache_path,
                document.updated_at,
            ),
        )
        self.connection.executemany(
            """
            INSERT OR REPLACE INTO chunks (chunk_id, doc_id, chunk_index, char_start, char_end)
            VALUES (?, ?, ?, ?, ?)
            """,
            [(chunk.id, chunk.doc_id, chunk.chunk_index, chunk.char_start, chunk.char_end) for chunk in chunks],
        )
        self.connection.commit()

    def mark_replaced(self, doc_id: str) -> None:
        self.connection.execute(
            "UPDATE documents SET status = 'replaced' WHERE doc_id = ?",
            (doc_id,),
        )
        self.connection.commit()

    def delete_chunk_rows(self, doc_id: str) -> None:
        self.connection.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        self.connection.commit()

    def get_chunk_ids(self, doc_id: str) -> List[str]:
        rows = self.connection.execute(
            "SELECT chunk_id FROM chunks WHERE doc_id = ? ORDER BY chunk_index ASC",
            (doc_id,),
        ).fetchall()
        return [row["chunk_id"] for row in rows]

    def delete_all(self) -> None:
        self.connection.execute("DELETE FROM chunks")
        self.connection.execute("DELETE FROM documents")
        self.connection.commit()

    def stats(self, kb_name: str) -> Dict[str, int]:
        documents = self.connection.execute(
            "SELECT COUNT(*) AS count FROM documents WHERE kb_name = ? AND status = 'active'",
            (kb_name,),
        ).fetchone()["count"]
        chunks = self.connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM chunks
            WHERE doc_id IN (
                SELECT doc_id FROM documents WHERE kb_name = ? AND status = 'active'
            )
            """,
            (kb_name,),
        ).fetchone()["count"]
        return {"documents": int(documents), "chunks": int(chunks)}

    @staticmethod
    def _row_to_document(row: sqlite3.Row) -> DocumentRow:
        return DocumentRow(
            doc_id=row["doc_id"],
            kb_name=row["kb_name"],
            source_rel_path=row["source_rel_path"],
            source_type=row["source_type"],
            parser=row["parser"],
            title=row["title"],
            content_hash=row["content_hash"],
            status=row["status"],
            chunk_count=int(row["chunk_count"]),
            cache_path=row["cache_path"],
            updated_at=row["updated_at"],
        )
