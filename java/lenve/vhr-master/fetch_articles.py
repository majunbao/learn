import os
import re
import requests

docs_dir = 'docs'
images_dir = 'docs/images'

# 重新创建docs目录
if not os.path.exists(docs_dir):
    os.makedirs(docs_dir)
if not os.path.exists(images_dir):
    os.makedirs(images_dir)

# 获取所有文章URL
base_url = 'https://vhr.javaboy.org/archive.html'

print('Fetching article list...')
response = requests.get(base_url)
content = response.text

# 提取文章链接
article_urls = re.findall(r'https://vhr\.javaboy\.org/\d{4}/\d{4}/vhr-\d+', content)
article_urls = list(set(article_urls))
article_urls.sort(key=lambda x: int(re.search(r'vhr-(\d+)', x).group(1)))

print(f'Found {len(article_urls)} articles')

for url in article_urls:
    num = re.search(r'vhr-(\d+)', url).group(1)
    
    print(f'Fetching article {num}...')
    
    try:
        resp = requests.get(url)
        html = resp.text
        
        # 提取标题
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
        if title_match:
            title = title_match.group(1).strip()
        else:
            title = f'Article {num}'
        
        # 提取正文内容
        # 找到文章主体部分
        content_match = re.search(r'<div class="post-content"[^>]*>(.*?)</div>\s*</article>', html, re.DOTALL)
        if content_match:
            article_content = content_match.group(1)
        else:
            article_content = html
        
        # 转换HTML到Markdown
        # 替换标题
        article_content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', article_content)
        article_content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', article_content)
        article_content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', article_content)
        
        # 替换代码块
        article_content = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'\n```\n\1\n```\n', article_content, flags=re.DOTALL)
        article_content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', article_content)
        
        # 替换链接
        article_content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', article_content)
        
        # 替换图片
        article_content = re.sub(r'<img[^>]*src="([^"]*)"[^>]*>', r'![](\1)', article_content)
        
        # 替换列表
        article_content = re.sub(r'<ul[^>]*>(.*?)</ul>', r'\1', article_content, flags=re.DOTALL)
        article_content = re.sub(r'<ol[^>]*>(.*?)</ol>', r'\1', article_content, flags=re.DOTALL)
        article_content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', article_content)
        
        # 替换段落
        article_content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', article_content, flags=re.DOTALL)
        
        # 替换强调
        article_content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', article_content)
        article_content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', article_content)
        
        # 清理HTML标签
        article_content = re.sub(r'<[^>]+>', '', article_content)
        
        # 清理多余空行
        article_content = re.sub(r'\n{3,}', '\n\n', article_content)
        
        # 构建完整文档
        full_content = f'# {num}.{title}\n\n{article_content}\n\n> 原文链接：{url}'
        
        # 保存文件
        filename = f'{num}.{title}.md'
        filepath = os.path.join(docs_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        print(f'Saved: {filename}')
        
    except Exception as e:
        print(f'Error fetching article {num}: {e}')

print('Done!')