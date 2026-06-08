"""
模拟数据生成脚本 - 为AI诊断能力测试埋入异常点
异常点说明：
1. 产品1(A级) - 战略性亏损：周万向翻倍(4491.92→8983.84)，周实际成交不变，ROI大幅降低
2. 产品4(B级) - 加购成本失控：周加购成本+50%(24.99→37.49)，周加购-30%(87→60)
3. 产品2(A级) - 品控翻车：周退款拉高到占周实际成交的25%以上(26811.4→15000)
4. 产品6(C级) - 数据爆发：周实际成交从423.2改为5200
5. 产品10(新品) - 加购成本崩塌：周加购成本改为55，周加购改为28
6. 产品13(新品) - 退款危机：周退款从1105改为2500
"""

import csv

# 读取原始数据
with open('weekly_data.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)

# 对每一行进行处理
for i, row in enumerate(rows):
    product_id = row[4]  # 商品id
    
    if product_id == '976079':  # 产品1 - A级 - 战略性亏损
        # 周万向翻倍
        row[6] = str(round(float(row[6]) * 2, 2))
        # 周实际投产 = 周实际成交 / 周万向
        row[7] = str(round(float(row[8]) / float(row[6]), 10))
        # 周付费占比 = 周万向 / 周成交金额
        row[15] = str(round(float(row[6]) / float(row[9]), 10))
        
    elif product_id == '976080':  # 产品2 - A级 - 品控翻车
        # 周退款拉高到周实际成交的25%以上
        actual_tx = float(row[8])  # 周实际成交 = 53041.61
        row[10] = str(round(actual_tx * 0.28, 2))  # 28% ≈ 14851.65
        # 周成交金额 = 周实际成交 + 周退款
        row[9] = str(round(float(row[8]) + float(row[10]), 2))
        # 周退款率 = 周退款 / 周成交金额
        # 月退款率也相应调整（简化处理，用周退款率近似）
        row[26] = str(round(float(row[10]) / float(row[9]), 10))
        
    elif product_id == '976082':  # 产品4 - B级 - 加购成本失控
        # 周加购成本+50%
        row[12] = str(round(float(row[12]) * 1.5, 10))
        # 周加购-30%
        row[11] = str(int(float(row[11]) * 0.7))
        
    elif product_id == '976084':  # 产品6 - C级 - 数据爆发
        # 周实际成交改为5200
        old_tx = float(row[8])
        row[8] = '5200'
        # 周成交金额 = 周实际成交 + 周退款
        row[9] = str(round(5200 + float(row[10]), 2))
        # 周实际投产 = 周实际成交 / 周万向
        row[7] = str(round(5200 / float(row[6]), 10))
        # 周付费占比 = 周万向 / 周成交金额
        row[15] = str(round(float(row[6]) / float(row[9]), 10))
        
    elif product_id == '976088':  # 产品10 - 新品 - 加购成本崩塌
        # 周加购成本改为55
        row[12] = '55'
        # 周加购改为28
        row[11] = '28'
        
    elif product_id == '976091':  # 产品13 - 新品 - 退款危机
        # 周退款改为2500
        row[10] = '2500'
        # 周成交金额 = 周实际成交 + 周退款
        row[9] = str(round(float(row[8]) + 2500, 2))
        # 周退款率
        row[26] = str(round(2500 / float(row[9]), 10))
        # 周付费占比 = 周万向 / 周成交金额
        row[15] = str(round(float(row[6]) / float(row[9]), 10))

# 写入新文件
with open('weekly_data_v2.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    # 写入注释行说明异常点
    f.write('# 模拟数据 - 埋入的异常点：1.产品1(A级)战略性亏损(周万向翻倍) 2.产品4(B级)加购成本失控(+50%,加购-30%) 3.产品2(A级)品控翻车(退款占成交28%) 4.产品6(C级)数据爆发(周实际成交→5200) 5.产品10(新品)加购成本崩塌(加购成本→55,加购→28) 6.产品13(新品)退款危机(退款→2500)\n')
    writer.writerow(header)
    writer.writerows(rows)

print("已生成 weekly_data_v2.csv，包含以下异常点：")
print("1. 产品1(A级) - 战略性亏损：周万向翻倍，ROI大幅降低")
print("2. 产品4(B级) - 加购成本失控：加购成本+50%，加购-30%")
print("3. 产品2(A级) - 品控翻车：退款占周实际成交28%")
print("4. 产品6(C级) - 数据爆发：周实际成交423.2→5200")
print("5. 产品10(新品) - 加购成本崩塌：加购成本→55，加购→28")
print("6. 产品13(新品) - 退款危机：退款1105→2500")
