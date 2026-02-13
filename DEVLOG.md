# DEVLOG

## 2026-02-09 - Baslangic ve Iskelet

- Repo sifirdan oldugu icin backend/frontend klasor yapisi kuruldu.
- FastAPI ve React/Vite temel dosyalari eklendi.
- `.gitignore` ve temel dependency dosyalari olusturuldu.
- Ilk commit/push ile iskelet sabitlendi.

## 2026-02-09 - Upload ve Kalici Katman

- SQLite tabanli `Document` modeli olusturuldu.
- Dosya yukleme endpointi (`POST /api/documents`) ve listeleme endpointi (`GET /api/documents`) eklendi.
- Dosya saklama servisi ve health endpointi ile temel API omurgasi tamamlandi.

## 2026-02-09 - Metin Cikarimi

- PDF ve gorsel dosyalari icin extraction pipeline gelistirildi.
- Gemini tabanli OCR katmani eklendi.
- Segment bazli kayit modeli eklendi (`document_segments`).
- Yukleme akisinda dil tespiti ve extraction asamasi devreye alindi.

## 2026-02-09 - Indexleme ve QA

- Chunk builder eklendi.
- Chroma vector store entegrasyonu yapildi.
- `document_chunks` modeli ile DB kaydi eklendi.
- `POST /api/questions` endpointi ve grounded QA servisi eklendi.
- Citation map, retrieval threshold ve no-evidence fallback davranisi eklendi.

## 2026-02-09 - Frontend

- Upload + belge listesi + soru-cevap + citation gosterimi tamamlandi.
- Responsive, tek sayfa, Turkce agirlikli UI teslim edildi.
- Error handling ve durum geri bildirimleri eklendi.

## 2026-02-09 - Testler ve Ortam Uyumlulugu

- Mock Gemini + fake vector store ile deterministik backend testleri yazildi.
- API key eksikliginde fail-fast davranisi testlendi.
- Cevrimde gorulen package uyumsuzluklari icin lazy import/fallback yapisi eklendi.
- `pytest_asyncio` plugin catismasina karsi test komutu notu eklendi.

## 2026-02-13 - Hardening ve Teslim Kalitesi

- PDF extraction icin "kisa native text" durumunda sayfanin kaybolmasina yol acan akis duzeltildi ve regression test eklendi.
- Dil tespiti heuristigi (TR/EN) duzeltildi; diacritics + token bazli yaklasimla temel unit testler eklendi.
- Gemini entegrasyonu guncel `google-genai` SDK uzerine tasindi (structured JSON output + batch embedding hedefi).
- Node/Vite calismayan ortamlarda kullanilabilirlik icin backend'den statik UI servis edilmesi eklendi ve testlendi.
- README/TESTING/RUNBOOK dokumanlari PowerShell uyumlu ve guncel akisi yansitacak sekilde guncellendi.

## Bugun tekrar baslasam farkli yapacaklarim

- Baslangicta AI, vector store ve storage icin soyut arayuzleri daha erken cikartirdim.
- Dilden bagimsiz daha guclu bir language detection kurgusu (harici model) planlardim.
- PDF OCR fallback icin birden fazla stratejiyi (poppler/tabula vb.) erken prototiplerdim.
