# AGENTS.md — mcp-web-scraper

## 🎯 Proje Amacı

Bu proje **Playwright** tabanlı otonom web scraper'ı **MCP (Model Context Protocol)**
üzerinden AI asistanlarına sunan gelişmiş bir server'dır.

JavaScript render eden siteler dahil her türlü web sayfasını okuyabilir,
form doldurabilir, ekran görüntüsü alabilir, değişiklikleri izleyebilir
ve çoklu URL'leri kuyruk sistemiyle işleyebilir.

---

## 🏗️ Mimari Genel Bakış

```
AI Asistan (Claude / Gemini / Cursor)
        │
        │  MCP Protokolü (JSON-RPC 2.0 over stdio)
        ▼
┌─────────────────────────────────────────────┐
│                server.py                     │
│         7 MCP Aracı (list_tools)            │
│         call_tool() yönlendirici            │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌─────────────────────┐
│  browser.py   │    │     queue.py         │
│  Playwright   │    │  AsyncIO Job Queue   │
│  BrowserPool  │    │  Worker Pool (3x)    │
│  - Chromium   │    │  Job Status Tracker  │
│  - Stealth    │    └─────────────────────┘
│  - Anti-bot   │             │
└───────┬───────┘             │
        │          ┌──────────┘
        ▼          ▼
┌─────────────────────────────┐
│         scraper.py           │
│  - scrape_page()             │
│  - extract_table()           │
│  - get_links()               │
│  - fill_form()               │
│  - take_screenshot()         │
│  - watch_page() → WebSocket  │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│         storage.py           │
│  - /tmp/screenshots/         │
│  - Job results (memory)      │
│  - Watch events (queue)      │
└─────────────────────────────┘
```

---

## 📦 Teknoloji Yığını

| Katman | Teknoloji | Versiyon | Neden? |
|--------|-----------|----------|--------|
| MCP Protokolü | `mcp` | ≥1.19.0 | Resmi Python SDK |
| Tarayıcı | `playwright` | ≥1.40.0 | JS render, gerçek tarayıcı |
| Anti-bot | `playwright-stealth` | ≥1.0.0 | Bot tespitini engelle |
| HTML Parse | `beautifulsoup4` | ≥4.12.0 | Tablo + link çıkarımı |
| HTML Parse | `lxml` | ≥5.0.0 | BS4 backend, hızlı parse |
| Async | `anyio` | ≥4.7.0 | Async task yönetimi |
| Retry | `tenacity` | ≥8.0.0 | Otomatik yeniden deneme |
| Paketleme | `hatchling` | latest | Modern build backend |
| Test | `pytest` + `pytest-asyncio` | ≥8.3.0 | Async test desteği |
| Mock | `pytest-playwright` | ≥0.4.0 | Tarayıcı mock'lama |
| Linter | `ruff` | ≥0.8.0 | Hızlı Python linter |

---

## 📁 Klasör Yapısı

```
mcp-web-scraper/
├── AGENTS.md                          ← Bu dosya
├── README.md                          ← Kullanıcı dokümantasyonu
├── smithery.yaml                      ← Smithery.ai deployment
├── pyproject.toml                     ← Paket tanımı
│
├── src/
│   └── mcp_web_scraper/
│       ├── __init__.py                ← __version__ = "0.1.0"
│       ├── __main__.py                ← python -m girişi
│       ├── server.py                  ← MCP araçları (7 araç)
│       ├── browser.py                 ← Playwright BrowserPool
│       ├── scraper.py                 ← Scraping iş mantığı
│       ├── queue.py                   ← AsyncIO job queue + workers
│       └── storage.py                 ← Dosya + memory storage
│
├── tests/
│   ├── test_scraper.py                ← Scraper testleri
│   ├── test_queue.py                  ← Queue testleri
│   └── conftest.py                    ← Playwright fixtures
│
└── .agent/
    ├── rules/
    │   ├── python-style.md
    │   ├── playwright-rules.md        ← Playwright özel kurallar
    │   └── mcp-protocol.md
    ├── workflows/
    │   ├── add-tool.md
    │   └── publish-to-pypi.md
    └── skills/
        └── web-scraper/
            └── SKILL.md
```

---

## 🛠️ 7 MCP Aracı

| Araç | Açıklama | Zorunlu Parametre | Zorluk |
|------|----------|-------------------|--------|
| `scrape_page` | URL'den içerik, başlık, metadata çıkar | `url` | ⭐⭐ |
| `scrape_queue` | Çoklu URL'leri kuyruğa ekle, job_id döndür | `urls[]` | ⭐⭐⭐ |
| `watch_page` | Sayfa değişikliğini periyodik izle | `url`, `interval_seconds` | ⭐⭐⭐⭐ |
| `take_screenshot` | Tam sayfa ekran görüntüsü al | `url` | ⭐⭐ |
| `fill_form` | CSS selector ile form doldur ve gönder | `url`, `fields{}` | ⭐⭐⭐⭐ |
| `extract_table` | HTML tabloyu JSON array'e çevir | `url` | ⭐⭐⭐ |
| `get_links` | Sayfadaki tüm linkleri filtreli listele | `url` | ⭐⭐ |

---

## 🔑 Değişmez Kod Kuralları

### BrowserPool — Tarayıcı Yönetimi
```python
# ✅ DOĞRU — Pool'dan al, işi bitince iade et
async with browser_pool.acquire() as page:
    await page.goto(url)
    content = await page.content()

# ❌ YANLIŞ — Her istekte yeni tarayıcı açma
browser = await playwright.chromium.launch()
page = await browser.new_page()
```

### Timeout Yönetimi
```python
# ✅ Her goto() için timeout zorunlu
await page.goto(url, timeout=30000, wait_until="networkidle")

# ✅ Selector beklerken timeout
await page.wait_for_selector("table", timeout=10000)
```

### Anti-Bot
```python
# ✅ Her yeni page'e stealth uygula
from playwright_stealth import stealth_async
await stealth_async(page)

# ✅ İnsan gibi davran
await page.mouse.move(100, 200)
await asyncio.sleep(random.uniform(0.5, 1.5))
```

### Job Queue
```python
# ✅ Job sonucu her zaman şu yapıda olmalı
{
    "job_id": "uuid4",
    "status": "pending" | "running" | "completed" | "failed",
    "total": 10,
    "completed": 7,
    "failed": 1,
    "results": [...],
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
}
```

### Screenshot Storage
```python
# ✅ Dosya yolu: /tmp/mcp-scraper/screenshots/{job_id}.png
# ✅ Base64 encode edip MCP response'a ekle
import base64
with open(path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
```

### Watch Page — WebSocket Alternatifi
```python
# WebSocket yerine polling + async generator kullan
# MCP stdio transport WebSocket desteklemez
# Değişiklik tespiti: content hash karşılaştırması
import hashlib
hash_before = hashlib.md5(content.encode()).hexdigest()
```

---

## 🧪 Test Kuralları

- Testlerde **gerçek URL'e istek atma** → `pytest-playwright` mock kullan
- Her araç için: başarılı senaryo + timeout senaryosu + geçersiz URL senaryosu
- BrowserPool testleri için: `@pytest.fixture` ile mock browser
- Queue testleri için: 3 URL → 2 başarılı + 1 hatalı senaryo

```python
# conftest.py fixture şablonu
@pytest.fixture
async def mock_page(mocker):
    page = AsyncMock()
    page.content.return_value = "<html><body>Test</body></html>"
    page.title.return_value = "Test Page"
    return page
```

---

## ⚠️ Önemli Kısıtlar

- **Robots.txt** her zaman kontrol edilmeli — ihlal eden URL'ler reddedilmeli
- **Rate limiting**: Aynı domain'e saniyede max 2 istek
- **Timeout**: Tüm operasyonlar max 30 saniye
- **Memory**: Watch görevi max 24 saat çalışabilir
- **Screenshot**: Max 10MB, /tmp/ altında saklanır
- **Form filling**: Şifre alanları loglanmaz, maskelenir
- **Queue**: Aynı anda max 10 aktif job

---

## 🌍 Yayın Platformları

Proje tamamlandığında sırayla eklenecek:

1. **PyPI** → `pip install mcp-web-scraper` / `uvx mcp-web-scraper`
2. **Smithery.ai** → https://smithery.ai/submit
3. **awesome-mcp-servers** → PR: Web Scraping kategorisi
4. **modelcontextprotocol/servers** → PR: Community Servers

```yaml
# smithery.yaml
name: mcp-web-scraper
description: >
  Autonomous web scraper via MCP. Playwright-based browser automation
  supporting JS rendering, form filling, screenshots, queue processing
  and page change monitoring.
categories:
  - web-scraping
  - browser-automation
  - data-extraction
startCommand:
  type: stdio
  command: uvx
  args: ["mcp-web-scraper"]
```

---

## 📝 Git Commit Kuralları

```
feat: yeni araç veya özellik
fix: hata düzeltme
test: test ekleme
docs: dokümantasyon
chore: bağımlılık / versiyon
perf: performans iyileştirmesi
security: güvenlik düzeltmesi
```