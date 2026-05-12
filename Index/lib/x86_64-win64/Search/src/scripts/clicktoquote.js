(function ($) {
  var clipRange = new ClipboardJS('.chapter .range', {
    text: function (trigger) {
      var text = $(trigger).attr('id');
      return '(' + text ? text : $(trigger).attr('title') + ')';
    }
  });

  var clipChapter = new ClipboardJS('.chapter .chapter_content', {
    text: function (trigger) {
      if (isSelection()) {
        return false;
      }
      return $(trigger).children('.iast').html().replaceAll('<br>', '\n').HTMLdecode().trim() + '\n\n'
        + $(trigger).children('.translation').html().replaceAll('<br>', '\n').HTMLdecode().trim() + '\n\n'
        + '\t(см.: ' + $(trigger).parents('.citation_block').find('.range').attr('title') + ').';
    }
  });
// новый clipComment - не вставляет точку даже тогда, когда нет номера
var clipComment = new ClipboardJS('.chapter .comment_item', {
  text: function (trigger) {
    if (isSelection()) {
      return false;
    }

    let commentNumber = $(trigger).children('.comment_number').text().trim();
    console.log("commentNumber:", commentNumber);
    let commentText = $(trigger).children('.comment_text').html().replaceAll('<br>', '\n').HTMLdecode().trim();
    let commentSource = $(trigger).children('.comment_number').attr('title');

    // Формируем текст с проверкой на пустой номер комментария
    let formattedText = (commentNumber ? commentNumber + '. ' : '') + commentText + ' (' + commentSource + ').';
    console.log("formattedText:", formattedText);

    return formattedText;
  }
});

/* старый clipComment - вставляет точку даже тогда, когда нет номера
  var clipComment = new ClipboardJS('.chapter .comment_item', {
    text: function (trigger) {
      if (isSelection()) {
        return false;
      }
      return $(trigger).children('.comment_number').text().trim() + '. '
        + $(trigger).children('.comment_text').html().replaceAll('<br>', '\n').HTMLdecode().trim() + ''
        + ' (' + $(trigger).children('.comment_number').attr('title') + ').';
    }
  });
*/
  String.prototype.HTMLdecode = function () {
    return $("<div/>").html(this).text();
  }

  function success(e) {
    e.trigger.classList.add('clipboard-processed');
    setTimeout(function () {
      e.trigger.classList.remove('clipboard-processed');
    }, 2000);
  }

  function isSelection() {
    // window.getSelection
    if (window.getSelection) {
      return window.getSelection().toString().length;
    }
    // document.getSelection
    else if (document.getSelection) {
     return document.getSelection().toString().length;
    }
    // document.selection
    else if (document.selection) {
      return document.selection.createRange().text.length;
    }
    else {
      return null;
    }
  }

  clipRange.on('success', success);
  clipChapter.on('success', success);
  clipComment.on('success', success);

}(jQuery));