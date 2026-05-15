$(document).ready(function() {
    let totalSourceCount = 0;

    // ── Engaged-user CTA ──────────────────────────────────────────────────────
    // After SEARCH_THRESHOLD searches in this browser, surface a stronger CTA
    // toward the paid course. Dismissal is sticky across page loads.
    const SEARCH_THRESHOLD = 3;

    function maybeShowEngagedCta() {
        const cta = document.getElementById('engagedCta');
        if (!cta) return;  // SYSTEMA_SANSCRITICUM_URL not configured
        if (cta.style.display === 'flex') return;  // already showing — don't re-animate
        if (localStorage.getItem('engagedCtaDismissed') === '1') return;
        const count = parseInt(localStorage.getItem('searchCount') || '0', 10);
        if (count < SEARCH_THRESHOLD) return;

        const link = document.getElementById('engagedCtaLink');
        if (link) link.href = cta.dataset.ssUrl;
        cta.style.display = 'flex';
        // Two-frame defer so the transition runs (display:none → flex isn't transitionable directly)
        requestAnimationFrame(() => requestAnimationFrame(() => {
            cta.style.opacity = '1';
            cta.style.transform = 'translateX(-50%) translateY(0)';
        }));
    }
    function incrementSearchCount() {
        const count = parseInt(localStorage.getItem('searchCount') || '0', 10) + 1;
        localStorage.setItem('searchCount', String(count));
        if (count >= SEARCH_THRESHOLD) maybeShowEngagedCta();
    }
    $(document).on('click', '#engagedCtaClose', function() {
        const cta = document.getElementById('engagedCta');
        if (!cta) return;
        cta.style.opacity = '0';
        cta.style.transform = 'translateX(-50%) translateY(20px)';
        setTimeout(() => { cta.style.display = 'none'; }, 400);
        localStorage.setItem('engagedCtaDismissed', '1');
    });
    // Show on page load if the user already crossed the threshold on a prior visit
    maybeShowEngagedCta();

    // ── Sources ──────────────────────────────────────────────────────────────
    fetch('/api/sources')
        .then(response => response.json())
        .then(sources => {
            totalSourceCount = sources.length;
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
            restoreFromUrl();
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

    // ── Permalink: restore state from URL on page load + popstate ────────────
    function restoreFromUrl() {
        const params = new URLSearchParams(window.location.search);
        const q = params.get('q');
        if (!q) {
            // Back-navigation to a URL with no query: reset visible state so the
            // page matches the address bar instead of showing stale results.
            $('#query').val('');
            $('#mode').val('plain');
            $('#case_sensitive').prop('checked', false);
            $('#whole_word').prop('checked', false);
            $('#sourcesGrid input').prop('checked', true);
            updateSourceCount();
            $('#results-area').empty();
            return;
        }

        $('#query').val(q);
        $('#mode').val(params.get('mode') || 'plain');
        $('#case_sensitive').prop('checked', params.get('cs') === '1');
        $('#whole_word').prop('checked', params.get('ww') === '1');

        const srcParam = params.get('src');
        if (srcParam !== null) {
            $('#sourcesGrid input').prop('checked', false);
            if (srcParam) {
                const ids = new Set(srcParam.split(',').map(Number));
                $('#sourcesGrid input').each(function() {
                    if (ids.has(parseInt($(this).val()))) $(this).prop('checked', true);
                });
            }
        }
        updateSourceCount();
        $('#searchForm').trigger('submit');
    }

    // ── Permalink: build URL from current search state ────────────────────────
    function buildPermalink(query, mode, case_sensitive, whole_word, source_ids) {
        const params = new URLSearchParams();
        params.set('q', query);
        if (mode && mode !== 'plain') params.set('mode', mode);
        if (case_sensitive) params.set('cs', '1');
        if (whole_word) params.set('ww', '1');
        if (source_ids.length !== totalSourceCount) {
            params.set('src', source_ids.join(','));
        }
        return '?' + params.toString();
    }

    window.addEventListener('popstate', restoreFromUrl);

    $(document).on('change', '#sourcesGrid input', updateSourceCount);

    $('#selectAll').click(() => {
        $('#sourcesGrid input').prop('checked', true);
        updateSourceCount();
    });
    $('#selectNone').click(() => {
        $('#sourcesGrid input').prop('checked', false);
        updateSourceCount();
    });

    // ── Search ────────────────────────────────────────────────────────────────
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

        // Update URL bar so the search is bookmarkable / shareable
        history.pushState({}, '', buildPermalink(query, mode, case_sensitive, whole_word, source_ids));

        // Count this search toward the engaged-user CTA threshold
        incrementSearchCount();

        $('#progressContainer').show();
        $('#searchProgress').val(0);
        $('#progressText').text('Поиск...');
        $('#results-area').empty().append('<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>');
        $('#searchProgress').val(30);

        fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, mode, case_sensitive, whole_word, source_ids, limit: 5000 })
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

    // ── Export ────────────────────────────────────────────────────────────────
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
        const url = `/api/search/export?query=${encodeURIComponent(query)}&mode=${mode}&case_sensitive=${case_sensitive}&whole_word=${whole_word}&source_ids=${source_ids.join(',')}`;
        window.location.href = url;
    });

    // ── Context window ────────────────────────────────────────────────────────
    $(document).on('click', '.btn-context', function() {
        const btn = $(this);
        const block = btn.closest('.citation_block');
        const panel = block.find('.context-panel');

        if (panel.is(':visible')) {
            panel.slideUp(150);
            btn.text('≡');
            return;
        }
        if (panel.data('loaded')) {
            panel.slideDown(150);
            btn.text('▲');
            return;
        }

        const sourceId = btn.data('source-id');
        const lineNum  = btn.data('line-num');
        btn.prop('disabled', true).text('…');

        fetch(`/api/search/context?source_id=${sourceId}&line_num=${lineNum}&window=5`)
            .then(r => r.json())
            .then(data => {
                let html = '<div class="ctx-lines">';
                data.before.forEach(l => {
                    html += ctxLineHtml(l, false);
                });
                if (data.current) {
                    html += ctxLineHtml(data.current, true);
                }
                data.after.forEach(l => {
                    html += ctxLineHtml(l, false);
                });
                html += '</div>';
                panel.html(html).data('loaded', true).slideDown(150);
                btn.prop('disabled', false).text('▲');
            })
            .catch(() => {
                panel.html('<p style="color:#c00;font-size:0.8rem;margin:2px 0">Ошибка загрузки контекста</p>')
                     .data('loaded', true).slideDown(150);
                btn.prop('disabled', false).text('≡');
            });
    });

    function ctxLineHtml(line, isFocal) {
        const num = escHtml(String(line.link_id || line.line_num));
        const focal = isFocal ? 'font-weight:600;' : 'opacity:0.75;';
        return `<div style="display:grid;grid-template-columns:3rem 1fr;gap:0.5rem;padding:2px 0;${focal}">` +
               `<span style="text-align:right;color:#aaa;font-size:0.75rem;padding-top:0.1rem;">${num}</span>` +
               `<span>${line.line_html}</span>` +
               `</div>`;
    }

    // ── Copy citation URL ─────────────────────────────────────────────────────
    $(document).on('click', '.btn-copy-citation', function() {
        const btn = $(this);
        const url = window.location.origin + btn.data('citation-url');
        const orig = btn.text();
        if (navigator.clipboard) {
            navigator.clipboard.writeText(url)
                .then(() => { btn.text('✓'); setTimeout(() => btn.text(orig), 1500); })
                .catch(() => prompt('Скопируйте ссылку:', url));
        } else {
            prompt('Скопируйте ссылку:', url);
        }
    });

    // ── Social share buttons (Telegram / VK / WhatsApp) ───────────────────────
    function openShare(network, btn) {
        const path  = btn.data('share-url');
        const title = btn.data('share-title') || 'Пахтанье океана';
        const url   = window.location.origin + path;
        const text  = `${title} — Пахтанье океана`;

        let target;
        if (network === 'tg') {
            target = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
        } else if (network === 'vk') {
            target = `https://vk.com/share.php?url=${encodeURIComponent(url)}&title=${encodeURIComponent(text)}`;
        } else if (network === 'wa') {
            target = `https://wa.me/?text=${encodeURIComponent(text + ' ' + url)}`;
        }
        window.open(target, '_blank', 'noopener,width=600,height=600');
    }
    $(document).on('click', '.btn-share-tg', function() { openShare('tg', $(this)); });
    $(document).on('click', '.btn-share-vk', function() { openShare('vk', $(this)); });
    $(document).on('click', '.btn-share-wa', function() { openShare('wa', $(this)); });

    // ── Lead capture ──────────────────────────────────────────────────────────
    let leadTriggered = false;
    $(window).scroll(function() {
        if (!leadTriggered && $(window).scrollTop() + $(window).height() > $(document).height() * 0.5) {
            if ($('#results-area .citation_block').length > 0) {
                $('#leadModal').fadeIn();
                leadTriggered = true;
            }
        }
    });

    $('#closeLead').click(() => $('#leadModal').fadeOut());
    $(window).click((e) => { if (e.target.id === 'leadModal') $('#leadModal').fadeOut(); });

    // Capture UTM params on first page load; persist for the session so the lead
    // form can attribute the visitor's original referral source.
    (function captureUtm() {
        const p = new URLSearchParams(window.location.search);
        ['utm_source', 'utm_medium', 'utm_campaign'].forEach(k => {
            const v = p.get(k);
            if (v && !sessionStorage.getItem(k)) sessionStorage.setItem(k, v);
        });
    })();

    $('#leadForm').submit(function(e) {
        e.preventDefault();
        const data = {
            email: $('#leadEmail').val(),
            name: $('#leadName').val() || null,
            telegram_username: $('#leadTelegram').val() || null,
            utm_source: sessionStorage.getItem('utm_source') || null,
            utm_medium: sessionStorage.getItem('utm_medium') || null,
            utm_campaign: sessionStorage.getItem('utm_campaign') || null,
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

    // ── AI panel ──────────────────────────────────────────────────────────────
    $(document).on('click', '#askAiBtn', function() {
        const query = $('#query').val();
        const contextLines = [];
        $('.citation_block').each(function() {
            const text = $(this).attr('data-text');
            if (text) contextLines.push(text);
            if (contextLines.length >= 25) return false;
        });

        $('#aiPanel').addClass('active');
        $('#aiLoading').show();
        $('#aiContent').empty();

        fetch('/api/ai/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, context_lines: contextLines })
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

function escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
