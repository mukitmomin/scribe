import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingDots } from './LoadingDots';

describe('LoadingDots', () => {
  it('renders without crashing', () => {
    const { container } = render(<LoadingDots />);
    expect(container).toBeTruthy();
  });

  it('renders three dot elements', () => {
    const { container } = render(<LoadingDots />);
    const dots = container.querySelectorAll('span');
    expect(dots).toHaveLength(3);
  });

  it('applies the correct CSS classes', () => {
    const { container } = render(<LoadingDots />);
    const loadingDotsDiv = container.firstChild as HTMLElement;
    expect(loadingDotsDiv.className).toContain('loadingDots');

    const dots = container.querySelectorAll('span');
    dots.forEach(dot => {
      expect(dot.className).toContain('dot');
    });
  });
});
