import os

docs_dir = 'docs'

for filename in os.listdir(docs_dir):
    if filename.endswith('.md') and filename != 'README.md':
        filepath = os.path.join(docs_dir, filename)
        
        # Read current UTF-8 content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if content looks like garbled text (mojibake)
        # UTF-8 interpreted as latin-1 then saved as UTF-8
        # To recover: read as latin-1, then decode as GBK
        
        try:
            # Convert UTF-8 back to bytes
            bytes_content = content.encode('latin-1')
            # Try to decode as GBK
            recovered_content = bytes_content.decode('gbk')
            
            # Check if recovered content has valid Chinese
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in recovered_content)
            
            if has_chinese:
                # Save recovered content as UTF-8
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(recovered_content)
                print(f'Recovered: {filename}')
            else:
                print(f'Skipped: {filename} (no Chinese found)')
        except Exception as e:
            print(f'Error: {filename} - {e}')

print('Done!')