#!/usr/bin/env python3
"""
私募产品导入脚本 - 直接调用 Railway API
"""
import json
import urllib.request
import urllib.error
import ssl

API_URL = "https://fintrack-api-production-879c.up.railway.app"

PRODUCTS = [
    {"name": "赫富城盈500指数增强二号A类", "code": "BNZ44A", "strategy_type": "量化指增", "risk_level": "R4", "lock_period": "180天/短期", "open_period": "成立后每周最后一个交易日为固定开放日，如本周无交易日，则本周不开放", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "星阔城盈自由现金流指数增强1号A类", "code": "BFE74A", "strategy_type": "量化指增", "risk_level": "R4", "lock_period": "180天/短期", "open_period": "成立后每周最后一个交易日为固定开放日，如本周无交易日，则本周不开放", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "以自由现金流指数（980092.CNI）为业绩基准，年化超额收益率≤4%或年化收益率≤0%，不计提；年化超额收益率＞4%且年化收益率＞0%，对年化超额收益率超出4%的部分按照【20%】的比例提取"},
    {"name": "星阔城盈红利低波100指数增强1号", "code": "SAZY92", "strategy_type": "量化指增", "risk_level": "R4", "lock_period": "180天/短期", "open_period": "成立后每周最后一个交易日为固定开放日，如本周无交易日，则本周不开放", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "以中证红利低波动100指数（930955.CSI）实际收益率为业绩基准，提取超额收益*20%(以份额取得的正收益为限)"},
    {"name": "和谐汇一医疗创新城盈1号A类", "code": "AXH68A", "strategy_type": "主观多头", "risk_level": "R5", "lock_period": "180天/短期", "open_period": "每周周三为固定开放日（遇非交易日顺延至当周下一个交易日（如有））", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "年化收益率5%以上提取20%，5%以下不提取"},
    {"name": "和谐汇一高端制造城盈1号", "code": "SAKD49", "strategy_type": "主观多头", "risk_level": "R5", "lock_period": "180天/短期", "open_period": "每月15日（遇非交易日顺延）和每月最后一个交易日为固定开放日", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "年化收益率5%以上提取20%，5%以下不提取"},
    {"name": "赫富城盈中证1000量化指数增强一号A类", "code": "ADL53A", "strategy_type": "量化指增", "risk_level": "R4", "lock_period": "365天/短期", "open_period": "每月10日为固定开放日（遇非交易日顺延）", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "当超额年化收益率≤6%或绝对收益率≤0%时：不提取；当超额年化收益率＞6%且绝对收益率＞0%时：仅对超额年化收益率超过6%的部分提取40%"},
    {"name": "启林城盈1000指数增强一号", "code": "SSZ753", "strategy_type": "量化指增", "risk_level": "R4", "lock_period": "365天/短期", "open_period": "每月15日为固定开放日（遇非交易日顺延）", "sales_coefficient": 0.5, "holding_coefficient": 1.2, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "中原财富-金石36期-凡二城盈", "code": "ZY0E9L", "strategy_type": "量化指增", "risk_level": "R4", "lock_period": "365天/短期", "open_period": "每月25日为固定开放日（遇非交易日顺延）", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益18%（含底层私募提取绝对收益16%）"},
    {"name": "星阔城盈中证1000指数增强一号A类", "code": "ST308A", "strategy_type": "量化指增", "risk_level": "R4", "lock_period": "180天/短期", "open_period": "每周最后一个交易日为固定开放日", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取超额收益*20%"},
    {"name": "凯纳靖戈城盈500增强一号", "code": "SQJ053", "strategy_type": "量化指增", "risk_level": "R5", "lock_period": "180天/短期", "open_period": "每月5日为固定开放日（遇非交易日顺延）", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "赫富城盈500指数增强一号A期", "code": "SQJ012", "strategy_type": "量化指增", "risk_level": "R5", "lock_period": "365天，持有不满730天需要收1%赎回费/短期", "open_period": "每月5日为固定开放日（遇非交易日顺延）", "sales_coefficient": 1.5, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "凯纳靖戈城盈500增强二号", "code": "SSF081", "strategy_type": "量化指增", "risk_level": "R4", "lock_period": "180天/短期", "open_period": "每月15日为固定开放日（遇非交易日顺延）", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "百瑞信托-聚宽城盈500增强1号", "code": "BR001S", "strategy_type": "量化指增", "risk_level": "R5", "lock_period": "180天/短期", "open_period": "每月20日为固定开放日（遇非交易日顺延）", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "因诺城盈300增强一号", "code": "SQN497", "strategy_type": "量化指增", "risk_level": "R5", "lock_period": "365天/短期", "open_period": "每月5日为固定开放日（遇非交易日顺延）", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "因诺城盈量化选股7号1期", "code": "SSU225", "strategy_type": "量化选股", "risk_level": "R4", "lock_period": "365天/短期", "open_period": "每月10日、25日为固定开放日\n（遇非交易日顺延）", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "优美利城盈金安长牛1号A类", "code": "AFN26A", "strategy_type": "其他", "risk_level": "R4", "lock_period": "180天/短期", "open_period": "每周周五为固定开放日（遇非交易日顺延）", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "天算城盈指增保护1号A类", "code": "BCC75A", "strategy_type": "其他", "risk_level": "R4", "lock_period": "180天/短期", "open_period": "成立后每周最后一个交易日为固定开放日，如本周无交易日，则本周不开放。", "sales_coefficient": 2.5, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "宁水城盈一期A类", "code": "AWV64A", "strategy_type": "其他", "risk_level": "R4", "lock_period": "180天/短期", "open_period": "每周周五为固定开放日（遇非交易日不顺延）", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": 0.5, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "尚艺城盈全天候稳健1号A类", "code": "AJR68A", "strategy_type": "全天候策略", "risk_level": "R3", "lock_period": "365天/短期", "open_period": "申购开放日为每周三，如遇非交易日不予顺延；赎回开放日为每月第2个和第4个周三，如遇非交易日不予顺延。", "sales_coefficient": 1.5, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "年化收益率5%以上提取40%，5%以下不提取"},
    {"name": "优美利城盈灵活配置12号A类", "code": "BLL07A", "strategy_type": "其他", "risk_level": "R3", "lock_period": "180天/短期", "open_period": "每周最后一个交易日为固定开放日，如遇节假日，则不予顺延", "sales_coefficient": 1.5, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "天宝城盈套利一期", "code": "SQR972", "strategy_type": "其他", "risk_level": "R4", "lock_period": "365天/短期", "open_period": "每日开放", "sales_coefficient": 1.5, "holding_coefficient": 2.0, "subscription_fee": 0.5, "service_fee": None, "management_fee": 2.0, "performance_fee": "提取绝对收益25%"},
    {"name": "天宝城盈套利二期", "code": "STR262", "strategy_type": "其他", "risk_level": "R3", "lock_period": "365天/短期", "open_period": "每日开放", "sales_coefficient": 1.5, "holding_coefficient": 2.0, "subscription_fee": 0.5, "service_fee": None, "management_fee": 2.0, "performance_fee": "提取绝对收益25%"},
    {"name": "天宝城盈套利十期", "code": "SATZ00", "strategy_type": "其他", "risk_level": "R3", "lock_period": "360天/短期", "open_period": "每周周三为固定开放日（遇非交易日不顺延）", "sales_coefficient": 1.5, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 2.0, "performance_fee": "提取绝对收益25%"},
    {"name": "中原财富-金石33期-天宝城盈2号", "code": "ZY0FXR", "strategy_type": "其他", "risk_level": "R3", "lock_period": "365天/短期", "open_period": "每周周三为固定开放日（遇非交易日顺延）", "sales_coefficient": 1.5, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益5%"},
    {"name": "乾元城盈套利一期", "code": "SACP52", "strategy_type": "其他", "risk_level": "R3", "lock_period": "180天/短期", "open_period": "每周周三为固定开放日（遇非交易日顺延）", "sales_coefficient": 1.5, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "当年化收益率≤6%时，提取比例为25%；\n年化收益率>6%时，对低于等于6%的部分按25%的比例进行提取，对超过6%的部分按35%的比例进行提取。"},
    {"name": "赫富跃升中证1000量化指数增强2号", "code": "SBBU37", "strategy_type": "量化指增", "risk_level": "R4", "lock_period": "180天/短期", "open_period": "成立后每周最后一个交易日为固定开放日", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "提取绝对收益20%"},
    {"name": "长信基金-金选CTA多策略1号", "code": "301188", "strategy_type": "其他", "custom_strategy": "CTA多策略", "risk_level": "R4", "lock_period": "180天/短期", "open_period": "每月开放", "sales_coefficient": 2.0, "holding_coefficient": 1.0, "subscription_fee": None, "service_fee": 1.0, "management_fee": 1.0, "performance_fee": "超额收益20%"},
]


def check_api():
    """检查 API 是否可用"""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(f"{API_URL}/health", method='GET')
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"API 检查失败: {e}")
        return False


def create_product(product):
    """创建一个产品"""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        data = json.dumps(product).encode('utf-8')
        req = urllib.request.Request(
            f"{API_URL}/api/private-fund/products",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            if resp.status == 200:
                return True, "成功"
            else:
                return False, f"HTTP {resp.status}"

    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        if "已存在" in error_msg:
            return True, "已存在"
        return False, f"HTTP {e.code}: {error_msg}"
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("私募产品导入工具")
    print(f"目标 API: {API_URL}")
    print("=" * 60)
    print()

    # 检查 API
    if not check_api():
        print("❌ API 连接失败，请检查网络或 API 地址")
        return

    print("✅ API 连接正常")
    print()

    # 导入产品
    success = 0
    failed = 0
    existed = 0

    for i, product in enumerate(PRODUCTS, 1):
        ok, msg = create_product(product)
        if ok:
            if msg == "已存在":
                print(f"[{i}/{len(PRODUCTS)}] ⚠️  {product['code']} - 已存在")
                existed += 1
            else:
                print(f"[{i}/{len(PRODUCTS)}] ✅ {product['code']} - {product['name'][:20]}...")
                success += 1
        else:
            print(f"[{i}/{len(PRODUCTS)}] ❌ {product['code']} - {msg}")
            failed += 1

    print()
    print("=" * 60)
    print(f"导入完成: 新增 {success} 个, 已存在 {existed} 个, 失败 {failed} 个")
    print("=" * 60)


if __name__ == "__main__":
    main()
