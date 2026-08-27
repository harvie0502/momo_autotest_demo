"""測試層級的 fixture。"""

import pytest

from pages.cart_page import CartPage
from pages.header import Header
from pages.home_page import HomePage


def clear_cart(page):
    """清空購物車：從首頁點 header 的購物車進去，按「全部刪除」。

    不看 header 的數字來決定要不要進去——那個數字剛載入時是伺服器給的 0，
    讀太早會誤判成「本來就是空的」。直接進購物車看有沒有商品列最準。
    """
    HomePage(page).open()
    Header(page).open_cart()
    cart = CartPage(page)
    if cart.has_items():
        cart.delete_all()


@pytest.fixture
def empty_cart(page):
    """後置動作：清空購物車內容。"""
    yield
    clear_cart(page)
