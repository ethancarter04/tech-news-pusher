# import os
# import requests
# import feedparser
# from datetime import datetime, timedelta
# import pytz

# # 从 GitHub Secrets 获取密钥
# SENDKEY = os.environ.get("SERVER_CHAN_SENDKEY")
# RSS_URL = "https://www.solidot.org/index.rss"

# # 伪装浏览器头，防止被反爬
# HEADERS = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
# }

# def fetch_recent_news():
#     try:
#         feed = feedparser.parse(RSS_URL, request_headers=HEADERS)
#         now_utc = datetime.now(pytz.utc)
#         time_threshold = now_utc - timedelta(hours=24)
        
#         news_list = []
#         for entry in feed.entries:
#             if hasattr(entry, 'published_parsed'):
#                 pub_time = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
#                 if pub_time >= time_threshold:
#                     news_list.append({
#                         "title": entry.title,
#                         "link": entry.link,
#                         "pub_date": pub_time.strftime("%Y-%m-%d %H:%M:%S")
#                     })
#         return news_list
#     except Exception as e:
#         print(f"抓取新闻出错: {e}")
#         return []

# def send_to_serverchan(news_list):
#     if not SENDKEY:
#         print("错误：未找到 SERVER_CHAN_SENDKEY 环境变量")
#         return

#     if not news_list:
#         title = "今日科技资讯 (暂无更新)"
#         content = "过去24小时内没有新的科技资讯，或抓取暂时失败。"
#     else:
#         title = f"今日科技资讯早报 (共 {len(news_list)} 条)"
#         content = "### 过去24小时科技资讯汇总\n\n"
#         for i, news in enumerate(news_list, 1):
#             content += f"{i}. **[{news['title']}]({news['link']})**\n\n"
            
#     api_url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
#     try:
#         requests.post(api_url, data={"title": title, "desp": content}, timeout=10)
#         print("推送成功")
#     except Exception as e:
#         print(f"推送失败: {e}")

# if __name__ == "__main__":
#     recent_news = fetch_recent_news()
#     send_to_serverchan(recent_news)


import os
import requests
import feedparser
from datetime import datetime, timedelta
import pytz

# ================= [新增/修改部分：配置区] =================
SENDKEY = os.environ.get("SERVER_CHAN_SENDKEY")
# [新增] 钉钉机器人的 Webhook 地址，同样从 Secrets 读取
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK")

# [修改] 将单一链接改为支持多个站点的列表，这里加了 V2EX 作为演示
RSS_SOURCES = [
    {"name": "Solidot奇客", "url": "https://www.solidot.org/index.rss"},
    {"name": "V2EX最热", "url": "https://www.v2ex.com/index.xml"} 
]
# ===========================================================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_recent_news():
    now_utc = datetime.now(pytz.utc)
    time_threshold = now_utc - timedelta(hours=24)
    all_news = []
    
    # ================= [修改部分：循环抓取多个源] =================
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"], request_headers=HEADERS)
            for entry in feed.entries:
                if hasattr(entry, 'published_parsed'):
                    pub_time = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
                    if pub_time >= time_threshold:
                        all_news.append({
                            "source": source["name"], # [新增] 记录资讯来源，方便排版
                            "title": entry.title,
                            "link": entry.link,
                            "pub_date": pub_time.strftime("%Y-%m-%d %H:%M:%S")
                        })
        except Exception as e:
            print(f"抓取 {source['name']} 出错: {e}")
    # =============================================================
    return all_news

# ================= [新增部分：提取公共的排版逻辑] =================
# 因为微信和钉钉都要发送一样的内容，我们把“排版”这部分独立成一个函数
def build_markdown_content(news_list):
    if not news_list:
        return "今日科技资讯 (暂无更新)", "过去24小时内没有新的科技资讯，或抓取暂时失败。"
        
    title = f"今日科技资讯早报 (共 {len(news_list)} 条)"
    content = "### 过去24小时科技资讯汇总\n\n"
    for i, news in enumerate(news_list, 1):
        # [修改] 拼接排版时，把上面提取到的 [来源名称] 加在标题前面
        content += f"{i}. **[{news['source']}]** [{news['title']}]({news['link']})\n\n"
    return title, content
# =================================================================

def send_to_serverchan(title, content):
    if not SENDKEY:
        print("未配置 SERVER_CHAN_SENDKEY，跳过微信推送")
        return
    api_url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
    try:
        requests.post(api_url, data={"title": title, "desp": content}, timeout=10)
        print("Server酱微信推送成功")
    except Exception as e:
        print(f"Server酱推送失败: {e}")

# ================= [新增部分：钉钉推送函数] =================
def send_to_dingtalk(title, content):
    if not DINGTALK_WEBHOOK:
        print("未配置 DINGTALK_WEBHOOK，跳过钉钉推送")
        return
    
    # 钉钉机器人要求的特定 JSON 格式
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": f"# {title}\n\n{content}"
        }
    }
    try:
        requests.post(DINGTALK_WEBHOOK, json=data, timeout=10)
        print("钉钉群组推送成功")
    except Exception as e:
        print(f"钉钉推送失败: {e}")
# ===========================================================

if __name__ == "__main__":
    recent_news = fetch_recent_news()
    # 1. 先把新闻列表交给排版函数，生成标题和内容
    msg_title, msg_content = build_markdown_content(recent_news)
    
    # 2. [新增] 分别调用两个推送通道。如果不配置钉钉Webhook，它会自动跳过，只发微信
    send_to_serverchan(msg_title, msg_content)
    send_to_dingtalk(msg_title, msg_content)
