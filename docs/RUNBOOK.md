# RUNBOOK

## Hizli Calistirma

1. `.env` icine `GEMINI_API_KEY` ekle
2. Backend'i ayaga kaldir
3. Frontend'i ayaga kaldir
4. `GET /api/health` ile servis durumunu dogrula

## Sorun Giderme

### `503` ve `API_KEY` hatasi

- Neden: Gemini anahtari tanimli degil
- Cozum: `GEMINI_API_KEY` veya `GOOGLE_API_KEY` tanimla

### `vector_store: down`

- Neden: Chroma ilklenemedi
- Cozum: `APP_CHROMA_DIR` yazma iznini ve paket surumlerini kontrol et

### Upload basarili ama QA no_evidence

- Olasi nedenler:
  - soru baglama uzak
  - retrieval threshold cok siki
  - dokuman status indexed degil
- Cozum:
  - `RETRIEVAL_MAX_DISTANCE` degerini kontrollu sekilde artir
  - `GET /api/documents` ile status kontrol et

## Operasyon Notlari

- Uretimde loglar merkezi sisteme aktarilmali
- API anahtari secret manager uzerinden verilmeli
- Vector/index dosyalari yedeklenmeli
