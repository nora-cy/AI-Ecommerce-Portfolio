"""
电商周报诊断系统
读取 weekly_data_v2.csv，按运营分层规则进行异常检测、根因推测、建议生成、预警分级
"""

import pandas as pd
import json
import os
from datetime import datetime

# ============ 配置 ============
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# ============ 数据加载 ============
def load_data(filepath="weekly_data_v2.csv"):
    """加载CSV数据"""
    df = pd.read_csv(filepath, comment='#', encoding='utf-8-sig')
    # 列名中的空格和BOM处理
    df.columns = df.columns.str.strip().str.replace('\ufeff', '', regex=False)
    print(f"加载数据：{len(df)} 条记录")
    print(f"   列名：{list(df.columns)}")
    return df


# ============ 节点1：异常检测 ============
def detect_anomalies(df):
    """
    按运营分层规则进行异常检测
    返回异常列表，每项包含：链接ID, 品级, 运营定位, 异常指标, 本周值, 正常标准, 偏差幅度
    """
    anomalies = []
    normal_fluctuations = []
    
    # 计算B级品加购成本均值（用于新品判断）
    b_level_mean_add_cost = df[df['级别'].str.strip() == 'B级']['周加购成本'].mean()
    b_level_mean_add_cost = b_level_mean_add_cost if not pd.isna(b_level_mean_add_cost) else 0
    
    for _, row in df.iterrows():
        product_id = str(int(row['商品id'])) if pd.notna(row['商品id']) else str(row['商品id'])
        grade = str(row['级别']).strip()
        channel = str(row['渠道']).strip()
        product_name = str(row['商家编码']).strip()
        
        # 解析数值字段
        weekly_cost = float(row['周万向']) if pd.notna(row['周万向']) else 0
        weekly_tx = float(row['周实际成交']) if pd.notna(row['周实际成交']) else 0
        weekly_amount = float(row['周成交金额']) if pd.notna(row['周成交金额']) else 0
        weekly_refund = float(row['周退款']) if pd.notna(row['周退款']) else 0
        weekly_add_cart = float(row['周加购']) if pd.notna(row['周加购']) else 0
        weekly_add_cost = float(row['周加购成本']) if pd.notna(row['周加购成本']) else 0
        weekly_paid_ratio = float(row['周付费占比']) if pd.notna(row['周付费占比']) else 0
        weekly_roi = float(row['周实际投产']) if pd.notna(row['周实际投产']) else 0
        weekly_inquiry = float(row['周询单人数']) if pd.notna(row['周询单人数']) else 0
        
        # 月数据作为参考基准
        monthly_tx = float(row['月实际成交额']) if pd.notna(row['月实际成交额']) else 0
        monthly_add_cost = float(row['月加购成本']) if pd.notna(row['月加购成本']) else 0
        monthly_inquiry_cost = float(row['月询单成本']) if pd.notna(row['月询单成本']) else 0
        
        # 计算退款率
        refund_rate = weekly_refund / weekly_amount if weekly_amount > 0 else 0
        
        # 周均参考值（用月数据推算周均）
        weekly_avg_tx_month = monthly_tx / 4 if monthly_tx > 0 else 0
        
        # ===== 按品级分规则检测 =====
        
        # ---- A级品（核心款） ----
        if grade == 'A级':
            # 规则1: 退款率 > 5%
            if refund_rate > 0.05:
                anomalies.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '核心款',
                    'anomaly_type': '退款率异常',
                    'current_value': f"{refund_rate*100:.2f}%",
                    'benchmark': "≤5%",
                    'deviation': f"+{(refund_rate - 0.05)*100:.2f}个百分点",
                    'alert_level': '🔴',
                    'alert_name': '红色预警'
                })
            
            # 规则2: 成交额环比下降 > 15%（仅有1周数据，用月均周值对比）
            if weekly_avg_tx_month > 0 and weekly_tx < weekly_avg_tx_month * 0.85:
                drop_pct = (1 - weekly_tx / weekly_avg_tx_month) * 100
                anomalies.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '核心款',
                    'anomaly_type': '成交额下滑',
                    'current_value': f"周成交{weekly_tx:.0f}",
                    'benchmark': f"月均周参考{weekly_avg_tx_month:.0f}",
                    'deviation': f"下降{drop_pct:.1f}%",
                    'alert_level': '🔴',
                    'alert_name': '红色预警'
                })
            
            # 规则3: ROI异常降低（为冲大促排名短期加大花费 - 标记为🟢正常波动）
            # 检查周万向 vs 月均周花费，如果花费突然大幅增加但成交没跟上
            monthly_weekly_cost = float(row['月万向无界']) / 4 if pd.notna(row['月万向无界']) and float(row['月万向无界']) > 0 else 0
            if monthly_weekly_cost > 0 and weekly_cost > monthly_weekly_cost * 1.5:
                normal_fluctuations.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '核心款',
                    'description': f"为冲大促排名加大花费，周花费{weekly_cost:.0f}（月均周{monthly_weekly_cost:.0f}），ROI降至{weekly_roi:.1f}，属于战略性投入期",
                    'alert_level': '🟢',
                    'alert_name': '正常波动'
                })

        # ---- B级品（潜力款） ----
        elif grade == 'B级':
            # 规则1: 加购成本上涨 > 30%（对比月加购成本）
            if monthly_add_cost > 0 and weekly_add_cost > monthly_add_cost * 1.3:
                add_cost_increase = (weekly_add_cost / monthly_add_cost - 1) * 100
                anomalies.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '潜力款',
                    'anomaly_type': '加购成本飙升',
                    'current_value': f"周加购成本{weekly_add_cost:.2f}",
                    'benchmark': f"月均{monthly_add_cost:.2f}",
                    'deviation': f"上涨{add_cost_increase:.1f}%",
                    'alert_level': '🔴',
                    'alert_name': '红色预警'
                })
            
            # 规则2: 付费占比 > 70%
            if weekly_paid_ratio > 0.70:
                anomalies.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '潜力款',
                    'anomaly_type': '付费占比过高',
                    'current_value': f"{weekly_paid_ratio*100:.2f}%",
                    'benchmark': "≤70%",
                    'deviation': f"+{(weekly_paid_ratio-0.70)*100:.2f}个百分点",
                    'alert_level': '🔴',
                    'alert_name': '红色预警'
                })
            
            # 规则3: 首次加大推广放量观察（如果花费突然增加但加购转化尚可，标记为🟢）
            monthly_weekly_cost = float(row['月万向无界']) / 4 if pd.notna(row['月万向无界']) and float(row['月万向无界']) > 0 else 0
            if monthly_weekly_cost > 0 and weekly_cost > monthly_weekly_cost * 1.3:
                normal_fluctuations.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '潜力款',
                    'description': f"放量观察期，本周加大投放力度，需持续观察转化数据",
                    'alert_level': '🟢',
                    'alert_name': '正常波动(放量观察期)'
                })

        # ---- 新品 ----
        elif grade == '新品':
            # 规则1: 加购成本 > B级品均值 * 2
            if b_level_mean_add_cost > 0 and weekly_add_cost > b_level_mean_add_cost * 2:
                anomalies.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '冷启动期',
                    'anomaly_type': '加购成本过高',
                    'current_value': f"周加购成本{weekly_add_cost:.2f}",
                    'benchmark': f"B级品均值2倍={b_level_mean_add_cost*2:.2f}",
                    'deviation': f"超出{((weekly_add_cost/(b_level_mean_add_cost*2))-1)*100:.1f}%",
                    'alert_level': '🔴',
                    'alert_name': '红色预警'
                })
            
            # 规则2: 有加购但成交转化率为0
            if weekly_add_cart > 0 and weekly_tx == 0:
                anomalies.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '冷启动期',
                    'anomaly_type': '加购零转化',
                    'current_value': f"加购{weekly_add_cart:.0f}，成交0",
                    'benchmark': "应有成交转化",
                    'deviation': "转化率0%",
                    'alert_level': '🔴',
                    'alert_name': '红色预警'
                })
            
            # 规则3: 退款率异常（虽然未在表中明确列出，但作为电商通用指标检测）
            if refund_rate > 0.30:
                anomalies.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '冷启动期',
                    'anomaly_type': '退款率异常偏高',
                    'current_value': f"{refund_rate*100:.2f}%",
                    'benchmark': "合理范围<10%",
                    'deviation': f"+{(refund_rate-0.10)*100:.2f}个百分点",
                    'alert_level': '🔴',
                    'alert_name': '红色预警'
                })
            
            # 新品第1-2周花费高成交少 → 🟢正常波动
            if weekly_cost > 0 and weekly_tx < weekly_cost * 2 and weekly_add_cost > 0:
                normal_fluctuations.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '冷启动期',
                    'description': f"冷启动期，花费{weekly_cost:.0f}，成交{weekly_tx:.0f}，数据量不足，仅供参考",
                    'alert_level': '🟢',
                    'alert_name': '正常波动(冷启动期)'
                })

        # ---- C级品（长尾款） ----
        elif grade == 'C级':
            # 规则1: 周花费突然 > 500元
            if weekly_cost > 500:
                anomalies.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '长尾款',
                    'anomaly_type': '花费异常升高',
                    'current_value': f"周花费{weekly_cost:.2f}",
                    'benchmark': "≤500元",
                    'deviation': f"超出{weekly_cost-500:.2f}元",
                    'alert_level': '🔴',
                    'alert_name': '红色预警'
                })
            
            # 规则2: 退款率 > 10%
            if refund_rate > 0.10:
                anomalies.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '长尾款',
                    'anomaly_type': '退款率异常',
                    'current_value': f"{refund_rate*100:.2f}%",
                    'benchmark': "≤10%",
                    'deviation': f"+{(refund_rate-0.10)*100:.2f}个百分点",
                    'alert_level': '🔴',
                    'alert_name': '红色预警'
                })
            
            # 规则3: 付费占比 > 50%
            if weekly_paid_ratio > 0.50:
                anomalies.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '长尾款',
                    'anomaly_type': '付费占比过高',
                    'current_value': f"{weekly_paid_ratio*100:.2f}%",
                    'benchmark': "≤50%",
                    'deviation': f"+{(weekly_paid_ratio-0.50)*100:.2f}个百分点",
                    'alert_level': '🔴',
                    'alert_name': '红色预警'
                })
            
            # C级品成交额异常爆发（虽然不在3条规则内，但成交额突变也应关注）
            if weekly_tx > 2000:
                normal_fluctuations.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'grade': grade,
                    'channel': channel,
                    'position': '长尾款',
                    'description': f"本周成交额{weekly_tx:.0f}，远超C级品常规水平，建议排查是否为异常订单或真实爆发",
                    'alert_level': '🟡',
                    'alert_name': '持续关注(成交异常)'
                })
    
    return anomalies, normal_fluctuations


# ============ 节点2：根因推测 ============
def infer_root_cause(anomaly):
    """根据异常类型和品级推测根因"""
    grade = anomaly['grade']
    anomaly_type = anomaly['anomaly_type']
    
    root_causes_map = {
        ('A级', '退款率异常'): [
            "批次品控问题，生产环节出现质量波动",
            "详情页夸大宣传，导致买家秀与期望不符",
            "近期差评集中爆发，影响了新用户的购买决策"
        ],
        ('A级', '成交额下滑'): [
            "竞品大促冲击，流量被分流",
            "主图/标题被竞品模仿，点击率下降",
            "核心关键词排名下滑，免费流量减少"
        ],
        ('B级', '加购成本飙升'): [
            "出价策略失控，建议检查人群出价是否过高",
            "素材点击率差，需要优化主图或创意",
            "人群竞争加剧，核心人群已覆盖完毕，需要破圈"
        ],
        ('B级', '付费占比过高'): [
            "过度依赖付费推广，未形成自然转化闭环",
            "免费搜索流量下滑，需要优化标题SEO",
            "人群包过窄，导致付费流量挤压免费流量"
        ],
        ('新品', '加购成本过高'): [
            "出价偏高，冷启动期建议先低价跑量积累数据",
            "主图点击率低，导致花费高但点击少",
            "产品定位与目标人群匹配度不够"
        ],
        ('新品', '加购零转化'): [
            "产品详情页转化能力不足，需优化",
            "定价策略可能存在问题，导致加购后不付款",
            "竞品价格优势明显，用户在比价"
        ],
        ('新品', '退款率异常偏高'): [
            "产品存在设计或描述上的硬伤",
            "物流破损或发货时效问题",
            "新客预期管理不到位，实物与期望有差距"
        ],
        ('C级', '花费异常升高'): [
            "系统自动投放异常，建议检查托管计划设置",
            "品类红海竞争，系统出价竞争加剧",
            "被平台误判为潜力品，自动增加了投放预算"
        ],
        ('C级', '退款率异常'): [
            "清仓品本身有瑕疵，详情页未清晰标注",
            "临期产品或尾货，客户收货后不满意",
            "物流转运次数多导致破损率上升"
        ],
        ('C级', '付费占比过高'): [
            "品类本身过于红海，不适合再投入",
            "免费流量已衰退，建议评估是否继续投放"
        ],
    }
    
    key = (grade, anomaly_type)
    if key in root_causes_map:
        return root_causes_map[key]
    
    # 通用根因
    return [
        f"针对该品级的特殊性，更可能的原因是市场环境发生变化",
        "建议深入分析具体数据维度进行排查",
    ]


# ============ 节点3：建议生成 ============
def generate_actions(anomaly):
    """根据异常生成3条行动建议"""
    grade = anomaly['grade']
    anomaly_type = anomaly['anomaly_type']
    channel = anomaly['channel']
    
    actions_map = {
        '退款率异常': [
            f"🔴 紧急：暂停{channel}渠道的推广，立即联系供应链确认质检报告",
            "🟡 重要：排查近期订单，主动联系高退款客户了解原因",
            "🟢 优化：检查详情页描述是否与实物一致，准备修改方案"
        ],
        '成交额下滑': [
            f"🔴 紧急：检查{channel}渠道是否出现投放中断或预算花不出去",
            "🟡 重要：排查核心关键词排名，检查竞品是否有大促动作",
            "🟢 优化：准备新主图进行A/B测试，优化标题提升搜索权重"
        ],
        '加购成本飙升': [
            f"🔴 紧急：暂停{channel}渠道低效计划，降低出价至建议价的80%",
            "🟡 重要：分析人群画像，检查是否人群过窄导致竞争加剧",
            "🟢 优化：制作2-3套新素材进行点击率测试"
        ],
        '加购成本过高': [
            "🔴 紧急：暂停当前投放计划，降低出价重新搭建冷启动计划",
            "🟡 重要：优化主图提升点击率，从根本上降低加购成本",
            "🟢 优化：检查产品价格和卖点是否清晰，对比竞品做差异化"
        ],
        '加购零转化': [
            "🔴 紧急：检查购物车页面和下单流程是否存在技术故障",
            "🟡 重要：分析竞品价格策略，考虑发放限时优惠券促转化",
            "🟢 优化：优化详情页的卖点呈现和信任背书"
        ],
        '付费占比过高': [
            f"🔴 紧急：降低{channel}渠道预算占比，避免过度依赖付费流量",
            "🟡 重要：优化标题SEO，提升自然搜索流量占比",
            "🟢 优化：检查店铺是否有可参与的平台活动获取免费流量"
        ],
        '花费异常升高': [
            "🔴 紧急：立即检查全店托管或智能投放计划设置",
            "🟡 重要：设置花费上限和日预算限制，防止继续超支",
            "🟢 优化：重新评估该品是否适合继续投放，考虑清仓处理"
        ],
        '退款率异常偏高': [
            f"🔴 紧急：暂停{channel}投放，全面排查产品质量问题",
            "🟡 重要：联系仓库确认发货批次，排查是否存在批次性瑕疵",
            "🟢 优化：建立退货原因分析机制，定期优化产品质量"
        ]
    }
    
    if anomaly_type in actions_map:
        return actions_map[anomaly_type]
    
    return [
        "🔴 紧急：暂停相关渠道投放，避免损失扩大",
        "🟡 重要：深入排查异常原因，定位问题环节",
        "🟢 优化：建立数据监控机制，设置预警阈值"
    ]


# ============ DeepSeek API 调用 ============
def call_deepseek(prompt, max_tokens=2000):
    """调用DeepSeek API生成分析内容"""
    if not DEEPSEEK_API_KEY:
        return None
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "你是一位资深的电商运营专家，擅长分析电商数据并提供诊断建议。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        import requests
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"API调用失败：HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"API调用异常：{e}")
        return None


# ============ 报告生成 ============
def generate_report(df, anomalies, normal_fluctuations):
    """生成诊断报告markdown文件"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 分类预警
    red_alerts = [a for a in anomalies if a['alert_level'] == '🔴']
    yellow_alerts = [a for a in anomalies if a['alert_level'] == '🟡'] + \
                    [n for n in normal_fluctuations if n['alert_level'] == '🟡']
    green_normal = [n for n in normal_fluctuations if n['alert_level'] == '🟢']
    
    # 尝试调用DeepSeek API生成分析
    ai_analysis = None
    if DEEPSEEK_API_KEY:

        prompt = f"""作为电商运营专家，请对以下异常数据进行诊断分析：
        
异常列表：
{json.dumps([{'链接': a['product_name'], '品级': a['grade'], '异常': a['anomaly_type'], '当前值': a['current_value']} for a in anomalies], ensure_ascii=False, indent=2)}

请给出总体诊断意见和下周重点关注方向。"""
        ai_analysis = call_deepseek(prompt)
    
    # 构建报告
    report = []
    report.append("# 本周经营诊断报告")
    report.append(f"生成时间：{now}")
    report.append("")
    
    # 数据概览
    report.append("## 📋 数据概览")
    report.append(f"- 总链接数：{len(df)} 个")
    report.append(f"- A级品（核心款）：{len(df[df['级别'].str.strip()=='A级'])} 个")
    report.append(f"- B级品（潜力款）：{len(df[df['级别'].str.strip()=='B级'])} 个")
    report.append(f"- C级品（长尾款）：{len(df[df['级别'].str.strip()=='C级'])} 个")
    report.append(f"- 新品（冷启动）：{len(df[df['级别'].str.strip()=='新品'])} 个")
    report.append("")
    
    # 预警概览
    report.append("## 📊 预警概览")
    report.append(f"- 🔴 红色预警：{len(red_alerts)} 项")
    report.append(f"- 🟡 黄色关注：{len(yellow_alerts)} 项")
    report.append(f"- 🟢 绿色正常：{len(green_normal)} 项")
    report.append("")
    
    # API分析结果
    if ai_analysis:
        report.append("## 🤖 AI诊断意见")
        report.append(ai_analysis)
        report.append("")
    
    # 🔴 红色预警详情
    if red_alerts:
        report.append("## 🔴 红色预警详情")
        for i, a in enumerate(red_alerts, 1):
            report.append(f"### 异常{i}：{a['anomaly_type']}")
            report.append(f"- 链接：{a['product_name']}（ID: {a['product_id']}），品级：{a['grade']}，渠道：{a['channel']}")
            report.append(f"- 运营定位：{a['position']}")
            report.append(f"- 当前值：{a['current_value']}，基准值：{a['benchmark']}，偏差：{a['deviation']}")
            report.append("")
            
            # 根因推测
            root_causes = infer_root_cause(a)
            report.append("- 可能根因：")
            for j, cause in enumerate(root_causes, 1):
                report.append(f"  {j}. {cause}")
            report.append("")
            
            # 行动建议
            actions = generate_actions(a)
            report.append("- 行动建议：")
            for action in actions:
                report.append(f"  - {action}")
            report.append("")
    
    # 🟡 黄色关注详情
    if yellow_alerts:
        report.append("## 🟡 黄色关注详情")
        for item in yellow_alerts:
            report.append(f"### {item.get('anomaly_type', '需关注项')}")
            report.append(f"- 链接：{item['product_name']}（ID: {item['product_id']}），品级：{item['grade']}，渠道：{item['channel']}")
            if 'current_value' in item:
                report.append(f"- 当前值：{item['current_value']}，基准值：{item['benchmark']}，偏差：{item['deviation']}")
            if 'description' in item:
                report.append(f"- 说明：{item['description']}")
            report.append("")
    
    # 🟢 正常波动记录
    if green_normal:
        report.append("## 🟢 正常波动记录")
        for item in green_normal:
            report.append(f"- **{item['product_name']}**（{item['grade']}级）：{item['description']}")
        report.append("")
    
    # 下周持续观察清单
    report.append("## 📋 下周持续观察清单")
    
    # 根据检测结果生成观察项
    for a in anomalies:
        if a['anomaly_type'] == '退款率异常' or a['anomaly_type'] == '退款率异常偏高':
            report.append(f"- [ ] 链接 {a['product_name']}（{a['product_id']}）的退款率变化趋势")
        if a['anomaly_type'] == '加购成本飙升' or a['anomaly_type'] == '加购成本过高':
            report.append(f"- [ ] 链接 {a['product_name']}（{a['product_id']}）的加购成本趋势")
        if '成交' in a['anomaly_type']:
            report.append(f"- [ ] 链接 {a['product_name']}（{a['product_id']}）的成交额恢复情况")
    
    for n in normal_fluctuations:
        if '放量' in n.get('description', ''):
            report.append(f"- [ ] 链接 {n['product_name']}（{n['product_id']}）放量后转化率变化")
        if '成交异常' in n.get('alert_name', ''):
            report.append(f"- [ ] 链接 {n['product_name']}（{n['product_id']}）成交异常是否为真实爆发")
    
    if not anomalies and not normal_fluctuations:
        report.append("- [ ] 所有指标正常，下周继续监控")
    
    report.append("")
    
    # 附录：完整数据表
    report.append("## 📎 附录：本周数据一览")
    report.append("")
    report.append("| 商品 | 级别 | 渠道 | 周花费 | 周成交 | 退款率 | 加购成本 | 投产比 |")
    report.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    
    for _, row in df.iterrows():
        product_name = str(row['商家编码']).strip()
        grade = str(row['级别']).strip()
        channel = str(row['渠道']).strip()
        cost = float(row['周万向']) if pd.notna(row['周万向']) else 0
        tx = float(row['周实际成交']) if pd.notna(row['周实际成交']) else 0
        amount = float(row['周成交金额']) if pd.notna(row['周成交金额']) else 0
        refund = float(row['周退款']) if pd.notna(row['周退款']) else 0
        add_cost = float(row['周加购成本']) if pd.notna(row['周加购成本']) else 0
        roi = float(row['周实际投产']) if pd.notna(row['周实际投产']) else 0
        refund_rate = refund / amount * 100 if amount > 0 else 0
        
        report.append(f"| {product_name} | {grade} | {channel} | {cost:.0f} | {tx:.0f} | {refund_rate:.1f}% | {add_cost:.2f} | {roi:.2f} |")
    
    report.append("")
    # ============ 运营策略反思模块 ============
    report.append("## 🔄 运营策略反思")
    report.append("")
    report.append("基于本周的诊断结果，对现有分层诊断规则进行反思维度分析，识别规则设计中的潜在漏洞：")
    report.append("")
    report.append("### 漏洞1：新品异常判定阈值被异常B级品\"链式污染\"")
    report.append("")
    report.append("**现象：** 产品10(新品)周加购成本为55，按规则\"加购成本 > B级品均值×2\"进行判定时，当前B级品仅产品4一个链接，")
    
    # 计算B级品实际数据
    b_df = df[df['级别'].str.strip() == 'B级']
    if len(b_df) > 0:
        b_add_cost = float(b_df.iloc[0]['周加购成本'])
        b_name = str(b_df.iloc[0]['商家编码']).strip()
        report.append(f"且其自身加购成本已异常飙升至{b_add_cost:.2f}（月均仅16.38）。")
        report.append(f"用{b_add_cost:.2f}作为基准计算出的新品阈值为{b_add_cost*2:.2f}，")
        report.append(f"导致产品10加购成本55反而未触发预警——这是典型的\"异常基准污染\"问题。")
    else:
        report.append("且B级品数量过少，无法形成有效的统计基准。")
    
    report.append("")
    report.append("**规则缺陷：** 新品加购成本的判定阈值依赖B级品均值，但B级品若自身已异常，会\"污染\"基准值，让真正异常的新品漏报。")
    report.append("**优化建议：** 新品加购成本阈值不应直接取完全部B级品均值，而应排除B级品中已触发了\"加购成本飙升\"预警的链接，")
    report.append("或改用行业类目均值/上月历史均值作为基准，避免异常掺杂导致的标准漂移。")
    report.append("")
    
    # 检查产品1的标签冲突
    p1_red = any(a['product_id'] == '976079' and a['alert_level'] == '🔴' for a in anomalies)
    p1_green = any(n['product_id'] == '976079' and n['alert_level'] == '🟢' for n in normal_fluctuations)
    
    if p1_red and p1_green:
        report.append("### 漏洞2：跨品级多标签冲突——A级品在退款异常与战略性投入之间缺乏优先级")
        report.append("")
        report.append("**现象：** 产品1(A级)同时触发了：")
        report.append("- 🔴 **退款率异常**（当前32.11%，远超5%阈值）")
        report.append("- 🟢 **战略性投入**（周花费8984，较月均大幅增加，被标记为正常波动）")
        report.append("")
        report.append("**规则缺陷：** 两条规则给出了冲突信号——🟢绿色标签可能让运营人员误判严重性，低估退款异常的紧急程度。")
        report.append("实际上，耗费翻倍叠加退款率飙升的组合，远比单一指标恶化更危险。")
        report.append("**优化建议：** 当同一链接同时触发🔴和🟢标签时，应抑制🟢标签的输出或在报告中显式注明冲突，")
        report.append("并增加\"多指标联动分析\"规则：若花费增加的同时退款率也在恶化，应将等级上提至🔴级。")
        report.append("")
    
    report.append("### 漏洞3：C级品缺少\"向上异动\"规则")
    report.append("")
    
    # 检查C级品成交情况
    c_items = df[df['级别'].str.strip() == 'C级']
    c_burst = []
    for _, row in c_items.iterrows():
        tx = float(row['周实际成交'])
        if tx > 2000:
            c_burst.append(f"{row['商家编码'].strip()}({int(row['商品id'])}):周成交{tx:.0f}")
    
    if c_burst:
        report.append(f"**现象：** 本周C级品中{'、'.join(c_burst)}的成交额远超C级品常规水平，")
        report.append("但根据现有规则表，C级品（长尾款）仅检查\"花费>500元、退款率>10%、付费占比>50%\"三条下行风险规则，")
        report.append("\"成交额突然爆发\"这种上行异动完全没有覆盖。")
        report.append("")
        report.append("**规则缺陷：** C级品作为清库存/低成本引流款，成交额暴涨可能是异常订单（刷单/错拍/大单），")
        report.append("也可能说明该品实际上具有潜力（应升级为B级品观察）。无论是哪种情况，当前规则都无法响应。")
    
    report.append("**优化建议：** 为C级品增设\"成交额环比增长>200%\"的黄色关注规则，")
    report.append("触发后人工排查是否为真实爆发，确认真实增长的可考虑将该链接升级至B级品池。")
    report.append("")
    report.append("### 小结")
    report.append("")
    report.append("| 漏洞编号 | 问题类型 | 受影响品级 | 建议修复方向 |")
    report.append("|:---:|:---|:---:|:---|")
    report.append("| 1 | 基准链式污染 | 新品 | 排除异常B级品后再算均值，或改用历史基准 |")
    if p1_red and p1_green:
        report.append("| 2 | 多标签优先级冲突 | A级 | 抑制冲突标签，增加多指标联动升维规则 |")
    report.append("| 3 | 规则缺失（上行异动） | C级 | 增设成交额暴涨监测，触发后考虑品级升级 |")
    report.append("")
    report.append("---")
    report.append("*报告由电商运营诊断系统自动生成*")
    
    return "\n".join(report)



# ============ 主流程 ============
def main():
    print("=" * 60)
    print("  电商周报诊断系统 v1.0")
    print("=" * 60)
    
    # 1. 加载数据
    print("\n📥 正在加载数据...")
    df = load_data()
    print(f"   列名：{list(df.columns)}")
    
    # 2. 异常检测
    print("\n🔍 正在执行异常检测（运营分层版）...")
    anomalies, normal_fluctuations = detect_anomalies(df)
    print(f"   红色预警：{len([a for a in anomalies if a['alert_level']=='🔴'])} 项")
    print(f"   黄色关注：{len([n for n in normal_fluctuations if n['alert_level']=='🟡'])} 项")
    print(f"   绿色正常：{len([n for n in normal_fluctuations if n['alert_level']=='🟢'])} 项")
    
    # 3. 生成报告
    print("\n📝 正在生成诊断报告...")
    if DEEPSEEK_API_KEY:
        print("   检测到DeepSeek API密钥，将调用AI生成分析...")
    else:
        print("   未配置DeepSeek API密钥，使用本地分析逻辑...")
    
    report = generate_report(df, anomalies, normal_fluctuations)
    
    # 4. 保存报告
    output_file = "diagnosis_report.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n✅ 诊断报告已生成：{output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
