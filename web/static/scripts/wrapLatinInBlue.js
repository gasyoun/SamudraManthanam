document.addEventListener('DOMContentLoaded', function() {
    const start = performance.now();
    var classNames = ['translation', 'comment_text'];

    classNames.forEach(function(className) {
        var elementsWithClass = document.querySelectorAll('.' + className);

        elementsWithClass.forEach(function(element) {
            highlightLatinText(element);
        });
    });

    const end = performance.now();
    const executionTime = end - start;
    console.log('Время выполнения: ' + executionTime + ' мс');
});

function highlightLatinText(element) {
    var tempDiv = document.createElement('div');
    tempDiv.innerHTML = element.innerHTML;

    processTextNodes(tempDiv);
    processDigitalNodes(tempDiv);
//    processSpecWordsNodes(tempDiv); // 

    element.innerHTML = tempDiv.innerHTML;
}

function processSpecWordsNodes(parentNode) {
        const wordsToReplace = {
            'Санджая': '<span class="blue-text">Санджая</span>',
            'Пандавы': 'Пандавы2',
            'Дурьодхана': 'Дурьодхана3',
            'Слово4': 'Замена4'
            // Добавьте остальные пары слов и замен по аналогии
        };

        function replaceWords(text, wordsToReplace) {
            let replacedText = text;
            for (const word in wordsToReplace) {
                if (wordsToReplace.hasOwnProperty(word)) {
                    const regex = new RegExp(word, 'g');
                    replacedText = replacedText.replace(regex, wordsToReplace[word]);
                }
            }
            return replacedText;
        }

    for (var i = 0; i < parentNode.childNodes.length; i++) {
        var node = parentNode.childNodes[i];
        if (node.nodeType === 3) { // Текстовый узел
                 const newText = replaceWords(node.nodeValue, wordsToReplace)
// работает единичная замена  var newText = node.nodeValue.replace(RegExp('Санджая', 'g'), 'Санджая2');
            // Создаем временный элемент span и вставляем обработанный текст
            var tempSpan = document.createElement('span');
            tempSpan.innerHTML = newText;

            // Заменяем текущий текстовый узел на временный span
            parentNode.replaceChild(tempSpan, node);
        } else if (node.nodeType === 1) { // Элемент
            // Рекурсивно обрабатываем дочерние узлы элемента
            processSpecWordsNodes(node);
        }
    }
}

function processTextNodes(parentNode) {
    // Перебираем дочерние узлы
    for (var i = 0; i < parentNode.childNodes.length; i++) {
        var node = parentNode.childNodes[i];
//	var regex = /\b(?:\P{L}*?[a-zA-Z]\p{L}*)|(?:\p{L}*[a-zA-Z]\P{L}*?)(?=\b)/gu;
        if (node.nodeType === 3) { // Текстовый узел
          var newText = node.nodeValue.replace(/([a-zA-ZāīūṛṝḷḻṃṁḥṅñṭḍṇśṣĀĪŪṚṜḶḺṂṀḤṄÑṬḌṆŚṢ]+)/g, '<span class="blue-text">$1</span>');
//            var newText = node.nodeValue.replace(regex, function(match) {return '<span class="blue-text">' + match + '</span>';});

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

function processDigitalNodes(parentNode) {
    // Перебираем дочерние узлы
    for (var i = 0; i < parentNode.childNodes.length; i++) {
        var node = parentNode.childNodes[i];

        if (node.nodeType === 3) { // Текстовый узел
            // Обрабатываем текстовый узел, выделяя латинские буквы
            var newText = node.nodeValue.replace(/([0-9]+)/g, '<span class="red-text">$1</span>');

            // Создаем временный элемент span и вставляем обработанный текст
            var tempSpan = document.createElement('span');
            tempSpan.innerHTML = newText;

            // Заменяем текущий текстовый узел на временный span
            parentNode.replaceChild(tempSpan, node);
        } else if (node.nodeType === 1) { // Элемент
            // Рекурсивно обрабатываем дочерние узлы элемента
            processDigitalNodes(node);
        }
    }
}
