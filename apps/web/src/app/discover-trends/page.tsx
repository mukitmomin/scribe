'use client';

import { useState } from 'react';
import { DiscoveryFocusSelector } from '@/components/TrendDiscovery/DiscoveryFocusSelector';
import { TopicSelector } from '@/components/TrendDiscovery/TopicSelector';
import { TrendingPaperCard } from '@/components/TrendDiscovery/TrendingPaperCard';
import { getBackendUrl } from '@/lib/config';
import type { FocusType, TrendingPaper, TrendDiscoveryResponse } from '@/lib/types/trends';
import styles from './page.module.css';

export default function DiscoverTrendsPage() {
  const [focus, setFocus] = useState<FocusType>('hot');
  const [topics, setTopics] = useState<string[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [papers, setPapers] = useState<TrendingPaper[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<TrendDiscoveryResponse['metadata'] | null>(null);

  const handleDiscover = async () => {
    setLoading(true);
    setError(null);

    try {
      // Build query params
      const params = new URLSearchParams();

      // For Phase 1, we use the existing GET endpoint with basic params
      // The topic is constructed from selected topics
      if (topics.length > 0) {
        params.append('topic', topics.join(','));
      }

      // Map focus to time_window
      const focusToTimeWindow: Record<FocusType, number> = {
        hot: 72,       // 3 days
        emerging: 168, // 7 days
        hidden: 336,   // 14 days
        deep: 720      // 30 days
      };
      params.append('time_window', focusToTimeWindow[focus].toString());

      // Max results based on focus
      const focusToMaxResults: Record<FocusType, number> = {
        hot: 10,
        emerging: 20,
        hidden: 30,
        deep: 15
      };
      params.append('max_results', focusToMaxResults[focus].toString());

      const url = getBackendUrl(`/api/v1/trends/discover?${params.toString()}`);
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch trends: ${response.statusText}`);
      }

      const data: TrendDiscoveryResponse = await response.json();
      setPapers(data.papers);
      setMetadata(data.metadata);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error discovering trends:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>📊 Discover Trending Papers</h1>
        <p className={styles.subtitle}>
          Find papers getting buzz in the AI community based on discussions across HackerNews, Reddit, and more.
        </p>
      </div>

      <div className={styles.controls}>
        <DiscoveryFocusSelector value={focus} onChange={setFocus} />

        <button
          className={styles.advancedToggle}
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? '▼' : '▶'} Advanced Options
        </button>

        {showAdvanced && (
          <div className={styles.advancedOptions}>
            <TopicSelector selected={topics} onChange={setTopics} />
          </div>
        )}

        <button
          className={styles.discoverButton}
          onClick={handleDiscover}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className={styles.spinner} />
              Discovering...
            </>
          ) : (
            <>🔍 Discover Trending Papers</>
          )}
        </button>
      </div>

      {error && (
        <div className={styles.error}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {papers.length > 0 && (
        <div className={styles.results}>
          <div className={styles.resultsHeader}>
            <h2 className={styles.resultsTitle}>
              📈 {papers.length} Trending Paper{papers.length !== 1 ? 's' : ''}
            </h2>
            {metadata && (
              <div className={styles.resultsMetadata}>
                <span>Sources: {metadata.sources_queried.join(', ')}</span>
                <span>•</span>
                <span>Time window: {metadata.time_window_hours}h</span>
              </div>
            )}
          </div>

          <div className={styles.papersList}>
            {papers.map((paper, index) => (
              <TrendingPaperCard key={paper.id} paper={paper} rank={index + 1} />
            ))}
          </div>
        </div>
      )}

      {!loading && !error && papers.length === 0 && (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>🔍</div>
          <p className={styles.emptyText}>
            Click "Discover Trending Papers" to find what's trending in AI research
          </p>
        </div>
      )}
    </div>
  );
}
