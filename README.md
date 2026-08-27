# momo 購物網 — 購買流程自動化測試

用 Playwright + pytest 針對 [momo 購物網](https://www.momoshop.com.tw/) 的搜尋與購買流程做端對端測試。
測試跑在**真實的線上網站**上，沒有任何 mock 或 stub。

---

## 測試情境

| 測試 | 情境 | 步驟 |
|---|---|---|
| `test_buy_from_cart` | 從購物車購買 | 搜尋（輸入時檢查關鍵字建議）→ 到搜尋結果頁 → 第一項加入購物車 → 進購物車 → 結帳 → 確認到結帳頁 |
| `test_buy_from_product_page` | 從商品頁購買 | 搜尋（輸入時檢查關鍵字建議）→ 到搜尋結果頁 → 點進第一項商品 → 確認到商品頁 → 直接購買 → 確認到結帳頁 |

兩個情境的後置動作都是**清空購物車**。

> 測試只確認「有到結帳頁、而且『確認結帳』按鈕在」，**不會真的送出訂單**。
> `CheckoutPage` 刻意不提供任何點擊 `#orderSave` 的方法，程式上就不可能誤送。

---

## 環境需求

| 項目 | 需求 | 備註 |
|---|---|---|
| 作業系統 | macOS / Windows / Linux | 開發與驗證環境為 macOS |
| Python | 3.9 以上 | 驗證環境為 3.9.6 |
| Google Chrome | 需要安裝 | 測試預設開本機 Chrome，原因見下方「第一次執行前」 |
| momo 帳號 | 需要一組可正常登入的帳號 | 測試會真的登入、真的把商品加進購物車 |

---

## 安裝

```bash
git clone <這個 repo 的網址>
cd momo_autotest
```

建立虛擬環境並安裝套件：

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

安裝 Playwright 的瀏覽器（作為 Chrome 的備援）：

```bash
playwright install chromium
```

---

## 設定帳密

複製範本後填入你自己的 momo 帳號密碼：

```bash
cp .env_example .env
```

`.env` 已經在 `.gitignore` 裡，不會進版控。內容：

| 變數 | 預設 | 說明 |
|---|---|---|
| `MOMO_ACCOUNT` | — | momo 帳號（手機 / 身分證字號 / 統一證號 擇一） |
| `MOMO_PASSWORD` | — | 密碼 |
| `MOMO_HEADLESS` | `false` | 是否無頭模式。**請保持 false**，原因見「已知限制」 |
| `MOMO_BROWSER_CHANNEL` | `chrome` | 用本機 Chrome；留空則改用 Playwright 內建 Chromium |
| `MOMO_HEADED_PAUSE_SEC` | `3` | 有頭模式下在結帳頁、登出前後各停幾秒方便人眼確認，設 `0` 關閉 |

---

## ⚠️ 第一次執行前：手動登入完成簡訊驗證

**這一步只需要做一次，但不做的話測試會登入失敗。**

momo 對沒看過的裝置會要求簡訊 OTP 驗證。這個驗證記錄是存在 momo 的伺服器上，
綁「帳號 + 瀏覽器身分」，不是存在瀏覽器的 cookie 裡。所以：

1. **用你自己的 Chrome 打開 <https://www.momoshop.com.tw/>**
2. 點右上角「登入」，輸入帳密
3. 如果跳出簡訊驗證，收簡訊並完成驗證

完成之後，自動化測試開的也是**同一個 Chrome**（`MOMO_BROWSER_CHANNEL=chrome`），
對 momo 來說是同一台裝置，就不會再要求簡訊驗證了。

> 為什麼一定要 Chrome？Playwright 內建的 Chromium 和 Firefox 的瀏覽器身分都不一樣，
> 對 momo 來說是沒驗證過的新裝置，會再次要求簡訊 OTP。
> 框架也把無頭模式的 User-Agent 從 `HeadlessChrome` 改回 `Chrome`（見 `conftest.py`
> 的 `stable_user_agent`），讓有頭 / 無頭跑起來是同一個身分。

---

## 執行測試

```bash
pytest
```

只跑其中一個情境：

```bash
pytest -k test_buy_from_cart
```

失敗時想看得更清楚（截圖 / 錄影 / trace）：

```bash
pytest --screenshot=only-on-failure --video=retain-on-failure --tracing=retain-on-failure
```

產出會放在 `test-results/`。用 `playwright show-trace test-results/<資料夾>/trace.zip` 開啟 trace。

---

## 專案結構

```
conftest.py                  瀏覽器設定 + 整包測試「登入一次、登出一次」
pytest.ini                   pytest 設定
requirements.txt
.env_example                 帳密與執行選項的範本

data/
  test_data.py               搜尋關鍵字等測試參數，腳本用名稱取用

pages/                       Page Object
  urls.py                    網址與網址樣式，集中一處
  helpers.py                 共用等待與規格選擇
  login_page.py              登入 / 登出
  home_page.py               首頁搜尋框與關鍵字建議
  search_result_page.py      搜尋結果、加入購物車
  product_page.py            商品頁、直接購買
  cart_page.py               購物車、全部刪除、結帳
  checkout_page.py           結帳頁（不提供送出訂單的方法）
  header.py                  header 的購物車入口與件數

tests/
  conftest.py                後置清空購物車
  test_purchase_flow.py      兩個購買情境
```

---

## 設計說明

### 登入只做一次

題目要求登入登出在整包測試中只執行一次。做法是把 pytest-playwright 的 `page` fixture
覆寫成 session scope：整個測試共用同一個已登入的 page，session 結束才登出。

### 全程走使用者路徑

除了「打開首頁」（使用者打開網站的起點）之外，站內移動一律用點擊，不直接開網址。
例如進購物車是點 header 的購物車，不是 `page.goto(購物車網址)`。

### 全部是動態等待

測試程式碼裡沒有任何固定秒數的 sleep。等待都是條件成立就往下走：

| 寫法 | 等什麼 |
|---|---|
| `locator.wait_for(state=...)` | 元素出現 / 消失 |
| `page.wait_for_url(...)` | 導頁到指定頁面 |
| `expect(...).to_have_text(...)` | 文字變成預期值 |

唯一的固定停頓是 `MOMO_HEADED_PAUSE_SEC`，那是給人眼看畫面用的，只在有頭模式生效。

### 選擇器優先順序

momo 有替不少元素標上 `data-testid`（`header-login-button`、`header-search-input`、
`spec-button-*` 等），優先使用；其次是語意化的 class 與 id；最後才是文字定位。

### 探索真實網站後才寫得出來的幾件事

這些都是實測發現的，直接影響實作，也都寫在對應的程式註解裡：

| 發現 | 影響 |
|---|---|
| 首頁按 Enter **不會**送出搜尋 | 一定要點搜尋鈕 |
| 關鍵字建議要**逐字輸入**才會觸發 | 用 `press_sequentially` 而不是 `fill` |
| 首頁 header 按鈕在 hydration 完成前沒有事件，點了完全沒反應也不報錯 | `click_until()`：點了就檢查有沒有效果，沒效果再點 |
| 購物車的「全部刪除」「結帳」會跳**原生 confirm 視窗**，Playwright 預設自動取消 | 操作期間掛上 dialog handler 按「確定」，做完就移除 |
| 商品規格有**兩種 UI**（下拉選單 / 按鈕方塊），同一個關鍵字底下兩種都會出現 | `choose_first_spec()` 兩種都處理，一律選第一個可選的 |
| 「直接購買」不是直接跳結帳，是先進購物車 | 情境 2 要再按一次「結帳」 |
| 結帳前後**網址完全不變**（同一個 SPA 換步驟） | 用畫面元素判斷有沒有到結帳頁，不比對網址 |
| header 購物車數字剛載入是 SSR 的 0，約 0.5 秒後才更新 | 測試比較「加入前後的差值」，不斷言絕對值 |

### 為什麼選這兩個情境

搜尋是 momo 的主要入口，而搜尋的價值在於**能不能買到東西**。所以測試涵蓋的是
「搜尋 → 找到商品 → 完成購買」這條完整的營收路徑，而不是只驗證搜尋結果有幾筆。
兩個情境對應使用者實際的兩種購買習慣：加入購物車再一起結帳、以及在商品頁直接下單。

---

## 已知限制與後續可優化

### 簡訊 OTP 無法自動化

目前第一次登入的簡訊驗證必須**人工完成**（見上方「第一次執行前」）。
原因是非 momo 內部人員無法取得簡訊內容。

後續若能取得驗證碼來源，這一段可以自動化，方向有幾個：

- 接 momo 內部的簡訊閘道 / 測試用 OTP API，測試直接取號填入
- 測試環境改用固定的測試帳號並關閉裝置驗證
- 串接可程式化的簡訊服務（如 Twilio）收取驗證碼

自動化之後，第一次執行就不需要人工介入，也才能真正放進 CI 排程跑。

### 無頭模式不能用

momo 的 WAF 會擋掉無頭瀏覽器打搜尋建議 API（預檢直接回 403），關鍵字建議清單出不來。
實測：有頭 15 筆建議、無頭 0 筆。所以 `MOMO_HEADLESS` 預設 `false`，**這也讓測試目前無法在無頭的 CI 環境執行**。

### 測試會動到真實帳號

測試會真的登入、真的把商品加進該帳號的購物車。後置動作會清空購物車，
但**不會**送出訂單。建議使用專門的測試帳號。

### 依賴線上網站

選擇器都是從線上網站實測得來的，momo 改版就需要更新。
所有選擇器都收在 `pages/` 底下的各個 Page Object，網址則集中在 `pages/urls.py`。
