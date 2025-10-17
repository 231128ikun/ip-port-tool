import pandas as pd
import sys
import os
import re
from pathlib import Path

# 设置工作目录为EXE文件所在目录
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

def clean_ip(ip_str):
    """清理IP地址"""
    ip_str = str(ip_str).strip()
    ip_str = re.sub(r'^https?://', '', ip_str)
    if '/' in ip_str:
        ip_str = ip_str.split('/')[0]
    if ':' in ip_str:
        ip_str = ip_str.split(':')[0]
    return ip_str

def get_safe_output_path(filename):
    """获取安全的输出文件路径"""
    if not filename.lower().endswith('.txt'):
        filename += '.txt'
    return str(Path.cwd() / filename)

def quick_mode(file_path):
    """快速模式：直接输出ip:port格式"""
    print("=== 快速模式 ===")
    print("说明：自动检测IP和端口列，输出ip:port格式，自动去重排序")
    
    try:
        df = pd.read_csv(file_path)
        print(f"✅ 成功读取文件，共 {len(df)} 行")
    except:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
            else:
                print("❌ 无法解析文件格式")
                return
        except Exception as e:
            print(f"❌ 文件读取失败: {e}")
            return
    
    ip_col = None
    port_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in ['ip', '地址', 'host']):
            ip_col = col
        elif any(keyword in col_lower for keyword in ['port', '端口']):
            port_col = col
    
    if not ip_col:
        print("❌ 无法自动检测IP列，请使用自定义模式")
        return
    
    print(f"📡 检测到IP列: {ip_col}")
    if port_col:
        print(f"🔌 检测到端口列: {port_col}")
    else:
        print("⚠️  未检测到端口列，使用默认端口443")
    
    results = []
    seen = set()
    
    for _, row in df.iterrows():
        try:
            ip = clean_ip(str(row[ip_col]))
            if not ip or len(ip) < 7:
                continue
                
            if port_col:
                port = str(row[port_col]).strip()
                if not port.isdigit():
                    port = "443"
            else:
                port = "443"
            
            item = f"{ip}:{port}"
            if item not in seen:
                seen.add(item)
                results.append(item)
        except:
            continue
    
    results.sort()
    
    output_file = get_safe_output_path("results")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in results:
                f.write(line + '\n')
        
        print(f"✅ 快速模式完成！共生成 {len(results)} 条去重记录")
        print(f"💾 输出文件: {output_file}")
        print(f"📁 文件位置: {os.path.abspath(output_file)}")
        
        print("\n📋 前10条结果预览:")
        for i, result in enumerate(results[:10], 1):
            print(f"  {i}. {result}")
            
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")

def custom_mode():
    """自定义模式：灵活的列选择和格式定义"""
    print("=== 自定义模式 ===")
    print("说明：自由选择列，自定义输出格式，支持去重和排序")
    
    file_path = input("📂 请输入CSV文件路径(可直接拖拽文件): ").strip('"')
    if not os.path.exists(file_path):
        print("❌ 文件不存在！")
        return
    
    try:
        df = pd.read_csv(file_path)
    except:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
            else:
                print("❌ 无法解析文件格式")
                return
        except Exception as e:
            print(f"❌ 文件读取失败: {e}")
            return
    
    print(f"✅ 成功读取文件，共 {len(df)} 行")
    
    print("\n📊 文件包含以下列:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    
    print("\n🎯 请选择要输出的列（输入数字，用空格分隔，如: 1 2 3 4 5）:")
    selected_indices = input("选择列: ").strip().split()
    
    selected_columns = []
    for index in selected_indices:
        if index.isdigit() and 1 <= int(index) <= len(df.columns):
            selected_columns.append(df.columns[int(index)-1])
    
    if not selected_columns:
        print("❌ 未选择任何列！")
        return
    
    print(f"\n🔄 已选择的列已重新编码:")
    for i, col in enumerate(selected_columns, 1):
        print(f"  {i}. {col}")
    
    print("\n👀 数据预览（前3行）:")
    for i in range(min(3, len(df))):
        preview_parts = []
        for col in selected_columns:
            value = str(df.iloc[i][col]).strip()
            preview_parts.append(value)
        print(f"  {i+1}. {' | '.join(preview_parts)}")
    
    print("\n📝 请选择输出格式:")
    format_options = [
        "1. [1] [2]                    → 第一列 第二列",
        "2. [1]:[2]                   → 第一列:第二列", 
        "3. [1]:[2]#[3]               → 第一列:第二列#第三列",
        "4. [1]:[2]#[3]|[4]           → 第一列:第二列#第三列|第四列",
        "5. [1]:[2]#[3]|[4]|[5]       → 第一列:第二列#第三列|第四列|第五列",
        "6. 自定义格式"
    ]
    
    for option in format_options:
        print(f"  {option}")
    
    format_choice = input("\n请选择格式(1-6): ").strip()
    
    if format_choice == "1":
        format_template = "[1] [2]"
    elif format_choice == "2":
        format_template = "[1]:[2]"
    elif format_choice == "3":
        if len(selected_columns) >= 3:
            format_template = "[1]:[2]#[3]"
        else:
            print("⚠️  需要至少选择3列才能使用此格式，已使用默认格式")
            format_template = "[1]:[2]"
    elif format_choice == "4":
        if len(selected_columns) >= 4:
            format_template = "[1]:[2]#[3]|[4]"
        else:
            print("⚠️  需要至少选择4列才能使用此格式，已使用默认格式")
            format_template = "[1]:[2]"
    elif format_choice == "5":
        if len(selected_columns) >= 5:
            format_template = "[1]:[2]#[3]|[4]|[5]"
        else:
            print("⚠️  需要至少选择5列才能使用此格式，已使用默认格式")
            format_template = "[1]:[2]"
    elif format_choice == "6":
        print("\n💡 自定义格式说明:")
        print("使用 [1]、[2]、[3] 等表示您选择的列")
        print(f"您选择了 {len(selected_columns)} 列，可以用 [1] 到 [{len(selected_columns)}]")
        print("\n📌 示例:")
        print(f"  [1]:[2]              → 第一列:第二列")
        print(f"  [1]:[2]#[3]          → 第一列:第二列#第三列")
        print(f"  [1]:[2]#[3]|[4]|[5]  → 第一列:第二列#第三列|第四列|第五列")
        format_template = input("\n请输入自定义格式: ").strip()
        if not format_template:
            format_template = "[1]:[2]"
    else:
        if len(selected_columns) >= 2:
            format_template = "[1]:[2]"
        else:
            format_template = "[1]"
    
    print("\n👀 格式预览:")
    preview_ok = False
    for i in range(min(3, len(df))):
        try:
            column_values = []
            for col in selected_columns:
                value = str(df.iloc[i][col]).strip()
                if col == selected_columns[0] and any(keyword in col.lower() for keyword in ['ip', '地址', 'host']):
                    value = clean_ip(value)
                column_values.append(value)
            
            result_line = format_template
            for j in range(len(column_values)):
                placeholder = f"[{j+1}]"
                result_line = result_line.replace(placeholder, column_values[j])
            
            print(f"  {i+1}. {result_line}")
            preview_ok = True
        except Exception as e:
            print(f"  {i+1}. ❌ 格式预览失败: {e}")
    
    if not preview_ok:
        print("❌ 格式预览失败，请检查格式是否正确")
        return
    
    confirm = input("\n✅ 是否继续处理所有数据? (y/n, 默认y): ").strip().lower()
    if confirm == 'n':
        print("⏹️  已取消操作")
        return
    
    deduplicate = input("🔄 是否去重? (y/n, 默认y): ").strip().lower()
    deduplicate = deduplicate != 'n'
    
    print("\n📊 排序选项:")
    print("0. 不排序")
    for i, col in enumerate(selected_columns, 1):
        print(f"{i}. 按第{i}列 ({col}) 排序")
    
    sort_choice = input("请选择排序方式(默认0): ").strip() or "0"
    
    output_file = input("\n💾 输出文件名(默认custom_results): ").strip()
    if not output_file:
        output_file = "custom_results"
    
    output_path = get_safe_output_path(output_file)
    
    print("\n⏳ 正在处理数据...")
    results = []
    seen = set() if deduplicate else None
    
    processed_count = 0
    for _, row in df.iterrows():
        try:
            column_values = []
            for col in selected_columns:
                value = str(row[col]).strip()
                if col == selected_columns[0] and any(keyword in col.lower() for keyword in ['ip', '地址', 'host']):
                    value = clean_ip(value)
                column_values.append(value)
            
            result_line = format_template
            for j in range(len(column_values)):
                placeholder = f"[{j+1}]"
                result_line = result_line.replace(placeholder, column_values[j])
            
            if deduplicate:
                if result_line not in seen:
                    seen.add(result_line)
                    if sort_choice.isdigit() and 1 <= int(sort_choice) <= len(selected_columns):
                        sort_col_index = int(sort_choice) - 1
                        sort_value = column_values[sort_col_index]
                        results.append((result_line, sort_value))
                    else:
                        results.append((result_line, result_line))
                    processed_count += 1
            else:
                if sort_choice.isdigit() and 1 <= int(sort_choice) <= len(selected_columns):
                    sort_col_index = int(sort_choice) - 1
                    sort_value = column_values[sort_col_index]
                    results.append((result_line, sort_value))
                else:
                    results.append((result_line, result_line))
                processed_count += 1
                    
        except Exception as e:
            continue
    
    print(f"✅ 已处理 {processed_count} 行数据")
    
    if sort_choice != "0" and sort_choice.isdigit() and 1 <= int(sort_choice) <= len(selected_columns):
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
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in sorted_results:
                f.write(line + '\n')
        
        print(f"\n🎉 处理完成！共生成 {len(sorted_results)} 条记录")
        print(f"💾 输出文件: {output_path}")
        print(f"📁 文件位置: {os.path.abspath(output_path)}")
        
        print("\n📋 前10条结果预览:")
        for i, result in enumerate(sorted_results[:10], 1):
            print(f"  {i}. {result}")
            
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")

def main():
    print("=" * 50)
    print("          📊 CSV文件处理工具")
    print("=" * 50)
    print("功能说明:")
    print("  • 快速模式: 拖拽文件自动处理，输出ip:port格式")
    print("  • 自定义模式: 自由选择列，自定义输出格式")
    print("  • 支持去重、排序、多种输出格式")
    print("  • 输出文件保存在程序所在目录")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            print(f"🔗 检测到拖拽文件: {file_path}")
            quick_mode(file_path)
        else:
            print("❌ 文件不存在！")
    else:
        print("🚀 请选择模式:")
        print("1. 快速模式 (推荐: 拖拽文件到本程序即可使用此模式)")
        print("2. 自定义模式 (高级: 自由选择列和输出格式)")
        
        choice = input("\n请选择模式(1/2): ").strip()
        
        if choice == '1':
            file_path = input("📂 请输入文件路径: ").strip('"')
            if os.path.exists(file_path):
                quick_mode(file_path)
            else:
                print("❌ 文件不存在！")
        elif choice == '2':
            custom_mode()
        else:
            print("❌ 无效选择！")
    
    print("\n" + "=" * 50)
    input("⏹️  按回车键退出...")

if __name__ == "__main__":
    main()