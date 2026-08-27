"""Page Object 共用的小工具。"""

import time

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

DEFAULT_TIMEOUT_SEC = 30
DEFAULT_TIMEOUT_MS = DEFAULT_TIMEOUT_SEC * 1000
# 點一次之後等多久才判定「這次沒生效、再點一次」。太短會在網路慢時重複點擊
# （例如結帳鈕被按兩次），太長則是真的沒生效時白等。
ATTEMPT_TIMEOUT_MS = 8_000
# 規格下拉選單「請選擇…」佔位選項的值
SPEC_PLACEHOLDER_VALUES = ("", "na")
# 一件商品最多處理幾組規格。純防呆，實際最多兩三組（顏色 + 尺寸）。
MAX_SPEC_GROUPS = 10
# 選規格的動作等多久。這些元素被挑中時就已經可按，正常瞬間完成，
# 用預設的 30 秒等於真的卡住時每一組都白等半分鐘。
SPEC_ACTION_TIMEOUT_MS = 8_000

# 算出「每一組規格的第一顆可按按鈕」在整份清單裡的索引。
# 同組按鈕共用父層，第一次看到某個父層時那顆就是該組的第一顆；disabled 跳過。
_FIRST_BUTTON_OF_EACH_GROUP = """elements => {
    const seen = new Set();
    const indexes = [];
    elements.forEach((element, i) => {
        if (element.disabled || element.getAttribute('aria-disabled') === 'true') return;
        if (seen.has(element.parentElement)) return;
        seen.add(element.parentElement);
        indexes.push(i);
    });
    return indexes;
}"""


def click_until(page: Page, trigger: str, expected: str, state: str = "attached",
                timeout_sec: int = DEFAULT_TIMEOUT_SEC):
    """一直點 trigger，直到 expected 進入指定狀態為止。

    momo 好幾個頁面（首頁 header、購物車）都有同一個問題：元素已經畫出來了，
    但 JS 事件還沒綁上去，太早點會完全沒反應也不會報錯。所以改成
    「點了就檢查有沒有效果，沒效果再點」，一成功就往下走。

    trigger 刻意不加 .first：選擇器同時命中兩顆時，要的是 strict mode 大聲報錯，
    而不是安靜地點到錯的那顆。timeout_sec 是總上限，每次嘗試都被剩餘時間夾住。
    """
    trigger_locator = page.locator(trigger)
    expected_locator = page.locator(expected).first
    deadline = time.monotonic() + timeout_sec
    def remaining_ms():
        return max(0, int((deadline - time.monotonic()) * 1000))

    def attempt_ms():
        return min(ATTEMPT_TIMEOUT_MS, remaining_ms())

    try:
        trigger_locator.wait_for(state="visible", timeout=remaining_ms())
    except PlaywrightTimeoutError:
        raise AssertionError(f"等了 {timeout_sec} 秒，{trigger} 一直沒有出現")

    click_error = None
    while True:
        try:
            trigger_locator.click(timeout=attempt_ms())
            click_error = None
        except PlaywrightTimeoutError as error:
            # 點不到通常代表上一輪其實成功了、trigger 已隨導頁消失，交給下面判定。
            # 但訊息要留著：真的被浮層擋住時，Playwright 會直接指出是誰擋的。
            click_error = error

        try:
            expected_locator.wait_for(state=state, timeout=attempt_ms())
            return
        except PlaywrightTimeoutError:
            pass

        if remaining_ms() == 0:
            message = f"點了 {trigger} 超過 {timeout_sec} 秒，{expected} 一直沒有變成 {state}"
            if click_error is not None:
                message += f"\n最後一次連點都沒點成：\n{click_error}"
            raise AssertionError(message)


def choose_first_spec(dropdowns: Locator, buttons: Locator):
    """把商品規格選起來，每一組都選第一個可選的。

    momo 的規格有兩種 UI，同一個關鍵字的結果也可能兩種都有，事前無法預測：
    組合商品（「2+6件組」）用 <select>，一般規格商品（「抗菌去漬」）用一排 button。
    沒選規格就按購買會被擋下來，而實測日用品關鍵字超過一半的第一項都需要選，
    所以這是常態，不能靠挑關鍵字迴避。

    測試在意的是走完購買流程，買到哪個規格不重要，一律選第一個可選的。
    """
    for i in range(dropdowns.count()):
        dropdown = dropdowns.nth(i)
        if dropdown.input_value() not in SPEC_PLACEHOLDER_VALUES:
            continue   # 已經選好了就別動，免得多觸發一次 onchange
        values = dropdown.locator("option").evaluate_all(
            "options => options.filter(o => !o.disabled).map(o => o.value)")
        choices = [v for v in values if v not in SPEC_PLACEHOLDER_VALUES]
        if choices:
            dropdown.select_option(choices[0], timeout=SPEC_ACTION_TIMEOUT_MS)

    # 一組一組處理，每組都重算索引：選完第一組後 momo 會重新渲染其餘幾組
    # （不可用的組合變成 disabled），沿用舊快照會點到錯的按鈕。
    # 只用 JS 算位置，實際點擊仍交給 Playwright，維持真實的使用者事件。
    for group in range(MAX_SPEC_GROUPS):
        first_of_each_group = buttons.evaluate_all(_FIRST_BUTTON_OF_EACH_GROUP)
        if group >= len(first_of_each_group):
            return
        buttons.nth(first_of_each_group[group]).click(timeout=SPEC_ACTION_TIMEOUT_MS)
