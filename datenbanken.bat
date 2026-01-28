@echo off
echo === FULL CLEANUP ===
docker stop /marketregime_db marketregime_qdrant qdrant qdrant-local orderpilot-db 2^>nul
docker rm /marketregime_db marketregime_qdrant qdrant qdrant-local orderpilot-db 2^>nul

echo === Starting NEW ===
cd /d D:\03_Git\02_Python\07_OrderPilot-AI
docker-compose -f docker-compose.db.yml up -d
docker run -d --name qdrant-new -p 6333:6333 qdrant/qdrant:latest

timeout /t 8
docker ps
echo === ENV ===
set PG_DSN=postgresql://orderpilot:orderpilot@localhost:5432/orderpilot
set QDRANT_URL=http://localhost:6333
set QDRANT_COLLECTION=kb_chunks_test
echo PG_DSN=%PG_DSN%
python datenbanken.py
pause
