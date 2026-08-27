"""測試資料集中在這裡，腳本用名稱取用，不同測試就能吃到不同的搜尋詞。

用法：
    from data.test_data import SEARCH_KEYWORDS
    keyword = SEARCH_KEYWORDS["tissue"]

挑關鍵字的原則：日用品類，長年有貨、結果多，才不會因為缺貨讓測試無謂地紅掉。
第一項商品是不是需要選規格的組合包不用管，框架會自動處理（見 pages/helpers.py
的 choose_first_spec）。
"""

SEARCH_KEYWORDS = {
    "tissue": "衛生紙",
    "detergent": "洗衣精",
    "water": "礦泉水",
    "toothpaste": "牙膏",
}
