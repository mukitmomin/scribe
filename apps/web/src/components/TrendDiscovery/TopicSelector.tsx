'use client';

import type { Topic } from '@/lib/types/trends';
import styles from './TopicSelector.module.css';

const TOPICS: Topic[] = [
  { id: 'llm', icon: '🤖', label: 'LLMs & Language Models' },
  { id: 'genai', icon: '🎨', label: 'Generative AI & Diffusion' },
  { id: 'agents', icon: '🧠', label: 'Agents & Reasoning' },
  { id: 'vision', icon: '👁️', label: 'Computer Vision' },
  { id: 'safety', icon: '🔬', label: 'Interpretability & Safety' },
  { id: 'efficiency', icon: '⚡', label: 'Efficiency & Optimization' },
];

const MAX_SELECTION = 3;

export function TopicSelector({
  selected,
  onChange
}: {
  selected: string[];
  onChange: (topics: string[]) => void;
}) {
  const toggleTopic = (topicId: string) => {
    if (selected.includes(topicId)) {
      onChange(selected.filter(t => t !== topicId));
    } else if (selected.length < MAX_SELECTION) {
      onChange([...selected, topicId]);
    }
  };

  return (
    <div className={styles.container}>
      <label className={styles.label}>
        Topic Areas <span className={styles.optional}>(optional, max {MAX_SELECTION})</span>
      </label>

      <div className={styles.chips}>
        {TOPICS.map(topic => {
          const isSelected = selected.includes(topic.id);
          const isDisabled = !isSelected && selected.length >= MAX_SELECTION;

          return (
            <button
              key={topic.id}
              className={`${styles.chip} ${isSelected ? styles.selected : ''} ${isDisabled ? styles.disabled : ''}`}
              onClick={() => toggleTopic(topic.id)}
              disabled={isDisabled}
              aria-label={topic.label}
              aria-pressed={isSelected}
            >
              <span className={styles.chipIcon}>{topic.icon}</span>
              <span className={styles.chipLabel}>{topic.label}</span>
              {isSelected && (
                <span className={styles.checkmark}>✓</span>
              )}
            </button>
          );
        })}
      </div>

      {selected.length >= MAX_SELECTION && (
        <p className={styles.hint}>
          Max {MAX_SELECTION} topics selected. Deselect one to choose another.
        </p>
      )}
    </div>
  );
}
