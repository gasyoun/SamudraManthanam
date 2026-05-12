$(document).ready(function() {
    // Populate sources
    fetch('/api/sources')
        .then(response => response.json())
        .then(sources => {
            const grid = $('#sourcesGrid');
            grid.empty();
            sources.forEach(source => {
                grid.append(`
                    <div class="option-item">
                        <input type="checkbox" id="src_${source.id}" value="${source.id}" checked>
                        <label for="src_${source.id}" style="font-size: 0.8rem;">${source.title}</label>
                    </div>
                `);
            });
        });

    // Select All / None
    $('#selectAll').click(() => $('#sourcesGrid input').prop('checked', true));
    $('#selectNone').click(() => $('#sourcesGrid input').prop('checked', false));

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

        // SSE for progress
        let eventSource = null;
        const source_ids_str = source_ids.length > 0 ? source_ids.join(',') : '';
        const sseUrl = `/api/search/stream?query=${encodeURIComponent(query)}&mode=${mode}&case_sensitive=${case_sensitive}&whole_word=${whole_word}&source_ids=${source_ids_str}`;
        
        try {
            eventSource = new EventSource(sseUrl);
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'progress') {
                    $('#searchProgress').val(data.percent);
                    $('#progressText').text(`Поиск... Найдено: ${data.found_so_far}`);
                } else if (data.type === 'done') {
                    eventSource.close();
                }
            };
            eventSource.onerror = function() {
                if (eventSource) eventSource.close();
            };
        } catch (e) {
            console.error("SSE Error:", e);
        }

        const requestData = {
            query: query,
            mode: mode,
            case_sensitive: case_sensitive,
            whole_word: whole_word,
            source_ids: source_ids.length > 0 ? source_ids : null,
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
            if (eventSource) eventSource.close();
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
            if (eventSource) eventSource.close();
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
        
        const url = `/api/search/export?query=${encodeURIComponent(query)}&mode=${mode}&case_sensitive=${case_sensitive}&whole_word=${whole_word}`;
        window.location.href = url;
    });
});
