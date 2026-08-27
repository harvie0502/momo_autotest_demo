"""測試層級的 fixture。"""

import pytest

from pages.cart_page import CartPage
from pages.header import Header
from pages.home_page import HomePage


def clear_cart(page):
    """清空購物車：從首頁點 header 的購物車進去，按「全部刪除」。

    不看 header 的數字決定要不要進去——那個數字剛載入時是伺服器給的 0，
    讀太早會誤判成「本來就是空的」。
    """
    HomePage(page).open()
    Header(page).open_cart()
    cart = CartPage(page)
    if cart.has_items():
        cart.delete_all()


@pytest.fixture
def clear_cart_after_test(page):
    """後置動作：測試結束後清空購物車。

    刻意只做後置。整包共用同一個 page，購物車是跨測試的共用狀態，
    每個測試自己收乾淨，下一個才不會被影響。
    """
    yield
    clear_cart(page)
