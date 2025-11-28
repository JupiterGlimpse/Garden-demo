#!/bin/bash
# 快速设置 pyenv 和 Python 3.11.6

echo "🔧 安装 pyenv..."
curl https://pyenv.run | bash

# 配置环境变量
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

echo "📦 安装 Python 3.11.6..."
pyenv install 3.11.6

echo "🎯 设置本地 Python 版本为 3.11.6..."
cd /home/user/Garden-demo
pyenv local 3.11.6

echo "✅ 完成！当前 Python 版本："
python --version

echo ""
echo "📝 接下来运行："
echo "  python -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements_twitter.txt"
