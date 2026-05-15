$(document).ready(function() {
    // Populate sources
    fetch('/api/sources')
        .then(response => response.json())
        .then(sources => {
            const grid = $('#sourcesGrid');
            grid.empty();
            sources.forEach(source => {
                const item = $('<div>').addClass('option-item');
                const checkbox = $('<input>')
                    .attr('type', 'checkbox')
                    .attr('id', `src_${source.id}`)
                    .val(source.id)
                    .prop('checked', true);
                const label = $('<label>')
                    .attr('for', `src_${source.id}`)
                    .css('font-size', '0.8rem')
                    .text(source.title);
                item.append(checkbox, label);
                grid.append(item);
            });
            updateSourceCount();
        });

    function updateSourceCount() {
        const total = $('#sourcesGrid input').length;
        const selected = $('#sourcesGrid input:checked').length;
        if (selected === total) {
            $('#sourceCount').text('Выбраны все источники');
        } else if (selected === 0) {
            $('#sourceCount').text('Источники не выбраны');
        } else {
            $('#sourceCount').text(`Выбрано источников: ${selected} из ${total}`);
        }
    }

    $(document).on('change', '#sourcesGrid input', updateSourceCount);

    // Select All / None
    $('#selectAll').click(() => {
        $('#sourcesGrid input').prop('checked', true);
        updateSourceCount();
    });
    $('#selectNone').click(() => {
        $('#sourcesGrid input').prop('checked', false);
        updateSourceCount();
    });

    // Form submit
    $('#searchForm').submit(function(e) {
        e.preventDefault();
        const query = $('#query').val();
        const mode = $('#mode').val();
        const case_sensitive = $('#case_sensitive').is(':checked');
        const whole_word = $('#whole_word').is(':checked');
        
        const source_ids = [];
        $('#sourcesGrid input:checked').each(function() {
            source_ids.push(parseInt($(this).val()));
        });

        // Show progress
        $('#progressContainer').show();
        $('#searchProgress').val(0);
        $('#progressText').text('Поиск...');
        $('#results-area').empty().append('<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>');

        $('#searchProgress').val(30);

        const requestData = {
            query: query,
            mode: mode,
            case_sensitive: case_sensitive,
            whole_word: whole_word,
            source_ids: source_ids, // Send the array (empty if none selected)
            limit: 5000
        };

        // Post search
        fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            $('#searchProgress').val(100);
            $('#progressContainer').hide();
            if (data.html_fragment) {
                $('#results-area').html(data.html_fragment);
                // Initialize scroll to top of results if needed
                window.scrollTo({ top: $('#results-area').offset().top - 20, behavior: 'smooth' });
            } else {
                $('#results-area').html('<p>Результатов не найдено.</p>');
            }
        })
        .catch(error => {
            $('#progressContainer').hide();
            $('#results-area').html(`<p style="color: red;">Ошибка при поиске: ${error.message}</p>`);
            console.error('Search error:', error);
        });
    });

    // Export button
    $('#exportBtn').click(function() {
        const query = $('#query').val();
        if (!query) return;
        const mode = $('#mode').val();
        const case_sensitive = $('#case_sensitive').is(':checked');
        const whole_word = $('#whole_word').is(':checked');
        
        const source_ids = [];
        $('#sourcesGrid input:checked').each(function() {
            source_ids.push(parseInt($(this).val()));
        });
        const source_ids_str = source_ids.join(',');
        
        const url = `/api/search/export?query=${encodeURIComponent(query)}&mode=${mode}&case_sensitive=${case_sensitive}&whole_word=${whole_word}&source_ids=${source_ids_str}`;
        window.location.href = url;
    });

    // Lead Capture Logic
    let leadTriggered = false;
    $(window).scroll(function() {
        if (!leadTriggered && $(window).scrollTop() + $(window).height() > $(document).height() * 0.5) {
            // Only trigger if we have results (meaning user is actually engaged)
            if ($('#results-area .citation_block').length > 0) {
                $('#leadModal').fadeIn();
                leadTriggered = true;
            }
        }
    });

    $('#closeLead').click(() => $('#leadModal').fadeOut());
    $(window).click((e) => { if (e.target.id === 'leadModal') $('#leadModal').fadeOut(); });

    $('#leadForm').submit(function(e) {
        e.preventDefault();
        const data = {
            email: $('#leadEmail').val(),
            name: $('#leadName').val(),
            consent_data: $('#consent_data').is(':checked'),
            consent_marketing: $('#consent_marketing').is(':checked')
        };

        fetch('/api/identity/lead', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(res => {
            if (res.status === 'success') {
                $('#leadForm').hide();
                $('#leadMessage').text('Спасибо! Мы будем на связи.').fadeIn();
                setTimeout(() => $('#leadModal').fadeOut(), 3000);
            } else {
                alert('Ошибка: ' + (res.detail || 'неизвестная ошибка'));
            }
        })
        .catch(err => alert('Ошибка при отправке: ' + err));
    });

    // AI Panel Logic
    $(document).on('click', '#askAiBtn', function() {
        const query = $('#query').val();
        const contextLines = [];
        $('.citation_block').each(function() {
            const text = $(this).attr('data-text');
            if (text) contextLines.push(text);
            if (contextLines.length >= 25) return false; // Max context rows
        });

        $('#aiPanel').addClass('active');
        $('#aiLoading').show();
        $('#aiContent').empty();

        fetch('/api/ai/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, context_lines: contextLines })
        })
        .then(response => response.json())
        .then(data => {
            $('#aiLoading').hide();
            if (data.explanation) {
                $('#aiContent').text(data.explanation);
            } else {
                $('#aiContent').text('Ошибка: ' + (data.detail || 'не удалось получить ответ от ИИ.'));
            }
        })
        .catch(err => {
            $('#aiLoading').hide();
            $('#aiContent').text('Ошибка сети: ' + err);
        });
    });

    $('#closeAiPanel').click(() => $('#aiPanel').removeClass('active'));
});
