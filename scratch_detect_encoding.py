import chardet

def detect(path):
    with open(path, 'rb') as f:
        raw = f.read(10000)
        return chardet.detect(raw)

path = "Index/lib/x86_64-win64/Data/mbh01.html"
print(detect(path))
