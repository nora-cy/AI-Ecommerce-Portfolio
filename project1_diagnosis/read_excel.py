import zipfile
import xml.etree.ElementTree as ET

def read_all_excel(filepath):
    """读取Excel文件所有数据"""
    with zipfile.ZipFile(filepath) as z:
        # 读取共享字符串表
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_tree = ET.parse(z.open('xl/sharedStrings.xml'))
            ss_root = ss_tree.getroot()
            ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            for si in ss_root.findall('.//s:si', ns):
                text_parts = []
                for t in si.findall('.//s:t', ns):
                    if t.text:
                        text_parts.append(t.text)
                shared_strings.append(''.join(text_parts))
        
        # 读取第一个sheet
        sheet_path = None
        wb_tree = ET.parse(z.open('xl/workbook.xml'))
        wb_root = wb_tree.getroot()
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
              'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
        
        sheets = wb_root.findall('.//s:sheet', ns)
        if sheets:
            first_sheet = sheets[0]
            rels_tree = ET.parse(z.open('xl/_rels/workbook.xml.rels'))
            rels_root = rels_tree.getroot()
            rels_ns = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
            
            for rel in rels_root.findall('.//r:Relationship', rels_ns):
                if rel.get('Id') == first_sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'):
                    target = rel.get('Target')
                    sheet_path = f'xl/{target}' if not target.startswith('/') else target[1:]
                    break
        
        if not sheet_path:
            for name in z.namelist():
                if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
                    sheet_path = name
                    break
        
        if not sheet_path:
            print("找不到工作表")
            return [], []
        
        # 读取sheet数据
        sheet_tree = ET.parse(z.open(sheet_path))
        sheet_root = sheet_tree.getroot()
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        
        rows = sheet_root.findall('.//s:row', ns)
        
        all_data = []
        for row in rows:
            cells = row.findall('.//s:c', ns)
            row_data = []
            for cell in cells:
                cell_type = cell.get('t')
                cell_value = cell.find('s:v', ns)
                value = cell_value.text if cell_value is not None else ''
                
                if cell_type == 's' and value:
                    idx = int(value)
                    if idx < len(shared_strings):
                        value = shared_strings[idx]
                
                row_data.append(value)
            all_data.append(row_data)
        
        return all_data

def filter_and_print(data):
    """筛选并打印C级和新品的数据"""
    if not data:
        print("没有数据")
        return
    
    # 第一行是表头
    header = data[0]
    print("=" * 120)
    print("表头:", header)
    print("=" * 120)
    
    # 找到"级别"列的索引（第3列，索引2）
    level_idx = 2  # 级别在第3列
    
    # 筛选C级和新品
    c_level_data = []
    new_product_data = []
    
    for row in data[1:]:  # 跳过表头
        if len(row) > level_idx:
            level = row[level_idx].strip()
            if level == 'C级':
                c_level_data.append(row)
            elif level == '新品':
                new_product_data.append(row)
    
    print("\n" + "=" * 120)
    print(f"【C级】数据共 {len(c_level_data)} 行:")
    print("=" * 120)
    if c_level_data:
        for row in c_level_data:
            print(row)
    else:
        print("无C级数据")
    
    print("\n" + "=" * 120)
    print(f"【新品】数据共 {len(new_product_data)} 行:")
    print("=" * 120)
    if new_product_data:
        for row in new_product_data:
            print(row)
    else:
        print("无新品数据")

if __name__ == '__main__':
    all_data = read_all_excel('原始数据.xlsx')
    filter_and_print(all_data)
