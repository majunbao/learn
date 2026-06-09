import os
import chardet

docs_dir = 'docs'

for filename in os.listdir(docs_dir):
    if filename.endswith('.md') and filename != 'README.md':
        filepath = os.path.join(docs_dir, filename)
        
        # Read raw bytes
        with open(filepath, 'rb') as f:
            raw_bytes = f.read()
        
        # Try to decode with different encodings
        content = None
        used_encoding = None
        
        # Try common Chinese encodings first
        for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
            try:
                content = raw_bytes.decode(enc)
                used_encoding = enc
                break
            except:
                continue
        
        # If all failed, use chardet
        if content is None:
            detected = chardet.detect(raw_bytes)
            encoding = detected['encoding']
            if encoding:
                try:
                    content = raw_bytes.decode(encoding)
                    used_encoding = encoding
                except:
                    pass
        
        # If still failed, use latin-1 as fallback
        if content is None:
            content = raw_bytes.decode('latin-1')
            used_encoding = 'latin-1'
        
        # Check if content looks like valid Chinese
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in content)
        
        if used_encoding != 'utf-8' or not has_chinese:
            # Write back with UTF-8
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Converted: {filename} (from {used_encoding} to utf-8)')
        else:
            print(f'Skipped: {filename} (already utf-8)')

print('Done!')