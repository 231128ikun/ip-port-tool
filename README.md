# IP端口处理工具

一个强大的CSV文件处理工具，支持IP和端口数据的提取、格式化、去重和导出。

全文件由AI指导下完成。本项目并不成熟，含金量并不高，用途也很局限，仅作为学习使用github的一次小尝试。

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 功能特点

- 🚀 **智能识别**: 自动检测CSV文件编码和分隔符
- 📁 **批量处理**: 支持同时处理多个文件
- ⚡ **高性能**: 采用pandas引擎，处理百万行数据无压力
- 🛡️ **安全可靠**: 纯本地处理，数据不上传
- 📈 **进度显示**: 实时显示处理进度和结果统计

此项目主要用于配合iptest或[类似测速项目](https://github.com/jackrun123/cfiptest)使用，或者可以方便[cm的订阅器](https://github.com/cmliu/WorkerVless2sub)的维护，是借助ai来完成的一个小工具。

## 📦 下载使用

### 方式一：直接下载EXE（推荐新手）
1. 前往 [Releases](https://github.com/231128ikun/ip-port-tool/releases) 页面
2. 下载最新版本的 `IP端口处理工具.exe`
3. 双击即可使用

### 方式二：运行源代码
```bash
# 克隆项目
git clone https://github.com/231128ikun/ip-port-tool.git

# 安装依赖
python -m pip install pandas

# 运行程序
python ip_tool.py
```

## 🎯 使用方法

### 快速模式（推荐新手）
1. 直接将CSV文件拖拽到 `IP端口处理工具.exe` 上
2. 自动输出 `results.txt`

### 自定义模式（高级功能）
1. 双击 `IP端口处理工具.exe`
2. 选择模式2
3. 按提示选择列和输出格式

### 命令行用法（适合自动化）
```bash
# 快速处理单个文件
python ip_tool.py -f input.csv

# 批量处理文件夹
python ip_tool.py -d ./data

# 指定输出格式
python ip_tool.py -f input.csv --format "[1]:[2]#[3]"
```

## 📝 输出格式示例

| 格式 | 示例输出 |
|------|----------|
| `[1]:[2]` | `192.168.1.1:443` |
| `[1]:[2]#[3]` | `192.168.1.1:443#Beijing` |
| `[1]:[2]#[3]\|[4]` | `192.168.1.1:443#Beijing\|20ms` |
| `[1]:[2]#[3]\|[4]\|[5]` | `192.168.1.1:443#Beijing\|20ms\|1000kB/s` |

## 🗂️ 支持的文件格式

- CSV文件 (.csv)
- 文本文件 (.txt)
- Excel文件 (.xlsx, .xls)
- 表格格式数据

## 🔧 系统要求

- **操作系统**: Windows 7/8/10/11 (64位)
- **运行环境**: 无需安装Python或其他依赖（EXE版本）
- **内存**: 至少 100MB 可用空间

## 🛠️ 开发者信息

- **编程语言**: Python 3.x
- **主要依赖**: pandas
- **打包工具**: PyInstaller

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情







