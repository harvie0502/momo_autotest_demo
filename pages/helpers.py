"""Page Object 共用的小工具。"""

import time

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

DEFAULT_TIMEOUT_SEC = 30
# 規格下拉選單第一個選項是「請選擇…」的佔位，值長這兩種
SPEC_PLACEHOLDER_VALUES = ("", "na")


def click_until(page: Page, trigger: str, expected: str, state: str = "attached",
                timeout_sec: int = DEFAULT_TIMEOUT_SEC):
    """一直點 trigger，直到 expected 進入指定狀態為止。

    momo 好幾個頁面（首頁的 header、購物車）都有同一個問題：元素已經畫出來了，
    但 JS 事件還沒綁上去，太早點會完全沒反應、也不會報錯。

    用「點了就檢查有沒有效果，沒效果再點」取代盲等一個固定秒數：
    一成功就往下走，真的有問題才會等到逾時。
    """
    trigger_locator = page.locator(trigger)
    expected_locator = page.locator(expected)
    trigger_locator.wait_for(state="visible")

    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        trigger_locator.click()
        try:
            expected_locator.first.wait_for(state=state, timeout=3_000)
            return
        except PlaywrightTimeoutError:
            continue
    raise AssertionError(
        f"點了 {trigger} 超過 {timeout_sec} 秒，{expected} 一直沒有變成 {state}"
    )


def choose_first_spec(dropdowns: Locator, buttons: Locator):
    """把還沒選的商品規格選起來，一律選第一個可選的。

    momo 的規格有兩種 UI，同一個關鍵字的搜尋結果也可能兩種都有，事前無法預測：

        下拉選單  組合商品（例如「2+6件組」）用 <select>，未選時的值是 "" 或 "na"
        按鈕方塊  一般規格商品（例如「抗菌去漬 / 室內晾乾」）用一排 button

    沒選規格就按購買 / 加入購物車會被 momo 擋下來，而實測日用品關鍵字有超過一半
    的第一項需要選規格，所以這是常態，不能靠挑關鍵字迴避。

    測試在意的是走完購買流程，買到哪一個規格不重要，所以一律選第一個可選的。
    商品有多組規格（例如顏色 + 尺寸）時，每一組都各選第一個。
    """
    for i in range(dropdowns.count()):
        dropdown = dropdowns.nth(i)
        values = dropdown.locator("option").evaluate_all(
            "options => options.filter(o => !o.disabled).map(o => o.value)")
        choices = [v for v in values if v not in SPEC_PLACEHOLDER_VALUES]
        if choices:
            dropdown.select_option(choices[0])

    # 同一組規格的按鈕放在同一個父層。這裡只用 JS 算出「每組第一顆」的位置，
    # 實際點擊仍然交給 Playwright，維持真實的使用者事件。
    first_of_each_group = buttons.evaluate_all("""elements => {
        const seen = new Set();
        const indexes = [];
        elements.forEach((element, i) => {
            if (!seen.has(element.parentElement)) {
                seen.add(element.parentElement);
                indexes.push(i);
            }
        });
        return indexes;
    }""")
    for i in first_of_each_group:
        buttons.nth(i).click()
