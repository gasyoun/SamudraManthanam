// script.js
document.addEventListener('DOMContentLoaded', function() {
    var classNames = ['translation', 'comment_text'];

    classNames.forEach(function(className) {
        var elementsWithClass = document.querySelectorAll('.' + className);

        elementsWithClass.forEach(function(element) {
            highlightLatinText(element);
        });
    });
});

function highlightLatinText(element) {
    // Создаем временный элемент div
    var tempDiv = document.createElement('div');
    tempDiv.innerHTML = element.innerHTML;

    // Обрабатываем латинские буквы внутри текстовых узлов
    processTextNodes(tempDiv);

    // Заменяем содержимое элемента обработанным HTML
    element.innerHTML = tempDiv.innerHTML;
}

function processTextNodes(parentNode) {
    // Перебираем дочерние узлы
    for (var i = 0; i < parentNode.childNodes.length; i++) {
        var node = parentNode.childNodes[i];

        if (node.nodeType === 3) { // Текстовый узел
            // Обрабатываем текстовый узел, выделяя латинские буквы
            var newText = node.nodeValue.replace(/([a-zA-ZāīūṛṝḷḻṃṁḥṅñṭḍṇśṣĀĪŪṚṜḶḺṂṀḤṄÑṬḌṆŚṢ]+)/g, '<span class="blue-text">$1</span>');

            // Создаем временный элемент span и вставляем обработанный текст
            var tempSpan = document.createElement('span');
            tempSpan.innerHTML = newText;

            // Заменяем текущий текстовый узел на временный span
            parentNode.replaceChild(tempSpan, node);
        } else if (node.nodeType === 1) { // Элемент
            // Рекурсивно обрабатываем дочерние узлы элемента
            processTextNodes(node);
        }
    }
}
