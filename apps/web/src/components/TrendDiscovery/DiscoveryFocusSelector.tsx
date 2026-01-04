'use client';

import { useState } from 'react';
import type { FocusType, FocusOption } from '@/lib/types/trends';
import styles from './DiscoveryFocusSelector.module.css';

const FOCUS_OPTIONS: FocusOption[] = [
  {
    value: 'hot',
    icon: '🔥',
    label: 'Hot Right Now',
    description: 'Papers with high engagement in the last 3 days'
  },
  {
    value: 'emerging',
    icon: '📈',
    label: 'Emerging Trends',
    description: 'Papers gaining traction quickly'
  },
  {
    value: 'hidden',
    icon: '💎',
    label: 'Hidden Gems',
    description: "Quality papers that haven't gone viral"
  },
  {
    value: 'deep',
    icon: '🎯',
    label: 'Deep Dives',
    description: 'Papers with in-depth expert discussions'
  }
];

export function DiscoveryFocusSelector({
  value,
  onChange
}: {
  value: FocusType;
  onChange: (focus: FocusType) => void;
}) {
  const [hoveredOption, setHoveredOption] = useState<FocusType | null>(null);

  return (
    <div className={styles.container}>
      <label className={styles.label}>
        What type of trends are you looking for?
      </label>

      <div className={styles.options}>
        {FOCUS_OPTIONS.map(option => (
          <button
            key={option.value}
            className={`${styles.option} ${value === option.value ? styles.selected : ''}`}
            onClick={() => onChange(option.value)}
            onMouseEnter={() => setHoveredOption(option.value)}
            onMouseLeave={() => setHoveredOption(null)}
            aria-label={option.label}
            aria-pressed={value === option.value}
          >
            <div className={styles.icon}>{option.icon}</div>
            <div className={styles.optionLabel}>{option.label}</div>
          </button>
        ))}
      </div>

      <div className={styles.description}>
        {FOCUS_OPTIONS.find(o => o.value === (hoveredOption || value))?.description}
      </div>
    </div>
  );
}
