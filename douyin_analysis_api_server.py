"""
抖音数据分析 HTTP API 服务
提供数据采集、分析、导出等所有功能的 HTTP 接口
独立实现，不依赖 MCP server
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
import uvicorn
import asyncio
import logging
from datetime import datetime
import sys
import os
import json
import pandas as pd
from pathlib import Path
import threading
import time
from urllib.parse import quote
from bs4 import BeautifulSoup
import jieba
from collections import Counter

# 导入 DrissionPage（如果可用）
try:
    from DrissionPage import ChromiumPage
    DRISSION_AVAILABLE = True
except ImportError:
    DRISSION_AVAILABLE = False
    logging.warning("DrissionPage 未安装，数据采集功能将不可用")

# 配置日志（支持通过环境变量 LOG_LEVEL 调整）
_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="抖音数据分析 API",
    description="抖音评论抓取工具：数据采集、分析、导出",
    version="2.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局数据存储
data_storage = {
    "videos": [],  # 视频数据
    "users": [],   # 用户数据
    "collection_tasks": {}  # 采集任务状态
}

# 请求/响应模型
class SearchRequest(BaseModel):
    """搜索采集请求"""
    keyword: str = Field(..., description="搜索关键词")
    search_type: Literal["video", "user"] = Field("video", description="搜索类型：video=视频，user=用户")
    scroll_count: int = Field(100, description="滚动次数", ge=1, le=1000)
    delay: float = Field(2.0, description="延迟时间（秒）", ge=0.5, le=10.0)


class CollectionStatusResponse(BaseModel):
    """采集状态响应"""
    task_id: str
    status: str  # running, completed, failed
    progress: float  # 0-100
    collected_count: int
    message: str


class AnalysisRequest(BaseModel):
    """数据分析请求"""
    data_type: Literal["video", "user"] = Field("video", description="数据类型")
    analysis_type: Literal["interaction", "content_length", "keywords"] = Field(
        ..., description="分析类型：interaction=互动数据，content_length=内容长度，keywords=高频词汇"
    )


class ExportRequest(BaseModel):
    """数据导出请求"""
    data_type: Literal["video", "user"] = Field("video", description="数据类型")
    format: Literal["excel", "json"] = Field("json", description="导出格式")


class CommentRequest(BaseModel):
    """视频评论请求"""
    video_url: str = Field(..., description="抖音视频链接")
    limit: int = Field(50, ge=1, le=500, description="最多抓取的评论条数")


class KeywordCommentRequest(BaseModel):
    """按关键词批量获取视频评论请求"""
    keyword: str = Field(..., description="搜索关键词")
    scroll_count: int = Field(80, ge=1, le=1000, description="搜索时的滚动次数")
    delay: float = Field(2.0, ge=0.5, le=10.0, description="每次滚动的延迟（秒）")
    max_videos: int = Field(10, ge=1, le=50, description="按热度选取的最大视频数量")
    per_video_limit: int = Field(50, ge=1, le=500, description="每个视频最多抓取的评论条数")


class UserCommentRequest(BaseModel):
    """按用户名/ID获取用户所有视频的评论请求"""
    user_input: str = Field(..., description="用户名或用户ID（抖音号）")
    per_video_limit: int = Field(50, ge=1, le=500, description="每个视频最多抓取的评论条数")
    scroll_count: int = Field(100, ge=1, le=500, description="用户主页滚动次数")
    delay: float = Field(2.0, ge=0.5, le=10.0, description="滚动延迟（秒）")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str
    features: List[str]
    timestamp: str


# 数据采集类（基于 douyin_analyzer.py）
class DouyinDataCollector:
    """抖音数据采集器"""
    
    def __init__(self):
        self.page = None
        self.is_running = False
        self.collected_data = []
    
    def init_browser(self):
        """初始化浏览器"""
        if not DRISSION_AVAILABLE:
            raise Exception("DrissionPage 未安装，无法进行数据采集")
        
        try:
            if self.page is None:
                self.page = ChromiumPage()
                time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"初始化浏览器失败: {e}")
            raise
    
    def clean_text(self, text):
        """清理文本"""
        return str(text).replace('\n', ' ').replace('\r', '').strip()
    
    def format_number(self, num_str):
        """格式化数字字符串"""
        try:
            num = int(num_str)
            if num >= 10000:
                return f"{num / 10000:.1f}万"
            return str(num)
        except ValueError:
            return num_str
    
    def extract_video_items(self, html):
        """提取视频数据"""
        soup = BeautifulSoup(html, 'html.parser')
        video_items = soup.select("li.SwZLHMKk")
        video_data = []
        
        for item in video_items:
            try:
                video_link = item.select_one('a.hY8lWHgA')
                if not video_link:
                    continue
                
                data = {
                    'video_url': video_link.get('href', '').strip(),
                    'cover_image': item.select_one('img').get('src', '').strip() if item.select_one('img') else '',
                    'title': item.select_one('div.VDYK8Xd7').get_text(strip=True) if item.select_one('div.VDYK8Xd7') else '无标题',
                    'author': item.select_one('span.MZNczJmS').get_text(strip=True) if item.select_one('span.MZNczJmS') else '未知作者',
                    'publish_time': item.select_one('span.faDtinfi').get_text(strip=True) if item.select_one('span.faDtinfi') else '',
                    'likes': item.select_one('span.cIiU4Muu').get_text(strip=True) if item.select_one('span.cIiU4Muu') else '0'
                }
                
                data = {k: self.clean_text(v) for k, v in data.items()}
                
                if data.get('video_url'):
                    video_data.append(data)
            except Exception as e:
                logger.debug(f"提取视频数据错误: {e}")
                continue
        
        return video_data
    
    def extract_user_data(self, html):
        """提取用户数据"""
        soup = BeautifulSoup(html, 'html.parser')
        user_items = soup.select("div.search-result-card > a.hY8lWHgA.poLTDMYS")
        user_data = []
        
        for item in user_items:
            try:
                user_link = item.get('href', '')
                title_elem = item.select_one('div.XQwChAbX p.v9LWb7QE span span span span span')
                title = title_elem.get_text(strip=True) if title_elem else ''
                avatar_elem = item.select_one('img.RlLOO79h')
                avatar_url = avatar_elem.get('src', '') if avatar_elem else ''
                
                stats_div = item.select_one('div.jjebLXt0')
                douyin_id = ''
                likes = '0'
                followers = '0'
                
                if stats_div:
                    spans = stats_div.select('span')
                    for span in spans:
                        text = span.get_text(strip=True)
                        if '抖音号:' in text or '抖音号：' in text:
                            id_span = span.select_one('span')
                            if id_span:
                                douyin_id = id_span.get_text(strip=True)
                        elif '获赞' in text:
                            likes = text.replace('获赞', '').strip()
                        elif '粉丝' in text:
                            followers = text.replace('粉丝', '').strip()
                
                desc_elem = item.select_one('p.Kdb5Km3i span span span span span')
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                data = {
                    'title': title,
                    'douyin_id': douyin_id,
                    'likes': likes,
                    'followers': followers,
                    'description': description,
                    'avatar_url': avatar_url,
                    'user_link': user_link
                }
                
                data = {k: self.clean_text(str(v)) for k, v in data.items()}
                
                if data.get('title'):
                    user_data.append(data)
            except Exception as e:
                logger.debug(f"提取用户数据错误: {e}")
                continue
        
        return user_data
    
    async def collect_user_videos(self, user_input: str, scroll_count: int, delay: float):
        """采集用户主页的所有视频"""
        try:
            logger.info(f"[user] collecting videos for user={user_input!r} scroll_count={scroll_count}")
            self.is_running = True
            self.collected_data = []
            
            if not self.init_browser():
                raise Exception("浏览器初始化失败")
            
            # 构建用户主页URL（支持用户名或ID）
            if user_input.startswith("http"):
                user_url = user_input
            elif "/" in user_input or user_input.startswith("@"):
                # 如果是 @username 格式，去掉 @
                username = user_input.lstrip("@")
                user_url = f"https://www.douyin.com/user/{username}"
            else:
                # 假设是抖音号或用户名
                user_url = f"https://www.douyin.com/user/{user_input}"
            
            logger.info(f"[user] opening user page: {user_url}")
            self.page.get(user_url)
            await asyncio.sleep(5)
            
            last_height = self.page.run_js("return document.body.scrollHeight")
            
            for i in range(scroll_count):
                if not self.is_running:
                    break
                
                try:
                    self.page.run_js("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(delay)
                    
                    new_height = self.page.run_js("return document.body.scrollHeight")
                    if new_height == last_height:
                        logger.info("[user] 已到达页面底部")
                        break
                    last_height = new_height
                    
                    page_source = self.page.html
                    new_data = self.extract_video_items(page_source)
                    
                    for data in new_data:
                        if data not in self.collected_data:
                            self.collected_data.append(data)
                    
                    logger.info(f"[user] scroll={i+1} collected={len(self.collected_data)} videos")
                    
                except Exception as e:
                    logger.error(f"[user] 滚动错误: {e}")
                    continue
            
            logger.info(f"[user] done collected={len(self.collected_data)} videos")
            return self.collected_data
            
        except Exception as e:
            logger.error(f"[user] 采集失败: {e}", exc_info=True)
            raise
        finally:
            self.is_running = False
            if self.page:
                try:
                    self.page.quit()
                except:
                    pass
                self.page = None
    
    async def collect_search_data(self, keyword: str, search_type: str, scroll_count: int, delay: float, task_id: str):
        """采集搜索数据（异步）"""
        try:
            logger.info(f"[collect] task={task_id} keyword={keyword!r} type={search_type} scroll_count={scroll_count} delay={delay}")
            self.is_running = True
            self.collected_data = []
            
            if not self.init_browser():
                raise Exception("浏览器初始化失败")
            
            search_url = f"https://www.douyin.com/search/{quote(keyword)}?source=normal_search&type={search_type}"
            logger.info(f"[collect] 访问搜索URL: {search_url}")
            
            self.page.get(search_url)
            await asyncio.sleep(5)
            
            last_height = self.page.run_js("return document.body.scrollHeight")
            
            for i in range(scroll_count):
                if not self.is_running:
                    logger.warning(f"[collect] task={task_id} 被停止，提前退出（i={i}/{scroll_count}）")
                    break
                
                try:
                    self.page.run_js("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(delay)
                    
                    new_height = self.page.run_js("return document.body.scrollHeight")
                    if new_height == last_height:
                        logger.info("已到达页面底部")
                        break
                    last_height = new_height
                    
                    page_source = self.page.html
                    
                    if search_type == 'user':
                        new_data = self.extract_user_data(page_source)
                    else:
                        container = BeautifulSoup(page_source, 'html.parser').select_one('[data-e2e="scroll-list"]')
                        if container:
                            new_data = self.extract_video_items(str(container))
                        else:
                            continue
                    
                    for data in new_data:
                        if data not in self.collected_data:
                            self.collected_data.append(data)
                    
                    progress = ((i + 1) / scroll_count) * 100
                    data_storage["collection_tasks"][task_id] = {
                        "status": "running",
                        "progress": progress,
                        "collected_count": len(self.collected_data),
                        "message": f"正在滚动... ({i+1}/{scroll_count})"
                    }
                    if (i + 1) % max(1, scroll_count // 10) == 0:
                        logger.info(f"[collect] task={task_id} progress={progress:.1f}% collected={len(self.collected_data)}")
                    
                except Exception as e:
                    logger.error(f"滚动错误: {e}")
                    continue
            
            # 保存数据
            if search_type == 'user':
                data_storage["users"] = self.collected_data
            else:
                data_storage["videos"] = self.collected_data
            
            data_storage["collection_tasks"][task_id] = {
                "status": "completed",
                "progress": 100,
                "collected_count": len(self.collected_data),
                "message": f"采集完成，共获取 {len(self.collected_data)} 条数据"
            }
            logger.info(f"[collect] task={task_id} 完成 collected={len(self.collected_data)}")
            
        except Exception as e:
            logger.error(f"[collect] task={task_id} 采集失败: {e}", exc_info=True)
            data_storage["collection_tasks"][task_id] = {
                "status": "failed",
                "progress": 0,
                "collected_count": 0,
                "message": f"采集失败: {str(e)}"
            }
        finally:
            self.is_running = False
            if self.page:
                try:
                    self.page.quit()
                except:
                    pass
                self.page = None


# 数据分析类
class DouyinDataAnalyzer:
    """抖音数据分析器"""
    
    @staticmethod
    def analyze_interaction_data(data: List[dict]) -> dict:
        """分析互动数据"""
        if not data:
            raise Exception("没有可分析的数据")
        
        likes_data = []
        for item in data:
            likes = str(item.get('likes', '0'))
            try:
                if '万' in likes:
                    num = float(likes.replace('万', '')) * 10000
                    likes_data.append(int(num))
                else:
                    likes_data.append(int(likes))
            except (ValueError, TypeError):
                continue
        
        if not likes_data:
            raise Exception("无法解析点赞数据")
        
        total_likes = sum(likes_data)
        avg_likes = total_likes / len(likes_data)
        max_likes = max(likes_data)
        
        return {
            "total_count": len(data),
            "total_likes": total_likes,
            "avg_likes": round(avg_likes, 2),
            "max_likes": max_likes,
            "min_likes": min(likes_data)
        }
    
    @staticmethod
    def analyze_content_length(data: List[dict]) -> dict:
        """分析内容长度"""
        if not data:
            raise Exception("没有可分析的数据")
        
        title_lengths = [len(str(item.get('title', ''))) for item in data]
        
        length_ranges = [
            {"range": "0-10", "count": 0, "percentage": 0},
            {"range": "11-20", "count": 0, "percentage": 0},
            {"range": "21-30", "count": 0, "percentage": 0},
            {"range": "31-50", "count": 0, "percentage": 0},
            {"range": "51-100", "count": 0, "percentage": 0},
            {"range": "100+", "count": 0, "percentage": 0}
        ]
        
        for length in title_lengths:
            if length <= 10:
                length_ranges[0]["count"] += 1
            elif length <= 20:
                length_ranges[1]["count"] += 1
            elif length <= 30:
                length_ranges[2]["count"] += 1
            elif length <= 50:
                length_ranges[3]["count"] += 1
            elif length <= 100:
                length_ranges[4]["count"] += 1
            else:
                length_ranges[5]["count"] += 1
        
        total = len(title_lengths)
        for r in length_ranges:
            r["percentage"] = round((r["count"] / total) * 100, 2) if total > 0 else 0
        
        return {
            "total_count": total,
            "avg_length": round(sum(title_lengths) / total, 2),
            "max_length": max(title_lengths),
            "min_length": min(title_lengths),
            "length_distribution": length_ranges
        }
    
    @staticmethod
    def analyze_keywords(data: List[dict], top_n: int = 100) -> dict:
        """分析高频词汇"""
        if not data:
            raise Exception("没有可分析的数据")
        
        all_titles = ' '.join(str(item.get('title', '')) for item in data)
        
        stop_words = {
            '的', '了', '是', '在', '我', '有', '和', '就', '都', '而', '及', '与', '着', '或', '等', '为',
            '一个', '没有', '这个', '那个', '但是', '而且', '只是', '不过', '这样', '一样', '一直', '一些',
            '这', '那', '也', '你', '我们', '他们', '它们', '把', '被', '让', '向', '往', '但', '去', '又',
            '能', '好', '给', '到', '看', '想', '要', '会', '多', '这些', '那些', '什么', '怎么', '如何',
            '为什么', '可以', '因为', '所以', '应该', '可能'
        }
        
        words = []
        for word in jieba.cut(all_titles):
            if len(word) > 1 and word not in stop_words:
                words.append(word)
        
        word_counts = Counter(words)
        top_words = word_counts.most_common(top_n)
        
        return {
            "total_titles": len(data),
            "total_words": len(words),
            "unique_words": len(word_counts),
            "top_keywords": [
                {
                    "rank": rank + 1,
                    "word": word,
                    "count": count,
                    "frequency": round((count / len(words)) * 100, 2) if words else 0
                }
                for rank, (word, count) in enumerate(top_words)
            ]
        }


# 全局采集器实例
collector = DouyinDataCollector()
analyzer = DouyinDataAnalyzer()


class DouyinCommentFetcher:
    """抖音评论抓取器"""

    def __init__(self, max_scrolls: int = 30):
        self.max_scrolls = max_scrolls

    async def resolve_video_url(self, url: str) -> str:
        """
        解析搜索页/弹窗链接到真正的视频详情页 URL：
        - 如果本身就是 /video/ 链接，直接返回
        - 否则打开页面，等待跳转，取最终 location.href
        """
        if "/video/" in url:
            norm = _normalize_douyin_url(url)
            logger.info(f"[resolve] already video url -> {norm}")
            return norm

        if not DRISSION_AVAILABLE:
            raise Exception("DrissionPage 未安装，无法解析视频链接")

        page = None
        try:
            # 使用有头模式（更稳定）
            page = ChromiumPage()
            logger.info(f"[resolve] opening url: {url}")
            page.get(url)
            await asyncio.sleep(5)
            final_url = page.run_js("return location.href;")
            if not final_url:
                final_url = page.url
            norm = _normalize_douyin_url(final_url)
            logger.info(f"[resolve] final url -> {norm}")
            return norm
        finally:
            if page:
                try:
                    page.quit()
                except Exception:
                    pass

    @staticmethod
    def _extract_comments_from_html(html: str):
        """从页面 HTML 中提取评论文本（只提取用户实际说的话）"""
        soup = BeautifulSoup(html, "html.parser")
        comments = []
        seen = set()

        # 抖音评论的多种可能选择器（按优先级）
        # 注意：要排除点赞数、回复数等数字，只取评论文本
        selectors = [
            # 最精确：评论详情文本
            'span[data-e2e="comment-level-1"]',
            'div[data-e2e="comment-level-1"] span',
            'p[data-e2e="comment-detail"]',
            'div[data-e2e="comment-item"] span',
            'li[data-e2e="comment-item"] span',
            # 通用评论容器中的文本节点
            'div[class*="CommentItem"] span',
            'div[class*="comment-item"] span',
        ]

        for selector in selectors:
            elements = soup.select(selector)
            logger.debug(f"[extract] selector={selector} found {len(elements)} elements")
            
            for ele in elements:
                # 获取纯文本，排除子元素中的数字（如点赞数）
                text = ele.get_text(" ", strip=True)
                
                # 过滤掉明显不是评论的内容：
                # - 太短（可能是数字或符号）
                # - 包含"点赞"、"回复"等关键词
                # - 是纯数字
                if not text or len(text) < 2:
                    continue
                if any(kw in text for kw in ["点赞", "回复", "条评论", "评论"]):
                    continue
                if text.isdigit() or (text.replace(".", "").isdigit()):
                    continue
                
                # 去重
                if text not in seen:
                    seen.add(text)
                    comments.append(text)
                    logger.debug(f"[extract] added comment: {text[:50]}...")
            
            if comments:
                logger.info(f"[extract] found {len(comments)} comments with selector={selector}")
                break  # 找到即返回

        # 如果还是没找到，尝试更宽泛的选择器（但要加强过滤）
        if not comments:
            logger.warning("[extract] no comments found with specific selectors, trying fallback")
            for ele in soup.select('div[class*="comment"], li[class*="comment"], span[class*="comment"]'):
                text = ele.get_text(" ", strip=True)
                # 更严格的过滤
                if text and len(text) > 5 and text not in seen:
                    # 排除数字、符号、常见UI文本
                    if not text.isdigit() and not any(kw in text for kw in ["点赞", "回复", "条", "评论数"]):
                        seen.add(text)
                        comments.append(text)

        logger.info(f"[extract] total extracted: {len(comments)} unique comments")
        return comments

    async def fetch_comments(self, video_url: str, limit: int = 50):
        """抓取视频评论，返回评论文本列表（只包含用户实际说的话）"""
        if not DRISSION_AVAILABLE:
            raise Exception("DrissionPage 未安装，无法抓取评论")

        page = None
        try:
            # DrissionPage 的 ChromiumPage 不支持 headless 参数
            # 默认使用有头模式（更稳定，抖音需要登录态）
            # 如果需要无头模式，需要通过 ChromiumOptions 配置，但抖音评论抓取建议用有头模式
            page = ChromiumPage()
            
            logger.info(f"[comments] opening video: {video_url} limit={limit}")
            page.get(video_url)
            await asyncio.sleep(8)  # 等待页面加载

            # 尝试点击"评论"按钮/标签（如果存在）
            try:
                comment_btn = page.ele('text:评论', timeout=3)
                if comment_btn:
                    comment_btn.click()
                    logger.info("[comments] clicked comment tab")
                    await asyncio.sleep(2)
            except Exception:
                logger.debug("[comments] no comment tab found or already open")

            comments = []
            seen = set()
            no_new_count = 0  # 连续没有新评论的次数

            for scroll_idx in range(self.max_scrolls):
                if len(comments) >= limit:
                    logger.info(f"[comments] reached limit: {len(comments)}/{limit}")
                    break

                html = page.html
                new_comments = self._extract_comments_from_html(html)

                added = 0
                for c in new_comments:
                    if c not in seen:
                        seen.add(c)
                        comments.append(c)
                        added += 1
                        if len(comments) >= limit:
                            break

                if added == 0:
                    no_new_count += 1
                    if no_new_count >= 3:  # 连续3次没有新评论，可能已经到底了
                        logger.info(f"[comments] no new comments for 3 scrolls, stopping")
                        break
                else:
                    no_new_count = 0

                logger.info(f"[comments] scroll={scroll_idx+1} collected={len(comments)}/{limit} (added={added})")

                # 滚动评论区域（而不是整个页面）
                # 尝试找到评论容器并滚动它
                try:
                    # 先尝试滚动评论容器
                    page.run_js("""
                        const commentArea = document.querySelector('[data-e2e="comment-list"], .comment-list, [class*="CommentList"]');
                        if (commentArea) {
                            commentArea.scrollTop = commentArea.scrollHeight;
                        } else {
                            window.scrollTo(0, document.body.scrollHeight);
                        }
                    """)
                except Exception:
                    # 兜底：滚动整个页面
                    page.run_js("window.scrollTo(0, document.body.scrollHeight)")
                
                await asyncio.sleep(1.5)

            result = comments[:limit]
            logger.info(f"[comments] final result: {len(result)} comments extracted")
            
            # 调试：打印前3条评论内容（确保是文本而不是数字）
            if result:
                logger.info(f"[comments] sample comments (first 3):")
                for i, c in enumerate(result[:3], 1):
                    logger.info(f"[comments]   #{i}: {c[:100]}...")
            
            return result

        except Exception as e:
            logger.error(f"[comments] error fetching comments: {e}", exc_info=True)
            raise
        finally:
            if page:
                try:
                    page.quit()
                except Exception:
                    pass


comment_fetcher = DouyinCommentFetcher()


def _parse_like_number(likes: str) -> int:
    """解析点赞数字符串（支持“万”）"""
    if not likes:
        return 0
    s = str(likes)
    try:
        if "万" in s:
            num = float(s.replace("万", "")) * 10000
            return int(num)
        return int(float(s))
    except Exception:
        return 0


def _normalize_douyin_url(url: str) -> str:
    """将采集到的抖音相对链接转换为完整链接"""
    if not url:
        return url
    if url.startswith("http"):
        return url
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return "https://www.douyin.com" + url
    return "https://www.douyin.com/" + url


@app.get("/", response_model=HealthResponse)
async def root():
    """根路径"""
    features = [
        "数据采集（关键词搜索、视频/用户搜索）",
        "数据分析（互动数据、内容长度、高频词汇）",
        "数据导出（Excel、JSON）"
    ]
    if DRISSION_AVAILABLE:
        features.append("浏览器自动化采集")
    else:
        features.append("（需要安装 DrissionPage 才能使用采集功能）")
    
    return HealthResponse(
        status="running",
        service="抖音数据分析 API",
        version="2.0.0",
        features=features,
        timestamp=datetime.now().isoformat()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return await root()


@app.post("/api/collect/search")
async def start_collection(request: SearchRequest, background_tasks: BackgroundTasks):
    """开始搜索采集"""
    if not DRISSION_AVAILABLE:
        raise HTTPException(status_code=503, detail="DrissionPage 未安装，无法进行数据采集")
    
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    data_storage["collection_tasks"][task_id] = {
        "status": "running",
        "progress": 0,
        "collected_count": 0,
        "message": "正在启动采集..."
    }
    
    # 在后台运行采集任务
    background_tasks.add_task(
        collector.collect_search_data,
        request.keyword,
        request.search_type,
        request.scroll_count,
        request.delay,
        task_id
    )
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "采集任务已启动",
        "status_url": f"/api/collect/status/{task_id}"
    }


@app.get("/api/collect/status/{task_id}")
async def get_collection_status(task_id: str):
    """获取采集状态"""
    if task_id not in data_storage["collection_tasks"]:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    status = data_storage["collection_tasks"][task_id]
    return CollectionStatusResponse(
        task_id=task_id,
        **status
    )


@app.post("/api/collect/stop/{task_id}")
async def stop_collection(task_id: str):
    """停止采集"""
    collector.is_running = False
    if task_id in data_storage["collection_tasks"]:
        data_storage["collection_tasks"][task_id]["status"] = "stopped"
        data_storage["collection_tasks"][task_id]["message"] = "采集已停止"
    
    return {"success": True, "message": "采集已停止"}


@app.get("/api/data/videos")
async def get_videos():
    """获取采集的视频数据"""
    return {
        "success": True,
        "count": len(data_storage["videos"]),
        "data": data_storage["videos"]
    }


@app.get("/api/data/users")
async def get_users():
    """获取采集的用户数据"""
    return {
        "success": True,
        "count": len(data_storage["users"]),
        "data": data_storage["users"]
    }


@app.post("/api/analyze")
async def analyze_data(request: AnalysisRequest):
    """数据分析"""
    data = data_storage["videos"] if request.data_type == "video" else data_storage["users"]
    
    if not data:
        raise HTTPException(status_code=400, detail=f"没有可分析的{request.data_type}数据")
    
    try:
        if request.analysis_type == "interaction":
            result = analyzer.analyze_interaction_data(data)
        elif request.analysis_type == "content_length":
            result = analyzer.analyze_content_length(data)
        elif request.analysis_type == "keywords":
            result = analyzer.analyze_keywords(data)
        else:
            raise HTTPException(status_code=400, detail="不支持的分析类型")
        
        return {
            "success": True,
            "data_type": request.data_type,
            "analysis_type": request.analysis_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/api/export")
async def export_data(request: ExportRequest):
    """导出数据"""
    data = data_storage["videos"] if request.data_type == "video" else data_storage["users"]
    
    if not data:
        raise HTTPException(status_code=400, detail=f"没有可导出的{request.data_type}数据")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        if request.format == "json":
            filename = f"douyin_{request.data_type}_{timestamp}.json"
            filepath = Path(filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return FileResponse(
                filepath,
                media_type='application/json',
                filename=filename
            )
        
        elif request.format == "excel":
            filename = f"douyin_{request.data_type}_{timestamp}.xlsx"
            filepath = Path(filename)
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False)
            
            return FileResponse(
                filepath,
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                filename=filename
            )
        
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@app.post("/api/video/comments")
async def get_video_comments(request: CommentRequest):
    """获取单个视频的评论并返回 comment 列表"""
    if not DRISSION_AVAILABLE:
        raise HTTPException(status_code=503, detail="DrissionPage 未安装，无法抓取评论")

    try:
        # 支持搜索页/弹窗链接，先解析成真正视频页
        real_url = await comment_fetcher.resolve_video_url(request.video_url)
        comments = await comment_fetcher.fetch_comments(real_url, request.limit)

        # 更新已采集的视频的评论数，便于前端排序
        for v in data_storage["videos"]:
            norm = _normalize_douyin_url(v.get("video_url") or "")
            if norm == real_url:
                v["comment_count"] = len(comments)

        return {
            "success": True,
            "video_url": real_url,
            "count": len(comments),
            "comments": [{"comment": c} for c in comments]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抓取评论失败: {str(e)}")


@app.post("/api/keyword/comments")
async def get_comments_by_keyword(request: KeywordCommentRequest):
    """
    根据关键词：
    1）搜索视频
    2）按热度（点赞数）选出前 max_videos 个
    3）对每个视频抓取最多 per_video_limit 条评论
    4）返回合并后的评论列表（只含 comment 节点）
    """
    if not DRISSION_AVAILABLE:
        raise HTTPException(status_code=503, detail="DrissionPage 未安装，无法抓取评论")

    logger.info(
        f"[keyword] keyword={request.keyword!r} max_videos={request.max_videos} per_video_limit={request.per_video_limit} "
        f"scroll_count={request.scroll_count} delay={request.delay}"
    )

    # 1. 先执行一次搜索采集（视频）
    task_id = f"keyword_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    try:
        await collector.collect_search_data(
            keyword=request.keyword,
            search_type="video",
            scroll_count=request.scroll_count,
            delay=request.delay,
            task_id=task_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索采集失败: {str(e)}")

    videos = collector.collected_data or []
    if not videos:
        logger.warning(f"[keyword] no videos collected for keyword={request.keyword!r}")
        return {
            "success": True,
            "keyword": request.keyword,
            "video_count": 0,
            "comment_count": 0,
            "comments": [],
        }

    # 保存到全局（可选）
    data_storage["videos"] = videos

    # 2. 按点赞数排序，取前 max_videos 个
    videos_sorted = sorted(
        videos,
        key=lambda v: _parse_like_number(v.get("likes", "0")),
        reverse=True,
    )
    top_videos = videos_sorted[: request.max_videos]
    logger.info(f"[keyword] collected_videos={len(videos)} top_videos={len(top_videos)}")
    for idx, v in enumerate(top_videos[:10], 1):
        logger.info(
            f"[keyword] top#{idx} likes={v.get('likes')} title={str(v.get('title',''))[:30]!r} url={_normalize_douyin_url(v.get('video_url') or '')}"
        )

    # 3. 逐个视频抓取评论
    all_comments: list[dict] = []
    total_comments = 0

    for v in top_videos:
        raw_url = v.get("video_url") or ""
        full_url = _normalize_douyin_url(raw_url)
        # 如果不是视频详情链接，尝试解析真实视频 URL
        if "/video/" not in full_url:
            try:
                full_url = await comment_fetcher.resolve_video_url(full_url)
            except Exception as e:
                logger.warning(f"解析视频链接失败: {full_url} - {e}")
                continue
        try:
            logger.info(f"[keyword] fetching comments for {full_url}")
            comments = await comment_fetcher.fetch_comments(
                full_url, request.per_video_limit
            )
            # 更新视频的评论数
            v["comment_count"] = len(comments)
            # 合并到总列表，只保留 comment 字段
            for c in comments:
                all_comments.append({"comment": c})
            total_comments += len(comments)
            logger.info(f"[keyword] comments_ok url={full_url} count={len(comments)} total={total_comments}")
        except Exception as e:
            logger.warning(f"抓取视频评论失败: {full_url} - {e}")
            continue

    logger.info(f"[keyword] done keyword={request.keyword!r} videos_used={len(top_videos)} total_comments={total_comments}")
    return {
        "success": True,
        "keyword": request.keyword,
        "video_count": len(top_videos),
        "comment_count": total_comments,
        "comments": all_comments,
    }


@app.post("/api/user/comments")
async def get_comments_by_user(request: UserCommentRequest):
    """
    根据用户名/ID：
    1）打开用户主页
    2）获取用户所有视频
    3）对每个视频抓取最多 per_video_limit 条评论
    4）返回合并后的评论列表（只含 comment 节点）
    """
    if not DRISSION_AVAILABLE:
        raise HTTPException(status_code=503, detail="DrissionPage 未安装，无法抓取评论")
    
    logger.info(
        f"[user] user_input={request.user_input!r} per_video_limit={request.per_video_limit} "
        f"scroll_count={request.scroll_count} delay={request.delay}"
    )
    
    # 1. 采集用户主页的所有视频
    try:
        videos = await collector.collect_user_videos(
            request.user_input,
            request.scroll_count,
            request.delay
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户视频失败: {str(e)}")
    
    if not videos:
        logger.warning(f"[user] no videos found for user={request.user_input!r}")
        return {
            "success": True,
            "user_input": request.user_input,
            "video_count": 0,
            "comment_count": 0,
            "comments": [],
        }
    
    logger.info(f"[user] collected_videos={len(videos)}")
    for idx, v in enumerate(videos[:10], 1):
        logger.info(
            f"[user] video#{idx} likes={v.get('likes')} title={str(v.get('title',''))[:30]!r} url={_normalize_douyin_url(v.get('video_url') or '')}"
        )
    
    # 2. 逐个视频抓取评论
    all_comments: list[dict] = []
    total_comments = 0
    
    for v in videos:
        raw_url = v.get("video_url") or ""
        full_url = _normalize_douyin_url(raw_url)
        # 如果不是视频详情链接，尝试解析真实视频 URL
        if "/video/" not in full_url:
            try:
                full_url = await comment_fetcher.resolve_video_url(full_url)
            except Exception as e:
                logger.warning(f"解析视频链接失败: {full_url} - {e}")
                continue
        try:
            logger.info(f"[user] fetching comments for {full_url}")
            comments = await comment_fetcher.fetch_comments(
                full_url, request.per_video_limit
            )
            # 合并到总列表，只保留 comment 字段
            for c in comments:
                all_comments.append({"comment": c})
            total_comments += len(comments)
            logger.info(f"[user] comments_ok url={full_url} count={len(comments)} total={total_comments}")
        except Exception as e:
            logger.warning(f"抓取视频评论失败: {full_url} - {e}")
            continue
    
    logger.info(f"[user] done user={request.user_input!r} videos_used={len(videos)} total_comments={total_comments}")
    return {
        "success": True,
        "user_input": request.user_input,
        "video_count": len(videos),
        "comment_count": total_comments,
        "comments": all_comments,
    }


if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"启动抖音数据分析 API 服务: http://{host}:{port}")
    logger.info(f"API 文档: http://{host}:{port}/docs")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
