# import os    //第一版本
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


# import os    //第二版本
# import requests
# import feedparser
# from datetime import datetime, timedelta
# import pytz

# # ================= [新增/修改部分：配置区] =================
# SENDKEY = os.environ.get("SERVER_CHAN_SENDKEY")
# # [新增] 钉钉机器人的 Webhook 地址，同样从 Secrets 读取
# DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK")

# # [修改] 将单一链接改为支持多个站点的列表，这里加了 V2EX 作为演示
# RSS_SOURCES = [
#     {"name": "Solidot奇客", "url": "https://www.solidot.org/index.rss"},
#     {"name": "V2EX最热", "url": "https://www.v2ex.com/index.xml"} 
# ]
# # ===========================================================

# HEADERS = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
# }

# def fetch_recent_news():
#     now_utc = datetime.now(pytz.utc)
#     time_threshold = now_utc - timedelta(hours=24)
#     all_news = []
    
#     # ================= [修改部分：循环抓取多个源] =================
#     for source in RSS_SOURCES:
#         try:
#             feed = feedparser.parse(source["url"], request_headers=HEADERS)
#             for entry in feed.entries:
#                 if hasattr(entry, 'published_parsed'):
#                     pub_time = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
#                     if pub_time >= time_threshold:
#                         all_news.append({
#                             "source": source["name"], # [新增] 记录资讯来源，方便排版
#                             "title": entry.title,
#                             "link": entry.link,
#                             "pub_date": pub_time.strftime("%Y-%m-%d %H:%M:%S")
#                         })
#         except Exception as e:
#             print(f"抓取 {source['name']} 出错: {e}")
#     # =============================================================
#     return all_news

# # ================= [新增部分：提取公共的排版逻辑] =================
# # 因为微信和钉钉都要发送一样的内容，我们把“排版”这部分独立成一个函数
# def build_markdown_content(news_list):
#     if not news_list:
#         return "今日科技资讯 (暂无更新)", "过去24小时内没有新的科技资讯，或抓取暂时失败。"
        
#     title = f"今日科技资讯早报 (共 {len(news_list)} 条)"
#     content = "### 过去24小时科技资讯汇总\n\n"
#     for i, news in enumerate(news_list, 1):
#         # [修改] 拼接排版时，把上面提取到的 [来源名称] 加在标题前面
#         content += f"{i}. **[{news['source']}]** [{news['title']}]({news['link']})\n\n"
#     return title, content
# # =================================================================

# def send_to_serverchan(title, content):
#     if not SENDKEY:
#         print("未配置 SERVER_CHAN_SENDKEY，跳过微信推送")
#         return
#     api_url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
#     try:
#         requests.post(api_url, data={"title": title, "desp": content}, timeout=10)
#         print("Server酱微信推送成功")
#     except Exception as e:
#         print(f"Server酱推送失败: {e}")


# # ================= [修改部分：钉钉推送函数，加入关键词和请求头] =================
# def send_to_dingtalk(title, content):
#     if not DINGTALK_WEBHOOK:
#         print("未配置 DINGTALK_WEBHOOK，跳过钉钉推送")
#         return
    
#     # 你的钉钉机器人安全设置关键词
#     KEYWORD = "新闻"
    
#     # 构造消息体，确保标题和正文中都包含关键词
#     data = {
#         "msgtype": "markdown",
#         "markdown": {
#             "title": f"【{KEYWORD}】{title}",
#             "text": f"# 【{KEYWORD}】{title}\n\n{content}\n\n---\n*{KEYWORD}机器人自动发送*"
#         }
#     }
    
#     # 明确指定发送 JSON 格式的数据
#     headers = {'Content-Type': 'application/json'}
    
#     try:
#         # 加上 headers，并打印 resp.text 方便我们在 Actions 日志里看报错详情
#         resp = requests.post(DINGTALK_WEBHOOK, json=data, headers=headers, timeout=10)
#         print(f"钉钉群组推送结果: {resp.text}")
#     except Exception as e:
#         print(f"钉钉推送失败: {e}")
# # ===========================================================
# # ===========================================================

# if __name__ == "__main__":
#     recent_news = fetch_recent_news()
#     # 1. 先把新闻列表交给排版函数，生成标题和内容
#     msg_title, msg_content = build_markdown_content(recent_news)
    
#     # 2. [新增] 分别调用两个推送通道。如果不配置钉钉Webhook，它会自动跳过，只发微信
#     send_to_serverchan(msg_title, msg_content)
#     send_to_dingtalk(msg_title, msg_content)

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# ================= 配置区 =================
SENDKEY = os.environ.get("SERVER_CHAN_SENDKEY")
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# [新增] 把你找到的精确网址放进监控列表，支持同时监控多个省份
TARGET_URLS = [
    {"name": "上海", "url": "https://www.zgjsks.com/html/zhaopin/sh/"},
    {"name": "江苏", "url": "https://www.zgjsks.com/html/zhaopin/js/"}
]

# ================= 炸山核心逻辑 =================
def fetch_jobs():
    jobs_list = []
    
    for target in TARGET_URLS:
        try:
            print(f"正在侦察 [{target['name']}] 考区: {target['url']}")
            resp = requests.get(target['url'], headers=HEADERS, timeout=15)
            resp.encoding = resp.apparent_encoding 
            
            if resp.status_code != 200:
                print(f"[{target['name']}] 遭遇防线！状态码: {resp.status_code}")
                continue
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 中公全国站的列表通用排版，通常在 zg_news_list 或 list 类的标签下
            list_items = soup.select('.zg_news_list li, .list li, .news_list li')
            
            print(f"[{target['name']}] 雷达扫描到 {len(list_items)} 条疑似公告情报...")
            
            # 每个省份取最顶部的 10 条最新公告进行分析
            for item in list_items[:10]:
                link_elem = item.find('a')
                date_elem = item.find('span')
                
                if link_elem and link_elem.text.strip():
                    title = link_elem.text.strip()
                    link = link_elem.get('href', '')
                    
                    # 补全相对路径网址
                    if link.startswith('/'):
                        link = "https://www.zgjsks.com" + link
                        
                    pub_date = date_elem.text.strip() if date_elem else "近期发布"
                    
                    # 【精准过滤】只保留真正带有官方性质的字眼
                    if "招聘" in title or "公告" in title or "录用" in title or "拟聘" in title:
                        jobs_list.append({
                            "region": target["name"], # 记录是哪个省的
                            "title": title,
                            "date": pub_date,
                            "link": link
                        })
                        
        except Exception as e:
            print(f"[{target['name']}] 炸山过程中出现意外: {e}")
            
    return jobs_list

# ================= 排版与推送逻辑 =================
def build_markdown_content(jobs_list):
    if not jobs_list:
        return "今日江沪教师招考 (暂无更新)", "今日暂未抓取到新的官方招聘公告，或页面结构需要校准。"
        
    title = f"今日江沪教师招考情报 (共 {len(jobs_list)} 条)"
    content = "### 最新教育局/公办学校招聘公告汇总\n\n"
    content += "> *温馨提示：请点击链接查看官方公告原文，并下载底部的 Excel 职位表搜索“音乐”等专业岗位。*\n\n"
    
    for i, job in enumerate(jobs_list, 1):
        # [修改] 在推送的标题前面加上 [上海] 或 [江苏] 的地区标签
        content += f"{i}. **[{job['region']}] [{job['title']}]({job['link']})**\n"
        content += f"   * 发布时间: <font color='#808080'>{job['date']}</font>\n\n"
    return title, content

def send_to_serverchan(title, content):
    if not SENDKEY: return
    try:
        requests.post(f"https://sctapi.ftqq.com/{SENDKEY}.send", data={"title": title, "desp": content}, timeout=10)
    except Exception as e:
        pass

def send_to_dingtalk(title, content):
    if not DINGTALK_WEBHOOK: return
    KEYWORD = "新闻" # 确保和钉钉机器人的安全关键词一致
    data = {"msgtype": "markdown", "markdown": {"title": f"【{KEYWORD}】{title}", "text": f"# 【{KEYWORD}】{title}\n\n{content}\n\n---\n*{KEYWORD}机器人自动监控*"}}
    try:
        requests.post(DINGTALK_WEBHOOK, json=data, headers={'Content-Type': 'application/json'}, timeout=10)
        print("钉钉推送尝试完成")
    except Exception as e:
        print(f"钉钉推送失败: {e}")

# ================= GitHub Actions 专属启动开关 =================
if __name__ == "__main__":
    print("挖掘机启动，开始执行公办招考抓取任务...")
    jobs = fetch_jobs()
    msg_title, msg_content = build_markdown_content(jobs)
    
    send_to_serverchan(msg_title, msg_content)
    send_to_dingtalk(msg_title, msg_content)
    print("任务执行完毕！")
