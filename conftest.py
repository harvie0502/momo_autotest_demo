"""全域 fixture：瀏覽器設定，以及整個測試 session 登入一次、登出一次。

覆寫 pytest-playwright 的 page fixture 把它改成 session scope，
所有 tests/ 底下的腳本共用同一個已登入的 page，不用各自再登入。
"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from pages.login_page import LoginPage, is_logged_in

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

# 預設有頭：momo 的 WAF 會擋掉 headless 的搜尋建議 API（預檢直接回 403），
# 關鍵字建議清單就出不來。要跑 headless 得接受這項功能測不到。
HEADLESS = os.getenv("MOMO_HEADLESS", "false").lower() != "false"
BROWSER_CHANNEL = os.getenv("MOMO_BROWSER_CHANNEL", "chrome")
HEADED_PAUSE_SEC = float(os.getenv("MOMO_HEADED_PAUSE_SEC", "3"))
DESKTOP_VIEWPORT = {"width": 1512, "height": 800}


@pytest.fixture(scope="session")
def config():
    account = os.getenv("MOMO_ACCOUNT", "")
    password = os.getenv("MOMO_PASSWORD", "")
    if not account or not password:
        pytest.fail("請先複製 .env_example 成 .env 並填入 MOMO_ACCOUNT / MOMO_PASSWORD")
    return {"account": account, "password": password}


# --- 瀏覽器設定 ---------------------------------------------------------


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """瀏覽器啟動參數。

    channel 一定要塞進這裡才有作用：pytest-playwright 啟動瀏覽器時只讀
    browser_type_launch_args，覆寫 browser_channel fixture 是沒有效果的。
    命令列的 --browser-channel 優先，這裡只在沒指定時補上預設值。
    """
    args = dict(browser_type_launch_args)
    if BROWSER_CHANNEL and "channel" not in args:
        # 用本機安裝的 Chrome，而不是 Playwright 內建的 Chromium。
        # momo 的裝置認證記在他們 server 上，綁「帳號 + 瀏覽器身分」；
        # 使用者是用自己的 Chrome 手動完成簡訊驗證的，測試也開同一個 Chrome，
        # 才算同一台裝置、不會再被要求驗證。
        args["channel"] = BROWSER_CHANNEL
    args["args"] = [
        *args.get("args", []),
        "--start-maximized",
        # Playwright 開的瀏覽器預設會把 navigator.webdriver 設成 true，
        # momo 登入時看到這個旗標會擋下來（回 ACT016）。關掉它讓測試瀏覽器
        # 跟一般瀏覽器一致，測到的才是真實的使用者行為。
        "--disable-blink-features=AutomationControlled",
    ]
    if not HEADLESS:
        args["headless"] = False
    return args


@pytest.fixture(scope="session")
def stable_user_agent(browser):
    """讓有頭 / 無頭跑起來是同一個瀏覽器身分。

    headless 的 Chrome 會把 UA 報成 HeadlessChrome，對 momo 就是另一台沒驗證過
    的裝置。這裡取實際 UA 再把 Headless 拿掉；版本號用讀的不寫死，換 Chrome
    版本也不用改。有頭模式本來就正常，不用動。
    """
    if not HEADLESS:
        return None
    probe = browser.new_context()
    user_agent = probe.new_page().evaluate("() => navigator.userAgent")
    probe.close()
    return user_agent.replace("HeadlessChrome", "Chrome")


@pytest.fixture(scope="session")
def context(browser, stable_user_agent):
    """視窗大小。

    有頭模式：--start-maximized 搭配 no_viewport=True 就是真的最大化視窗。
    無頭模式：沒有真的視窗，用固定桌機解析度，避免拿到 momo 的手機版版型。
    """
    context = browser.new_context(
        locale="zh-TW",
        no_viewport=not HEADLESS,
        viewport=DESKTOP_VIEWPORT if HEADLESS else None,
        user_agent=stable_user_agent,
    )
    yield context
    context.close()


# --- 登入 / 登出（整個 session 各一次）----------------------------------


@pytest.fixture(scope="session")
def page(context, config):
    """整個測試 session 唯一的 page，開場就登入，結束才登出。"""
    page = context.new_page()

    login_page = LoginPage(page)
    login_page.login(config["account"], config["password"])
    assert is_logged_in(page), "登入流程跑完了，但 header 沒有變成「登出」"

    yield page

    _pause_to_watch(page)   # 看得到登出前還是登入狀態
    login_page.logout()
    _pause_to_watch(page)   # 看得到 header 變回「登入」


# --- 觀察用停頓 ---------------------------------------------------------


def _pause_to_watch(page):
    """有頭模式停一下讓人看得到畫面；無頭模式直接跳過。"""
    if not HEADLESS and HEADED_PAUSE_SEC > 0:
        page.wait_for_timeout(HEADED_PAUSE_SEC * 1000)


@pytest.fixture
def pause(page):
    """讓測試在關鍵畫面停一下，方便人眼確認。

    只在有頭模式生效，無頭跑 CI 不會白等。秒數由 MOMO_HEADED_PAUSE_SEC 控制。
    """
    return lambda: _pause_to_watch(page)
