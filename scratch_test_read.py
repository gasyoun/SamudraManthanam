path = "Index/lib/x86_64-win64/Data/mbh01.html"

def try_read(path, encoding):
    try:
        with open(path, 'r', encoding=encoding) as f:
            line = f.readline()
            print(f"[{encoding}] First line: {line.strip()}")
            return True
    except Exception as e:
        print(f"[{encoding}] Error: {e}")
        return False

try_read(path, 'utf-8')
try_read(path, 'windows-1251')
