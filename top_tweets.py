#!/usr/bin/env python3
"""
获取指定 Twitter/X 账号在特定时间范围内的高赞/转发 Top5 推文

使用方法:
    python top_tweets.py

依赖安装:
    pip install snscrape
"""

import snscrape.modules.twitter as sntwitter
from datetime import datetime
from typing import List, Dict
import json


class TwitterTopTweetsFetcher:
    """Twitter 高赞推文获取器"""

    def __init__(self, usernames: List[str], start_date: str, end_date: str):
        """
        初始化

        Args:
            usernames: 要查询的用户名列表 (不带@)
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
        """
        self.usernames = usernames
        self.start_date = start_date
        self.end_date = end_date

    def fetch_tweets(self, username: str, max_tweets: int = 100) -> List[Dict]:
        """
        获取指定用户的推文

        Args:
            username: 用户名
            max_tweets: 最多获取推文数量

        Returns:
            推文列表
        """
        tweets = []
        query = f"from:{username} since:{self.start_date} until:{self.end_date}"

        print(f"正在获取 @{username} 的推文...")

        try:
            for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
                if i >= max_tweets:
                    break

                tweets.append({
                    'id': tweet.id,
                    'date': tweet.date.strftime('%Y-%m-%d %H:%M:%S'),
                    'content': tweet.rawContent,
                    'likes': tweet.likeCount or 0,
                    'retweets': tweet.retweetCount or 0,
                    'replies': tweet.replyCount or 0,
                    'url': tweet.url,
                    'username': username
                })

        except Exception as e:
            print(f"获取 @{username} 推文时出错: {e}")

        return tweets

    def get_top_tweets(self, tweets: List[Dict], top_n: int = 5,
                       sort_by: str = 'likes') -> List[Dict]:
        """
        获取 Top N 推文

        Args:
            tweets: 推文列表
            top_n: 返回前 N 条
            sort_by: 排序依据 ('likes', 'retweets', 'combined')

        Returns:
            Top N 推文列表
        """
        if sort_by == 'combined':
            # 综合考虑点赞和转发
            sorted_tweets = sorted(
                tweets,
                key=lambda x: x['likes'] + x['retweets'] * 2,  # 转发权重更高
                reverse=True
            )
        else:
            sorted_tweets = sorted(
                tweets,
                key=lambda x: x[sort_by],
                reverse=True
            )

        return sorted_tweets[:top_n]

    def run(self, max_tweets_per_user: int = 100, top_n: int = 5,
            sort_by: str = 'likes') -> Dict[str, List[Dict]]:
        """
        执行获取所有账号的 Top 推文

        Args:
            max_tweets_per_user: 每个用户最多获取推文数
            top_n: 返回前 N 条
            sort_by: 排序依据

        Returns:
            每个用户的 Top 推文
        """
        results = {}

        for username in self.usernames:
            tweets = self.fetch_tweets(username, max_tweets_per_user)
            top_tweets = self.get_top_tweets(tweets, top_n, sort_by)
            results[username] = top_tweets

            print(f"\n@{username} 的 Top {top_n} 推文 (按 {sort_by} 排序):")
            print("-" * 80)
            for i, tweet in enumerate(top_tweets, 1):
                print(f"\n{i}. [{tweet['date']}]")
                print(f"   ❤️  {tweet['likes']} | 🔄 {tweet['retweets']} | 💬 {tweet['replies']}")
                print(f"   {tweet['content'][:100]}{'...' if len(tweet['content']) > 100 else ''}")
                print(f"   🔗 {tweet['url']}")

        return results

    def save_to_json(self, results: Dict[str, List[Dict]], filename: str = 'top_tweets.json'):
        """保存结果到 JSON 文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到 {filename}")


def main():
    """主函数 - 在这里配置你的参数"""

    # ============= 配置区域 =============
    # 要查询的账号列表（不带 @ 符号）
    USERNAMES = [
        'elonmusk',
        'OpenAI',
        # 在这里添加更多账号...
    ]

    # 时间范围
    START_DATE = '2024-01-01'  # 开始日期
    END_DATE = '2024-12-31'    # 结束日期

    # 每个账号最多获取多少条推文（越多越慢但越准确）
    MAX_TWEETS_PER_USER = 100

    # 返回 Top N
    TOP_N = 5

    # 排序方式: 'likes' (点赞数), 'retweets' (转发数), 'combined' (综合)
    SORT_BY = 'likes'
    # ===================================

    fetcher = TwitterTopTweetsFetcher(
        usernames=USERNAMES,
        start_date=START_DATE,
        end_date=END_DATE
    )

    results = fetcher.run(
        max_tweets_per_user=MAX_TWEETS_PER_USER,
        top_n=TOP_N,
        sort_by=SORT_BY
    )

    # 保存结果
    fetcher.save_to_json(results)


if __name__ == '__main__':
    main()
