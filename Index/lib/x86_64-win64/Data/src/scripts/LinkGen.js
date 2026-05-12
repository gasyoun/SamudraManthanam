// Объект с соответствиями слов для замены
const replacements = {
    'Слово1': 'ссылка1',
    'Слово2': 'ссылка2',
    'Слово3': 'ссылка3'
    // добавьте остальные пары слов и ссылок по аналогии
};

// Функция для замены слов в тексте
function replaceWords(text) {
    // Проходим по каждому ключу объекта replacements
    Object.keys(replacements).forEach(word => {
        // Создаем регулярное выражение для поиска слова с учетом регистра
        const regex = new RegExp('\\b' + word + '\\b', 'gi');
        // Заменяем найденные слова на слова из объекта replacements
        text = text.replace(regex, replacements[word]);
    });
    return text;
}

// Пример использования функции replaceWords
const exampleText = 'Текст с Слово1 и Слово2, которые будут заменены';
const newText = replaceWords(exampleText);
console.log(newText);
