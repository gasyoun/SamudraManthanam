/* reader.js — keyboard nav, font-size persistence, copy-citation, and
 * mobile sidebar toggle for /sources/{slug}.
 *
 * Loaded by source_view.html. Pure vanilla JS — no jQuery, no build step.
 * Touches DOM elements created in the template; falls back gracefully when
 * elements aren't present (e.g. sources with no chapters → no sidebar JS).
 */
(function () {
    'use strict';

    /* ────────────────────────────────────────────────────────────────────
     * Font-size persistence
     * ──────────────────────────────────────────────────────────────────── */
    var FONT_STORAGE_KEY = 'sm_reader_font_size';
    var FONT_SIZES = ['0.9rem', '1.0rem', '1.1rem', '1.25rem', '1.45rem'];
    var DEFAULT_FONT_IDX = 2;

    function readFontIdx() {
        var raw = parseInt(localStorage.getItem(FONT_STORAGE_KEY), 10);
        if (isNaN(raw) || raw < 0 || raw >= FONT_SIZES.length) return DEFAULT_FONT_IDX;
        return raw;
    }

    function applyFontIdx(idx) {
        var clamped = Math.max(0, Math.min(FONT_SIZES.length - 1, idx));
        document.documentElement.style.setProperty('--reader-font-size', FONT_SIZES[clamped]);
        localStorage.setItem(FONT_STORAGE_KEY, String(clamped));
        return clamped;
    }

    applyFontIdx(readFontIdx());

    var btnFontSmaller = document.getElementById('rdr-font-smaller');
    var btnFontLarger = document.getElementById('rdr-font-larger');
    if (btnFontSmaller) btnFontSmaller.addEventListener('click', function () { applyFontIdx(readFontIdx() - 1); });
    if (btnFontLarger) btnFontLarger.addEventListener('click', function () { applyFontIdx(readFontIdx() + 1); });

    /* ────────────────────────────────────────────────────────────────────
     * Copy citation — markdown-link form
     * ──────────────────────────────────────────────────────────────────── */
    function buildCitationMarkdown(linkId, lineNum) {
        var sourceTitle = (document.querySelector('.reader-header h1') || {}).textContent || '';
        sourceTitle = sourceTitle.trim();
        var url = new URL(window.location.href);
        url.hash = '';
        if (linkId) {
            url.searchParams.set('highlight', linkId);
        } else if (lineNum) {
            url.searchParams.set('highlight', String(lineNum));
        }
        var label = linkId || lineNum || '';
        return '[' + sourceTitle + ' ' + label + '](' + url.toString() + ')';
    }

    function copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text);
        }
        // Fallback for older browsers / non-HTTPS contexts.
        return new Promise(function (resolve, reject) {
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.select();
            try {
                document.execCommand('copy');
                resolve();
            } catch (e) {
                reject(e);
            } finally {
                document.body.removeChild(ta);
            }
        });
    }

    // Delegated handler — citation buttons are inserted per line via CSS hover.
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('.copy-citation-btn');
        if (!btn) return;
        e.preventDefault();
        var row = btn.closest('.line-row');
        if (!row) return;
        var md = buildCitationMarkdown(row.dataset.linkId, row.dataset.lineNum);
        copyToClipboard(md).then(function () {
            var original = btn.textContent;
            btn.textContent = '✓';
            btn.classList.add('copied');
            setTimeout(function () {
                btn.textContent = original;
                btn.classList.remove('copied');
            }, 1200);
        });
    });

    /* ────────────────────────────────────────────────────────────────────
     * Keyboard navigation: j/k = next/prev verse, [ ] = chapter, gg/G = top/bottom
     * ──────────────────────────────────────────────────────────────────── */
    var lines = function () { return Array.from(document.querySelectorAll('.line-row')); };
    var chapters = function () { return Array.from(document.querySelectorAll('.chapter-heading')); };

    function focusedLineIndex(all) {
        var current = document.querySelector('.line-row.focused')
            || document.querySelector('.line-row.highlighted');
        if (current) return all.indexOf(current);
        // Fall back to first line whose top is below the toolbar.
        for (var i = 0; i < all.length; i++) {
            if (all[i].getBoundingClientRect().top > 120) return Math.max(0, i - 1);
        }
        return -1;
    }

    function focusLine(row) {
        var prev = document.querySelector('.line-row.focused');
        if (prev) prev.classList.remove('focused');
        row.classList.add('focused');
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function jumpChapter(direction) {
        var chs = chapters();
        if (chs.length === 0) return;
        var here = window.scrollY + 100;
        var target = null;
        if (direction > 0) {
            for (var i = 0; i < chs.length; i++) {
                if (chs[i].offsetTop > here + 50) { target = chs[i]; break; }
            }
        } else {
            for (var j = chs.length - 1; j >= 0; j--) {
                if (chs[j].offsetTop < here - 50) { target = chs[j]; break; }
            }
        }
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    var lastGTime = 0;
    document.addEventListener('keydown', function (e) {
        // Don't capture when user is typing in form fields.
        var tag = (e.target.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
        if (e.target.isContentEditable) return;
        if (e.metaKey || e.ctrlKey || e.altKey) return;

        switch (e.key) {
            case 'j': {
                var all = lines();
                var idx = focusedLineIndex(all);
                if (idx < all.length - 1) focusLine(all[idx + 1]);
                e.preventDefault();
                break;
            }
            case 'k': {
                var all2 = lines();
                var idx2 = focusedLineIndex(all2);
                if (idx2 > 0) focusLine(all2[idx2 - 1]);
                e.preventDefault();
                break;
            }
            case ']':
                jumpChapter(+1);
                e.preventDefault();
                break;
            case '[':
                jumpChapter(-1);
                e.preventDefault();
                break;
            case 'g':
                if (e.shiftKey) {
                    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                } else {
                    var now = Date.now();
                    if (now - lastGTime < 500) {
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                        lastGTime = 0;
                    } else {
                        lastGTime = now;
                    }
                }
                e.preventDefault();
                break;
            case '?':
                toggleHelp();
                e.preventDefault();
                break;
        }
    });

    /* ────────────────────────────────────────────────────────────────────
     * Help overlay
     * ──────────────────────────────────────────────────────────────────── */
    function toggleHelp() {
        var existing = document.getElementById('rdr-help');
        if (existing) {
            existing.parentNode.removeChild(existing);
            return;
        }
        var overlay = document.createElement('div');
        overlay.id = 'rdr-help';
        overlay.className = 'rdr-help';
        overlay.innerHTML =
            '<div class="rdr-help-card">' +
            '<h3>Клавиатура</h3>' +
            '<dl>' +
            '<dt>j / k</dt><dd>следующий / предыдущий стих</dd>' +
            '<dt>] / [</dt><dd>следующая / предыдущая глава</dd>' +
            '<dt>g g</dt><dd>к началу</dd>' +
            '<dt>G</dt><dd>к концу</dd>' +
            '<dt>?</dt><dd>показать / скрыть эту справку</dd>' +
            '</dl>' +
            '<button type="button" class="btn btn-secondary">Закрыть</button>' +
            '</div>';
        overlay.addEventListener('click', function (ev) {
            if (ev.target === overlay || ev.target.tagName === 'BUTTON') {
                overlay.parentNode.removeChild(overlay);
            }
        });
        document.body.appendChild(overlay);
    }

    var helpBtn = document.getElementById('rdr-help-btn');
    if (helpBtn) helpBtn.addEventListener('click', toggleHelp);

    /* ────────────────────────────────────────────────────────────────────
     * Mobile sidebar toggle
     * ──────────────────────────────────────────────────────────────────── */
    var sidebarBtn = document.getElementById('rdr-sidebar-toggle');
    var sidebar = document.querySelector('.rdr-sidebar');
    if (sidebarBtn && sidebar) {
        sidebarBtn.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });
        // Tapping a chapter link inside the drawer closes it.
        sidebar.addEventListener('click', function (e) {
            if (e.target.tagName === 'A') sidebar.classList.remove('open');
        });
    }
})();
