import pandas as pd
import sys
import os
import re
import urllib.parse
import argparse
from pathlib import Path

# 设置工作目录为EXE文件所在目录
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

def clean_ip(ip_str):
    """清理IP地址"""
    ip_str = str(ip_str).strip()
    ip_str = re.sub(r'^https?://', '', ip_str)
    if '/' in ip_str:
        ip_str = ip_str.split('/')[0]
    return ip_str

def get_safe_output_path(filename):
    """获取安全的输出文件路径"""
    if not filename.lower().endswith('.txt'):
        filename += '.txt'
    return str(Path.cwd() / filename)

def detect_column_content_type(column_data):
    """智能检测列内容类型"""
    if not column_data or len(column_data) == 0:
        return 'unknown'
    
    ip_port_count = 0
    ip_only_count = 0
    mixed_count = 0
    
    for value in column_data[:10]:
        str_value = str(value).strip()
        if re.match(r'^\d+\.\d+\.\d+\.\d+:\d+$', str_value):
            ip_port_count += 1
        elif re.match(r'^\d+\.\d+\.\d+\.\d+$', str_value):
            ip_only_count += 1
        elif re.match(r'.*\d+\.\d+\.\d+\.\d+.*', str_value):
            mixed_count += 1
    
    if ip_port_count > 0:
        return 'ip_port'
    elif ip_only_count > 0:
        return 'ip_only'
    elif mixed_count > 0:
        return 'mixed'
    else:
        return 'other'

def extract_ip_port_from_mixed(text):
    """从混合文本中提取IP和端口"""
    # 尝试匹配 IP:端口 格式
    ip_port_match = re.search(r'(\d+\.\d+\.\d+\.\d+):(\d+)', text)
    if ip_port_match:
        return f"{ip_port_match.group(1)}:{ip_port_match.group(2)}"
    
    # 尝试匹配 IP,端口 格式（逗号分隔）
    ip_comma_port_match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s*,\s*(\d+)', text)
    if ip_comma_port_match:
        return f"{ip_comma_port_match.group(1)}:{ip_comma_port_match.group(2)}"
    
    # 尝试匹配纯IP
    ip_only_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', text)
    if ip_only_match:
        return ip_only_match.group(1)
    
    return None

def is_special_format_file(file_path):
    """检测文件是否为特殊格式文件（包含vless、trojan等协议）"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = [f.readline().strip() for _ in range(5)]
        
        for line in first_lines:
            if line and any(proto in line.lower() for proto in ['vless://', 'trojan://', 'ss://', 'vmess://']):
                return True
        return False
    except:
        return False

def parse_special_format(line):
    """解析特殊格式链接，返回 IP:端口#备注 格式"""
    line = line.strip()
    
    # 匹配各种特殊协议
    patterns = [
        r'^(vless|trojan|vmess)://[^@]+@([^:]+):(\d+)[^#]*(#.*)?',  # vless/trojan/vmess
        r'^ss://[^#]+#(.+)$',  # ss
    ]
    
    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            if match.group(1) in ['vless', 'trojan', 'vmess']:
                domain = match.group(2)
                port = match.group(3)
                remark = match.group(4) or ""
                
                # URL解码
                try:
                    domain = urllib.parse.unquote(domain)
                    if remark:
                        remark = urllib.parse.unquote(remark)
                except:
                    pass
                
                return f"{domain}:{port}{remark}"
    
    return None

def extract_special_format(file_path):
    """从特殊格式文件中提取信息"""
    print("🔍 正在提取文件信息...")
    
    results = []
    seen = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            special_info = parse_special_format(line)
            if special_info and special_info not in seen:
                seen.add(special_info)
                results.append(special_info)
        
        results.sort()
        return results
        
    except Exception as e:
        print(f"❌ 处理文件失败: {e}")
        return []

def process_excel_file(file_path, selected_sheets=None):
    """处理Excel文件 - 支持多工作表选择"""
    try:
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        if selected_sheets:
            dfs = {}
            for sheet_name in selected_sheets:
                if sheet_name in sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    dfs[sheet_name] = df
                    print(f"✅ 成功读取工作表 '{sheet_name}'，共 {len(df)} 行")
                else:
                    print(f"⚠️  工作表 '{sheet_name}' 不存在，已跳过")
            return dfs
        else:
            print(f"✅ 检测到Excel文件，包含以下工作表: {sheet_names}")
            print("\n📊 请选择要处理的工作表(输入数字，多选用空格分隔，如: 1 2 3):")
            for i, sheet in enumerate(sheet_names, 1):
                print(f"  {i}. {sheet}")
            
            sheet_choices = input("选择工作表(默认1): ").strip().split()
            if not sheet_choices:
                sheet_choices = ["1"]
            
            selected_dfs = {}
            for choice in sheet_choices:
                if choice.isdigit() and 1 <= int(choice) <= len(sheet_names):
                    sheet_name = sheet_names[int(choice)-1]
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    selected_dfs[sheet_name] = df
                    print(f"✅ 成功读取工作表 '{sheet_name}'，共 {len(df)} 行")
                else:
                    print(f"⚠️  无效选择: {choice}，已跳过")
            
            return selected_dfs if selected_dfs else None
        
    except Exception as e:
        print(f"❌ Excel文件读取失败: {e}")
        return None

def smart_parse_text(file_path):
    """智能解析文本文件为表格格式"""
    print("🔍 正在分析文本文件结构...")
    
    separators = [',', '#', '|', ':', '-', '\t', ' ']
    
    lines = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('-----'):
                lines.append(line)
    
    if not lines:
        return None
    
    separator_scores = {}
    for sep in separators:
        score = 0
        consistent_columns = True
        column_count = None
        
        for line in lines:
            if sep in line:
                parts = line.split(sep)
                parts = [p.strip() for p in parts if p.strip()]
                
                if column_count is None:
                    column_count = len(parts)
                elif len(parts) != column_count:
                    consistent_columns = False
                    break
                
                score += 1
        
        if consistent_columns and column_count and column_count > 1:
            separator_scores[sep] = score * column_count
    
    best_separator = max(separator_scores, key=separator_scores.get) if separator_scores else None
    
    if not best_separator:
        print("❌ 无法识别文本文件的分隔符结构")
        return None
    
    print(f"✅ 识别到分隔符: '{best_separator}'")
    
    data = []
    max_columns = 0
    
    for line in lines:
        parts = [p.strip() for p in line.split(best_separator) if p.strip()]
        if parts:
            data.append(parts)
            max_columns = max(max_columns, len(parts))
    
    for row in data:
        while len(row) < max_columns:
            row.append("")
    
    columns = []
    for i in range(max_columns):
        sample_values = [row[i] for row in data if i < len(row) and row[i]]
        col_type = "文本"
        
        if sample_values:
            first_value = sample_values[0]
            if re.match(r'^\d+\.\d+\.\d+\.\d+:\d+$', first_value):
                col_type = "IP:端口"
            elif re.match(r'^\d+\.\d+\.\d+\.\d+$', first_value):
                col_type = "IP地址"
            elif re.match(r'.*\d+\.\d+\.\d+\.\d+.*', first_value):
                col_type = "混合内容"
            elif first_value.isdigit() and 1 <= int(first_value) <= 65535:
                col_type = "端口"
        
        columns.append(f"列{i+1}({col_type})")
    
    print(f"✅ 成功解析为 {len(data)} 行 × {max_columns} 列")
    return pd.DataFrame(data, columns=columns)

def process_csv_file(file_path):
    """处理CSV文件"""
    try:
        # 尝试多种编码方式
        encodings = ['utf-8', 'gbk', 'utf-8-sig', 'latin-1']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"✅ 成功读取CSV文件({encoding})，共 {len(df)} 行")
                break
            except:
                continue
        
        if df is None:
            # 如果标准方法都失败，尝试手动解析
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                data = []
                headers = None
                for line in lines:
                    if '|' in line:
                        parts = [part.strip() for part in line.split('|') if part.strip()]
                        if not headers and len(parts) > 1:
                            headers = parts
                        elif headers and len(parts) == len(headers):
                            data.append(parts)
                
                if headers and data:
                    df = pd.DataFrame(data, columns=headers)
                    print(f"✅ 成功解析表格格式，共 {len(df)} 行")
                    return df
            except Exception as e:
                print(f"❌ 文件读取失败: {e}")
        
        return df
    except Exception as e:
        print(f"❌ CSV文件读取失败: {e}")
        return None

def extract_from_text_advanced(file_path, extract_mode="ip_space_port", default_port=""):
    """从文本文件中提取IP和端口（增强版，支持多种格式）"""
    print(f"📝 正在从文本文件提取数据...")
    
    results = []
    seen = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        print(f"✅ 成功读取文件，共 {len(lines)} 行")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('-----'):
                continue
            
            # 尝试多种提取方式
            extracted = extract_ip_port_from_mixed(line)
            
            if extracted:
                # 如果只有IP没有端口
                if ':' not in extracted:
                    # 仅IP模式直接使用IP
                    if extract_mode == "ip_only":
                        result_item = extracted
                    # 其他模式需要端口
                    elif default_port:
                        if extract_mode == "ip_space_port":
                            result_item = f"{extracted} {default_port}"
                        else:
                            result_item = f"{extracted}:{default_port}"
                    else:
                        # 没有默认端口且需要端口，跳过
                        continue
                else:
                    # 有IP和端口
                    if extract_mode == "ip_space_port":
                        ip, port = extracted.split(':')
                        result_item = f"{ip} {port}"
                    elif extract_mode == "ip_only":
                        result_item = extracted.split(':')[0]
                    else:
                        result_item = extracted
                
                if result_item and result_item not in seen:
                    seen.add(result_item)
                    results.append(result_item)
            
        results.sort()
        return results
        
    except Exception as e:
        print(f"❌ 处理文本文件失败: {e}")
        return []

def process_dataframe_for_quick_mode(df, extract_mode="ip_space_port", default_port=""):
    """处理DataFrame数据用于快速模式"""
    ip_col = None
    port_col = None
    ip_col_type = 'unknown'
    
    # 检测列类型
    for col in df.columns:
        col_lower = str(col).lower()
        sample_data = df[col].dropna().head(10).tolist()
        col_type = detect_column_content_type(sample_data)
        
        if col_type in ['ip_port', 'ip_only', 'mixed']:
            ip_col = col
            ip_col_type = col_type
            print(f"📡 检测到IP列 '{col}' - 类型: {col_type}")
            break
        elif any(keyword in col_lower for keyword in ['ip', '地址', 'host', 'input']):
            ip_col = col
            ip_col_type = detect_column_content_type(sample_data)
            print(f"📡 检测到IP列 '{col}' - 类型: {ip_col_type}")
            break
    
    if not ip_col:
        print("❌ 无法自动检测IP列")
        return []
    
    # 检测端口列
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in ['port', '端口']):
            port_col = col
            print(f"🔌 检测到端口列: {col}")
            break
    
    results = []
    seen = set()
    
    for _, row in df.iterrows():
        try:
            ip_value = str(row[ip_col]).strip()
            if not ip_value:
                continue
                
            # 处理IP列
            if ip_col_type == 'ip_port':
                # 已经是IP:端口格式
                if extract_mode == "ip_space_port":
                    ip, port = ip_value.split(':')
                    result_item = f"{ip} {port}"
                elif extract_mode == "ip_only":
                    result_item = ip_value.split(':')[0]
                else:
                    result_item = ip_value
            elif ip_col_type == 'mixed':
                # 混合内容，尝试提取IP和端口
                extracted = extract_ip_port_from_mixed(ip_value)
                if extracted:
                    if ':' not in extracted:
                        if extract_mode == "ip_only":
                            result_item = extracted
                        elif default_port:
                            if extract_mode == "ip_space_port":
                                result_item = f"{extracted} {default_port}"
                            else:
                                result_item = f"{extracted}:{default_port}"
                        else:
                            continue  # 没有端口且没有默认端口，跳过
                    else:
                        if extract_mode == "ip_space_port":
                            ip, port = extracted.split(':')
                            result_item = f"{ip} {port}"
                        elif extract_mode == "ip_only":
                            result_item = extracted.split(':')[0]
                        else:
                            result_item = extracted
                else:
                    continue
            elif ip_col_type == 'ip_only':
                # 纯IP
                if extract_mode == "ip_only":
                    result_item = ip_value
                elif port_col:
                    port_value = str(row[port_col]).strip()
                    if port_value and port_value.isdigit():
                        if extract_mode == "ip_space_port":
                            result_item = f"{ip_value} {port_value}"
                        else:
                            result_item = f"{ip_value}:{port_value}"
                    elif default_port:
                        if extract_mode == "ip_space_port":
                            result_item = f"{ip_value} {default_port}"
                        else:
                            result_item = f"{ip_value}:{default_port}"
                    else:
                        continue  # 没有端口且没有默认端口，跳过
                elif default_port:
                    if extract_mode == "ip_space_port":
                        result_item = f"{ip_value} {default_port}"
                    else:
                        result_item = f"{ip_value}:{default_port}"
                else:
                    continue  # 没有端口且没有默认端口，跳过
            else:
                result_item = ip_value
                
            if result_item and result_item not in seen:
                seen.add(result_item)
                results.append(result_item)
                
        except Exception as e:
            continue
    
    results.sort()
    return results

def quick_mode(file_path, extract_mode="ip_space_port", is_drag_drop=False):
    """快速模式：支持多种输出格式"""
    print("=== 快速模式 ===")
    
    # 检测是否为特殊格式文件
    if is_special_format_file(file_path):
        if is_drag_drop:
            # 拖拽模式直接使用 IP:端口#备注 格式
            results = extract_special_format(file_path)
            output_filename = "ip_port_remark_results"
            print("🔍 检测到特殊格式文件，使用 IP:端口#备注 格式输出")
        else:
            # 交互模式让用户选择
            print("🔍 检测到特殊格式文件，请选择输出格式:")
            print("1. IP:端口#备注 格式")
            print("2. IP 空格 端口 格式")
            print("3. 仅IP模式")
            
            choice = input("请选择(1/2/3, 默认1): ").strip()
            if choice == "2":
                special_results = extract_special_format(file_path)
                results = []
                for item in special_results:
                    match = re.match(r'([^:]+):(\d+)(#.*)?', item)
                    if match:
                        results.append(f"{match.group(1)} {match.group(2)}")
                extract_mode = "ip_space_port"
                output_filename = "ip_port_results"
            elif choice == "3":
                special_results = extract_special_format(file_path)
                results = []
                for item in special_results:
                    match = re.match(r'([^:]+):(\d+)(#.*)?', item)
                    if match:
                        results.append(match.group(1))
                extract_mode = "ip_only"
                output_filename = "ip_results"
            else:
                results = extract_special_format(file_path)
                extract_mode = "ip_port_remark"
                output_filename = "ip_port_remark_results"
    else:
        file_ext = os.path.splitext(file_path)[1].lower()
        output_filename = "results"
        
        # 设置默认端口 - 只有需要端口的模式才询问
        default_port = ""
        if extract_mode in ["ip_space_port", "ip_port_remark"]:
            if not is_drag_drop:
                print("💡 说明: 如果数据中只有IP没有端口，可以为其添加默认端口")
                port_choice = input("🔧 是否为纯IP添加默认端口？(y/n, 默认n): ").strip().lower()
                if port_choice == 'y':
                    default_port = input("请输入默认端口(直接回车使用443): ").strip()
                    if not default_port or not default_port.isdigit():
                        default_port = "443"
                    print(f"✅ 将使用默认端口: {default_port}")
                else:
                    print("✅ 不添加默认端口，仅提取包含端口的数据")
            else:
                # 拖拽模式不添加默认端口
                default_port = ""
                print("✅ 拖拽模式：不添加默认端口，仅提取包含端口的数据")
        else:
            # 仅IP模式不需要端口
            print("✅ 仅IP模式：提取所有IP地址，不关心端口")
        
        # 处理不同类型文件
        if file_ext in ['.xlsx', '.xls']:
            print("说明：自动检测IP列，智能处理IP和端口")
            dfs_dict = process_excel_file(file_path)
            if not dfs_dict:
                return
            
            all_results = []
            for sheet_name, df in dfs_dict.items():
                print(f"\n📊 处理工作表: {sheet_name}")
                sheet_results = process_dataframe_for_quick_mode(df, extract_mode, default_port)
                if sheet_results:
                    all_results.append(f"----- {sheet_name} -----")
                    all_results.extend(sheet_results)
            
            results = all_results
            
        elif file_ext in ['.txt']:
            if extract_mode == "ip_only":
                print("说明：从文本文件中只提取IP地址，自动去重排序")
                output_filename = "ip_results"
            elif extract_mode == "ip_port_remark":
                print("说明：从文本文件中提取 IP:端口#备注 格式")
                output_filename = "ip_port_remark_results"
            else:
                print("说明：从文本文件中提取 IP 空格 端口 格式")
                output_filename = "ip_port_results"
                
            results = extract_from_text_advanced(file_path, extract_mode, default_port)
            
        else:  # CSV和其他格式
            print("说明：自动检测IP列，智能处理IP和端口")
            df = process_csv_file(file_path)
            if df is None:
                return
            results = process_dataframe_for_quick_mode(df, extract_mode, default_port)
    
    if not results or (len(results) == 1 and results[0].startswith('-----')):
        print("❌ 未提取到任何有效数据")
        if is_drag_drop:
            input("\n⏹️  按回车键退出...")
        return
    
    if not is_drag_drop:
        output_file = input(f"💾 输出文件名(默认{output_filename}): ").strip()
        if not output_file:
            output_file = output_filename
    else:
        output_file = output_filename
    
    output_path = get_safe_output_path(output_file)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in results:
                f.write(line + '\n')
        
        valid_count = len([line for line in results if not line.startswith('-----')])
        print(f"✅ 处理完成！共生成 {valid_count} 条去重记录")
        print(f"💾 输出文件: {output_path}")
        
        print("\n📋 前10条结果预览:")
        preview_count = 0
        for i, result in enumerate(results):
            if not result.startswith('-----'):
                print(f"  {preview_count + 1}. {result}")
                preview_count += 1
                if preview_count >= 10:
                    break
            
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")
    
    if is_drag_drop:
        input("\n⏹️  按回车键退出...")

def truncate_format(format_template, max_columns):
    """根据最大列数截断格式"""
    # 移除超过max_columns的占位符
    for i in range(max_columns + 1, 10):
        format_template = format_template.replace(f'[{i}]', '')
    return format_template

def custom_mode():
    """自定义模式：支持CSV、TXT和Excel文件的灵活处理"""
    print("=== 自定义模式 ===")
    print("说明：自由选择列，自定义输出格式，支持去重和排序")
    
    file_path = input("📂 请输入文件路径(可直接拖拽文件): ").strip('"')
    if not os.path.exists(file_path):
        print("❌ 文件不存在！")
        return
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # 根据文件类型选择解析方式
    if file_ext in ['.xlsx', '.xls']:
        dfs_dict = process_excel_file(file_path)
        if not dfs_dict:
            return
        
        # 自定义模式暂时只处理第一个工作表（保持简单）
        sheet_name = list(dfs_dict.keys())[0]
        df = dfs_dict[sheet_name]
        print(f"📊 已选择工作表: {sheet_name}")
        
    elif file_ext in ['.csv']:
        df = process_csv_file(file_path)
    else:
        df = smart_parse_text(file_path)
    
    if df is None:
        print("❌ 无法解析文件")
        return
    
    print(f"✅ 成功读取文件，共 {len(df)} 行")
    
    # 显示所有列
    print("\n📊 文件包含以下列:")
    for i, col in enumerate(df.columns, 1):
        sample_values = []
        for j in range(min(3, len(df))):
            if pd.notna(df.iloc[j][col]) and str(df.iloc[j][col]).strip():
                sample_values.append(str(df.iloc[j][col]).strip())
        
        sample_preview = " | ".join(sample_values[:2]) if sample_values else "空"
        print(f"  {i}. {col} → 示例: {sample_preview}")
    
    # 选择要输出的列
    print("\n🎯 请选择要输出的列（输入数字，用空格分隔，如: 1 2 3 4 5）:")
    selected_indices = input("选择列: ").strip().split()
    
    selected_columns = []
    for index in selected_indices:
        if index.isdigit() and 1 <= int(index) <= len(df.columns):
            selected_columns.append(df.columns[int(index)-1])
    
    if not selected_columns:
        print("❌ 未选择任何列！")
        return
    
    print(f"\n🔄 已选择的列:")
    for i, col in enumerate(selected_columns, 1):
        print(f"  {i}. {col}")
    
    # 显示数据预览
    print("\n👀 数据预览（前3行）:")
    for i in range(min(3, len(df))):
        preview_parts = []
        for col in selected_columns:
            value = str(df.iloc[i][col]).strip() if pd.notna(df.iloc[i][col]) else ""
            preview_parts.append(value)
        print(f"  {i+1}. {' | '.join(preview_parts)}")
    
    # 输出格式选项 - 根据选择的列数智能调整
    selected_count = len(selected_columns)
    print(f"\n📝 请选择输出格式 (基于您选择的 {selected_count} 列):")
    
    format_options = []
    if selected_count >= 1:
        format_options.append("1. [1]                         → 第一列")
    if selected_count >= 2:
        format_options.append("2. [1]:[2]                    → 第一列:第二列")
    if selected_count >= 3:
        format_options.append("3. [1]:[2]#[3]                → 第一列:第二列#第三列")
    if selected_count >= 4:
        format_options.append("4. [1]:[2]#[3]|[4]            → 第一列:第二列#第三列|第四列")
    if selected_count >= 5:
        format_options.append("5. [1]:[2]#[3]|[4]|[5]        → 第一列:第二列#第三列|第四列|第五列")
    
    format_options.append("6. 自定义格式")
    
    for option in format_options:
        print(f"  {option}")
    
    format_choice = input("\n请选择格式(默认1): ").strip()
    
    if format_choice == "2" and selected_count >= 2:
        format_template = "[1]:[2]"
    elif format_choice == "3" and selected_count >= 3:
        format_template = "[1]:[2]#[3]"
    elif format_choice == "4" and selected_count >= 4:
        format_template = "[1]:[2]#[3]|[4]"
    elif format_choice == "5" and selected_count >= 5:
        format_template = "[1]:[2]#[3]|[4]|[5]"
    elif format_choice == "6":
        print("\n💡 自定义格式说明:")
        print(f"使用 [1] 到 [{selected_count}] 表示您选择的列")
        print("示例: [1]:[2]#[3] → 第一列:第二列#第三列")
        custom_format = input("\n请输入自定义格式: ").strip()
        if custom_format:
            format_template = truncate_format(custom_format, selected_count)
        else:
            format_template = "[1]"
    else:
        format_template = "[1]"
    
    print(f"✅ 最终使用的格式: {format_template}")
    
    # 预览格式效果
    print("\n👀 格式预览:")
    preview_ok = False
    for i in range(min(3, len(df))):
        try:
            column_values = []
            for col in selected_columns:
                value = str(df.iloc[i][col]).strip() if pd.notna(df.iloc[i][col]) else ""
                # 如果是IP地址列，进行清理
                if 'IP' in col or 'ip' in col.lower():
                    value = clean_ip(value)
                column_values.append(value)
            
            result_line = format_template
            for j in range(len(column_values)):
                result_line = result_line.replace(f"[{j+1}]", column_values[j])
            
            print(f"  {i+1}. {result_line}")
            preview_ok = True
        except Exception as e:
            print(f"  {i+1}. ❌ 格式预览失败")
    
    if not preview_ok:
        print("❌ 格式预览失败，请检查格式是否正确")
        return
    
    # 确认继续
    confirm = input("\n✅ 是否继续处理所有数据? (y/n, 默认y): ").strip().lower()
    if confirm == 'n':
        print("⏹️  已取消操作")
        return
    
    # 处理选项
    deduplicate = input("🔄 是否去重? (y/n, 默认y): ").strip().lower() != 'n'
    
    print("\n📊 排序选项:")
    print("0. 不排序")
    for i, col in enumerate(selected_columns, 1):
        print(f"{i}. 按第{i}列 ({col}) 排序")
    
    sort_choice = input("请选择排序方式(默认0): ").strip() or "0"
    
    output_file = input("\n💾 输出文件名(默认custom_results): ").strip()
    if not output_file:
        output_file = "custom_results"
    
    output_path = get_safe_output_path(output_file)
    
    # 处理所有数据
    print("\n⏳ 正在处理数据...")
    results = []
    seen = set() if deduplicate else None
    
    processed_count = 0
    for _, row in df.iterrows():
        try:
            column_values = []
            for col in selected_columns:
                value = str(row[col]).strip() if pd.notna(row[col]) else ""
                if 'IP' in col or 'ip' in col.lower():
                    value = clean_ip(value)
                column_values.append(value)
            
            result_line = format_template
            for j in range(len(column_values)):
                result_line = result_line.replace(f"[{j+1}]", column_values[j])
            
            if deduplicate:
                if result_line not in seen:
                    seen.add(result_line)
                    sort_value = column_values[int(sort_choice)-1] if sort_choice.isdigit() and 1 <= int(sort_choice) <= len(selected_columns) else result_line
                    results.append((result_line, sort_value))
                    processed_count += 1
            else:
                sort_value = column_values[int(sort_choice)-1] if sort_choice.isdigit() and 1 <= int(sort_choice) <= len(selected_columns) else result_line
                results.append((result_line, sort_value))
                processed_count += 1
                    
        except:
            continue
    
    print(f"✅ 已处理 {processed_count} 行数据")
    
    # 排序
    if sort_choice != "0":
        try:
            results.sort(key=lambda x: x[1])
            print(f"✅ 已按第{sort_choice}列排序")
        except:
            results.sort(key=lambda x: x[0])
            print("⚠️  按指定列排序失败，已按输出内容排序")
    else:
        results.sort(key=lambda x: x[0])
        print("✅ 已按输出内容排序")
    
    sorted_results = [item[0] for item in results]
    
    # 保存结果
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in sorted_results:
                f.write(line + '\n')
        
        print(f"\n🎉 处理完成！共生成 {len(sorted_results)} 条记录")
        print(f"💾 输出文件: {output_path}")
        
        print("\n📋 前10条结果预览:")
        for i, result in enumerate(sorted_results[:10], 1):
            print(f"  {i}. {result}")
            
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")

def show_usage():
    """显示使用说明"""
    program_name = os.path.basename(sys.argv[0])
    print(f"""
🚀 IP处理工具 v2.2

使用方法:
  交互模式: {program_name}
  拖拽模式: 直接将文件拖拽到程序上
  命令行模式: {program_name} [参数]

命令行参数:
  -u, --usage         显示此使用说明
  -f, --file string   输入文件路径
  -m, --mode string   输出模式: ipportremark(IP:端口#备注), ipspace(IP 空格 端口), iponly(仅IP)
                      默认: ipspace
  -o, --out string    输出文件名 (默认: "results.txt")
  -p, --port int      默认端口号 (默认: 443)

示例:
  {program_name} -f data.txt -m ipportremark -o output.txt
  {program_name} -f data.xlsx -m ipspace -p 8080

支持的文件格式:
  • 文本文件: .txt
  • Excel文件: .xlsx, .xls  
  • CSV文件: .csv

输出格式示例:
  • IP:端口#备注: 192.168.1.1:443#CN
  • IP 空格 端口: 192.168.1.1 443
  • 仅IP: 192.168.1.1
    """)

def command_line_mode():
    """命令行模式"""
    program_name = os.path.basename(sys.argv[0])
    parser = argparse.ArgumentParser(description=f'{program_name} - IP处理工具', add_help=False)
    parser.add_argument('-u', '--usage', action='store_true', help='显示使用说明')
    parser.add_argument('-f', '--file', type=str, help='输入文件路径')
    parser.add_argument('-m', '--mode', type=str, choices=['ipportremark', 'ipspace', 'iponly'], 
                       default='ipspace', help='输出模式 (默认: ipspace)')
    parser.add_argument('-o', '--out', type=str, default='results.txt', help='输出文件名')
    parser.add_argument('-p', '--port', type=int, default=443, help='默认端口号')
    
    args = parser.parse_args()
    
    if args.usage or not args.file:
        show_usage()
        return
    
    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        return
    
    # 映射模式参数
    mode_map = {
        'ipportremark': 'ip_port_remark',
        'ipspace': 'ip_space_port',
        'iponly': 'ip_only'
    }
    
    extract_mode = mode_map[args.mode]
    
    print(f"🔧 命令行模式:")
    print(f"   输入文件: {args.file}")
    print(f"   输出模式: {args.mode}")
    print(f"   输出文件: {args.out}")
    print(f"   默认端口: {args.port}")
    
    # 检测是否为特殊格式文件
    if is_special_format_file(args.file):
        if args.mode == 'ipportremark':
            results = extract_special_format(args.file)
        elif args.mode == 'ipspace':
            special_results = extract_special_format(args.file)
            results = []
            for item in special_results:
                match = re.match(r'([^:]+):(\d+)(#.*)?', item)
                if match:
                    results.append(f"{match.group(1)} {match.group(2)}")
        elif args.mode == 'iponly':
            special_results = extract_special_format(args.file)
            results = []
            for item in special_results:
                match = re.match(r'([^:]+):(\d+)(#.*)?', item)
                if match:
                    results.append(match.group(1))
    else:
        # 普通文件处理
        file_ext = os.path.splitext(args.file)[1].lower()
        
        if file_ext in ['.xlsx', '.xls']:
            dfs_dict = process_excel_file(args.file, selected_sheets=None)
            if not dfs_dict:
                return
            results = []
            for sheet_name, df in dfs_dict.items():
                sheet_results = process_dataframe_for_quick_mode(df, extract_mode, str(args.port))
                if sheet_results:
                    results.extend(sheet_results)
        elif file_ext in ['.txt']:
            results = extract_from_text_advanced(args.file, extract_mode, str(args.port))
        else:
            df = process_csv_file(args.file)
            if df is None:
                return
            results = process_dataframe_for_quick_mode(df, extract_mode, str(args.port))
    
    if not results:
        print("❌ 未提取到任何有效数据")
        return
    
    # 保存结果
    output_path = get_safe_output_path(args.out)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in results:
                f.write(line + '\n')
        
        valid_count = len([line for line in results if not line.startswith('-----')])
        print(f"✅ 处理完成！共生成 {valid_count} 条去重记录")
        print(f"💾 输出文件: {output_path}")
        
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")

def main():
    """主函数"""
    try:
        # 检查命令行参数
        if len(sys.argv) > 1 and sys.argv[1] not in ['-u', '--usage', '-f', '--file', '-m', '--mode', '-o', '--out', '-p', '--port']:
            # 拖拽文件启动
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                print("=" * 50)
                print("          🚀 IP处理工具 v2.2")
                print("=" * 50)
                print(f"📁 检测到拖拽文件: {file_path}")
                
                if is_special_format_file(file_path):
                    # 特殊格式文件，使用 IP:端口#备注 格式
                    quick_mode(file_path, "ip_port_remark", is_drag_drop=True)
                else:
                    # 普通文件，使用IP空格端口格式
                    quick_mode(file_path, "ip_space_port", is_drag_drop=True)
            else:
                print("❌ 文件不存在！")
                input("\n⏹️  按回车键退出...")
            return
        
        # 检查命令行模式
        if len(sys.argv) > 1:
            command_line_mode()
            return
        
        print("=" * 50)
        print("          🚀 IP处理工具 v2.2")
        print("=" * 50)
        print("📋 功能说明:")
        print("  • 快速模式: 拖拽文件自动处理")
        print("  • 自定义模式: 支持CSV/TXT/Excel，自由选择列")
        print("  • 智能解析: 自动识别文本文件结构")
        print("  • 支持去重、排序、多种输出格式")
        print("=" * 50)
        
        print("🎯 请选择模式:")
        print("1. 快速模式 (拖拽文件到本程序即可使用)")
        print("2. 自定义模式 (支持CSV/TXT/Excel文件)")
        print("3. 显示使用说明")
        
        choice = input("\n请选择模式(1/2/3): ").strip()
        
        if choice == '1':
            file_path = input("📂 请输入文件路径: ").strip('"')
            if os.path.exists(file_path):
                if is_special_format_file(file_path):
                    print("🔍 检测到特殊格式文件")
                    quick_mode(file_path, "ip_port_remark", is_drag_drop=False)
                else:
                    print("\n📝 请选择输出格式:")
                    print("1. IP:端口#备注 格式")
                    print("2. IP 空格 端口 格式（默认）")
                    print("3. 仅IP地址")
                    mode_choice = input("请选择(1/2/3, 默认2): ").strip()
                    if mode_choice == "1":
                        quick_mode(file_path, "ip_port_remark", is_drag_drop=False)
                    elif mode_choice == "3":
                        quick_mode(file_path, "ip_only", is_drag_drop=False)
                    else:
                        quick_mode(file_path, "ip_space_port", is_drag_drop=False)
            else:
                print("❌ 文件不存在！")
        elif choice == '2':
            # 调用自定义模式
            custom_mode()
        elif choice == '3':
            show_usage()
        else:
            print("❌ 无效选择！")
        
        print("\n" + "=" * 50)
        input("⏹️  按回车键退出...")
        
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        print("💡 请检查文件路径和格式是否正确")
        input("\n⏹️  按回车键退出...")

if __name__ == "__main__":
    main()
