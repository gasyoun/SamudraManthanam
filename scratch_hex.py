path = "Index/lib/x86_64-win64/Data/Словарь Смирнова.txt"
with open(path, 'rb') as f:
    raw = f.read(100)
    print(raw.hex(' '))
