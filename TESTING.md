# TESTING

Bu dokuman, sistemin nasil test edildigini, hangi senaryolarda nasil davrandigini ve bilinen sinirlari aciklar.

## 1) Otomasyon Testleri

Calistirma komutu:

```bash
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
python -m pytest backend/tests -q
```

Son durum:

- `4 passed`

Kapsanan testler:

1. Desteklenen/desteklenmeyen formatlarin upload davranisi
2. Grounded answer + citation donusu
3. Belgede olmayan bilgi icin `no_evidence` davranisi
4. API key eksikliginde fail-fast (503)

## 2) Senaryo Bazli Dogrulama

### Senaryo A - PDF upload

- Girdi: Metin iceren PDF
- Beklenen: `status=indexed`, belge listesinde gorunmeli
- Sonuc: Basarili

### Senaryo B - Desteklenmeyen format

- Girdi: `.txt`
- Beklenen: `rejected_files` altinda anlamli hata
- Sonuc: Basarili

### Senaryo C - Belgede olan bilgi sorusu

- Soru: Ankara bilgisini soran soru
- Beklenen: `mode=grounded_answer`, citation dolu
- Sonuc: Basarili

### Senaryo D - Belgede olmayan bilgi

- Soru: Mars ussu gibi baglam disi soru
- Beklenen: `mode=no_evidence`, citation bos
- Sonuc: Basarili

### Senaryo E - API key yok

- Kosul: `GEMINI_API_KEY` tanimsiz
- Beklenen: Upload/QA adimlarinda fail-fast + anlamli hata
- Sonuc: Basarili

## 3) Farkli Belge Tiplerinde Davranis

- Turkce metin: Destekleniyor
- Ingilizce metin: Destekleniyor
- Taranmis PDF: Sayfada image objesi varsa OCR fallback calisir
- Tablolu belgeler: Temel destek var; karma tablolar icin ek parser iyilestirmesi gerekebilir

## 4) Bilinen Yetersizlikler

- PDF OCR fallback kapasitesi, PDF icindeki image cikarmanin basarisina bagli
- Citation kontrolu sentence-level degil, chunk-level
- Dil tespiti heuristik oldugu icin kisa metinlerde `unknown` donebilir

## 5) Gelistirme Onerileri

1. Daha guclu language detection modeli
2. OCR pipeline icin ikinci fallback motoru
3. QA cikisi icin stricter JSON schema enforcement
4. Retrieval ve prompt metrikleri icin gozlemlenebilirlik paneli
