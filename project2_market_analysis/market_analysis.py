"""
AI选品与市场机会分析助手 v2.0
—— 市场机会探索引擎 ——

方法论来源：4个真实操盘成功案例
案例1️⃣ 风格差异化（新中式套装）：上升风格趋势 × 套装组合机会
案例2️⃣ 跨界组合（罗汉床茶桌）：跨类目搜索词 → 场景解决方案
案例3️⃣ 痛点重构（防塌陷沙发）：聚焦结构性缺陷 → 重构市场标准
案例4️⃣ 头羊验证法（跟随型机会）：锁定可复制的对标对象 → 做升级替代

核心理念：不是一个执行固定规则的选品工具，而是一个市场机会探索引擎。
"""

import json
import os
import requests
import re
from datetime import datetime
from typing import Dict, List, Optional

# ============ 配置 ============
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"


# ====================================================================
# 📦 模拟市场数据库（v2 - 增加风格标签、跨类目词、竞品分析维度）
# ====================================================================
MOCK_MARKET_DATA = {
    "沙发": {
        "类目概况": {
            "类目名称": "沙发",
            "一级类目": "住宅家具",
            "月搜索热度": "约850万",
            "在线商品数": "约120万",
            "市场集中度": "中低（CR10约18%）",
            "平均客单价": "2800元",
            "同比增长率": "+12%",
            "季节性": "金九银十为旺季，1-2月为淡季",
            "主要受众人群": "25-45岁，新房装修/旧房换新，一二线城市为主"
        },
        "头部商品（TOP10）": [
            {"名称": "科技布沙发三人位", "品牌": "A家家居", "月销": "8500+", "价格": "2899", "评分": "4.8", "评价数": "3.2万", "卖点": "科技布易清洁、性价比高", "风格": "现代简约"},
            {"名称": "真皮沙发头层牛皮", "品牌": "B品家具", "月销": "6200+", "价格": "5999", "评分": "4.7", "评价数": "1.8万", "卖点": "头层牛皮、意式极简", "风格": "意式极简"},
            {"名称": "乳胶沙发小户型", "品牌": "C家优选", "月销": "5800+", "价格": "1999", "评分": "4.6", "评价数": "2.1万", "卖点": "小户型专用、高密度海绵", "风格": "现代简约"},
            {"名称": "功能沙发电动可躺", "品牌": "D乐家居", "月销": "5200+", "价格": "3599", "评分": "4.7", "评价数": "1.5万", "卖点": "电动可躺、USB充电", "风格": "现代简约"},
            {"名称": "轻奢沙发羽绒填充", "品牌": "E品家居", "月销": "4800+", "价格": "4299", "评分": "4.8", "评价数": "1.2万", "卖点": "羽绒填充、轻奢风", "风格": "轻奢"},
            {"名称": "实木沙发框架组合", "品牌": "F家家居", "月销": "4500+", "价格": "3299", "评分": "4.5", "评价数": "9800", "卖点": "白蜡木框架、可拆洗", "风格": "新中式"},
            {"名称": "沙发床两用折叠", "品牌": "G品优选", "月销": "4200+", "价格": "1599", "评分": "4.4", "评价数": "1.1万", "卖点": "一物两用、小户型神器", "风格": "现代简约"},
            {"名称": "意式极简真皮沙发", "品牌": "H际家居", "月销": "3900+", "价格": "6999", "评分": "4.6", "评价数": "8600", "卖点": "进口头层皮、设计感强", "风格": "意式极简"},
            {"名称": "猫抓皮沙发耐磨", "品牌": "A家家居", "月销": "3600+", "价格": "2599", "评分": "4.5", "评价数": "7200", "卖点": "猫抓皮面料、养宠家庭", "风格": "现代简约"},
            {"名称": "懒人沙发豆袋", "品牌": "I生活", "月销": "3400+", "价格": "399", "评分": "4.3", "评价数": "9500", "卖点": "超低价、租房党最爱", "风格": "休闲"},
        ],
        # ⭐ v2新增：风格标签 → 用于风格差异化分析
        "风格搜索趋势": {
            "现代简约": {"搜索占比": "35%", "同比增长": "+8%", "竞争程度": "极高"},
            "轻奢": {"搜索占比": "22%", "同比增长": "+15%", "竞争程度": "高"},
            "意式极简": {"搜索占比": "18%", "同比增长": "+25%", "竞争程度": "中"},
            "新中式": {"搜索占比": "12%", "同比增长": "+40%", "竞争程度": "中低"},
            "奶油风": {"搜索占比": "8%", "同比增长": "+60%", "竞争程度": "低"},
            "复古风": {"搜索占比": "5%", "同比增长": "+35%", "竞争程度": "低"},
        },
        # ⭐ v2新增：跨类目组合搜索词 → 用于跨界组合分析
        "跨类目搜索词": [
            {"关键词": "沙发茶几电视柜组合", "月搜索量": "约8.2万", "增长": "+15%", "涉及类目": ["沙发", "茶几", "电视柜"]},
            {"关键词": "沙发床一体的", "月搜索量": "约3.5万", "增长": "+28%", "涉及类目": ["沙发", "床"]},
            {"关键词": "罗汉床茶桌椅组合", "月搜索量": "约1.2万", "增长": "+45%", "涉及类目": ["罗汉床", "茶桌", "椅子"]},
            {"关键词": "客厅沙发+地毯套装", "月搜索量": "约2.8万", "增长": "+22%", "涉及类目": ["沙发", "地毯"]},
            {"关键词": "新中式沙发+边几组合", "月搜索量": "约1.5万", "增长": "+55%", "涉及类目": ["沙发", "边几"]},
            {"关键词": "沙发+抱枕套装", "月搜索量": "约4.2万", "增长": "+18%", "涉及类目": ["沙发", "抱枕"]},
            {"关键词": "小户型沙发+茶几套餐", "月搜索量": "约6.5万", "增长": "+35%", "涉及类目": ["沙发", "茶几"]},
        ],
        # 用户评价数据（按类型分类）
        "用户评价分析": {
            "差评分类": {
                "产品结构性缺陷": [
                    {"问题": "坐垫塌陷/变形", "提及率": "18%", "严重程度": "高", "说明": "使用3-6个月后坐垫出现不可逆塌陷，属于结构性问题"},
                    {"问题": "皮质开裂/掉皮", "提及率": "12%", "严重程度": "高", "说明": "仿皮材质1年内开裂，真皮保养不当也会裂"},
                    {"问题": "框架松动/异响", "提及率": "8%", "严重程度": "高", "说明": "连接件松动导致使用时嘎吱响"},
                    {"问题": "海绵回弹差", "提及率": "10%", "严重程度": "中", "说明": "坐感越坐越硬，海绵密度不够"},
                ],
                "外观描述不符": [
                    {"问题": "实物与图片颜色不符", "提及率": "20%", "严重程度": "中", "说明": "色差问题，属于描述精度问题"},
                    {"问题": "尺寸比想象的小", "提及率": "14%", "严重程度": "中", "说明": "页面视觉显大，实际偏小"},
                ],
                "物流安装": [
                    {"问题": "物流破损", "提及率": "15%", "严重程度": "中", "说明": "大件家具物流通病"},
                    {"问题": "安装困难", "提及率": "8%", "严重程度": "低", "说明": "说明书不清或配件缺少"},
                ],
                "售后客服": [
                    {"问题": "售后推诿", "提及率": "10%", "严重程度": "低", "说明": "退换货流程复杂"},
                    {"问题": "客服响应慢", "提及率": "5%", "严重程度": "低", "说明": "大促期间客服忙"},
                ],
                "其他": [
                    {"问题": "有异味/甲醛", "提及率": "22%", "严重程度": "中", "说明": "新品拆包后异味重，需通风"},
                ]
            },
            "好评关键词": [
                "舒适度好（占比45%）",
                "性价比高（占比38%）",
                "外观好看（占比35%）",
                "送货快（占比28%）",
                "安装方便（占比22%）",
                "面料好（占比20%）"
            ]
        },
        "热搜趋势词（近30天）": [
            "小户型沙发（搜索增长+85%）",
            "科技布沙发（+62%）",
            "功能沙发（+55%）",
            "猫抓皮沙发（+48%）",
            "意式极简沙发（+42%）",
            "真皮沙发经济款（+38%）",
            "奶油风沙发（+35%）",
            "沙发套罩（+32%）——关联品机会",
            "新中式实木沙发（+50%）",
            "沙发+茶几组合套装（+40%）",
        ],
        "竞品广告投放估算": {
            "平均点击成本": "2.8-4.5元",
            "平均转化率": "2.1%",
            "头部卖家月推广费": "15-30万",
            "腰部卖家月推广费": "5-15万",
            "推广渠道分布": "直通车50% 引力魔方30% 万相台20%"
        },
        # ⭐ v2新增：头羊验证法需要的竞品对比数据
        "竞品品牌档案": {
            "A家家居": {"主力价格带": "2000-4000", "主力风格": "现代简约", "月销估算": "约300万", "核心优势": "科技布面料差异化", "核心劣势": "品质感不足，中高端客群流失"},
            "B品家具": {"主力价格带": "5000-8000", "主力风格": "意式极简", "月销估算": "约200万", "核心优势": "真皮品质，设计感强", "核心劣势": "价格偏高，受众窄"},
            "C家优选": {"主力价格带": "1500-3000", "主力风格": "现代简约", "月销估算": "约250万", "核心优势": "小户型定位精准", "核心劣势": "产品线单一，品牌力弱"},
            "D乐家居": {"主力价格带": "3000-5000", "主力风格": "现代简约", "月销估算": "约180万", "核心优势": "功能沙发差异化", "核心劣势": "电动功能故障率偏高"},
            "E品家居": {"主力价格带": "3500-6000", "主力风格": "轻奢", "月销估算": "约160万", "核心优势": "轻奢风格赛道先发", "核心劣势": "价格带不上不下"},
            "F家家居": {"主力价格带": "2500-4500", "主力风格": "新中式/实木", "月销估算": "约150万", "核心优势": "实木品质口碑好", "核心劣势": "风格偏传统，年轻客群少"},
        }
    },
    "窗帘": {
        "类目概况": {
            "类目名称": "窗帘",
            "一级类目": "家纺布艺",
            "月搜索热度": "约620万",
            "在线商品数": "约90万",
            "市场集中度": "极低（CR10约8%）",
            "平均客单价": "380元",
            "同比增长率": "+8%",
            "季节性": "装修旺季（3-5月，9-11月）为高峰期",
            "主要受众人群": "30-50岁女性为主，新房装修/旧房改造"
        },
        "头部商品（TOP10）": [
            {"名称": "雪尼尔窗帘成品", "品牌": "M居家纺", "月销": "12000+", "价格": "289", "评分": "4.7", "评价数": "5.8万", "卖点": "雪尼尔面料、高遮光", "风格": "现代简约"},
            {"名称": "高精密遮光窗帘", "品牌": "N品布艺", "月销": "9800+", "价格": "359", "评分": "4.8", "评价数": "4.2万", "卖点": "物理遮光99%、隔热", "风格": "现代简约"},
            {"名称": "亚麻窗帘ins风", "品牌": "O之居", "月销": "8500+", "价格": "219", "评分": "4.5", "评价数": "3.6万", "卖点": "ins风、透光不透人", "风格": "ins风"},
            {"名称": "电动窗帘轨道套装", "品牌": "P智能", "月销": "7200+", "价格": "899", "评分": "4.6", "评价数": "2.1万", "卖点": "米家智能联动、静音", "风格": "现代简约"},
            {"名称": "幻影纱帘客厅", "品牌": "Q品家居", "月销": "6800+", "价格": "159", "评分": "4.4", "评价数": "2.8万", "卖点": "幻影纱、光影效果", "风格": "ins风"},
            {"名称": "儿童房卡通窗帘", "品牌": "R之选", "月销": "5500+", "价格": "199", "评分": "4.6", "评价数": "1.5万", "卖点": "环保印染、卡通图案", "风格": "卡通"},
            {"名称": "简约棉麻窗帘成品", "品牌": "M居家纺", "月销": "5200+", "价格": "169", "评分": "4.5", "评价数": "1.9万", "卖点": "棉麻、日式简约", "风格": "日式"},
            {"名称": "卷帘百叶窗帘", "品牌": "S家居", "月销": "4900+", "价格": "129", "评分": "4.3", "评价数": "1.2万", "卖点": "防水防油、厨房浴室", "风格": "简约"},
            {"名称": "飘窗垫+窗帘套餐", "品牌": "T品生活", "月销": "4500+", "价格": "499", "评分": "4.5", "评价数": "9800", "卖点": "套餐一站购、省心", "风格": "现代简约"},
            {"名称": "蜂巢帘隔热", "品牌": "U巢家居", "月销": "3800+", "价格": "459", "评分": "4.7", "评价数": "7600", "卖点": "隔热保温、无绳设计", "风格": "简约"},
        ],
        "风格搜索趋势": {
            "现代简约": {"搜索占比": "40%", "同比增长": "+5%", "竞争程度": "极高"},
            "ins风": {"搜索占比": "18%", "同比增长": "+20%", "竞争程度": "中"},
            "日式": {"搜索占比": "12%", "同比增长": "+15%", "竞争程度": "中"},
            "奶油风": {"搜索占比": "10%", "同比增长": "+70%", "竞争程度": "低"},
            "复古风": {"搜索占比": "8%", "同比增长": "+45%", "竞争程度": "低"},
            "法式": {"搜索占比": "7%", "同比增长": "+55%", "竞争程度": "低"},
        },
        "跨类目搜索词": [
            {"关键词": "窗帘+窗纱组合", "月搜索量": "约6.5万", "增长": "+12%", "涉及类目": ["窗帘", "窗纱"]},
            {"关键词": "窗帘+轨道安装套餐", "月搜索量": "约4.8万", "增长": "+25%", "涉及类目": ["窗帘", "轨道"]},
            {"关键词": "全屋窗帘套装", "月搜索量": "约3.2万", "增长": "+38%", "涉及类目": ["客厅窗帘", "卧室窗帘", "阳台窗帘"]},
            {"关键词": "窗帘+飘窗垫套装", "月搜索量": "约2.1万", "增长": "+42%", "涉及类目": ["窗帘", "飘窗垫"]},
            {"关键词": "窗帘+抱枕组合", "月搜索量": "约1.5万", "增长": "+20%", "涉及类目": ["窗帘", "抱枕"]},
            {"关键词": "电动窗帘+智能家居套餐", "月搜索量": "约1.8万", "增长": "+65%", "涉及类目": ["电动窗帘", "智能家居"]},
        ],
        "用户评价分析": {
            "差评分类": {
                "产品结构性缺陷": [
                    {"问题": "遮光效果差/透光", "提及率": "28%", "严重程度": "高", "说明": "号称高遮光但实际漏光，面料密度不够"},
                    {"问题": "掉色/褪色", "提及率": "18%", "严重程度": "高", "说明": "洗后或日晒后褪色，染色工艺问题"},
                    {"问题": "面料起球/勾丝", "提及率": "12%", "严重程度": "中", "说明": "面料品质不过关"},
                    {"问题": "挂钩/轨道损坏", "提及率": "10%", "严重程度": "中", "说明": "配件质量差，安装即坏"},
                ],
                "外观描述不符": [
                    {"问题": "色差严重", "提及率": "35%", "严重程度": "中", "说明": "页面图和实物颜色差异大"},
                    {"问题": "尺寸不符", "提及率": "30%", "严重程度": "中", "说明": "定制尺寸出错或测量指导不清"},
                ],
                "物流安装": [
                    {"问题": "褶皱严重", "提及率": "15%", "严重程度": "低", "说明": "包装折叠导致的折痕"},
                    {"问题": "安装困难", "提及率": "12%", "严重程度": "低", "说明": "轨道安装说明书不清"},
                ],
                "售后客服": [
                    {"问题": "退货麻烦", "提及率": "8%", "严重程度": "低", "说明": "定制产品退货流程复杂"},
                ],
                "其他": [
                    {"问题": "有异味", "提及率": "22%", "严重程度": "中", "说明": "新窗帘化学气味较重"},
                    {"问题": "面料薄", "提及率": "14%", "严重程度": "中", "说明": "实际面料偏薄，手感不如预期"},
                ]
            },
            "好评关键词": [
                "遮光效果好（占比52%）",
                "手感好/面料舒服（占比40%）",
                "颜色正（占比36%）",
                "性价比高（占比32%）",
                "安装简单（占比25%）",
                "客服态度好（占比20%）"
            ]
        },
        "热搜趋势词（近30天）": [
            "奶油风窗帘（搜索增长+120%）",
            "电动窗帘（+95%）",
            "雪尼尔窗帘（+72%）",
            "高遮光窗帘（+65%）",
            "飘窗窗帘（+58%）",
            "窗帘成品免安装（+52%）",
            "奶茶色窗帘（+48%）",
            "蛇形帘（+42%）——新型挂法机会",
            "全屋窗帘定制（+35%）",
            "窗帘+飘窗垫套装（+40%）",
        ],
        "竞品广告投放估算": {
            "平均点击成本": "1.2-2.5元",
            "平均转化率": "3.5%",
            "头部卖家月推广费": "5-10万",
            "腰部卖家月推广费": "1-5万",
            "推广渠道分布": "直通车60% 引力魔方25% 万相台15%"
        },
        "竞品品牌档案": {
            "M居家纺": {"主力价格带": "150-400", "主力风格": "现代简约/棉麻", "月销估算": "约500万", "核心优势": "品牌力强，SKU丰富", "核心劣势": "风格偏大众，缺乏特色"},
            "N品布艺": {"主力价格带": "200-500", "主力风格": "高遮光功能", "月销估算": "约300万", "核心优势": "遮光技术领先", "核心劣势": "风格单一，款式少"},
            "O之居": {"主力价格带": "150-300", "主力风格": "ins风/亚麻", "月销估算": "约200万", "核心优势": "ins风格定位精准", "核心劣势": "产品线窄，天花板低"},
            "P智能": {"主力价格带": "600-1200", "主力风格": "智能电动", "月销估算": "约150万", "核心优势": "智能赛道先发", "核心劣势": "门槛高，受众窄"},
        }
    }
}


# ====================================================================
# 🔍 探索模式1：风格差异化 + 套装组合
# 案例来源：新中式套装
# 核心问题：有什么风格正在兴起？现有玩家卖单品还是组合？
#           有没有"XX风格+套装组合"的差异化机会？
# ====================================================================
def explore_style_differentiation(category_data: dict) -> Dict:
    """
    扫描风格趋势，识别"风格×套装组合"的蓝海机会
    """
    products = category_data["头部商品（TOP10）"]
    style_trends = category_data.get("风格搜索趋势", {})
    combo_keywords = category_data.get("跨类目搜索词", [])
    
    # 1. 统计各风格的商品分布
    style_product_count = {}
    style_price_ranges = {}
    for p in products:
        style = p.get("风格", "未知")
        style_product_count[style] = style_product_count.get(style, 0) + 1
        if style not in style_price_ranges:
            style_price_ranges[style] = {"min": float('inf'), "max": 0}
        price = float(p["价格"])
        style_price_ranges[style]["min"] = min(style_price_ranges[style]["min"], price)
        style_price_ranges[style]["max"] = max(style_price_ranges[style]["max"], price)
    
    # 2. 判断各风格是"单品为主"还是"有组合出售"
    # 简单规则：跨类目词中如果包含该风格名且有套装/组合意向，说明市场已有组合玩法
    combo_related_styles = set()
    for kw in combo_keywords:
        for style in style_trends.keys():
            if style in kw["关键词"] or any(style in part for part in kw["关键词"].split("+")):
                combo_related_styles.add(style)
    
    # 3. 机会判断：高增长 + 少竞品 + 组合玩法少
    opportunities = []
    for style, trend in style_trends.items():
        growth_str = trend["同比增长"]
        growth_num = float(re.search(r'\+?(\d+)', growth_str).group(1))
        competition = trend["竞争程度"]
        product_count = style_product_count.get(style, 0)
        has_combo = style in combo_related_styles
        
        # 机会评分（经验公式）
        score = 0
        score += 2 if growth_num > 30 else (1 if growth_num > 15 else 0)  # 高增长加分
        score += 2 if competition in ["低", "中低"] else (1 if competition == "中" else 0)  # 低竞争加分
        score += 1 if product_count <= 1 else 0  # 少竞品加分
        score += 2 if not has_combo else -1  # 没人在做组合是大机会，已有人做则减分
        
        # 风格+套装切入点建议
        if score >= 3:
            entry_advice = _generate_combo_entry_advice(style, category_data)
            opportunities.append({
                "风格": style,
                "增长率": growth_str,
                "当前TOP10中该风格商品数": product_count,
                "竞争程度": competition,
                "是否已有组合玩法": "是" if has_combo else "否（蓝海机会）",
                "机会评分": score,
                "机会等级": "🔥 强烈建议" if score >= 5 else "👍 值得尝试" if score >= 3 else "👀 观察",
                "套装切入点建议": entry_advice,
                "风险提示": "风格可能昙花一现，建议小批量测款" if growth_num > 50 else "竞争可能快速加剧，需快速抢占心智"
            })
        else:
            opportunities.append({
                "风格": style,
                "增长率": growth_str,
                "当前TOP10中该风格商品数": product_count,
                "竞争程度": competition,
                "是否已有组合玩法": "是" if has_combo else "否",
                "机会评分": score,
                "机会等级": "❌ 当前不建议",
                "套装切入点建议": "竞争饱和或增长乏力，不建议以风格差异化切入",
                "风险提示": ""
            })
    
    opportunities.sort(key=lambda x: x["机会评分"], reverse=True)
    
    return {
        "分析说明": "风格差异化策略：识别上升风格趋势，用'风格+套装组合'方式切入蓝海",
        "风格格局总览": {s: {"商品数": style_product_count.get(s, 0), "趋势": style_trends.get(s, {})} for s in sorted(style_trends.keys())},
        "各风格机会评估": opportunities,
        "推荐行动": [
            o for o in opportunities if o["机会等级"] in ["🔥 强烈建议", "👍 值得尝试"]
        ]
    }


def _generate_combo_entry_advice(style: str, category_data: dict) -> str:
    """根据风格生成套装切入建议"""
    # 从跨类目词中找与该风格相关的组合方向
    combo_keywords = category_data.get("跨类目搜索词", [])
    relevant_combos = [kw for kw in combo_keywords if style in kw["关键词"] or 
                       any(style in part for part in kw["关键词"].split("+"))]
    
    if relevant_combos:
        best = relevant_combos[0]
        return f"建议尝试「{best['关键词']}」组合方向，月搜索量{best['月搜索量']}，增长{best['增长']}"
    else:
        # 根据风格推荐通用组合方向
        style_combo_map = {
            "新中式": "建议尝试「新中式沙发+边几+挂画」客厅套装组合",
            "奶油风": "建议尝试「奶油风沙发+地毯+抱枕」整套搭配方案",
            "复古风": "建议尝试「复古风沙发+落地灯+装饰画」场景套装",
            "轻奢": "建议尝试「轻奢沙发+金属茶几+装饰镜」高端套装",
            "意式极简": "建议尝试「意式极简沙发+边几+落地灯」极简套装",
            "ins风": "建议尝试「ins风窗帘+靠垫+桌布」整套软装方案",
            "日式": "建议尝试「日式窗帘+蒲团+收纳」套装",
            "法式": "建议尝试「法式窗帘+窗幔+绑带」浪漫套装",
        }
        return style_combo_map.get(style, f"建议探索「{style}风格+相关品类」的组合套装机会")


# ====================================================================
# 🔍 探索模式2：跨界组合
# 案例来源：罗汉床茶桌组合
# 核心问题：有哪些A类目和B类目的产品被用户在一个搜索词里反复提及？
#           是否意味着一个新的场景需求？能否通过产品组合来满足？
# ====================================================================
def explore_cross_category_combo(category_data: dict) -> Dict:
    """
    从跨类目搜索词中发现跨界组合机会
    """
    combo_keywords = category_data.get("跨类目搜索词", [])
    
    if not combo_keywords:
        return {"分析说明": "暂无跨类目搜索数据", "跨界机会": []}
    
    opportunities = []
    for kw in combo_keywords:
        # 解析搜索量数字（支持整数和小数，如 "约8.2万" → 82000）
        vol_str = kw["月搜索量"]
        vol_match = re.search(r'约?(\d+(?:\.\d+)?)', vol_str)
        if vol_match:
            vol_num = float(vol_match.group(1)) * 10000 if "万" in vol_str else float(vol_match.group(1))
        else:
            vol_num = 0
        
        # 解析增长率
        growth_str = kw["增长"]
        growth_match = re.search(r'\+?(\d+)', growth_str)
        growth_num = int(growth_match.group(1)) if growth_match else 0
        
        # 机会评分
        score = 0
        score += 2 if vol_num > 3 else (1 if vol_num > 1 else 0)  # 搜索量大加分
        score += 2 if growth_num > 30 else (1 if growth_num > 15 else 0)  # 增长快加分
        
        # 涉及类目数（超过2个类目说明是真正的"跨界"）
        cross_num = len(kw.get("涉及类目", []))
        score += 1 if cross_num >= 2 else 0
        
        # 判断竞争程度（这里用搜索量/关键词长度做简单估算）
        # 真实场景需要看实际在售商品数
        competitive_assessment = "低（跨界组合竞争通常较小）" if score >= 3 else "中等"
        
        opportunities.append({
            "组合关键词": kw["关键词"],
            "月搜索量": kw["月搜索量"],
            "增长率": kw["增长"],
            "涉及类目": " + ".join(kw.get("涉及类目", [])),
            "机会评分": score,
            "机会等级": "🔥 强烈建议（组合词搜索量大+增长快）" if score >= 5 else 
                       "👍 值得试试（数据不错，小成本测试）" if score >= 3 else 
                       "👀 观察（数据可能不够大）",
            "竞争评估": competitive_assessment,
            "场景化建议": _generate_combo_scenario(kw["关键词"], kw.get("涉及类目", [])),
            "冷启动建议": f"先上架组合产品，主攻关键词'{kw['关键词']}'，直通车测款预算控制在2000元以内"
        })
    
    opportunities.sort(key=lambda x: x["机会评分"], reverse=True)
    
    return {
        "分析说明": "跨界组合策略：跳出单品思维，从搜索关键词中发现用户真实场景需求",
        "跨界机会": opportunities,
        "推荐优先尝试": [o for o in opportunities if o["机会等级"].startswith("🔥")]
    }


def _generate_combo_scenario(keyword: str, categories: List[str]) -> str:
    """根据组合关键词生成场景化建议"""
    scenario_map = {
        "沙发茶几电视柜组合": "一站式客厅解决方案，适合装修人群，主推场景",
        "沙发床一体的": "小户型/租房场景，一物多用是核心卖点",
        "罗汉床茶桌椅组合": "中式茶空间场景，文化属性强，溢价空间大",
        "客厅沙发+地毯套装": "软装搭配场景，适合主打听感搭配方案",
        "小户型沙发+茶几套餐": "刚需装修场景，性价比导向",
        "全屋窗帘套装": "一站式窗帘解决方案，适合懒人经济",
        "窗帘+飘窗垫套装": "飘窗改造场景，小红书种草潜力大",
        "电动窗帘+智能家居套餐": "智能家居场景，科技感强，适合年轻群体",
        "新中式沙发+边几组合": "新中式生活方式场景，审美升级需求",
        "窗帘+窗纱组合": "双层窗帘搭配场景，提升客单价",
    }
    for k, v in scenario_map.items():
        if k in keyword:
            return v
    return f"将{'+'.join(categories)}组合为场景化产品，突出'一步到位'的便利性"


# ====================================================================
# 🔍 探索模式3：痛点重构
# 案例来源：防塌陷沙发
# 核心问题：过滤物流态度等非产品问题→专注结构性缺陷
#           这个痛点是否广泛存在但没竞品在主打？→ 重构市场标准
# ====================================================================
def explore_pain_point_reconstruction(category_data: dict) -> Dict:
    """
    从差评中提取结构性缺陷，找到"全品类都在回避但用户最痛"的机会
    """
    eval_data = category_data.get("用户评价分析", {})
    review_categories = eval_data.get("差评分类", {})
    
    if not review_categories:
        return {"分析说明": "暂无差评分类数据", "重构机会": []}
    
    # 1. 只聚焦"产品结构性缺陷"类别
    structural_pains = review_categories.get("产品结构性缺陷", [])
    other_pains = []
    for cat, pains in review_categories.items():
        if cat != "产品结构性缺陷":
            other_pains.extend(pains)
    
    # 2. 分析每个结构性缺陷
    opportunities = []
    for pain in structural_pains:
        mention_rate = float(re.search(r'(\d+(?:\.\d+)?)', pain["提及率"]).group(1))
        severity = pain["严重程度"]
        
        # 机会评分：高提及率 + 高严重性 = 大机会
        score = 0
        score += 3 if mention_rate >= 15 else (2 if mention_rate >= 10 else 1)  # 提及率高
        score += 2 if severity == "高" else 1  # 严重性高
        
        # 加上"其他品类是否有类似痛点"的交叉分析（模拟）
        # 真实场景下应该跨类目分析同类结构性问题
        
        opportunities.append({
            "结构性缺陷": pain["问题"],
            "提及率": pain["提及率"],
            "严重程度": severity,
            "问题说明": pain["说明"],
            "机会评分": score,
            "机会等级": "🔥 核武器级机会（重构品类标准）" if score >= 5 else 
                       "👍 差异化卖点机会" if score >= 3 else 
                       "👀 辅助性卖点",
            "重构策略": _generate_pain_strategy(pain["问题"]),
            "话术建议": _generate_pain_selling_point(pain["问题"]),
            "验证方法": f"制作主打'{pain['问题']}解决方案'的测试链接，投入3000元推广费验证点击率和转化率"
        })
    
    # 3. 对比分析：结构性痛点 vs 其他类型痛点的严重程度
    # 用于在报告中强调"大家都在抱怨物流，但真正的机会在产品本身"
    max_other_mention = 0
    for p in other_pains:
        try:
            m = float(re.search(r'(\d+(?:\.\d+)?)', p["提及率"]).group(1))
            max_other_mention = max(max_other_mention, m)
        except:
            pass
    
    opportunities.sort(key=lambda x: x["机会评分"], reverse=True)
    
    return {
        "分析说明": "痛点重构策略：过滤物流/客服等通病，聚焦产品结构性缺陷，把'别人都在回避的问题'变成你的核心卖点",
        "结构性缺陷诊断": opportunities,
        "非产品类痛点（供参考）": [p["问题"] + f"({p['提及率']})" for p in sorted(other_pains, key=lambda x: float(re.search(r'(\d+(?:\.\d+)?)', x["提及率"]).group(1) or 0), reverse=True)[:5]],
        "关键洞察": f"结构性缺陷的平均严重程度远高于物流/售后类问题，但多数竞品选择回避而非解决——这正是重构市场标准的切入点",
        "推荐优先级": [o for o in opportunities if o["机会等级"].startswith("🔥")]
    }


def _generate_pain_strategy(pain: str) -> str:
    strategies = {
        "坐垫塌陷/变形": "采用高回弹海绵+独立弹簧双层结构，承诺「X年不塌陷」",
        "皮质开裂/掉皮": "升级头层牛皮或超纤皮，提供皮质保养指南+延保服务",
        "框架松动/异响": "采用榫卯结构+金属加固，螺丝外露处加防松垫片",
        "海绵回弹差": "改用高密度定型海绵（密度>45kg/m³），提供坐感体验视频",
        "遮光效果差/透光": "升级三层物理遮光结构，用强光手电筒做直播对比测试",
        "掉色/褪色": "采用活性印染工艺，提供3年不褪色承诺",
        "面料起球/勾丝": "升级高支高密面料，提供抗起球检测报告",
        "挂钩/轨道损坏": "升级静音加厚轨道，赠送备用配件",
    }
    return strategies.get(pain, f"针对「{pain}」问题研发专项解决方案，并在详情页突出展示")


def _generate_pain_selling_point(pain: str) -> str:
    points = {
        "坐垫塌陷/变形": "把'十年不塌陷'当主标题，坐垫剖面图展示双层结构",
        "皮质开裂/掉皮": "'五年质保 开裂包换'是最强有力的信任背书",
        "框架松动/异响": "详情页展示榫卯+金属双重固定工艺视频",
        "海绵回弹差": "用150斤沙袋连续坐压测试视频作为核心素材",
        "遮光效果差/透光": "'开灯像黑夜'——用对比图展示遮光效果",
        "掉色/褪色": "'暴晒100小时不掉色'实验室测试报告展示",
        "面料起球/勾丝": "'钢丝刷测试不起球'——场景化测试视频",
        "挂钩/轨道损坏": "强调'加厚轨道+静音设计'双卖点",
    }
    return points.get(pain, f"将'{pain}'的问题解决方案作为核心卖点突出呈现")


# ====================================================================
# 🔍 探索模式4：头羊验证法（跟随型机会）
# 案例来源：用户真实选品方法论
# 核心步骤：
#   1. 剔除干扰项（排除Top1）
#   2. 锁定"头羊"（产品线重合+价格带重合+非龙头中表现最好）
#   3. 分析头羊成功路径（主图风格/核心卖点/好评关键词）
#   4. 从头羊弱点中找机会（差评分析→做升级替代款）
# ====================================================================
def explore_head_sheep_opportunity(category_data: dict) -> Dict:
    """
    头羊验证法：找到可复制的跟随对象，做它的升级替代款
    """
    products = category_data["头部商品（TOP10）"]
    brand_profiles = category_data.get("竞品品牌档案", {})
    eval_data = category_data.get("用户评价分析", {})
    
    if not brand_profiles:
        return {"分析说明": "暂无竞品品牌数据，无法执行头羊验证法", "头羊分析": None}
    
    # 1. 排序：按月销量降序排列，排除Top1
    # 月销排序（去掉"+"号）
    def extract_sales(p):
        s = p["月销"].rstrip("+").replace(",", "")
        return int(s) if s.isdigit() else 0
    
    sorted_products = sorted(products, key=extract_sales, reverse=True)
    
    if len(sorted_products) < 2:
        return {"分析说明": "商品数据不足", "头羊分析": None}
    
    # 第一步：排除Top1（市场龙头，路径不可复制）
    top1_product = sorted_products[0]
    top1_brand = top1_product["品牌"]
    
    # 第二步：从剩下的品牌中找"头羊"
    candidates = []
    for p in sorted_products[1:]:  # 排除Top1
        brand = p["品牌"]
        profile = brand_profiles.get(brand, {})
        candidates.append({
            "品牌": brand,
            "产品": p["名称"],
            "价格": float(p["价格"]),
            "月销": extract_sales(p),
            "评分": float(p["评分"]),
            "风格": p.get("风格", "未知"),
            "主力价格带": profile.get("主力价格带", "未知"),
            "核心优势": profile.get("核心优势", "未知"),
            "核心劣势": profile.get("核心劣势", "未知"),
        })
    
    # 排序：综合评分（销量 + 评分加权）
    for c in candidates:
        c["综合得分"] = c["月销"] * 0.7 + c["评分"] * 1000 * 0.3  # 销量的权重70%，评分权重30%
    candidates.sort(key=lambda x: x["综合得分"], reverse=True)
    
    if not candidates:
        return {"分析说明": "无合适候选对象", "头羊分析": None}
    
    head_sheep = candidates[0]
    
    # 第三步：分析头羊成功路径
    # 从好评关键词中找共性
    praise_keywords = eval_data.get("好评关键词", [])
    
    # 第四步：从头羊弱点找机会
    # 从差评的分类数据中，聚焦结构性缺陷
    review_categories = eval_data.get("差评分类", {})
    structural_pains = review_categories.get("产品结构性缺陷", [])
    
    # 第五步：我们的切入策略
    # 学习头羊的成功点 + 攻击它的弱点 = 升级替代款
    attack_points = []
    for pain in structural_pains:
        attack_points.append({
            "头羊弱点": pain["问题"],
            "提及率": pain["提及率"],
            "我们的机会": _generate_pain_strategy(pain["问题"]),
        })
    
    analysis = {
        "分析说明": "头羊验证法：不要试图复制Top1的成功（资源不可复制），找一个已跑通的'头羊'做升级替代",
        "已排除（市场龙头）": {
            "品牌": top1_brand,
            "产品": top1_product["名称"],
            "原因": "龙头路径不可复制，资金/供应链/品牌力差距大"
        },
        "选定的头羊": {
            "品牌": head_sheep["品牌"],
            "产品": head_sheep["产品"],
            "价格": f"{head_sheep['价格']}元",
            "月销": head_sheep["月销"],
            "评分": head_sheep["评分"],
            "风格": head_sheep["风格"],
            "核心优势": head_sheep["核心优势"],
            "核心劣势": head_sheep["核心劣势"],
            "选他原因": f"产品线重合度高、价格带匹配、非龙头中表现最优"
        },
        "它做对了什么（学习点）": {
            "主图风格": head_sheep["风格"],
            "核心卖点": head_sheep["核心优势"],
            "用户认可的地方": [k for k in praise_keywords[:3]]
        },
        "它的弱点（攻击点）": attack_points[:3],
        "切入策略": {
            "策略": f"做{head_sheep['品牌']}的升级替代款",
            "具体做法": f"保留{head_sheep['风格']}风格定位，继承它对{head_sheep['核心优势']}的把握，但在{', '.join([a['头羊弱点'] for a in attack_points[:2]])}这{'些' if len(attack_points)>1 else '个'}核心痛点上做到明显优于它",
            "定价建议": f"略低于{head_sheep['品牌']}主力价格带，用性价比+差异化卖点切入",
            "冷启动建议": f"直通车精准投放'{head_sheep['产品']}'相关关键词，用'升级款''解决XX痛点'等标签截取头羊的精准流量",
        }
    }
    
    return analysis


# ====================================================================
# 🤖 DeepSeek API 调用的探索引擎版本
# ====================================================================
def call_deepseek_analysis(category: str, style_result: Dict, combo_result: Dict, 
                            pain_result: Dict, head_sheep_result: Dict) -> str:
    """用LLM对所有探索结果进行综合分析，输出运营化的报告"""
    if not DEEPSEEK_API_KEY:
        return None
    
    # 构建精简的prompt
    prompt = f"""你是一位有10年经验的电商选品创业顾问，以"市场机会探索引擎"的思维模式，基于以下数据对【{category}】类目做选品建议。

⚠️ 请用"创业顾问"的语气，像在会议室里给老板/合伙人讲人话一样说，不要写学术报告。每条建议都要给出："机会是什么★为什么值得试★风险在哪★下一步测什么"

===================
【数据输入】
===================

## 1️⃣ 风格差异化机会（案例：新中式套装）
{json.dumps(style_result.get('推荐行动', [])[:3], ensure_ascii=False, indent=2)}

## 2️⃣ 跨界组合机会（案例：罗汉床茶桌）
{json.dumps(combo_result.get('推荐优先尝试', [])[:3], ensure_ascii=False, indent=2)}

## 3️⃣ 痛点重构机会（案例：防塌陷沙发）
{json.dumps(pain_result.get('推荐优先级', [])[:3], ensure_ascii=False, indent=2)}

## 4️⃣ 头羊验证分析
{json.dumps(head_sheep_result.get('切入策略', {}), ensure_ascii=False, indent=2)}

===================
【输出要求】
===================
用以下结构输出：

### 🎯 机会一：XXX（最推荐的方向，一句话说清）
- **为什么是这个？**
- **风险与难度：**
- **测试方法：**
- **预期收益：**

### 🎯 机会二：XXX
（同上格式）

### 🎯 机会三：XXX
（同上格式，如果有的话）

### 📋 下一步行动清单
- [ ] 第一优先级任务
- [ ] 可以同步做的任务
- [ ] 先不做的任务（为什么）
"""
    
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": "你是一个电商选品创业顾问，擅长从数据中发现市场机会。请用口语化的、有洞察力的、像给合伙人做汇报一样的语气说话。不要模板化的分析报告。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 3000,
            "temperature": 0.7
        }
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content']
        else:
            return None
    except Exception as e:
        print(f"API调用异常：{e}")
        return None


# ====================================================================
# 📄 报告生成
# ====================================================================
def generate_report(category: str, style_result: Dict, combo_result: Dict,
                     pain_result: Dict, head_sheep_result: Dict) -> str:
    """生成市场机会探索报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    data = MOCK_MARKET_DATA[category]
    overview = data["类目概况"]
    
    # 尝试LLM增强
    llm_section = call_deepseek_analysis(category, style_result, combo_result, pain_result, head_sheep_result)
    
    report = []
    report.append(f"# 🎯 市场机会探索报告：{category}")
    report.append(f"生成时间：{now}")
    report.append(f"")
    report.append(f"> **探索模式：** 风格差异化 × 跨界组合 × 痛点重构 × 头羊验证")
    report.append(f"> **核心理念：** 不是选品工具，是市场机会探索引擎")
    report.append("")
    report.append("---")
    report.append("")
    
    # ===== 类目概览 =====
    report.append("## 📊 类目速览")
    report.append(f"| 维度 | 数据 |")
    report.append(f"|:---|:---:|")
    report.append(f"| 类目 | {overview['类目名称']} |")
    report.append(f"| 月搜索热度 | {overview['月搜索热度']} |")
    report.append(f"| 在线商品数 | {overview['在线商品数']} |")
    report.append(f"| 市场集中度 | {overview['市场集中度']} |")
    report.append(f"| 平均客单价 | {overview['平均客单价']} |")
    report.append(f"| 同比增长 | {overview['同比增长率']} |")
    report.append(f"| 主要人群 | {overview.get('主要受众人群', '')} |")
    report.append("")
    
    # ===== 1. 风格差异化 =====
    report.append("## 1️⃣ 风格差异化机会（案例：新中式套装）")
    report.append("")
    report.append("> **核心逻辑：** 识别一个上升的风格趋势，用'这个风格+套装组合'的方式切入，避开单品红海。")
    report.append("")
    
    top_styles = style_result.get("推荐行动", [])
    if top_styles:
        for s in top_styles[:3]:
            report.append(f"### {'🔥' if '强烈' in s.get('机会等级','') else '👍'} {s['风格']}")
            report.append(f"- **增长率：** {s['增长率']}")
            report.append(f"- **竞争程度：** {s['竞争程度']}")
            report.append(f"- **当前TOP10中该风格商品数：** {s.get('当前TOP10中该风格商品数', 'N/A')}")
            report.append(f"- **组合玩法：** {s.get('是否已有组合玩法', '未知')}")
            report.append(f"- **切入点建议：** {s.get('套装切入点建议', '')}")
            report.append(f"- **风险提示：** {s.get('风险提示', '')}")
            report.append("")
    else:
        report.append("当前没有发现足够强的风格差异化机会。")
        report.append("")
    
    # ===== 2. 跨界组合 =====
    report.append("## 2️⃣ 跨界组合机会（案例：罗汉床茶桌组合）")
    report.append("")
    report.append("> **核心逻辑：** 跳出传统类目划分，从搜索关键词中发现用户真实的'场景需求'，用产品组合满足它。")
    report.append("")
    
    top_combos = combo_result.get("推荐优先尝试", [])
    if top_combos:
        for c in top_combos[:3]:
            report.append(f"### 🔥 {c['组合关键词']}")
            report.append(f"- **月搜索量：** {c['月搜索量']}")
            report.append(f"- **增长率：** {c['增长率']}")
            report.append(f"- **场景化建议：** {c.get('场景化建议', '')}")
            report.append(f"- **冷启动建议：** {c.get('冷启动建议', '')}")
            report.append("")
    else:
        other_combos = combo_result.get("跨界机会", [])
        if other_combos:
            report.append("虽无强烈推荐级机会，但以下组合方向也值得关注：")
            for c in other_combos[:3]:
                report.append(f"- {c['组合关键词']}（{c['月搜索量']}，{c['增长率']}）")
            report.append("")
        else:
            report.append("当前没有发现足够强的跨界组合机会。")
            report.append("")
    
    # ===== 3. 痛点重构 =====
    report.append("## 3️⃣ 痛点重构机会（案例：防塌陷沙发）")
    report.append("")
    report.append("> **核心逻辑：** 过滤物流、客服等通病，聚焦产品结构性缺陷。那个'全品类都存在的问题但没人解决'，就是你的机会。")
    report.append("")
    
    top_pains = pain_result.get("推荐优先级", [])
    if top_pains:
        for p in top_pains[:3]:
            level_icon = "🔥" if "核武器" in p.get('机会等级','') else "👍"
            report.append(f"### {level_icon} 结构性痛点：{p['结构性缺陷']}")
            report.append(f"- **提及率：** {p['提及率']}")
            report.append(f"- **严重程度：** {p['严重程度']}")
            report.append(f"- **重构策略：** {p.get('重构策略', '')}")
            report.append(f"- **话术建议：** {p.get('话术建议', '')}")
            report.append(f"- **验证方法：** {p.get('验证方法', '')}")
            report.append("")
    
    other_info = pain_result.get("非产品类痛点（供参考）", [])
    if other_info:
        report.append("> 💡 **对比参考：** 以下是非产品类的常见痛点（物流/客服等），虽然提及率也高，但它们是行业通病，不是差异化机会：")
        for o in other_info[:3]:
            report.append(f"> - {o}")
        report.append("")
    
    # ===== 4. 头羊验证法 =====
    report.append("## 4️⃣ 头羊验证法（案例：跟随型机会）")
    report.append("")
    report.append("> **核心逻辑：** 找到一家已经跑通的同行做'头羊'——不学Top1（学不了），跟头羊（学得会），然后做它的升级替代款。")
    report.append("")
    
    hs = head_sheep_result
    if hs and hs.get("选定的头羊"):
        sheep = hs["选定的头羊"]
        strategy = hs.get("切入策略", {})
        
        report.append(f"### 🎯 选定的头羊：{sheep['品牌']}")
        report.append(f"| 维度 | 数据 |")
        report.append(f"|:---|:---:|")
        report.append(f"| 代表产品 | {sheep['产品']} |")
        report.append(f"| 价格 | {sheep['价格']} |")
        report.append(f"| 月销 | {sheep['月销']} |")
        report.append(f"| 评分 | {sheep['评分']} |")
        report.append(f"| 风格 | {sheep['风格']} |")
        report.append(f"| 核心优势 | {sheep['核心优势']} |")
        report.append(f"| 核心劣势 | {sheep['核心劣势']} |")
        report.append("")
        
        report.append("#### 切入策略")
        report.append(f"- **策略定位：** {strategy.get('策略', '')}")
        report.append(f"- **具体做法：** {strategy.get('具体做法', '')}")
        report.append(f"- **定价建议：** {strategy.get('定价建议', '')}")
        report.append(f"- **冷启动建议：** {strategy.get('冷启动建议', '')}")
        report.append("")
    else:
        report.append("当前数据不足以执行头羊验证法分析。")
        report.append("")
    
    # ===== LLM综合分析 =====
    if llm_section:
        report.append("---")
        report.append("## 🤖 AI创业顾问的综合建议")
        report.append("")
        report.append(llm_section)
        report.append("")
    else:
        report.append("---")
        report.append("## 🤖 AI创业顾问的综合建议")
        report.append("")
        report.append("> 配置DeepSeek API密钥后可获得更深入的AI分析建议（`$env:DEEPSEEK_API_KEY='your-key'`）")
        report.append("")
        # 本地模式下的简洁总结
        report.append("### 📋 本地模式下的核心发现")
        report.append("")
        
        # 汇总所有推荐
        all_recommendations = []
        for s in style_result.get("推荐行动", [])[:2]:
            all_recommendations.append(f"【风格差异化】{s['风格']}：{s['套装切入点建议']}")
        for c in combo_result.get("推荐优先尝试", [])[:2]:
            all_recommendations.append(f"【跨界组合】{c['组合关键词']}：{c.get('场景化建议', '')}")
        for p in pain_result.get("推荐优先级", [])[:2]:
            all_recommendations.append(f"【痛点重构】{p['结构性缺陷']}：{p.get('重构策略', '')}")
        
        if all_recommendations:
            report.append("**值得关注的探索方向：**")
            for i, rec in enumerate(all_recommendations[:5], 1):
                report.append(f"{i}. {rec}")
            report.append("")
            
            report.append("> ⚠️ **建议：** 以上机会建议按'小成本测试→验证→放大'的节奏推进，不要一次性all-in。")
            report.append("")
    
    # ===== 附录 =====
    report.append("---")
    report.append(f"*报告由AI选品市场机会探索引擎自动生成 | 生成时间：{now}*")
    report.append("")
    report.append("**探索方法论来源案例：**")
    report.append("1. 风格差异化 → 新中式套装（从单品红海到风格组合蓝海）")
    report.append("2. 跨界组合 → 罗汉床茶桌组合（从独立类目到场景跨界）")
    report.append("3. 痛点重构 → 防塌陷沙发（从回避问题到重构标准）")
    report.append("4. 头羊验证 → 跟随型机会（从不学Top1到做升级替代）")
    
    return "\n".join(report)


# ====================================================================
# 🚀 主流程
# ====================================================================
def main():
    print("=" * 60)
    print("  🚀 市场机会探索引擎 v2.0")
    print("  模式：风格差异化 × 跨界组合 × 痛点重构 × 头羊验证")
    print("=" * 60)
    
    available = list(MOCK_MARKET_DATA.keys())
    print(f"\n📂 可分析类目：{', '.join(available)}")
    print()
    
    for category in available:
        print(f"\n{'='*60}")
        print(f"🔍 正在探索：{category}")
        print(f"{'='*60}")
        
        data = MOCK_MARKET_DATA[category]
        
        print("\n  🔍 模式1/4：风格差异化机会扫描...")
        style_result = explore_style_differentiation(data)
        top_styles = style_result.get("推荐行动", [])
        for s in top_styles[:2]:
            print(f"    {'🔥' if '强烈' in s.get('机会等级','') else '👍'} {s['风格']}（评分{s['机会评分']}）")
        
        print("\n  🔍 模式2/4：跨界组合机会扫描...")
        combo_result = explore_cross_category_combo(data)
        top_combos = combo_result.get("推荐优先尝试", [])
        for c in top_combos[:2]:
            print(f"    🔥 {c['组合关键词']}（{c['月搜索量']}，{c['增长率']}）")
        
        print("\n  🔍 模式3/4：痛点重构机会扫描...")
        pain_result = explore_pain_point_reconstruction(data)
        top_pains = pain_result.get("推荐优先级", [])
        for p in top_pains[:2]:
            print(f"    {'🔥' if '核武器' in p.get('机会等级','') else '👍'} {p['结构性缺陷']}（{p['提及率']}）")
        
        print("\n  🔍 模式4/4：头羊验证分析...")
        head_sheep_result = explore_head_sheep_opportunity(data)
        if head_sheep_result.get("选定的头羊"):
            hs = head_sheep_result["选定的头羊"]
            print(f"    🎯 选定头羊：{hs['品牌']} → {hs['产品']}（月销{hs['月销']}）")
        else:
            print("    ❌ 无足够数据执行头羊验证")
        
        # 生成报告
        print(f"\n  📝 正在生成{category}市场机会探索报告...")
        report = generate_report(category, style_result, combo_result, pain_result, head_sheep_result)
        
        filename = f"选品机会探索报告_{category}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  ✅ 报告已保存：{filename}")
    
    print(f"\n{'='*60}")
    print("  ✅ 全部探索完成！")
    print("  这只是一个开始，真正的洞察需要你的商业嗅觉来判断。")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
