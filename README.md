# 抖音评论抓取工具

一个基于 FastAPI 的抖音评论抓取工具，支持通过关键词搜索、视频地址、用户名/ID 三种方式批量获取抖音视频评论，并导出为 JSON 格式。

**独立实现，不依赖任何 MCP server 或外部服务。**

## ✨ 功能特性

- 🔍 **关键词搜索**：输入关键词，自动搜索高热度视频并抓取评论
- 🎯 **视频地址**：直接输入视频链接，快速获取该视频的所有评论
- 👤 **用户主页**：输入用户名或ID，自动获取该用户所有视频的评论
- 📥 **一键导出**：自动下载 JSON 文件，格式统一，方便后续处理
- 🌐 **Web 界面**：简洁美观的网页操作界面，无需命令行

## 📋 系统要求

- Python 3.10 或更高版本
- Chrome 浏览器（用于浏览器自动化）
- Windows / macOS / Linux

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

**Windows 用户：**
```cmd
start_api_server.bat
```

**macOS/Linux 用户：**
```bash
python douyin_analysis_api_server.py
```

**或手动启动：**
```bash
python douyin_analysis_api_server.py
```

服务启动后，你会看到：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 3. 打开网页界面

在浏览器中打开 `douyin_comments_client.html` 文件（双击即可）

或者访问：`file:///你的路径/douyin_comments_client.html`

## 📖 使用说明

### 功能一：关键词搜索

1. 选择 **"关键词搜索"** Tab
2. 输入搜索关键词（如：益生菌、科技、美食）
3. 设置参数：
   - **视频数量**：按点赞数排序，取前 N 个视频（默认 10）
   - **每个视频评论数上限**：每个视频最多抓取多少条评论（默认 50）
   - **搜索深度**：滚动次数，越多采集的视频越多（默认 80）
4. 点击 **"开始搜索并抓取评论"**
5. 等待完成后，会自动下载 JSON 文件

### 功能二：视频地址

1. 选择 **"视频地址"** Tab
2. 输入视频链接（支持以下格式）：
   - 视频详情页：`https://www.douyin.com/video/xxxxx`
   - 分享链接：`https://v.douyin.com/xxxxx/`
   - 搜索页链接：`https://www.douyin.com/root/search/...modal_id=xxxxx`
3. 设置评论数上限（默认 50）
4. 点击 **"抓取该视频评论"**
5. 等待完成后，会自动下载 JSON 文件

### 功能三：用户名/ID

1. 选择 **"用户名/ID"** Tab
2. 输入用户名或用户ID（支持以下格式）：
   - 用户名：`@username` 或 `username`
   - 抖音号：直接输入抖音号
   - 主页链接：`https://www.douyin.com/user/xxxxx`
3. 设置参数：
   - **每个视频评论数上限**：每个视频最多抓取多少条评论（默认 50）
   - **主页滚动次数**：滚动次数越多，采集的视频越多（默认 100）
4. 点击 **"获取用户所有视频评论"**
5. 等待完成后，会自动下载 JSON 文件

## 📁 输出格式

所有功能导出的 JSON 文件格式统一：

```json
{
  "comments": [
    { "comment": "用户实际说的话" },
    { "comment": "另一条评论" },
    ...
  ]
}
```

文件名格式：
- 关键词搜索：`comments_关键词_时间戳.json`
- 视频地址：`comments_video_时间戳.json`
- 用户名/ID：`comments_user_用户名_时间戳.json`

## ⚙️ 配置说明

### 修改服务端口

编辑 `douyin_analysis_api_server.py`，找到：

```python
port = int(os.getenv("API_PORT", "8000"))  # 修改这里的 8000
```

或通过环境变量：

```bash
# Windows
set API_PORT=8080
python douyin_analysis_api_server.py

# macOS/Linux
export API_PORT=8080
python douyin_analysis_api_server.py
```

### 允许外部访问

编辑 `douyin_analysis_api_server.py`，找到：

```python
host = os.getenv("API_HOST", "127.0.0.1")  # 改为 "0.0.0.0"
```

**注意**：允许外部访问时，请配置防火墙规则。

## 🔧 项目结构

```
.
├── douyin_analysis_api_server.py  # 主服务文件（必需）
├── douyin_comments_client.html    # 网页操作界面（必需）
├── requirements.txt                # Python 依赖（必需）
├── start_api_server.bat           # Windows 启动脚本（可选）
├── start_api_server.ps1           # PowerShell 启动脚本（可选）
└── README.md                      # 本文件
```

## ⚠️ 注意事项

1. **登录状态**：首次使用时，浏览器会自动打开，请在浏览器中登录你的抖音账号，以便正常访问评论区域。

2. **抓取速度**：评论抓取需要一定时间，请耐心等待。每个视频的抓取时间取决于评论数量和网络速度。

3. **浏览器窗口**：抓取过程中会打开 Chrome 浏览器窗口，这是正常的（用于浏览器自动化），请不要关闭。

4. **数据使用**：请遵守抖音平台的使用条款，仅用于个人学习和研究目的。

5. **网络环境**：建议使用稳定的网络连接，避免频繁请求导致被限制。

## 🐛 常见问题

### Q: 提示 "DrissionPage 未安装"
A: 运行 `pip install -r requirements.txt` 安装所有依赖。

### Q: 浏览器打不开或报错
A: 确保已安装 Chrome 浏览器，并且版本较新。

### Q: 抓取不到评论
A: 
- 确保浏览器中已登录抖音账号
- 检查视频链接是否正确
- 尝试增加等待时间（可能需要修改代码中的 `await asyncio.sleep(8)` 为更大的值）

### Q: 端口被占用
A: 修改 `douyin_analysis_api_server.py` 中的端口号，或关闭占用 8000 端口的其他程序。

### Q: 评论内容不对（是数字而不是文本）
A: 这是抖音页面结构变化导致的，需要更新选择器。请提交 Issue 并提供错误日志。

## 📝 更新日志

### v2.0.0
- ✅ 新增视频地址直接抓取功能
- ✅ 新增用户名/ID 批量抓取功能
- ✅ 优化评论提取逻辑，确保获取真实评论文本
- ✅ 改进网页界面，支持 Tab 切换
- ✅ 增强日志输出，便于调试

## 📄 许可证

本项目仅供学习研究使用禁止商用，请遵守相关法律法规和平台规则。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题或建议，请提交 GitHub Issue。

---

**祝使用愉快！** 🎉
