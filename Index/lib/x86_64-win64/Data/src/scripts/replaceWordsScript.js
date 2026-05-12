// replaceWordsScript.js
function replaceWords() {
    const wordsToReplace = {
        'Санджая': 'Санджая3',
        'апельсин': 'апельсин3',
        'Дхритараштра': 'Дхритараштра3'
        // Добавьте остальные пары слов и ссылок по аналогии
    };

    const classNames = ['text1', 'text2', 'text3', 'translation']; // Список классов для замены слов

    classNames.forEach(className => {
        const textElements = document.querySelectorAll('.' + className);
        textElements.forEach(textElement => {
            let text = textElement.innerHTML;
            Object.keys(wordsToReplace).forEach(key => {
                const regex = new RegExp(key, 'g');
                text = text.replace(regex, wordsToReplace[key]);
            });
            textElement.innerHTML = text;
        });
    });
}

// Вызываем функцию для замены слов при загрузке страницы
window.onload = replaceWords;
