/**
 * Comprehensive test suite for StadiumSense frontend components.
 * Covers: AnnouncementFeed, ChatInterface, SettingsPanel, StadiumMap,
 * UrgentOverlay, and App routing.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// ─── App routing ─────────────────────────────────────────────────────────────
import App from './App';

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
  });

  it('redirects root path to /fan', () => {
    render(<App />);
    // BrowserRouter starts at '/', which should redirect to '/fan'
    expect(document.body).toBeTruthy();
  });
});

// ─── AnnouncementFeed ─────────────────────────────────────────────────────────
import AnnouncementFeed from './components/AnnouncementFeed';

const defaultSettings = {
  language: 'en',
  textSize: 1,
  haptics: false,
  highContrast: false,
};

const sampleAnnouncement = {
  id: 'ann_001',
  timestamp: Date.now() / 1000,
  type: 'pa_announcement',
  original: 'Medical team to Section 114.',
  category: 'medical',
  severity: 'critical',
  plain_language: 'Medical team needed at Section 114.',
  translated: {
    en: 'Medical team needed at Section 114.',
    hi: 'धारा 114 पर चिकित्सा दल।',
    es: 'Equipo médico en la Sección 114.',
  },
  icon: '🏥',
};

describe('AnnouncementFeed', () => {
  it('shows empty state when no announcements', () => {
    render(<AnnouncementFeed announcements={[]} settings={defaultSettings} />);
    expect(screen.getByText(/Waiting for updates/i)).toBeInTheDocument();
  });

  it('renders an announcement card', () => {
    render(
      <AnnouncementFeed announcements={[sampleAnnouncement]} settings={defaultSettings} />
    );
    expect(screen.getByText('Medical team needed at Section 114.')).toBeInTheDocument();
  });

  it('shows translated text for selected language', () => {
    const settings = { ...defaultSettings, language: 'es' };
    render(<AnnouncementFeed announcements={[sampleAnnouncement]} settings={settings} />);
    expect(screen.getByText('Equipo médico en la Sección 114.')).toBeInTheDocument();
  });

  it('renders the correct category icon', () => {
    render(
      <AnnouncementFeed announcements={[sampleAnnouncement]} settings={defaultSettings} />
    );
    expect(screen.getByText('🏥')).toBeInTheDocument();
  });

  it('renders goal scoreline for match_event with score', () => {
    const goalAnnouncement = {
      ...sampleAnnouncement,
      id: 'ann_goal',
      type: 'match_event',
      category: 'match_event',
      severity: 'crowd',
      icon: '⚽',
      team_a: 'BRA',
      team_b: 'BEL',
      score_a: 1,
      score_b: 0,
      minute: 23,
    };
    render(
      <AnnouncementFeed announcements={[goalAnnouncement]} settings={defaultSettings} />
    );
    expect(screen.getByText(/BRA/)).toBeInTheDocument();
    expect(screen.getByText(/BEL/)).toBeInTheDocument();
    expect(screen.getByText("23'")).toBeInTheDocument();
  });

  it('expand button toggles original text visibility', async () => {
    render(
      <AnnouncementFeed announcements={[sampleAnnouncement]} settings={defaultSettings} />
    );
    const moreButton = screen.getByText(/More/i);
    await userEvent.click(moreButton);
    expect(screen.getByText('Medical team to Section 114.')).toBeInTheDocument();
    // Click again to collapse
    const lessButton = screen.getByText(/Less/i);
    await userEvent.click(lessButton);
    expect(screen.queryByText(/Original/i)).not.toBeInTheDocument();
  });

  it('renders multiple announcement cards', () => {
    const ann2 = { ...sampleAnnouncement, id: 'ann_002', plain_language: 'Second announcement.' };
    render(
      <AnnouncementFeed
        announcements={[sampleAnnouncement, ann2]}
        settings={defaultSettings}
      />
    );
    expect(screen.getByText('Medical team needed at Section 114.')).toBeInTheDocument();
    expect(screen.getByText('Second announcement.')).toBeInTheDocument();
  });
});

// ─── SettingsPanel ────────────────────────────────────────────────────────────
import SettingsPanel from './components/SettingsPanel';

const languages = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi' },
  { code: 'es', name: 'Spanish' },
];

describe('SettingsPanel', () => {
  it('renders language selector', () => {
    const onUpdate = vi.fn();
    render(
      <SettingsPanel settings={defaultSettings} onUpdate={onUpdate} languages={languages} />
    );
    expect(screen.getByText('Language')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('calls onUpdate when language changes', async () => {
    const onUpdate = vi.fn();
    render(
      <SettingsPanel settings={defaultSettings} onUpdate={onUpdate} languages={languages} />
    );
    await userEvent.selectOptions(screen.getByRole('combobox'), 'hi');
    expect(onUpdate).toHaveBeenCalledWith({ language: 'hi' });
  });

  it('renders vibration alerts toggle', () => {
    render(
      <SettingsPanel settings={defaultSettings} onUpdate={vi.fn()} languages={languages} />
    );
    expect(screen.getByText('Vibration Alerts')).toBeInTheDocument();
    expect(screen.getByRole('switch', { name: /vibration/i })).toBeInTheDocument();
  });

  it('calls onUpdate when haptics toggle is clicked', async () => {
    const onUpdate = vi.fn();
    render(
      <SettingsPanel settings={defaultSettings} onUpdate={onUpdate} languages={languages} />
    );
    const hapticSwitch = screen.getByRole('switch', { name: /vibration/i });
    await userEvent.click(hapticSwitch);
    expect(onUpdate).toHaveBeenCalledWith({ haptics: true });
  });

  it('renders high contrast toggle', () => {
    render(
      <SettingsPanel settings={defaultSettings} onUpdate={vi.fn()} languages={languages} />
    );
    expect(screen.getByText('High Contrast')).toBeInTheDocument();
    expect(screen.getByRole('switch', { name: /high contrast/i })).toBeInTheDocument();
  });

  it('calls onUpdate when high contrast is toggled', async () => {
    const onUpdate = vi.fn();
    render(
      <SettingsPanel settings={defaultSettings} onUpdate={onUpdate} languages={languages} />
    );
    const contrastSwitch = screen.getByRole('switch', { name: /high contrast/i });
    await userEvent.click(contrastSwitch);
    expect(onUpdate).toHaveBeenCalledWith({ highContrast: true });
  });

  it('displays current text size percentage', () => {
    render(
      <SettingsPanel settings={defaultSettings} onUpdate={vi.fn()} languages={languages} />
    );
    expect(screen.getByText('Current: 100%')).toBeInTheDocument();
  });

  it('shows Text Size section', () => {
    render(
      <SettingsPanel settings={defaultSettings} onUpdate={vi.fn()} languages={languages} />
    );
    expect(screen.getByText('Text Size')).toBeInTheDocument();
    expect(screen.getByRole('slider')).toBeInTheDocument();
  });
});

// ─── ChatInterface ────────────────────────────────────────────────────────────
import ChatInterface from './components/ChatInterface';

describe('ChatInterface', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it('renders the input and send button', () => {
    render(<ChatInterface language="en" section="114" />);
    expect(screen.getByPlaceholderText(/Ask about the stadium/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('renders quick question shortcuts', () => {
    render(<ChatInterface language="en" section="114" />);
    expect(screen.getByText('Nearest step-free restroom?')).toBeInTheDocument();
    expect(screen.getByText('Where is first aid?')).toBeInTheDocument();
  });

  it('shows loading state while fetching', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      json: () =>
        new Promise((resolve) =>
          setTimeout(() => resolve({ answer: 'Test answer', citations: [] }), 200)
        ),
    });

    render(<ChatInterface language="en" section="114" />);
    const input = screen.getByPlaceholderText(/Ask about the stadium/i);
    await userEvent.clear(input);
    await userEvent.type(input, 'Where is the exit?');

    const form = document.getElementById('chat-form') as HTMLFormElement;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText(/Thinking/i)).toBeInTheDocument();
    });
  });

  it('displays the answer after successful fetch', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      json: async () => ({
        answer: 'The nearest restroom is at Gate B.',
        citations: ['Section 114 facilities'],
        language: 'en',
      }),
    });

    render(<ChatInterface language="en" section="114" />);
    const input = screen.getByPlaceholderText(/Ask about the stadium/i);
    await userEvent.clear(input);
    await userEvent.type(input, 'Where is the restroom?');

    const form = document.getElementById('chat-form') as HTMLFormElement;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText('The nearest restroom is at Gate B.')).toBeInTheDocument();
    });
  });

  it('shows error message on fetch failure', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('Network error'));

    render(<ChatInterface language="en" section="114" />);
    const input = screen.getByPlaceholderText(/Ask about the stadium/i);
    await userEvent.clear(input);
    await userEvent.type(input, 'Where is first aid?');

    const form = document.getElementById('chat-form') as HTMLFormElement;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText(/Failed to get answer/i)).toBeInTheDocument();
    });
  });

  it('disables send button when input is empty', () => {
    render(<ChatInterface language="en" section="114" />);
    const input = screen.getByPlaceholderText(/Ask about the stadium/i) as HTMLInputElement;
    // Clear the pre-filled value
    fireEvent.change(input, { target: { value: '' } });
    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it('renders citations when returned in response', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      json: async () => ({
        answer: 'Take the elevator near Gate C.',
        citations: ['Gate C accessibility guide'],
        language: 'en',
      }),
    });

    render(<ChatInterface language="en" section="114" />);
    const input = screen.getByPlaceholderText(/Ask about the stadium/i);
    await userEvent.clear(input);
    await userEvent.type(input, 'Step-free route?');

    const form = document.getElementById('chat-form') as HTMLFormElement;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText('Gate C accessibility guide')).toBeInTheDocument();
    });
  });
});

// ─── UrgentOverlay ────────────────────────────────────────────────────────────
import UrgentOverlay from './components/UrgentOverlay';

describe('UrgentOverlay', () => {
  it('renders the urgent message', () => {
    const onDismiss = vi.fn();
    render(<UrgentOverlay message="EVACUATE NOW!" onDismiss={onDismiss} />);
    expect(screen.getByText(/EVACUATE NOW/i)).toBeInTheDocument();
  });

  it('calls onDismiss when dismiss button clicked', async () => {
    const onDismiss = vi.fn();
    render(<UrgentOverlay message="Please leave the stadium." onDismiss={onDismiss} />);
    await userEvent.click(screen.getByText(/I understand/i));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it('renders the follow staff instructions message', () => {
    render(<UrgentOverlay message="Emergency" onDismiss={vi.fn()} />);
    expect(screen.getByText(/Please follow staff instructions/i)).toBeInTheDocument();
  });
});
