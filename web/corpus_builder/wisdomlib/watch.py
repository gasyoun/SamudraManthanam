#!/usr/bin/env python
"""wisdomlib Stage C watcher — emits a status bar every N% (default 5%).

Counts the downloaded chapter files (content/<slug>/doc*.html) for the books in
content/_manifest.json against their total chapter_count, measures a LIVE rate
window (never trusts a frozen mtime — a reaped crawl looks "done" by elapsed
time), and prints a bar each time it crosses a new bucket. Mirrors the NWS
scraper's _nws_watch.py.

  python watch.py                 watch, bar each 5%
  python watch.py 10              bar each 10%
  python watch.py --once          print the current bar once and exit
  python watch.py --supervise     also relaunch stageC (same selection) if it stalls

The manifest is written by `crawl.py stageC` when a real run starts, and records
the selected books + the exact argv, so --supervise relaunches that same slice.
State (last bucket + rate samples) persists to content/_watch_state.json, so a
reaped/restarted watcher resumes its bucket tracking instead of re-announcing.
"""
import os, sys, json, time, glob, collections, subprocess
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, 'content')
MANIFEST = os.path.join(CONTENT, '_manifest.json')
STATE = os.path.join(CONTENT, '_watch_state.json')
STATUS_TXT = os.path.join(CONTENT, '_status.txt')      # live one-line bar, every poll
PROGRESS_LOG = os.path.join(CONTENT, '_progress.log')  # one line per bucket (history)
POLL = 30          # seconds between samples
STALL = 180        # seconds with no new write → consider the crawl dead


def load_manifest():
    try:
        return json.load(open(MANIFEST, encoding='utf-8'))
    except Exception:
        return None


def snapshot(man):
    """downloaded pages, books complete, total books, secs-since-newest, total pages."""
    books = man.get('books', [])
    n = done = 0
    mtimes = []
    for slug, cc in books:
        files = glob.glob(os.path.join(CONTENT, slug, 'doc*.html'))
        c = len(files)
        n += min(c, cc) if cc else c          # cap at expected so pct never exceeds 100
        if cc and c >= cc:
            done += 1
        mtimes += [os.path.getmtime(f) for f in files]
    total = man.get('total_chapters') or sum(cc for _, cc in books)
    newest = (time.time() - max(mtimes)) if mtimes else 1e9
    return n, done, len(books), newest, total


def bar(pct, width=40):
    fill = int(round(width * pct / 100))
    return '[' + '#' * fill + '·' * (width - fill) + ']'


def fmt_eta(sec):
    if sec is None or sec == float('inf'):
        return '—'
    h, rem = divmod(int(sec), 3600)
    m, _ = divmod(rem, 60)
    return ('%dh%02dm' % (h, m)) if h else ('%dm' % m)


def status_str(n, done, books, newest, total, rate_ppm, eta, tag=''):
    pct = 100 * n / total if total else 0
    stall = ('  ⚠ STALLED (no write %.0fs — relaunch: python crawl.py stageC ...)' % newest
             if newest > STALL else '')
    return ('%s %s %5.1f%%  %d/%d pages  books %d/%d  %.0f pg/min  ETA %s%s%s'
            % (time.strftime('%H:%M:%S'), bar(pct), pct, n, total, done, books,
               rate_ppm, fmt_eta(eta), ('  ' + tag) if tag else '', stall))


def line(n, done, books, newest, total, rate_ppm, eta, tag=''):
    s = status_str(n, done, books, newest, total, rate_ppm, eta, tag)
    print(s)
    sys.stdout.flush()
    return s


def load_state():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE, encoding='utf-8'))
        except Exception:
            pass
    return {'last_bucket': -1, 'samples': []}


def save_state(st):
    json.dump(st, open(STATE, 'w', encoding='utf-8'))


def rate_eta(samples, n, total):
    """pages/min over the live window + ETA to total."""
    if len(samples) >= 2:
        (t0, c0), (t1, c1) = samples[0], samples[-1]
        dt, dc = t1 - t0, c1 - c0
        if dt > 0 and dc > 0:
            ppm = 60 * dc / dt
            eta = (total - n) / (dc / dt) if total > n else 0
            return ppm, eta
    return 0.0, None


def main():
    args = sys.argv[1:]
    once = '--once' in args
    supervise = '--supervise' in args
    step = next((float(a) for a in args if a.replace('.', '').isdigit()), 5.0)

    man = load_manifest()
    if not man:
        print('no Stage C manifest yet — start the crawl first '
              '(python crawl.py stageC ...)')
        return
    relaunch = [sys.executable, 'crawl.py'] + (man.get('argv') or ['stageC'])

    if once:
        n, done, books, newest, total = snapshot(man)
        ppm, eta = rate_eta(load_state().get('samples', []), n, total)
        s = line(n, done, books, newest, total, ppm, eta)
        open(STATUS_TXT, 'w', encoding='utf-8').write(s + '\n')
        return

    st = load_state()
    samples = collections.deque(st.get('samples', []), maxlen=20)
    print('watching Stage C, bar every %g%%%s (Ctrl-C to stop)'
          % (step, '  [supervise on]' if supervise else ''))
    print('  live bar: content/_status.txt   milestones: content/_progress.log')
    while True:
        n, done, books, newest, total = snapshot(man)
        if not total:
            print('manifest has no chapters to track'); return
        samples.append([time.time(), n])
        st['samples'] = list(samples)
        ppm, eta = rate_eta(samples, n, total)
        # live bar — rewritten every poll so there's always a current status to read
        open(STATUS_TXT, 'w', encoding='utf-8').write(
            status_str(n, done, books, newest, total, ppm, eta) + '\n')
        bucket = int((100 * n / total) // step)
        if bucket > st.get('last_bucket', -1):
            s = line(n, done, books, newest, total, ppm, eta, tag='◆ %g%% mark' % (bucket * step))
            open(PROGRESS_LOG, 'a', encoding='utf-8').write(s + '\n')
            st['last_bucket'] = bucket
        save_state(st)
        if n >= total:
            s = line(n, done, books, newest, total, ppm, eta, tag='✅ COMPLETE')
            open(PROGRESS_LOG, 'a', encoding='utf-8').write(s + '\n')
            return
        if supervise and newest > STALL:
            print('  ↻ stalled — relaunching: %s' % ' '.join(relaunch))
            subprocess.Popen(relaunch, cwd=HERE)
            time.sleep(POLL)
        time.sleep(POLL)


if __name__ == '__main__':
    main()
