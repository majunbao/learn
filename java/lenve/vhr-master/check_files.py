import os

docs_dir = 'docs'

garbled_files = []
good_files = []

for filename in os.listdir(docs_dir):
    if filename.endswith('.md') and filename != 'README.md':
        filepath = os.path.join(docs_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if content has valid Chinese characters
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in content)
        
        # Check if content has garbled characters (mojibake pattern)
        # Common garbled patterns: æ, å, ç, è, é, etc.
        has_garbled = any(char in 'æåçèéêëìíîïòóôõöùúûüýÿ' for char in content)
        
        if has_garbled and not has_chinese:
            garbled_files.append(filename)
            print(f'Garbled: {filename}')
        elif has_chinese:
            good_files.append(filename)
            print(f'Good: {filename}')
        else:
            garbled_files.append(filename)
            print(f'Unknown: {filename}')

print(f'\nTotal good files: {len(good_files)}')
print(f'Total garbled files: {len(garbled_files)}')
print('\nGarbled files list:')
for f in garbled_files:
    print(f)