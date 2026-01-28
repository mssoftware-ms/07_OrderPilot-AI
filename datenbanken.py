#!/usr/bin/env python3
"""
RAG Stack Smoke Test (Self-hosted):
- Postgres: connect, create schema, insert docs, run FTS query
- Qdrant: connect, create collection, upsert vectors, run vector search

No OpenAI required. This only proves your DB/infra can support RAG.

Env:
  PG_DSN="postgresql://user:pass@localhost:5432/dbname"
  QDRANT_URL="http://localhost:6333"   # or http://localhost:6336
  QDRANT_COLLECTION="kb_chunks_test"
"""

from __future__ import annotations

import os
import sys
import time
import json
import hashlib
from dataclasses import dataclass
from typing import Any
import requests


# -------------------------
# Helpers
# -------------------------

@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def dummy_embedding(text: str, dim: int = 128) -> list[float]:
    """Deterministic pseudo-embedding for infrastructure tests (NOT for production relevance)."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    out: list[float] = []
    seed = h
    while len(out) < dim:
        seed = hashlib.sha256(seed).digest()
        for b in seed:
            out.append(((b / 255.0) * 2.0) - 1.0)
            if len(out) >= dim:
                break
    return out


def report(checks: list[Check]) -> int:
    width = max(len(c.name) for c in checks) if checks else 10
    passed = sum(1 for c in checks if c.ok)
    total = len(checks)
    print("\n=== RAG Stack Smoke Test ===")
    for c in checks:
        print(f"{'OK ' if c.ok else 'FAIL'} | {c.name.ljust(width)} | {c.detail}")
    print(f"\nChecks: {passed}/{total}")
    return 0 if passed == total else 1


# -------------------------
# Postgres
# -------------------------

def pg_connect(dsn: str):
    # Prefer psycopg3, fallback psycopg2
    try:
        import psycopg  # type: ignore
        return psycopg.connect(dsn), "psycopg3"
    except Exception:
        import psycopg2  # type: ignore
        return psycopg2.connect(dsn), "psycopg2"


def postgres_checks(checks: list[Check], dsn: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    try:
        t0 = time.time()
        conn, driver = pg_connect(dsn)
        checks.append(Check("Postgres Connect", True, f"{driver} in {int((time.time()-t0)*1000)} ms"))
    except Exception as e:
        checks.append(Check("Postgres Connect", False, str(e)))
        return meta

    try:
        cur = conn.cursor()
        cur.execute("select version()")
        ver = cur.fetchone()[0]
        checks.append(Check("Postgres Version", True, ver))
    except Exception as e:
        checks.append(Check("Postgres Version", False, str(e)))

    # Create schema
    try:
        cur.execute("""
            create table if not exists kb_chunks(
                id bigserial primary key,
                chunk text not null,
                meta jsonb not null,
                created_at timestamptz not null default now()
            )
        """)
        cur.execute("""
            create table if not exists runtime_vars(
                k text primary key,
                value_json jsonb not null,
                updated_at timestamptz not null default now()
            )
        """)
        cur.execute("create index if not exists kb_chunks_fts_gin on kb_chunks using gin (to_tsvector('simple', chunk))")
        conn.commit()
        checks.append(Check("Postgres Schema", True, "Tables + GIN(FTS) Index OK"))
    except Exception as e:
        conn.rollback()
        checks.append(Check("Postgres Schema", False, str(e)))

    # Insert sample docs
    docs = [
        ("CEL/DSL: Variablen wie account.balance, market.regime, position.side. Logik: &&, ||, has().", {"type": "dsl"}),
        ("Intern: market.regime liefert TREND|RANGE|VOLATILE. position.side liefert LONG|SHORT|FLAT.", {"type": "vars"}),
        ("RAG: Chunks speichern, dann via FTS oder Vector Search relevante Chunks zur Frage ziehen.", {"type": "rag"}),
    ]
    try:
        cur.execute("delete from kb_chunks where meta->>'type' in ('dsl','vars','rag')")
        for chunk, meta_obj in docs:
            cur.execute("insert into kb_chunks(chunk, meta) values (%s, %s) returning id", (chunk, json.dumps(meta_obj)))
            _id = cur.fetchone()[0]
            meta.setdefault("inserted_ids", []).append(_id)
        conn.commit()
        checks.append(Check("Postgres Insert", True, f"{len(docs)} docs inserted"))
    except Exception as e:
        conn.rollback()
        checks.append(Check("Postgres Insert", False, str(e)))

    # FTS query
    try:
        q = "market.regime"
        t0 = time.time()
        cur.execute("""
            select id, left(chunk, 120)
            from kb_chunks
            where to_tsvector('simple', chunk) @@ plainto_tsquery('simple', %s)
            limit 5
        """, (q,))
        rows = cur.fetchall()
        ms = int((time.time()-t0)*1000)
        checks.append(Check("Postgres FTS Query", True, f"{len(rows)} hits in {ms} ms (q='{q}')"))
        meta["fts_hits"] = rows
    except Exception as e:
        checks.append(Check("Postgres FTS Query", False, str(e)))

    try:
        conn.close()
        checks.append(Check("Postgres Close", True, "OK"))
    except Exception as e:
        checks.append(Check("Postgres Close", False, str(e)))

    return meta


# -------------------------
# Qdrant
# -------------------------

def qdrant_checks(checks: list[Check], base_url: str, collection: str, dim: int = 128) -> None:
    base_url = base_url.rstrip("/")

    # Health
    try:
        r = requests.get(f"{base_url}/healthz", timeout=3)
        ok = (r.status_code == 200)
        checks.append(Check("Qdrant Health", ok, f"HTTP {r.status_code}"))
        if not ok:
            return
    except Exception as e:
        checks.append(Check("Qdrant Health", False, str(e)))
        return

    # Ensure collection
    try:
        r = requests.get(f"{base_url}/collections/{collection}", timeout=5)
        if r.status_code == 200:
            checks.append(Check("Qdrant Collection", True, f"exists: {collection}"))
        else:
            payload = {
                "vectors": {"size": dim, "distance": "Cosine"}
            }
            rc = requests.put(f"{base_url}/collections/{collection}", json=payload, timeout=10)
            checks.append(Check("Qdrant Collection", rc.status_code in (200, 201), f"create HTTP {rc.status_code}"))
    except Exception as e:
        checks.append(Check("Qdrant Collection", False, str(e)))
        return

    # Upsert points
    try:
        points = []
        for pid, text in enumerate([
            "CEL Variable account.balance beschreibt den Kontostand.",
            "market.regime liefert TREND/RANGE/VOLATILE und steuert StrategySets.",
            "RAG braucht Retrieval: Vector Search + FTS + Kontextinjektion.",
        ], start=1):
            points.append({
                "id": pid,
                "vector": dummy_embedding(text, dim),
                "payload": {"text": text, "kind": "demo"}
            })

        up = {"points": points}
        r = requests.put(f"{base_url}/collections/{collection}/points?wait=true", json=up, timeout=20)
        checks.append(Check("Qdrant Upsert", r.status_code == 200, f"HTTP {r.status_code}"))
    except Exception as e:
        checks.append(Check("Qdrant Upsert", False, str(e)))
        return

    # Search
    try:
        query = "Wie nutze ich market.regime in der Strategie?"
        qv = dummy_embedding(query, dim)
        payload = {"vector": qv, "limit": 3, "with_payload": True}
        t0 = time.time()
        r = requests.post(f"{base_url}/collections/{collection}/points/search", json=payload, timeout=10)
        ms = int((time.time()-t0)*1000)
        if r.status_code != 200:
            checks.append(Check("Qdrant Search", False, f"HTTP {r.status_code}: {r.text[:200]}"))
            return
        res = r.json().get("result", [])
        checks.append(Check("Qdrant Search", True, f"{len(res)} hits in {ms} ms"))
    except Exception as e:
        checks.append(Check("Qdrant Search", False, str(e)))


def main() -> int:
    checks: list[Check] = []

    pg_dsn = os.getenv("PG_DSN", "").strip()
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333").strip()
    collection = os.getenv("QDRANT_COLLECTION", "kb_chunks_test").strip()

    if not pg_dsn:
        checks.append(Check("Config PG_DSN", False, "PG_DSN env fehlt (postgresql://user:pass@host:port/db)"))
        return report(checks)

    postgres_checks(checks, pg_dsn)
    qdrant_checks(checks, qdrant_url, collection, dim=128)

    return report(checks)


if __name__ == "__main__":
    raise SystemExit(main())
