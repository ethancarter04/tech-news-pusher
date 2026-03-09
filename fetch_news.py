import os
import requests
import feedparser
from datetime import datetime, timedelta
import pytz

# 从 GitHub Secrets 获取密钥
SENDKEY = os.environ.get("SERVER_CHAN_SENDKEY")
RSS_URL = "https://www.solidot.org/index.rss"

# 伪装浏览器头，防止被反爬
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_recent_news():
    try:
        feed = feedparser.parse(RSS_URL, request_headers=HEADERS)
        now_utc = datetime.now(pytz.utc)
        time_threshold = now_utc - timedelta(hours=24)
        
        news_list = []
        for entry in feed.entries:
            if hasattr(entry, 'published_parsed'):
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
                if pub_time >= time_threshold:
                    news_list.append({
                        "title": entry.title,
                        "link": entry.link,
                        "pub_date": pub_time.strftime("%Y-%m-%d %H:%M:%S")
                    })
        return news_list
    except Exception as e:
        print(f"抓取新闻出错: {e}")
        return []

def send_to_serverchan(news_list):
    if not SENDKEY:
        print("错误：未找到 SERVER_CHAN_SENDKEY 环境变量")
        return

    if not news_list:
        title = "今日科技资讯 (暂无更新)"
        content = "过去24小时内没有新的科技资讯，或抓取暂时失败。"
    else:
        title = f"今日科技资讯早报 (共 {len(news_list)} 条)"
        content = "### 过去24小时科技资讯汇总\n\n"
        for i, news in enumerate(news_list, 1):
            content += f"{i}. **[{news['title']}]({news['link']})**\n\n"
            
    api_url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
    try:
        requests.post(api_url, data={"title": title, "desp": content}, timeout=10)
        print("推送成功")
    except Exception as e:
        print(f"推送失败: {e}")

if __name__ == "__main__":
    recent_news = fetch_recent_news()
    send_to_serverchan(recent_news)
