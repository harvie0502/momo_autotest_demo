"""執行設定，從 .env 讀進來。

獨立成一個模組是因為 conftest 和測試都要用：conftest 用來決定怎麼開瀏覽器，
測試用來判斷無頭模式下要不要跳過關鍵字建議的檢查。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

TRUE_VALUES = ("1", "true", "yes", "on")


def _flag(name: str, default: bool) -> bool:
    """把環境變數轉成布林值。明確列出代表「是」的字面值，其餘一律為否。

    不能寫成 `!= "false"`：那會讓空字串、`0`、`no` 全變成 True，跟預期相反。
    """
    raw = os.getenv(name, "").strip().lower()
    return default if raw == "" else raw in TRUE_VALUES


def _seconds(name: str, default: float) -> float:
    """把環境變數轉成秒數。填錯要在這裡講清楚，而不是在 import 階段丟 traceback。"""
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        raise ValueError(
            f"環境變數 {name} 必須是數字（單位：秒），目前填的是 {raw!r}。"
            f"請修改 .env 或改用 {name}={default} 這樣的值。"
        ) from None


ACCOUNT = os.getenv("MOMO_ACCOUNT", "")
PASSWORD = os.getenv("MOMO_PASSWORD", "")

# 預設有頭。momo 的 WAF 會擋掉無頭瀏覽器打搜尋建議 API（預檢直接回 403），
# 關鍵字建議清單出不來，所以無頭模式下那一項檢查會被跳過。
HEADLESS = _flag("MOMO_HEADLESS", default=False)

# 用本機安裝的 Chrome；留空則改用 Playwright 內建的 Chromium
BROWSER_CHANNEL = os.getenv("MOMO_BROWSER_CHANNEL", "chrome")

# 有頭模式下的觀察用停頓秒數
HEADED_PAUSE_SEC = _seconds("MOMO_HEADED_PAUSE_SEC", default=3)
