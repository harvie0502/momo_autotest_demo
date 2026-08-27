"""全域 fixture：瀏覽器設定，以及整包測試登入一次、登出一次。

把 pytest-playwright 的 context / page 覆寫成 session scope，
所有測試共用同一個已登入的 page。代價是它內建的 --screenshot / --video /
--tracing 會失效——那些掛在它自己的 function scope context 上。
失敗時看 terminal 的斷言訊息與 HTML 報告。
"""

from pathlib import Path

import pytest
from playwright.sync_api import expect

from pages.helpers import DEFAULT_TIMEOUT_MS
from pages.login_page import LoginPage, is_logged_in
from settings import ACCOUNT, BROWSER_CHANNEL, HEADED_PAUSE_SEC, HEADLESS, PASSWORD

DESKTOP_VIEWPORT = {"width": 1512, "height": 800}

def _output_dir(config) -> Path:
    """產出目錄。跟 pytest-playwright 的 --output 對齊，截圖 / trace / 報告都放這。"""
    return Path(config.getoption("--output")).absolute()


def pytest_configure(config):
    """報告路徑跟著 --output 走；expect() 的預設逾時只有 5 秒，拉齊成 30 秒。"""
    if getattr(config.option, "htmlpath", None) is None:
        config.option.htmlpath = str(_output_dir(config) / "report.html")
    expect.set_options(timeout=DEFAULT_TIMEOUT_MS)


# --- 瀏覽器 -------------------------------------------------------------


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, browser_name):
    """channel 一定要塞進這裡才有作用：啟動瀏覽器時只讀 browser_type_launch_args。

    用本機 Chrome 而不是內建 Chromium——momo 的裝置認證綁「帳號 + 瀏覽器身分」，
    要跟使用者手動完成簡訊驗證的那個瀏覽器一致。channel 只對 chromium 有意義。
    """
    args = dict(browser_type_launch_args)
    if BROWSER_CHANNEL and browser_name == "chromium" and "channel" not in args:
        args["channel"] = BROWSER_CHANNEL

    # navigator.webdriver 為 true 會被 momo 登入擋下（回 ACT016）
    flags = [*args.get("args", []), "--disable-blink-features=AutomationControlled"]
    if not HEADLESS:
        flags.append("--start-maximized")
    args["args"] = flags
    args["headless"] = HEADLESS   # 兩邊都明寫，以 MOMO_HEADLESS 為準
    return args


@pytest.fixture(scope="session")
def stable_user_agent(browser):
    """無頭的 Chrome 會把 UA 報成 HeadlessChrome，對 momo 是另一台沒驗證過的裝置。

    取實際 UA 再把 Headless 拿掉，版本號不寫死。有頭本來就正常，不用動。
    """
    if not HEADLESS:
        return None
    probe = browser.new_context()
    user_agent = probe.new_page().evaluate("() => navigator.userAgent")
    probe.close()
    return user_agent.replace("HeadlessChrome", "Chrome")


@pytest.fixture(scope="session")
def context(browser, browser_context_args, stable_user_agent):
    """整包共用的 context：視窗大小與語系。"""
    args = {
        "locale": "zh-TW",
        # 有頭：--start-maximized 配 no_viewport 就是真的最大化。
        # 無頭：沒有真的視窗，給固定桌機解析度，避免拿到手機版版型。
        "no_viewport": not HEADLESS,
        "viewport": DESKTOP_VIEWPORT if HEADLESS else None,
        "user_agent": stable_user_agent,
    }
    # 合併命令列來的設定（--device、--base-url），不然那些參數會無聲失效
    args.update(browser_context_args)
    if args.get("viewport") is not None:
        args["no_viewport"] = False   # 兩者不能同時給值

    context = browser.new_context(**args)
    yield context
    context.close()


# --- 登入 / 登出（整包各一次）-------------------------------------------


@pytest.fixture(scope="session")
def page(context):
    """整包唯一的 page，開場就登入，結束才登出。"""
    if not ACCOUNT or not PASSWORD:
        pytest.fail("請先複製 .env_example 成 .env 並填入 MOMO_ACCOUNT / MOMO_PASSWORD")

    page = context.new_page()
    login_page = LoginPage(page)
    login_page.login(ACCOUNT, PASSWORD)
    assert is_logged_in(page), "登入流程跑完了，但 header 沒有變成「登出」"

    yield page

    _pause(page)
    login_page.logout()
    _pause(page)


def _pause(page):
    """有頭模式停一下讓人看得到畫面；無頭直接跳過。"""
    if not HEADLESS and HEADED_PAUSE_SEC > 0:
        page.wait_for_timeout(HEADED_PAUSE_SEC * 1000)


@pytest.fixture
def pause(page):
    """讓測試在關鍵畫面停一下，秒數由 MOMO_HEADED_PAUSE_SEC 控制。"""
    return lambda: _pause(page)


# --- 報告 -------------------------------------------------------------


def pytest_html_report_title(report):
    report.title = "momo 購物流程自動化測試報告"


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    """pytest-playwright 開場會清掉產出目錄，而 pytest-html 不會自己建，
    全部通過時就會寫檔失敗。tryfirst 保證這裡先跑。"""
    _output_dir(session.config).mkdir(parents=True, exist_ok=True)
