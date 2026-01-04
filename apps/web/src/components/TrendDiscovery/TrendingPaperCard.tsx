'use client';

import type { TrendingPaper } from '@/lib/types/trends';
import styles from './TrendingPaperCard.module.css';

function getTrendBadge(trendScore: number): { icon: string; label: string; color: string } {
  if (trendScore >= 80) return { icon: '🔥', label: 'Trending', color: '#ef4444' };
  if (trendScore >= 60) return { icon: '📈', label: 'Rising', color: '#f59e0b' };
  if (trendScore >= 40) return { icon: '💎', label: 'Notable', color: '#3b82f6' };
  return { icon: '📊', label: 'Active', color: '#6b7280' };
}

export function TrendingPaperCard({ paper, rank }: { paper: TrendingPaper; rank: number }) {
  const badge = getTrendBadge(paper.trend_score);

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.rank}>{rank}</div>
        <div className={styles.titleSection}>
          <h3 className={styles.title}>{paper.title}</h3>
          <div className={styles.meta}>
            <span className={styles.paperId}>[{paper.id}]</span>
            <span
              className={styles.badge}
              style={{ backgroundColor: `${badge.color}15`, color: badge.color }}
            >
              {badge.icon} {badge.label}
            </span>
            <span className={styles.score}>
              {paper.trend_score.toFixed(1)} trend score
            </span>
          </div>
        </div>
      </div>

      {paper.trending_reasons && paper.trending_reasons.length > 0 && (
        <div className={styles.reasons}>
          {paper.trending_reasons.map((reason, index) => (
            <div key={index} className={styles.reason}>
              <span className={styles.reasonIcon}>•</span>
              <span>{reason}</span>
            </div>
          ))}
        </div>
      )}

      {paper.abstract && (
        <p className={styles.abstract}>
          {paper.abstract.length > 200
            ? `${paper.abstract.substring(0, 200)}...`
            : paper.abstract}
        </p>
      )}

      <div className={styles.actions}>
        <a
          href={`https://arxiv.org/abs/${paper.id}`}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.button}
        >
          📄 Read Paper
        </a>
        {paper.discussion_urls && paper.discussion_urls.length > 0 && (
          <a
            href={paper.discussion_urls[0]}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.button}
          >
            💬 View Discussions ({paper.discussion_urls.length})
          </a>
        )}
        <div className={styles.stats}>
          <span className={styles.stat}>
            {paper.total_mentions} mention{paper.total_mentions !== 1 ? 's' : ''}
          </span>
          <span className={styles.stat}>
            {paper.total_engagement} engagement
          </span>
          {paper.buzz_velocity > 0 && (
            <span className={styles.stat}>
              {paper.buzz_velocity.toFixed(1)} velocity
            </span>
          )}
        </div>
      </div>

      {paper.sources && paper.sources.length > 0 && (
        <div className={styles.sources}>
          <span className={styles.sourcesLabel}>Sources:</span>
          {paper.sources.map(source => (
            <span key={source} className={styles.sourceTag}>
              {source}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
