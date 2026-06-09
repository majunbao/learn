import os
import re
import chardet

docs_dir = 'docs'

for filename in os.listdir(docs_dir):
    if filename.endswith('.md') and filename != 'README.md':
        filepath = os.path.join(docs_dir, filename)
        
        # Read raw bytes
        with open(filepath, 'rb') as f:
            raw_bytes = f.read()
        
        # Detect encoding
        detected = chardet.detect(raw_bytes)
        encoding = detected['encoding']
        
        if encoding is None:
            encoding = 'utf-8'
        
        # Try to decode
        try:
            content = raw_bytes.decode(encoding)
        except:
            # Fallback to common encodings
            for enc in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                try:
                    content = raw_bytes.decode(enc)
                    encoding = enc
                    break
                except:
                    continue
        
        # Find the original link
        link_match = re.search(r'^> 原文链接：(https://[^\n]+)', content)
        
        if link_match:
            link_line = link_match.group(0)
            
            # Remove the link line
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                if line.startswith('> 原文链接：'):
                    continue
                new_lines.append(line)
            
            # Remove trailing empty lines
            while new_lines and new_lines[-1].strip() == '':
                new_lines.pop()
            
            # Add link at end
            new_lines.append('')
            new_lines.append(link_line)
            
            # Write back with UTF-8
            new_content = '\n'.join(new_lines)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f'Updated: {filename} (from {encoding} to utf-8)')
        else:
            # Just convert encoding
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Converted: {filename} (from {encoding} to utf-8)')

print('Done!')