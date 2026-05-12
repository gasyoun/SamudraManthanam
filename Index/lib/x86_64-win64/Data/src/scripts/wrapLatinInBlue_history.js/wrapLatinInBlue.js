// script.js
function wrapLatinInBlue(classNames) {
    document.addEventListener('DOMContentLoaded', function() {
        classNames.forEach(function(className) {
            var elementsWithClass = document.querySelectorAll('.' + className);

            elementsWithClass.forEach(function(element) {
                var elementText = element.innerHTML;

                // Заменяем латинские символы на обрамленный HTML-тег
                var newElementText = elementText.replace(/[a-zA-ZāīūṛṝḷḻṃṁḥṅñṭḍṇśṣĀĪŪṚṜḶḺṂṀḤṄÑṬḌṆŚṢ]+/g, function(match) {
                    return '<span class="blue-text">' + match + '</span>';
                });

                // Обновляем содержимое элемента
                element.innerHTML = newElementText;
            });
        });
    });
}

// Вызываем функцию с именами классов
wrapLatinInBlue(['chapter_block translation', 'chapter_block iast']);
//wrapLatinInBlue(['class1', 'class2', 'class3', 'chapter_block translation', 'comment_text']);
