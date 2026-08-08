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

    // ── Wait timer (search + AI) ─────────────────────────────────────────────
    // Long queries (full corpus, morph, regex, AI) used to sit on a static
    // "Поиск…" with no clock — users could not tell if the tab was frozen.
    function formatElapsed(ms) {
        const s = ms / 1000;
        if (s < 60) {
            return (s < 10 ? s.toFixed(1) : String(Math.floor(s))).replace('.', ',') + ' с';
        }
        const m = Math.floor(s / 60);
        const rem = Math.floor(s % 60);
        return m + ' мин ' + rem + ' с';
    }
    function startWaitTimer(onTick, intervalMs) {
        const t0 = (typeof performance !== 'undefined' && performance.now)
            ? performance.now()
            : Date.now();
        const tick = function () {
            const now = (typeof performance !== 'undefined' && performance.now)
                ? performance.now()
                : Date.now();
            onTick(now - t0);
        };
        tick();
        const id = setInterval(tick, intervalMs || 200);
        return {
            stop: function () {
                clearInterval(id);
                const now = (typeof performance !== 'undefined' && performance.now)
                    ? performance.now()
                    : Date.now();
                return now - t0;
            }
        };
    }
    /** Progress bar that creeps toward 90% while waiting (never pretends to know %). */
    function waitProgressPct(ms) {
        return Math.min(90, 8 + 82 * (1 - Math.exp(-ms / 12000)));
    }

    // ── Sources ──────────────────────────────────────────────────────────────
    // Disable Find/HTML buttons until sources resolve — submitting earlier would
    // send source_ids=[] and the server (correctly) returns no results, leaving
    // the user staring at "Результатов не найдено." with no idea why.
    $('#searchForm button[type="submit"], #exportBtn').prop('disabled', true);

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
                    .attr('data-slug', source.slug || '')
                    .val(source.id)
                    .prop('checked', true);
                const label = $('<label>')
                    .attr('for', `src_${source.id}`)
                    .css('font-size', '0.8rem')
                    .text(source.title);
                item.append(checkbox, label);
                grid.append(item);
            });
            $('#searchForm button[type="submit"], #exportBtn').prop('disabled', false);
            updateSourceCount();
            restoreFromUrl();
        })
        .catch(err => {
            console.error('Failed to load sources:', err);
            if (navigator.onLine === false) {
                // Offline (e.g. a cached PWA shell): /api/sources can't load, but
                // offline search must stay reachable — re-enable the Find button.
                // With no source checkboxes the offline path searches all
                // installed packs. The HTML-export button stays disabled (it is
                // a server-only endpoint).
                $('#searchForm button[type="submit"]').prop('disabled', false);
                $('#sourcesGrid').empty();
                $('#sourceCount').text('Нет сети — доступен офлайн-поиск по загруженным текстам.');
            } else {
                $('#sourceCount').text('Не удалось загрузить источники. Перезагрузите страницу.');
            }
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
                // Tokens are slugs (stable across re-ingests). Numeric tokens
                // are accepted too for old bookmarked URLs that carried ids.
                const tokens = new Set(srcParam.split(','));
                $('#sourcesGrid input').each(function() {
                    if (tokens.has($(this).data('slug')) || tokens.has($(this).val())) {
                        $(this).prop('checked', true);
                    }
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
            // Permalinks carry slugs, not ids: ids renumber on every corpus
            // re-ingest, slugs are derived from filenames and survive.
            const slugs = [];
            $('#sourcesGrid input:checked').each(function() {
                slugs.push($(this).data('slug') || $(this).val());
            });
            params.set('src', slugs.join(','));
        }
        return '?' + params.toString();
    }

    window.addEventListener('popstate', restoreFromUrl);

    $(document).on('change', '#sourcesGrid input', updateSourceCount);

    $('#selectAll').on('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        $('#sourcesGrid input').prop('checked', true);
        updateSourceCount();
    });
    $('#selectNone').on('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
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

        // ── Offline routing ───────────────────────────────────────────────────
        // When the network is down and the offline-search bridge is present,
        // run the query locally instead of hitting /api/search. Gated strictly
        // on navigator.onLine === false so the online path is never affected.
        if (navigator.onLine === false && window.SamudraOffline) {
            if (mode === 'morphological') {
                $('#progressContainer').hide();
                $('#results-area').html('<div class="offline-banner">⚡ Офлайн · морфологический поиск (по основам) недоступен без сети. Используйте обычный или regex-поиск.</div>');
                return;
            }
            runOfflineSearch(query, mode, case_sensitive, whole_word, source_ids);
            return;
        }

        $('#progressContainer').show();
        $('#searchProgress').val(0);
        $('#results-area').empty().append(
            '<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>'
        );

        const wait = startWaitTimer(function (ms) {
            $('#progressText').text('Идёт поиск… ' + formatElapsed(ms));
            $('#searchProgress').val(waitProgressPct(ms));
        });

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
            const wallMs = wait.stop();
            $('#searchProgress').val(100);
            const serverMs = (data && typeof data.elapsed_ms === 'number') ? data.elapsed_ms : null;
            const doneLabel = serverMs != null
                ? ('Готово за ' + formatElapsed(serverMs) +
                   (Math.abs(serverMs - wallMs) > 500
                       ? ' (в браузере ' + formatElapsed(wallMs) + ')'
                       : ''))
                : ('Готово за ' + formatElapsed(wallMs));
            $('#progressText').text(doneLabel);
            // Keep the "done in Xs" line visible briefly so the clock is not lost.
            setTimeout(function () { $('#progressContainer').hide(); }, 1200);
            if (data.html_fragment) {
                $('#results-area').html(data.html_fragment);
                window.scrollTo({ top: $('#results-area').offset().top - 20, behavior: 'smooth' });
            } else {
                $('#results-area').html('<p>Результатов не найдено.</p>');
            }
        })
        .catch(error => {
            wait.stop();
            $('#progressContainer').hide();
            $('#results-area').html(`<p style="color: red;">Ошибка при поиске: ${error.message}</p>`);
            console.error('Search error:', error);
        });
    });

    // ── Offline search (local, via window.SamudraOffline bridge) ──────────────
    function runOfflineSearch(query, mode, case_sensitive, whole_word, source_ids) {
        $('#progressContainer').show();
        $('#searchProgress').val(0);
        $('#results-area').empty().append('<div class="skeleton"></div><div class="skeleton"></div>');

        const wait = startWaitTimer(function (ms) {
            $('#progressText').text('Офлайн-поиск… ' + formatElapsed(ms));
            $('#searchProgress').val(waitProgressPct(ms));
        });

        window.SamudraOffline.search({
            query: query,
            mode: mode,
            caseSensitive: case_sensitive,
            wholeWord: whole_word,
            sourceIds: source_ids.length ? source_ids : null
        })
        .then(function(res) {
            const wallMs = wait.stop();
            $('#searchProgress').val(100);
            $('#progressText').text('Готово за ' + formatElapsed(wallMs));
            setTimeout(function () { $('#progressContainer').hide(); }, 1200);
            $('#results-area').html(window.SamudraOffline.renderHtml(query, res.rows, { timeout: res.timeout }));
            updateNetPill();
            if (res.rows.length) {
                window.scrollTo({ top: $('#results-area').offset().top - 20, behavior: 'smooth' });
            }
        })
        .catch(function(err) {
            wait.stop();
            $('#progressContainer').hide();
            if (err && err.code === 'NO_PACK') {
                $('#results-area').html('<div class="offline-banner">⚡ Офлайн · нет загруженного индекса для поиска. ' +
                    '<a href="/offline-settings">Скачать офлайн-поиск</a>, пока есть сеть.</div>');
            } else {
                $('#results-area').html('<p style="color: red;">Ошибка офлайн-поиска: ' + escHtml(err && err.message || String(err)) + '</p>');
            }
            updateNetPill();
        });
    }

    // ── Network-status pill ───────────────────────────────────────────────────
    function updateNetPill() {
        var el = document.getElementById('netStatus');
        if (!el) return;
        if (navigator.onLine) {
            el.className = 'option-item online';
            el.innerHTML = '<span class="dot">●</span> Онлайн';
            return;
        }
        el.className = 'option-item offline';
        if (window.SamudraOffline && window.SamudraOffline.isAvailable()) {
            el.innerHTML = '<span class="dot">○</span> Офлайн · локальный поиск';
        } else if (window.SamudraOffline && window.SamudraOffline.isReady()) {
            el.innerHTML = '<span class="dot">○</span> Офлайн · <a href="/offline-settings">нет индекса</a>';
        } else {
            el.innerHTML = '<span class="dot">○</span> Офлайн';
        }
    }
    window.addEventListener('online', updateNetPill);
    window.addEventListener('offline', function() {
        updateNetPill();
        // Pre-warm the local engine; refresh the pill once a pack is detected.
        if (window.SamudraOffline) {
            window.SamudraOffline.whenReady().then(updateNetPill, updateNetPill);
        }
    });
    updateNetPill();

    // ── Export ────────────────────────────────────────────────────────────────
    $('#exportBtn').click(function() {
        const query = $('#query').val();
        if (!query) return;
        // HTML export is a server-only endpoint. Offline, navigating to it would
        // abandon the SPA for a request that can't complete — guard it.
        if (navigator.onLine === false) {
            $('#results-area').html('<div class="offline-banner">⚡ Офлайн · экспорт в HTML недоступен без сети.</div>');
            return;
        }
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
        // The lead form POSTs to /api/identity/lead, which can't complete
        // offline. Offline results also render .citation_block blocks, so this
        // trigger would otherwise pop a modal that can't be submitted — gate it
        // on connectivity.
        if (navigator.onLine === false) return;
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
    // Mirror server caps in web/app/routers/ai.py — long dictionary lines
    // (e.g. encyclopedic Агни entries) exceed MAX_CONTEXT_LINE_LEN and used to
    // return FastAPI 422 with detail=[{msg,loc,…}], which JS stringified as
    // "[object Object]".
    const AI_MAX_CONTEXT_LINES = 25;
    const AI_MAX_LINE_LEN = 2000;

    function formatApiDetail(detail) {
        if (detail == null || detail === '') return '';
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) {
            return detail.map(function (item) {
                if (typeof item === 'string') return item;
                if (item && typeof item.msg === 'string') return item.msg;
                try { return JSON.stringify(item); } catch (_) { return String(item); }
            }).filter(Boolean).join('; ');
        }
        if (typeof detail === 'object') {
            if (typeof detail.msg === 'string') return detail.msg;
            try { return JSON.stringify(detail); } catch (_) { return String(detail); }
        }
        return String(detail);
    }

    $(document).on('click', '#askAiBtn', function() {
        const query = $('#query').val();
        const contextLines = [];
        $('.citation_block').each(function() {
            let text = $(this).attr('data-text');
            if (!text) return;
            if (text.length > AI_MAX_LINE_LEN) {
                text = text.slice(0, AI_MAX_LINE_LEN);
            }
            contextLines.push(text);
            if (contextLines.length >= AI_MAX_CONTEXT_LINES) return false;
        });

        $('#aiPanel').addClass('active');
        $('#aiLoading').show();
        $('#aiContent').html(
            '<div id="aiThinkStatus" class="ai-think-status" role="status" aria-live="polite">' +
            'ИИ думает… 0,0 с</div>'
        );

        const wait = startWaitTimer(function (ms) {
            $('#aiThinkStatus').text('ИИ думает… ' + formatElapsed(ms));
        });

        fetch('/api/ai/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, context_lines: contextLines })
        })
        .then(function (response) {
            return response.json().then(function (data) {
                return { ok: response.ok, status: response.status, data: data };
            });
        })
        .then(function (resp) {
            const wallMs = wait.stop();
            $('#aiLoading').hide();
            const data = resp.data || {};
            if (resp.ok && data.explanation) {
                $('#aiContent').html(
                    '<div class="ai-think-done">Ответ за ' + formatElapsed(wallMs) + '</div>'
                );
                // text() after prepend would wipe the badge — append text node.
                $('#aiContent').append(document.createTextNode(data.explanation));
            } else {
                const detailMsg = formatApiDetail(data.detail)
                    || (resp.ok ? 'не удалось получить ответ от ИИ.' : ('HTTP ' + resp.status));
                $('#aiContent').text('Ошибка: ' + detailMsg +
                    ' (ждали ' + formatElapsed(wallMs) + ')');
            }
        })
        .catch(err => {
            const wallMs = wait.stop();
            $('#aiLoading').hide();
            $('#aiContent').text('Ошибка сети: ' + err + ' (ждали ' + formatElapsed(wallMs) + ')');
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
