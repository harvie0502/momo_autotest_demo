"""購買流程。

兩個情境都從搜尋出發，差別在「從哪裡把商品買下去」：

    情境 1  從購物車購買：搜尋 → 第一項加入購物車 → 進購物車 → 結帳
    情境 2  從商品頁購買：搜尋 → 點進第一項商品 → 直接購買 → 結帳

共同的部分抽成兩個 helper：前面的搜尋（含關鍵字建議檢查），
以及後面的「從購物車結帳並確認到結帳頁」。
兩個情境的後置動作都是清空購物車，由 empty_cart fixture 負責。
"""

from data.test_data import SEARCH_KEYWORDS
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.header import Header
from pages.home_page import HomePage
from pages.product_page import ProductPage
from pages.search_result_page import SearchResultPage


def search_from_home(page, keyword) -> SearchResultPage:
    """從首頁搜尋關鍵字，回傳搜尋結果頁。

    對應兩個情境共同的步驟 1、2：
      1. 輸入文字時同步檢查是否有顯示關鍵字
      2. 跳到搜尋結果頁面
    """
    home = HomePage(page).open()
    home.type_keyword(keyword)

    suggestions = home.get_suggestions()
    assert suggestions, f"輸入「{keyword}」之後沒有出現任何關鍵字建議"
    assert all(keyword in s for s in suggestions), \
        f"關鍵字建議應該都要跟「{keyword}」相關，實際拿到：{suggestions}"

    home.submit_search()
    results = SearchResultPage(page).wait_until_loaded()
    assert "/search/" in page.url, f"沒有到搜尋結果頁，目前網址：{page.url}"
    assert results.product_count() > 0, f"搜尋「{keyword}」沒有任何結果"
    return results


def checkout_from_cart(page, pause, product_code, product_name):
    """在購物車確認商品在裡面，按結帳，並確認有到結帳頁。

    兩個情境最後都會走到購物車（情境 2 的「直接購買」也是先進購物車），
    所以這一段共用。

    結帳頁只檢查「訂購人資料在上面、確認結帳鈕在下面」，不會真的送出訂單。
    """
    cart = CartPage(page).wait_until_has_items()
    assert product_code in cart.product_numbers(), \
        f"購物車裡找不到商品 {product_code}（{product_name}），" \
        f"目前購物車有：{cart.product_numbers()}"
    cart.checkout()

    checkout = CheckoutPage(page).wait_until_loaded()
    checkout.scroll_to_submit_button()   # 往下滑到結帳鈕，跟使用者一樣
    pause()                              # 有頭模式停一下，方便人眼確認結帳頁

    assert "訂購人資料" in checkout.visible_sections(), \
        f"結帳頁最上方應該是訂購人資料，實際找到的區塊：{checkout.visible_sections()}"
    assert checkout.has_submit_button(), \
        f"結帳頁上找不到「確認結帳」按鈕（商品：{product_name}）"


def test_buy_from_cart(page, empty_cart, pause):
    """情境 1：搜尋後把第一項商品加入購物車，再從購物車結帳。"""
    results = search_from_home(page, SEARCH_KEYWORDS["tissue"])

    # 3. 選擇第一項產品加入購物車
    #    加入前先記下 header 的件數，加入後看它有沒有加一——比斷言絕對值可靠，
    #    購物車本來有沒有東西都不影響。
    header = Header(page)
    count_before = header.cart_count()

    product_name = results.first_product_name()
    product_code = results.first_product_code()
    results.add_first_product_to_cart()
    header.wait_for_cart_count(count_before + 1)

    # 4. 從購物車進行結帳    5. 檢查是否正常到結帳頁面
    header.open_cart()
    checkout_from_cart(page, pause, product_code, product_name)


def test_buy_from_product_page(page, empty_cart, pause):
    """情境 2：搜尋後點進第一項商品，從商品頁直接購買。"""
    results = search_from_home(page, SEARCH_KEYWORDS["detergent"])

    # 3. 點擊第一項產品
    product_code = results.first_product_code()
    product_name = results.open_first_product()

    # 4. 檢查是否到產品頁，而且是剛剛點的那一件
    product = ProductPage(page).wait_until_loaded()
    assert product.product_code() == product_code, \
        f"點進來的商品頁不是搜尋結果第一項：{product.product_code()} != {product_code}"
    assert product.is_in_stock(), f"「{product_name}」目前是售完補貨中，買不了"

    # 5. 點擊購買並確認是否到結帳頁面
    #    momo 的「直接購買」會先把商品帶到購物車頁，再按「結帳」才進結帳頁
    product.buy_now()
    checkout_from_cart(page, pause, product_code, product_name)
