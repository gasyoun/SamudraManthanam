path = "Index/lib/x86_64-win64/Data/Словарь Смирнова.txt"
with open(path, 'r', encoding='windows-1251') as f:
    line = f.readline().strip()
    print(f"CP1251: {line}")
