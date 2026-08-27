"""momo 會員登入 / 登出，都走真實使用者流程。

登入：開首頁 → 點 header 的「登入」→ 在跳出的登入視窗（iframe）填帳密。
登出：開首頁 → 點 header 的「登出」，直接登出，沒有視窗。

header 上那顆按鈕登入前後是同一個元素，只是 data-testid 會換：
未登入是 header-login-button，登入後變成 header-logout-button。
所以「有沒有登入」直接看這顆按鈕現在是哪一個就好。
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.helpers import click_until
from pages.urls import HOME_URL


class LoginPage:
    LOGIN_ENTRY = '[data-testid="header-login-button"]'   # 未登入時的 header 按鈕
    LOGOUT_ENTRY = '[data-testid="header-logout-button"]'  # 登入後的 header 按鈕
    LOGIN_IFRAME = "iframe.loginIframe"                   # 登入視窗
    ACCOUNT_INPUT = "input.inputOrder0"                   # 帳號
    PASSWORD_INPUT = "input.inputOrder1"                  # 密碼
    SUBMIT_BUTTON = "a.login"                             # 登入視窗裡的「登入」
    ERROR_HINT = "span.hint"                              # 登入失敗的提示

    def __init__(self, page: Page):
        self.page = page

    def login(self, account: str, password: str):
        self.page.goto(HOME_URL, wait_until="domcontentloaded")
        click_until(self.page, self.LOGIN_ENTRY, self.LOGIN_IFRAME)

        form = self.page.frame_locator(self.LOGIN_IFRAME)
        form.locator(self.ACCOUNT_INPUT).fill(account)
        form.locator(self.PASSWORD_INPUT).fill(password)
        form.locator(self.SUBMIT_BUTTON).click()

        # 登入成功後 header 那顆按鈕會變成「登出」，這是使用者看得到的訊號
        try:
            self.page.locator(self.LOGOUT_ENTRY).wait_for(state="visible", timeout=60_000)
        except PlaywrightTimeoutError:
            raise AssertionError(
                f"登入失敗，header 沒有變成「登出」。站方訊息：{self._error_message() or '（無）'}"
            )

    def logout(self):
        self.page.goto(HOME_URL, wait_until="domcontentloaded")
        click_until(self.page, self.LOGOUT_ENTRY, self.LOGIN_ENTRY)

    def _error_message(self) -> str:
        hint = self.page.frame_locator(self.LOGIN_IFRAME).locator(self.ERROR_HINT)
        return hint.first.inner_text().strip() if hint.count() else ""


def is_logged_in(page: Page) -> bool:
    """header 那顆按鈕顯示「登出」就代表已登入。"""
    return page.locator(LoginPage.LOGOUT_ENTRY).count() > 0
