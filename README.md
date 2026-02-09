# TUSAS Belge Analiz ve Soru-Cevap Sistemi (MVP)

Bu proje, TUSAS case study isterleri dogrultusunda PDF/JPG/PNG belgelerini yukleyip metin cikarimi yapan, belgeleri indeksleyen ve dogal dil sorularini belge baglaminda cevaplayan bir MVP sunar.

## Ozellikler

- PDF, JPG, PNG belge yukleme
- PDF icin native metin cikarimi ve gerekirse OCR fallback
- Gorseller icin Gemini tabanli OCR
- Chunk tabanli indeksleme ve vector store (Chroma + otomatik local fallback)
- Gemini ile grounded soru-cevap
- Citation zorunlulugu ve no-evidence davranisi
- FastAPI backend + React frontend

## Teknoloji Secimi

- Backend: FastAPI, SQLAlchemy, SQLite
- AI: Gemini (OCR, embedding, QA)
- Vector DB: Chroma (persistent), hata durumunda Local JSON fallback
- Frontend: React + Vite + TypeScript
- Test: Pytest + mock Gemini/vector store

## Proje Yapisi

- `backend/app`: API, servisler, veri modelleri
- `backend/tests`: mock tabanli backend testleri
- `frontend/src`: web arayuzu
- `docs/RUNBOOK.md`: operasyon notlari
- `DEVLOG.md`: gelistirme gunlugu
- `TESTING.md`: test senaryolari ve sonuclar

## Kurulum

### 1) Ortam degiskenleri

`.env.example` dosyasini referans alin.

Zorunlu:

- `GEMINI_API_KEY`

Opsiyonel ama onemli:

- `GEMINI_USE_SYSTEM_PROXY=false` (varsayilan). Sistem proxy'si hataliysa Gemini baglantisini korur.
- `GEMINI_MODEL=gemini-2.5-pro` (onerilen kalite odakli varsayilan)
- `GEMINI_EMBED_MODEL=gemini-embedding-001` (onerilen embedding modeli)

### 2) Backend

```bash
python -m venv backend/.venv
backend/.venv/Scripts/activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Frontend

```bash
cd frontend
npm install
npm run dev
```

Varsayilan frontend adresi: `http://localhost:5173`

## API Ozeti

- `GET /api/health`
- `POST /api/documents` (`multipart/form-data`, `files[]`)
- `GET /api/documents`
- `POST /api/questions`

### `POST /api/questions` ornek

```json
{
  "question": "Belgede merkez sehri nedir?",
  "document_ids": ["<document_id>"],
  "top_k": 5
}
```

Ornek cevap:

```json
{
  "answer": "Belgeye gore merkez Ankara'dadir.",
  "mode": "grounded_answer",
  "citations": [
    {
      "document_id": "...",
      "filename": "ankara.pdf",
      "page": 1,
      "chunk_id": "...",
      "snippet": "TUSAS merkezi Ankara'dadir..."
    }
  ],
  "confidence": 0.83,
  "used_chunks": 3
}
```

## Halusinasyon Onleme Yaklasimi

- Retrieval mesafe esigi (`RETRIEVAL_MAX_DISTANCE`) ile on filtreleme
- Prompt seviyesinde "yalnizca baglam" kurali
- Citation zorunlulugu
- Desteklenmeyen soruda sabit no-evidence yaniti:
  - `Bu bilgi belgede bulunamadi.`

## Test Calistirma

```bash
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
python -m pytest backend/tests -q
```

## Bilinen Sinirlar

- PDF OCR fallback, pypdf ile sayfadaki gorsel objelerine baglidir
- Cok karmasik tablo/sekil belgelerinde ek iyilestirme gerekebilir
- Gercek model davranisi API kota ve model yanit degiskenliginden etkilenebilir
