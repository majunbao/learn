import os
import re
import requests
from bs4 import BeautifulSoup

docs_dir = 'docs'

# 乱码文件列表
garbled_files = [
    '01.权限数据库设计.md',
    '04.密码加密并加盐.md',
    '10.角色资源关系管理.md',
    '11.用户角色关系管理.md',
    '12.部门数据库设计与存储过程编写.md',
    '15.职位管理和职称管理功能介绍.md',
    '17.利用git标签回退至任意版本.md',
    '18.员工基本信息管理功能介绍.md',
    '20.高级搜索功能介绍.md',
    '23.POI生成Excel.md',
    '26.SpringBoot中使用Freemarker邮件模板生成邮件.md',
    '27.Java中邮件的发送.md',
    '29.工资账套管理功能介绍.md',
    '30.员工账套设置功能介绍.md',
    '31.在线聊天功能介绍.md',
    '33.系统通知功能实现.md',
    '34.两年了，微人事重大更新.md',
    '44.Spring Boot+Vue首页加载优化-1.md',
    '45.Spring Boot+Vue首页加载优化-2.md',
    '48.Spring Boot+Vue 如何避免前端页面 404.md',
    '51.前后端分离以及Vue.js入门.md',
    '54.简化微人事部署，Flyway 搞起来.md'
]

# 提取文件编号
def get_article_num(filename):
    match = re.search(r'^(\d+)', filename)
    if match:
        return match.group(1)
    return None

# 构建URL
def build_url(num):
    # 根据编号构建URL
    # 格式: https://vhr.javaboy.org/YYYY/MMDD/vhr-NUM
    # 需要根据编号确定日期
    
    # 从archive页面获取正确的URL
    base_url = 'https://vhr.javaboy.org/archive.html'
    response = requests.get(base_url)
    content = response.text
    
    # 查找对应的URL
    pattern = f'https://vhr\\.javaboy\\.org/\\d{{4}}/\\d{{4}}/vhr-{num}'
    match = re.search(pattern, content)
    if match:
        return match.group(0)
    return None

# 获取文章内容
def fetch_article(url):
    response = requests.get(url)
    html = response.text
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 提取标题
    title_tag = soup.find('h1')
    if title_tag:
        title = title_tag.get_text().strip()
    else:
        title = 'Unknown'
    
    # 提取正文
    content_div = soup.find('div', class_='post-content')
    if not content_div:
        content_div = soup.find('article')
    
    if content_div:
        # 转换HTML到Markdown
        # 处理标题
        for h2 in content_div.find_all('h2'):
            h2.replace_with(f'\n## {h2.get_text()}\n')
        for h3 in content_div.find_all('h3'):
            h3.replace_with(f'\n### {h3.get_text()}\n')
        for h4 in content_div.find_all('h4'):
            h4.replace_with(f'\n#### {h4.get_text()}\n')
        
        # 处理代码块
        for pre in content_div.find_all('pre'):
            code = pre.find('code')
            if code:
                lang = code.get('class', [''])[0].replace('language-', '')
                code_text = code.get_text()
                pre.replace_with(f'\n```{lang}\n{code_text}\n```\n')
            else:
                pre.replace_with(f'\n```\n{pre.get_text()}\n```\n')
        
        for code in content_div.find_all('code'):
            if code.parent.name != 'pre':
                code.replace_with(f'`{code.get_text()}`')
        
        # 处理链接
        for a in content_div.find_all('a'):
            href = a.get('href', '')
            text = a.get_text()
            a.replace_with(f'[{text}]({href})')
        
        # 处理图片
        for img in content_div.find_all('img'):
            src = img.get('src', '')
            # 转换为本地路径
            if 'doubaocdn.com' in src:
                img_id = src.split('/')[-1]
                img.replace_with(f'![](images/{img_id}.png)')
            else:
                img.replace_with(f'![]({src})')
        
        # 处理列表
        for ul in content_div.find_all('ul'):
            for li in ul.find_all('li'):
                li.replace_with(f'- {li.get_text()}\n')
        for ol in content_div.find_all('ol'):
            for i, li in enumerate(ol.find_all('li'), 1):
                li.replace_with(f'{i}. {li.get_text()}\n')
        
        # 处理段落
        for p in content_div.find_all('p'):
            p.replace_with(f'{p.get_text()}\n\n')
        
        # 处理强调
        for strong in content_div.find_all('strong'):
            strong.replace_with(f'**{strong.get_text()}**')
        for em in content_div.find_all('em'):
            em.replace_with(f'*{em.get_text()}*')
        
        # 获取文本
        text = content_div.get_text()
        
        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return title, text, url
    
    return title, '', url

# 处理每个乱码文件
for filename in garbled_files:
    num = get_article_num(filename)
    if num:
        print(f'Fetching article {num}...')
        
        url = build_url(num)
        if url:
            try:
                title, content, article_url = fetch_article(url)
                
                # 构建完整文档
                full_content = f'# {num}.{title}\n\n{content}\n\n> 原文链接：{article_url}'
                
                # 保存文件
                filepath = os.path.join(docs_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(full_content)
                
                print(f'Saved: {filename}')
            except Exception as e:
                print(f'Error fetching {filename}: {e}')
        else:
            print(f'URL not found for {filename}')

print('Done!')