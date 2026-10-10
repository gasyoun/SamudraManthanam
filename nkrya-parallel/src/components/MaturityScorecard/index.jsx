import React from 'react';
import feed from '@site/data/maturity_nkrya_2026-10-10.json';

// Palette: Docusaurus/Infima CSS variables only (var(--ifm-*)) — light+dark
// theme-aware by construction, no hex values in this file. The house palette
// rule (viz-page skill Phase 0) is satisfied by the theme's own token system.

function scoreVar(score) {
  if (score >= 5) return 'var(--ifm-color-success)';
  if (score === 4) return 'var(--ifm-color-primary)';
  return 'var(--ifm-color-warning)';
}

export function StatStrip() {
  return (
    <div className="row" style={{ margin: '-.5rem' }}>
      {feed.hero.map((h) => (
        <div className="col col--4" key={h.value + h.label} style={{ padding: '.5rem' }}>
          <a href={h.source_url} style={{ textDecoration: 'none', color: 'inherit' }}>
            <div
              style={{
                border: '1px solid var(--ifm-color-emphasis-300)',
                borderRadius: 'var(--ifm-global-radius)',
                padding: '1rem',
                background: 'var(--ifm-card-background-color, var(--ifm-background-color))',
              }}
            >
              <div style={{ fontSize: '2rem', fontWeight: 700, lineHeight: 1.1 }}>
                {h.value}
              </div>
              <div style={{ fontSize: '.85rem', color: 'var(--ifm-color-emphasis-700)' }}>
                {h.label}
              </div>
            </div>
          </a>
        </div>
      ))}
    </div>
  );
}

export function AxisCard({ axis }) {
  const pct = Math.round((axis.score / 5) * 100);
  return (
    <div
      style={{
        border: '1px solid var(--ifm-color-emphasis-300)',
        borderRadius: 'var(--ifm-global-radius)',
        padding: '1rem 1.25rem',
        marginBottom: '.75rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          gap: '.75rem',
          flexWrap: 'wrap',
        }}
      >
        <strong style={{ fontSize: '1.05rem' }}>{axis.axis}</strong>
        <span
          style={{
            fontVariantNumeric: 'tabular-nums',
            fontWeight: 700,
            color: scoreVar(axis.score),
            whiteSpace: 'nowrap',
          }}
        >
          {axis.score}/5
        </span>
      </div>
      <div
        aria-label={`Оценка ${axis.score} из 5`}
        role="img"
        style={{
          height: '.5rem',
          borderRadius: '.25rem',
          background: 'var(--ifm-color-emphasis-200)',
          margin: '.5rem 0 .65rem',
          overflow: 'hidden',
        }}
      >
        <div style={{ width: `${pct}%`, height: '100%', background: scoreVar(axis.score) }} />
      </div>
      <div style={{ fontSize: '.92rem' }}>{axis.fact}</div>
      <div
        style={{
          marginTop: '.5rem',
          fontSize: '.8rem',
          color: 'var(--ifm-color-emphasis-600)',
        }}
      >
        Источник:{' '}
        {axis.sources.map((s, i) => (
          <span key={s.url}>
            {i > 0 && ' · '}
            <a href={s.url}>{s.label}</a>
          </span>
        ))}{' '}
        · дата данных: {axis.date}
      </div>
    </div>
  );
}

export function Scorecards() {
  return (
    <div>
      {feed.axes.map((a) => (
        <AxisCard key={a.id} axis={a} />
      ))}
    </div>
  );
}

export function CompareChart() {
  const c = feed.compare;
  const max = Math.max(...c.rows.map((r) => r.value));
  return (
    <div
      style={{
        border: '1px solid var(--ifm-color-emphasis-300)',
        borderRadius: 'var(--ifm-global-radius)',
        padding: '1rem 1.25rem',
      }}
    >
      <strong>{c.title}</strong>
      <div style={{ display: 'grid', gap: '.45rem', margin: '.75rem 0' }}>
        {c.rows.map((r) => (
          <div key={r.label} style={{ display: 'grid', gridTemplateColumns: 'minmax(14rem, 22rem) 1fr', alignItems: 'center', gap: '.6rem' }}>
            <span style={{ fontSize: '.88rem' }}>{r.label}</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
              <span
                style={{
                  width: `${Math.max(2, Math.round((r.value / max) * 100))}%`,
                  minWidth: '.35rem',
                  height: '1rem',
                  borderRadius: '.2rem',
                  background: r.label.startsWith('НКРЯ')
                    ? 'var(--ifm-color-emphasis-400)'
                    : 'var(--ifm-color-primary)',
                  display: 'inline-block',
                }}
              />
              <span style={{ fontVariantNumeric: 'tabular-nums', fontSize: '.88rem', fontWeight: 600 }}>
                {r.display}
              </span>
            </span>
          </div>
        ))}
      </div>
      <div style={{ fontSize: '.8rem', color: 'var(--ifm-color-emphasis-600)' }}>{c.note}</div>
    </div>
  );
}

export function Residuals() {
  return (
    <ol style={{ paddingLeft: '1.2rem' }}>
      {feed.residuals.map((r) => (
        <li key={r.id} style={{ marginBottom: '.4rem' }}>
          {r.text}{' '}
          <span
            style={{
              fontSize: '.72rem',
              border: '1px solid var(--ifm-color-warning)',
              color: 'var(--ifm-color-warning-contrast-foreground, inherit)',
              borderRadius: '999px',
              padding: '.05rem .5rem',
              whiteSpace: 'nowrap',
            }}
          >
            {r.status}
          </span>
        </li>
      ))}
    </ol>
  );
}

export function AuditTable() {
  return (
    <table style={{ display: 'block', overflowX: 'auto' }}>
      <thead>
        <tr>
          <th>Ось</th>
          <th>Оценка</th>
          <th>Ключевой факт</th>
          <th>Источник</th>
          <th>Дата данных</th>
        </tr>
      </thead>
      <tbody>
        {feed.axes.map((a) => (
          <tr key={a.id}>
            <td>{a.axis}</td>
            <td style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 700 }}>{a.score}/5</td>
            <td>{a.fact}</td>
            <td>
              {a.sources.map((s) => (
                <div key={s.url}>
                  <a href={s.url}>{s.label}</a>
                </div>
              ))}
            </td>
            <td>{a.date}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function Verdict() {
  return (
    <div
      style={{
        borderLeft: '4px solid var(--ifm-color-primary)',
        background: 'var(--ifm-color-emphasis-100)',
        padding: '.85rem 1rem',
        borderRadius: '0 var(--ifm-global-radius) var(--ifm-global-radius) 0',
        fontSize: '1.02rem',
      }}
    >
      <strong>Вердикт:</strong> {feed.verdict}
    </div>
  );
}
