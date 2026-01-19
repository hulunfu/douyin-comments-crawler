# API 接口说明文档

## 基础信息

- **服务地址**: `http://127.0.0.1:8000`
- **API 文档**: `http://127.0.0.1:8000/docs` (Swagger UI)
- **服务版本**: 2.0.0

## 接口列表

### 1. 健康检查

**GET** `/health`

检查服务是否正常运行。

**响应示例：**
```json
{
  "status": "running",
  "service": "抖音数据分析 API",
  "version": "2.0.0",
  "features": [
    "数据采集（关键词搜索、视频/用户搜索）",
    "数据分析（互动数据、内容长度、高频词汇）",
    "数据导出（Excel、JSON）",
    "浏览器自动化采集"
  ],
  "timestamp": "2025-01-19T20:00:00"
}
```

---

### 2. 关键词搜索并抓取评论

**POST** `/api/keyword/comments`

根据关键词搜索视频，按热度排序后抓取前 N 个视频的评论。

**请求体：**
```json
{
  "keyword": "益生菌",
  "max_videos": 10,
  "per_video_limit": 50,
  "scroll_count": 80,
  "delay": 2.0
}
```

**参数说明：**
- `keyword` (string, 必需): 搜索关键词
- `max_videos` (int, 可选): 选取的视频数量（按点赞数排序），默认 10，范围 1-50
- `per_video_limit` (int, 可选): 每个视频最多抓取的评论数，默认 50，范围 1-500
- `scroll_count` (int, 可选): 搜索时的滚动次数，默认 80，范围 1-1000
- `delay` (float, 可选): 每次滚动的延迟（秒），默认 2.0，范围 0.5-10.0

**响应示例：**
```json
{
  "success": true,
  "keyword": "益生菌",
  "video_count": 10,
  "comment_count": 500,
  "comments": [
    { "comment": "这个配方不错，我试过了" },
    { "comment": "喝了肚子不舒服" },
    { "comment": "在哪里买的？" }
  ]
}
```

**使用示例（Python）：**
```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/api/keyword/comments",
    json={
        "keyword": "益生菌",
        "max_videos": 10,
        "per_video_limit": 50
    }
)
data = response.json()
print(f"共获取 {data['comment_count']} 条评论")
```

---

### 3. 单个视频评论抓取

**POST** `/api/video/comments`

直接通过视频链接抓取该视频的评论。

**请求体：**
```json
{
  "video_url": "https://www.douyin.com/video/7100767495958678821",
  "limit": 50
}
```

**参数说明：**
- `video_url` (string, 必需): 视频链接，支持以下格式：
  - 视频详情页：`https://www.douyin.com/video/xxxxx`
  - 分享链接：`https://v.douyin.com/xxxxx/`
  - 搜索页链接：`https://www.douyin.com/root/search/...modal_id=xxxxx`
- `limit` (int, 可选): 最多抓取的评论数，默认 50，范围 1-500

**响应示例：**
```json
{
  "success": true,
  "video_url": "https://www.douyin.com/video/7100767495958678821",
  "count": 50,
  "comments": [
    { "comment": "评论内容1" },
    { "comment": "评论内容2" }
  ]
}
```

**使用示例（curl）：**
```bash
curl -X POST "http://127.0.0.1:8000/api/video/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.douyin.com/video/7100767495958678821",
    "limit": 50
  }'
```

---

### 4. 用户所有视频评论抓取

**POST** `/api/user/comments`

根据用户名或ID，获取该用户所有视频的评论。

**请求体：**
```json
{
  "user_input": "@username",
  "per_video_limit": 50,
  "scroll_count": 100,
  "delay": 2.0
}
```

**参数说明：**
- `user_input` (string, 必需): 用户名或用户ID，支持以下格式：
  - 用户名：`@username` 或 `username`
  - 抖音号：直接输入抖音号
  - 主页链接：`https://www.douyin.com/user/xxxxx`
- `per_video_limit` (int, 可选): 每个视频最多抓取的评论数，默认 50，范围 1-500
- `scroll_count` (int, 可选): 用户主页滚动次数，默认 100，范围 1-500
- `delay` (float, 可选): 滚动延迟（秒），默认 2.0，范围 0.5-10.0

**响应示例：**
```json
{
  "success": true,
  "user_input": "@username",
  "video_count": 20,
  "comment_count": 1000,
  "comments": [
    { "comment": "评论内容1" },
    { "comment": "评论内容2" }
  ]
}
```

**使用示例（JavaScript）：**
```javascript
fetch('http://127.0.0.1:8000/api/user/comments', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_input: '@username',
    per_video_limit: 50
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

---

### 5. 数据采集（搜索）

**POST** `/api/collect/search`

启动关键词搜索采集任务（异步）。

**请求体：**
```json
{
  "keyword": "科技",
  "search_type": "video",
  "scroll_count": 100,
  "delay": 2.0
}
```

**响应：**
```json
{
  "success": true,
  "task_id": "task_20250119_200000_123456",
  "message": "采集任务已启动",
  "status_url": "/api/collect/status/task_20250119_200000_123456"
}
```

---

### 6. 查询采集状态

**GET** `/api/collect/status/{task_id}`

查询采集任务的当前状态。

**响应示例：**
```json
{
  "task_id": "task_20250119_200000_123456",
  "status": "running",
  "progress": 45.5,
  "collected_count": 23,
  "message": "正在滚动... (45/100)"
}
```

**状态值：**
- `running`: 正在采集
- `completed`: 采集完成
- `failed`: 采集失败
- `stopped`: 已停止

---

### 7. 获取视频数据

**GET** `/api/data/videos`

获取已采集的所有视频数据。

**响应示例：**
```json
{
  "success": true,
  "count": 50,
  "data": [
    {
      "video_url": "https://www.douyin.com/video/xxxxx",
      "cover_image": "https://...",
      "title": "视频标题",
      "author": "作者昵称",
      "publish_time": "2024-01-01",
      "likes": "1.2万"
    }
  ]
}
```

---

### 8. 获取用户数据

**GET** `/api/data/users`

获取已采集的所有用户数据。

**响应示例：**
```json
{
  "success": true,
  "count": 30,
  "data": [
    {
      "title": "用户名",
      "douyin_id": "douyin123",
      "likes": "10万",
      "followers": "5万",
      "description": "用户简介",
      "avatar_url": "https://...",
      "user_link": "https://www.douyin.com/user/xxxxx"
    }
  ]
}
```

---

### 9. 数据分析

**POST** `/api/analyze`

对采集的数据进行分析。

**请求体：**
```json
{
  "data_type": "video",
  "analysis_type": "interaction"
}
```

**参数说明：**
- `data_type`: `"video"` 或 `"user"`
- `analysis_type`: 
  - `"interaction"`: 互动数据分析
  - `"content_length"`: 内容长度分析
  - `"keywords"`: 高频词汇分析

**响应示例（互动数据分析）：**
```json
{
  "success": true,
  "data_type": "video",
  "analysis_type": "interaction",
  "result": {
    "total_count": 50,
    "total_likes": 1250000,
    "avg_likes": 25000,
    "max_likes": 100000,
    "min_likes": 100
  },
  "timestamp": "2025-01-19T20:00:00"
}
```

---

### 10. 数据导出

**POST** `/api/export`

导出采集的数据为文件。

**请求体：**
```json
{
  "data_type": "video",
  "format": "excel"
}
```

**参数说明：**
- `data_type`: `"video"` 或 `"user"`
- `format`: `"excel"` 或 `"json"`

**响应：**
返回文件下载（Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet 或 application/json）

---

## 错误处理

所有接口在出错时都会返回标准的错误响应：

```json
{
  "detail": "错误描述信息"
}
```

**HTTP 状态码：**
- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误
- `503`: 服务不可用（通常是 DrissionPage 未安装）

---

## 注意事项

1. **评论抓取需要时间**：每个视频的评论抓取可能需要 10-30 秒，请耐心等待。

2. **需要登录状态**：首次使用时，浏览器会自动打开，请在浏览器中登录抖音账号。

3. **浏览器窗口**：抓取过程中会打开 Chrome 浏览器窗口，这是正常的，请不要关闭。

4. **并发限制**：建议不要同时发起多个抓取请求，避免资源冲突。

5. **数据格式**：所有评论接口返回的 JSON 格式统一为：
   ```json
   {
     "comments": [
       { "comment": "评论内容" }
     ]
   }
   ```

---

## 完整示例

### Python 完整示例

```python
import requests
import json

# 1. 关键词搜索抓取评论
response = requests.post(
    "http://127.0.0.1:8000/api/keyword/comments",
    json={
        "keyword": "益生菌",
        "max_videos": 5,
        "per_video_limit": 30
    }
)
data = response.json()

# 保存为 JSON 文件
with open("comments.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"共获取 {data['comment_count']} 条评论")
```

### JavaScript 完整示例

```javascript
// 抓取单个视频评论
async function fetchVideoComments(videoUrl) {
    const response = await fetch('http://127.0.0.1:8000/api/video/comments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            video_url: videoUrl,
            limit: 50
        })
    });
    
    const data = await response.json();
    
    // 下载 JSON
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'comments.json';
    a.click();
    
    return data;
}
```

---

更多信息请访问：`http://127.0.0.1:8000/docs` 查看交互式 API 文档。
