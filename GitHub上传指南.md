# GitHub 上传指南

## 📋 准备工作

### 1. 安装 Git

如果还没有安装 Git，请先下载安装：

- **Windows**: https://git-scm.com/download/win
- **macOS**: `brew install git` 或从官网下载
- **Linux**: `sudo apt install git` (Ubuntu/Debian)

安装完成后，验证：
```bash
git --version
```

### 2. 创建 GitHub 账号

如果还没有 GitHub 账号，请访问 https://github.com 注册。

### 3. 在 GitHub 上创建新仓库

1. 登录 GitHub
2. 点击右上角 **"+"** → **"New repository"**
3. 填写仓库信息：
   - **Repository name**: 例如 `douyin-comments-crawler`
   - **Description**: 例如 "抖音评论抓取工具"
   - **Visibility**: 选择 Public（公开）或 Private（私有）
   - **不要**勾选 "Initialize this repository with a README"（因为本地已有文件）
4. 点击 **"Create repository"**

---

## 🚀 上传步骤

### 方法一：命令行上传（推荐）

#### 步骤 1: 初始化 Git 仓库

打开命令行（PowerShell 或 CMD），进入项目目录：

```bash
cd D:\MCP
```

初始化 Git 仓库：

```bash
git init
```

#### 步骤 2: 配置 Git（首次使用需要）

```bash
# 设置用户名（替换为你的 GitHub 用户名）
git config --global user.name "你的用户名"

# 设置邮箱（替换为你的 GitHub 邮箱）
git config --global user.email "your.email@example.com"
```

#### 步骤 3: 添加文件

```bash
# 添加所有需要的文件
git add douyin_analysis_api_server.py
git add douyin_comments_client.html
git add requirements.txt
git add README.md
git add API接口说明.md
git add 安装说明.md
git add 项目文件说明.md
git add start_api_server.bat
git add start_api_server.ps1
git add .gitignore
git add GitHub上传指南.md
```

或者一次性添加所有文件（推荐）：

```bash
git add .
```

#### 步骤 4: 提交文件

```bash
git commit -m "Initial commit: 抖音评论抓取工具"
```

#### 步骤 5: 连接到 GitHub 仓库

```bash
# 替换为你的 GitHub 用户名和仓库名
git remote add origin https://github.com/你的用户名/仓库名.git
```

例如：
```bash
git remote add origin https://github.com/username/douyin-comments-crawler.git
```

#### 步骤 6: 推送代码

```bash
# 设置主分支名称（GitHub 默认使用 main）
git branch -M main

# 推送代码到 GitHub
git push -u origin main
```

**注意**：首次推送可能需要输入 GitHub 用户名和密码（或 Personal Access Token）。

---

### 方法二：使用 GitHub Desktop（图形界面）

如果你更喜欢图形界面：

1. **下载 GitHub Desktop**
   - https://desktop.github.com/

2. **登录 GitHub 账号**

3. **添加本地仓库**
   - File → Add Local Repository
   - 选择项目目录 `D:\MCP`

4. **提交更改**
   - 在左侧勾选要提交的文件
   - 填写提交信息：`Initial commit: 抖音评论抓取工具`
   - 点击 "Commit to main"

5. **发布到 GitHub**
   - 点击 "Publish repository"
   - 填写仓库名称和描述
   - 选择 Public 或 Private
   - 点击 "Publish repository"

---

## 🔐 身份验证

### 使用 Personal Access Token（推荐）

GitHub 已不再支持密码登录，需要使用 Personal Access Token：

1. **生成 Token**
   - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 点击 "Generate new token (classic)"
   - 填写 Note（例如：`本地开发`）
   - 勾选 `repo` 权限
   - 点击 "Generate token"
   - **复制生成的 token**（只显示一次，请保存好）

2. **使用 Token**
   - 推送时，用户名输入你的 GitHub 用户名
   - 密码输入刚才生成的 token

### 使用 SSH（可选，更安全）

1. **生成 SSH 密钥**
   ```bash
   ssh-keygen -t ed25519 -C "your.email@example.com"
   ```
   按 Enter 使用默认路径，可以设置密码（可选）

2. **复制公钥**
   ```bash
   # Windows
   type %USERPROFILE%\.ssh\id_ed25519.pub
   
   # macOS/Linux
   cat ~/.ssh/id_ed25519.pub
   ```

3. **添加到 GitHub**
   - GitHub → Settings → SSH and GPG keys
   - 点击 "New SSH key"
   - 粘贴公钥内容
   - 点击 "Add SSH key"

4. **使用 SSH URL**
   ```bash
   git remote set-url origin git@github.com:你的用户名/仓库名.git
   ```

---

## ✅ 验证上传

上传完成后，访问你的 GitHub 仓库页面，应该能看到所有文件：

```
https://github.com/你的用户名/仓库名
```

---

## 🔄 后续更新

如果以后修改了代码，需要更新到 GitHub：

```bash
# 1. 查看更改
git status

# 2. 添加更改的文件
git add .

# 3. 提交更改
git commit -m "更新说明：例如：修复评论提取bug"

# 4. 推送到 GitHub
git push
```

---

## 🐛 常见问题

### Q: 提示 "remote origin already exists"

**解决方案：**
```bash
# 删除旧的远程仓库
git remote remove origin

# 重新添加
git remote add origin https://github.com/你的用户名/仓库名.git
```

### Q: 提示 "Authentication failed"

**解决方案：**
- 确保使用 Personal Access Token 而不是密码
- 或配置 SSH 密钥

### Q: 提示 "Permission denied"

**解决方案：**
- 检查仓库名称是否正确
- 确保有该仓库的写入权限
- 检查是否使用了正确的用户名

### Q: 想忽略某些文件

**解决方案：**
- 文件已在 `.gitignore` 中配置
- 如果还有文件不想上传，编辑 `.gitignore` 文件

---

## 📝 完整命令示例

```bash
# 进入项目目录
cd D:\MCP

# 初始化仓库
git init

# 配置 Git（首次使用）
git config --global user.name "你的用户名"
git config --global user.email "your.email@example.com"

# 添加文件
git add .

# 提交
git commit -m "Initial commit: 抖音评论抓取工具"

# 连接远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/仓库名.git

# 设置主分支
git branch -M main

# 推送代码
git push -u origin main
```

---

## 🎉 完成！

上传成功后，你的项目就可以：
- ✅ 被其他人看到和使用
- ✅ 通过 GitHub 下载
- ✅ 接受 Issue 和 Pull Request
- ✅ 进行版本管理

祝上传顺利！🚀
