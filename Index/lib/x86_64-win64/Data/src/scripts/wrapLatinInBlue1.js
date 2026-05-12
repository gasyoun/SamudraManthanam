// script.js
// Функция, которая будет вызываться при появлении элементов в области видимости
function handleIntersection(entries, observer) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            var element = entry.target;
            highlightLatinText(element);
            observer.unobserve(element); // Остановка отслеживания этого элемента, после того как он станет видимым
        }
    });
}

// Создаем новый Intersection Observer
const observer = new IntersectionObserver(handleIntersection, { threshold: 0.5 });

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
    // Создаем временный элемент div
    var tempDiv = document.createElement('div');
    tempDiv.innerHTML = element.innerHTML;

    // Обрабатываем латинские буквы внутри текстовых узлов
    processSpecWordsNodes(tempDiv)
    processTextNodes(tempDiv);
    processDigitalNodes(tempDiv);

    // Заменяем содержимое элемента обработанным HTML
    element.innerHTML = tempDiv.innerHTML;
}

function processTextNodes(parentNode) {
    // Слова для выделения голубым фоном
    const wordsToHighlight = ['Кришна', 'Арджуна', 'Санджая', 'Дхритараштра'];

    // Перебираем дочерние узлы
    for (var i = 0; i < parentNode.childNodes.length; i++) {
        var node = parentNode.childNodes[i];
        if (node.nodeType === 3) { // Текстовый узел
            // Проходим по словам для выделения
            wordsToHighlight.forEach(word => {
                // Создаем регулярное выражение для поиска слова с учетом регистра
                const regex = new RegExp('\\b' + word + '\\b', 'gi');
                // Заменяем найденные слова на обернутый спан с голубым фоном
                node.nodeValue = node.nodeValue.replace(regex, '<span class="blue-text">$&</span>');
            });
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

function processWordsNodes(parentNode) {
    const wordsToReplace = {
        'Кришна': 'Кришна2',
        'Санджая': 'Санджая3',
        'Пандавы': 'Пандавы555'
        // Добавьте остальные пары слов и ссылок по аналогии
    };
    // Перебираем дочерние узлы
    for (var i = 0; i < parentNode.childNodes.length; i++) {
        var node = parentNode.childNodes[i];

        if (node.nodeType === 3) { // Текстовый узел
            // Обрабатываем текстовый узел, выделяя латинские буквы
            Object.keys(wordsToReplace).forEach(key => {
                const regex = new RegExp(key, 'g');
                newText = text.replace(regex, wordsToReplace[key]);
               // Создаем временный элемент span и вставляем обработанный текст
               var tempSpan = document.createElement('span');
               tempSpan.innerHTML = newText;
               // Заменяем текущий текстовый узел на временный span
               parentNode.replaceChild(tempSpan, node);
            });
        } else if (node.nodeType === 1) { // Элемент
            // Рекурсивно обрабатываем дочерние узлы элемента
            processWordsNodes(node);
        }
    }
}
