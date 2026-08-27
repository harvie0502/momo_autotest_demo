"""momo 的網址與網址樣式。

momo 把功能切在不同 host 上，這裡集中定義，避免散落在各個 Page Object：
    www.momoshop.com.tw   首頁 / 搜尋結果 / 商品頁
    cart.momoshop.com.tw  購物車與結帳

只有首頁需要完整網址（使用者打開網站的起點），站內其他頁面一律用點擊進入，
所以下面只留「等導頁結果」用的網址樣式。這些頁面的網址都帶一堆行銷參數，
用樣式比對比寫死完整網址耐得住變動。
"""

HOME_URL = "https://www.momoshop.com.tw/main/Main.jsp"

SEARCH_URL_PATTERN = "**/search/**"
PRODUCT_URL_PATTERN = "**/product/**"
CART_URL_PATTERN = "**/view/cart/**"
