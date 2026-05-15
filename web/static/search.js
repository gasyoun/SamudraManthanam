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
});
