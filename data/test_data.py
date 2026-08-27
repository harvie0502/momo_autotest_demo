"""測試資料，腳本用名稱取用，不同測試可以吃到不同的搜尋詞。

挑關鍵字的原則：日用品，長年有貨、結果多。第一項商品需不需要選規格不用管，
框架會自動處理（見 pages/helpers.py 的 choose_first_spec）。
"""

SEARCH_KEYWORDS = {
    "tissue": "衛生紙",
    "detergent": "洗衣精",
}
