# mcp-web-scraper

Playwright tabanlı, Javascript render eden sayfaları otonom şekilde tarayan (scrape) ve bunu **Model Context Protocol (MCP)** standartlarıyla AI Asistanlarına sunan gelişmiş bir web scraper sunucusudur. 

## 🌟 Özellikler
- **`scrape_page`**: Herhangi bir URL'den metin içeriklerini, başlığı ve sayfaya dair metadataları okuyun.
- **`scrape_queue`**: Birden fazla URL'yi arka plan kuyruğuna (job queue) ekleyerek otonom olarak asenkron tarayın.
- **`watch_page`**: Belirli bir URL'in kaynak içeriği değiştiğinde canlı bildirimler (polling/events) alın.
- **`take_screenshot`**: Hedef web sayfasının tam ekran görüntüsünü yüksek boyutlu şifrelenmiş (Base64) biçimde yakalayın.
- **`fill_form`**: CSS Selector'ları kullanarak otomatik ve otonom şekilde web formları doldurun.
- **`extract_table`**: Hedefteki karmaşık HTML tablolarını kolayca yapılandırılmış JSON verilerine (Array) ayrıştırın.
- **`get_links`**: Sayfa üzerindeki tüm bağlantıları (links) tek tuşla etiketleyip çekin.

## 🚀 Anti-Bot (İnsan Taklidi / Stealth)
Eskimiş dış kütüphanelere bağlı kalmaksızın, kendi içinde barındırdığı **manuel stealth** protokolleri sayesinde:
- Cloudflare vb. `webdriver` algılayıcılarını tamamen maskeler.
- Yapay fare hareketleri ile gerçek insan taklidi yapar.
- İzole context, özel `user-agent` ve dil (`tr-TR`) ayarları üzerinden işlem sağlar.

## 🛠️ Kurulum
Projeyi ayağa kaldırmak için sisteminizde **Python 3.10+** yüklü olmalıdır.

```bash
# Projeyi GitHub üzerinden klonlayın
git clone https://github.com/iamseyhmus7/mcp-web-scraper.git
cd mcp-web-scraper

# Gereksinimleri yükleyin
pip install -e .

# Playwright otomasyonu için Chromium tarayıcısını indirin
playwright install chromium
```

## 🎮 Kullanım

### AI Asistanları (Claude Desktop, Cursor vb.) Üzerinden MCP Entegrasyonu
Bu server, standart bir `stdio_server` altyapısı kullanarak JSON-RPC 2.0 mimarisini destekler. AI istemcinizin konfigürasyon (örn: `claude_desktop_config.json`) dosyasına aşağıdaki ayarları ekleyin:

```json
{
  "mcpServers": {
    "mcp-web-scraper": {
      "command": "python",
      "args": ["-m", "mcp_web_scraper.server"]
    }
  }
}
```

*Alternatif olarak `uvx` kurarak doğrudan Smithery komutları (`smithery.yaml`) aracılığıyla kullanabilirsiniz.*

### Deneme ve Geliştirme (Test)
Uçtan uca tüm bu MCP tool'larının gerçek dünyada nasıl çalıştığını (Wikipedia ve Example sayfalarında) test etmek için proje içindeki test betiğini kullanabilirsiniz:

```bash
# Tüm tool'ların çıktılarını terminale yansıtan test scripti
python test_real.py

# Unittest'leri test etmek isterseniz:
pytest tests/
```

## 👨‍💻 Geliştirici
- [Şeyhmus OK](https://github.com/iamseyhmus7)
