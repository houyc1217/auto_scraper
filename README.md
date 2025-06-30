# Auto Scraper

一个自动化新闻抓取和同步工具，支持多站点抓取并同步到Dify知识库。

## 功能特点

- 支持多站点新闻抓取
- 自动同步到Dify知识库
- 可配置的抓取规则
- 智能会话池管理
- 防反爬虫策略

## 项目结构

## 配置说明

在 `config.yaml` 中配置：
- 目标网站信息
- 抓取规则
- Dify API设置

## 运行方式

```bash
# Windows
run_sync.bat

# 其他系统
python main.py
```

## 安装依赖
pip install -r requirements.txt