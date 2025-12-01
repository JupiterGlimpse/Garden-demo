# Twitter 高赞推文获取脚本

## 简介

这是一个简单的 Python 脚本，用于获取指定 Twitter/X 账号在特定时间范围内的高赞/转发 Top5 推文。

**特点:**
- ✅ 无需 API key
- ✅ 简单易用
- ✅ 性能良好
- ✅ 支持多账号批量查询
- ✅ **自动翻译为中文**

## 安装依赖

```bash
pip install snscrape deep-translator
```

或者使用 requirements 文件：

```bash
pip install -r requirements_twitter.txt
```

## 使用方法

### 1. 编辑配置

打开 `top_tweets.py` 文件，修改配置区域的参数：

```python
# 要查询的账号列表（不带 @ 符号）
USERNAMES = [
    'elonmusk',
    'OpenAI',
    # 添加更多账号...
]

# 时间范围
START_DATE = '2024-01-01'  # 开始日期
END_DATE = '2024-12-31'    # 结束日期

# 每个账号最多获取多少条推文
MAX_TWEETS_PER_USER = 100

# 返回 Top N
TOP_N = 5

# 排序方式: 'likes' (点赞数), 'retweets' (转发数), 'combined' (综合)
SORT_BY = 'likes'

# 是否翻译为中文（推荐开启）
TRANSLATE_TO_CHINESE = True
```

### 2. 运行脚本

```bash
python top_tweets.py
```

### 3. 查看结果

结果会输出到终端，同时保存到 `top_tweets.json` 文件。

## 输出示例

```
正在获取 @elonmusk 的推文...

@elonmusk 的 Top 5 推文 (按 点赞数 排序):
--------------------------------------------------------------------------------

1. [2024-03-15 10:30:00]
   ❤️  125000 | 🔄 45000 | 💬 8500
   这是一个示例推文内容的中文翻译...
   [原文] This is an example tweet content...
   🔗 https://twitter.com/elonmusk/status/123456789

2. [2024-03-14 15:20:00]
   ❤️  98000 | 🔄 32000 | 💬 6200
   另一条推文的中文翻译...
   [原文] Another example tweet...
   🔗 https://twitter.com/elonmusk/status/123456788
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `USERNAMES` | 要查询的账号列表 | `['elonmusk', 'OpenAI']` |
| `START_DATE` | 开始日期 | `'2024-01-01'` |
| `END_DATE` | 结束日期 | `'2024-12-31'` |
| `MAX_TWEETS_PER_USER` | 每账号最多获取推文数 | `100` |
| `TOP_N` | 返回前 N 条 | `5` |
| `SORT_BY` | 排序方式 | `'likes'` |
| `TRANSLATE_TO_CHINESE` | 是否翻译为中文 | `True` |

### 排序方式说明

- `'likes'`: 按点赞数排序
- `'retweets'`: 按转发数排序
- `'combined'`: 综合排序（点赞 + 转发×2）

## 注意事项

1. **速率限制**: 请求过于频繁可能被限制，建议合理设置 `MAX_TWEETS_PER_USER`
2. **网络问题**: 如果遇到网络错误，请稍后重试
3. **账号名**: 使用账号用户名（不带 @ 符号）
4. **日期格式**: 使用 `YYYY-MM-DD` 格式

## 故障排除

### 问题: 安装 snscrape 失败

**解决方案:**

```bash
# 使用 pip 最新版本
pip install --upgrade pip

# 从 GitHub 安装最新版本
pip install git+https://github.com/JustAnotherArchivist/snscrape.git
```

### 问题: 获取推文失败

**可能原因:**
- 网络连接问题
- Twitter/X 限制爬虫
- 账号不存在或已被封禁

**建议:**
- 检查网络连接
- 减少 `MAX_TWEETS_PER_USER` 数量
- 确认账号名正确

## 性能优化建议

1. **减少查询范围**: 缩小时间范围可以加快速度
2. **降低获取数量**: 减少 `MAX_TWEETS_PER_USER` 可以更快完成
3. **批量处理**: 如果账号很多，可以分批运行

## License

MIT
