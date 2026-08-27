"""搜尋結果頁。

商品清單的結構（momo 有給每張卡片可辨識的 id）：

    <ul class="listAreaUl">
      <li class="listAreaLi" id="search-goods-item-0">
        <input name="viewProdId" value="3252331">      <- 商品編號
        <div class="btnArea"><a class="addToCart">     <- 卡片上的購物車鈕
        <h3 class="prdName"><a class="prdName">...     <- 商品名稱

點卡片上的購物車鈕不會直接加入，會先跳出「請選擇商品規格」的視窗，
在那裡再按一次「加入購物車」才真的加進去。
"""

from playwright.sync_api import Page

from pages.helpers import choose_first_spec
from pages.urls import PRODUCT_URL_PATTERN


class SearchResultPage:
    PRODUCT_CARD = "li.listAreaLi"
    PRODUCT_NAME = "a.prdName"
    PRODUCT_CODE = "input[name='viewProdId']"
    ADD_TO_CART_BUTTON = "a.addToCart"

    SPEC_DIALOG = "div.prdTypeArea-box"          # 請選擇商品規格
    SPEC_DROPDOWN = "select"                     # 視窗裡的 select 全是規格
    SPEC_BUTTON = "button.f2e-spec-button"       # 按鈕方塊式的規格
    SPEC_CONFIRM_BUTTON = "a.enterBtn"           # 視窗裡的「加入購物車」

    def __init__(self, page: Page):
        self.page = page

    def wait_until_loaded(self):
        """等到第一張商品卡片可見才算載入完成。

        只等 URL 不夠：momo 的商品清單是前端渲染的，URL 對了但卡片還沒出來，
        後面的點擊就會撲空。
        """
        self.page.locator(self.PRODUCT_CARD).first.wait_for(state="visible")
        return self

    def product_count(self) -> int:
        return self.page.locator(self.PRODUCT_CARD).count()

    def first_card(self):
        return self.page.locator(self.PRODUCT_CARD).first

    def first_product_name(self) -> str:
        return self.first_card().locator(self.PRODUCT_NAME).first.inner_text().strip()

    def first_product_code(self) -> str:
        return self.first_card().locator(self.PRODUCT_CODE).first.input_value()

    def open_first_product(self) -> str:
        """點第一項商品進到商品頁，回傳商品名稱。"""
        name = self.first_product_name()
        card = self.first_card()
        card.scroll_into_view_if_needed()
        card.locator(self.PRODUCT_NAME).first.click()
        self.page.wait_for_url(PRODUCT_URL_PATTERN, wait_until="domcontentloaded")
        return name

    def add_first_product_to_cart(self):
        """把第一項商品加入購物車。

        加入是非同步的，這裡只等規格視窗關閉（代表送出了）。
        「真的加進去了」要看 header 的購物車數字，由呼叫端用
        Header.wait_for_cart_count() 確認。
        """
        card = self.first_card()
        card.scroll_into_view_if_needed()
        # 購物車鈕平常是藏起來的，滑鼠移到卡片上才會顯示
        card.hover()
        card.locator(self.ADD_TO_CART_BUTTON).first.click()

        dialog = self.page.locator(self.SPEC_DIALOG)
        dialog.wait_for(state="visible")
        choose_first_spec(dialog.locator(self.SPEC_DROPDOWN),
                          dialog.locator(self.SPEC_BUTTON))
        dialog.locator(self.SPEC_CONFIRM_BUTTON).click()
        dialog.wait_for(state="detached")
