import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll } from 'vitest';

// Mock react-i18next to return the key as the translation
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en_us' },
  }),
}));

import ConsolePanel from '../components/ConsolePanel';

beforeAll(() => {
  // jsdom does not implement scrollIntoView
  Element.prototype.scrollIntoView = vi.fn();
});

describe('ConsolePanel', () => {
  it('renders empty state when no lines', () => {
    render(<ConsolePanel lines={[]} onClear={() => {}} />);
    expect(screen.getByText('no_console_output')).toBeInTheDocument();
  });

  it('renders lines', () => {
    render(<ConsolePanel lines={['hello', 'world']} onClear={() => {}} />);
    expect(screen.getByText('hello')).toBeInTheDocument();
    expect(screen.getByText('world')).toBeInTheDocument();
  });

  it('calls onClear when clear button is clicked', () => {
    const onClear = vi.fn();
    render(<ConsolePanel lines={['test']} onClear={onClear} />);
    fireEvent.click(screen.getByText('clear'));
    expect(onClear).toHaveBeenCalledOnce();
  });
});
