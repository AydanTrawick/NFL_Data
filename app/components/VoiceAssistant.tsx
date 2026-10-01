'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';

type Turn = { role: 'user' | 'assistant'; text: string };
type RecognitionResult = { results: ArrayLike<ArrayLike<{ transcript: string }>> };
type Recognition = {
  lang: string;
  interimResults: boolean;
  onresult: ((event: RecognitionResult) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

export default function VoiceAssistant() {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [notice, setNotice] = useState('');
  const [canListen, setCanListen] = useState(false);
  const [playbackUrl, setPlaybackUrl] = useState('');
  const requestBusy = useRef(false);
  const recognition = useRef<Recognition | null>(null);
  const audio = useRef<HTMLAudioElement | null>(null);
  const audioUrl = useRef<string | null>(null);
  const feed = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const speechWindow = window as Window & { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };
    const Speech = speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition;
    setCanListen(Boolean(Speech));
    if (!Speech) return;
    const instance = new Speech();
    instance.lang = 'en-US';
    instance.interimResults = false;
    instance.onresult = event => {
      const spoken = Array.from(event.results).map(result => result[0]?.transcript || '').join(' ').trim();
      if (spoken) { setDraft(spoken); void ask(spoken); }
    };
    instance.onerror = event => { setListening(false); setNotice(event.error === 'not-allowed' ? 'Allow microphone access in your browser to ask by voice.' : 'I could not hear that. Try again or type your question.'); };
    instance.onend = () => setListening(false);
    recognition.current = instance;
    return () => { instance.stop(); if (audioUrl.current) URL.revokeObjectURL(audioUrl.current); };
  // The speech recognizer is initialized once for this persistent site-wide assistant.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { if (feed.current) feed.current.scrollTop = feed.current.scrollHeight; }, [turns, busy]);
  useEffect(() => {
    if (!playbackUrl || !audio.current) return;
    void audio.current.play().catch(() => setNotice('Voice reply is ready. Press play below to hear it.'));
  }, [playbackUrl, open]);

  async function ask(question: string) {
    const clean = question.trim();
    if (clean.length < 3 || requestBusy.current) return;
    requestBusy.current = true;
    recognition.current?.stop();
    audio.current?.pause();
    setPlaybackUrl('');
    setDraft(''); setNotice(''); setTurns(previous => [...previous, { role: 'user', text: clean }]); setBusy(true);
    try {
      const response = await fetch('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: clean }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'I could not answer that question.');
      const answer = String(result.answer || 'I could not find an answer in the season data.');
      setTurns(previous => [...previous, { role: 'assistant', text: answer }]);
      try {
        const speechResponse = await fetch('/api/voice/speak', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: answer }) });
        if (!speechResponse.ok) {
          const details = await speechResponse.json().catch(() => ({}));
          setNotice(details.error || 'Text reply is ready; voice playback is unavailable.');
          return;
        }
        const blob = await speechResponse.blob();
        if (audioUrl.current) URL.revokeObjectURL(audioUrl.current);
        audioUrl.current = URL.createObjectURL(blob);
        setPlaybackUrl(audioUrl.current);
      } catch { setNotice('Text reply is ready; voice playback is unavailable.'); }
    } catch (error) {
      setTurns(previous => [...previous, { role: 'assistant', text: error instanceof Error ? error.message : 'I could not answer that question.' }]);
    } finally { requestBusy.current = false; setBusy(false); }
  }

  function submit(event: FormEvent) { event.preventDefault(); void ask(draft); }
  function toggleListening() {
    if (!recognition.current) { setNotice('Voice input is not supported by this browser. Type your question instead.'); return; }
    setNotice('');
    if (listening) { recognition.current.stop(); setListening(false); }
    else { try { setListening(true); recognition.current.start(); } catch { setListening(false); setNotice('Microphone is busy. Try again in a moment.'); } }
  }

  return <>
    {open && <section className="voice-panel" aria-label="Season data voice assistant">
      <header className="voice-head"><div><span className="live-dot" />SEASON DATA ASSISTANT<small>PLAYERS · TEAMS · 2025 SEASON</small></div><button className="voice-close" onClick={() => setOpen(false)} aria-label="Close assistant">×</button></header>
      <div className="voice-feed" ref={feed} aria-live="polite">
        {!turns.length && <p className="voice-welcome">Ask about a player, team, or season stat. You can keep browsing while I answer.</p>}
        {turns.map((turn, index) => <div key={index} className={`voice-turn ${turn.role}`}><span>{turn.role === 'user' ? 'YOU' : 'SNAP'}</span><p>{turn.text}</p></div>)}
        {busy && <p className="voice-working">CHECKING THE SEASON DATA…</p>}
      </div>
      {playbackUrl && <audio className="voice-audio" ref={audio} src={playbackUrl} controls preload="none" aria-label="Spoken answer" />}
      {notice && <p className="voice-notice" role="status">{notice}</p>}
      <form className="voice-form" onSubmit={submit}>
        {canListen && <button type="button" disabled={busy} className={`voice-mic${listening ? ' is-listening' : ''}`} onClick={toggleListening} aria-label={listening ? 'Stop listening' : 'Ask by voice'} title={listening ? 'Stop listening' : 'Ask by voice'}>{listening ? '■' : '●'}</button>}
        <input value={draft} onChange={event => setDraft(event.target.value)} maxLength={500} placeholder={listening ? 'Listening…' : 'Ask about a player or team'} aria-label="Ask the season data assistant" />
        <button type="submit" disabled={busy || draft.trim().length < 3} aria-label="Send question">↑</button>
      </form>
      <p className="voice-foot">MICROPHONE INPUT · ELEVENLABS VOICE REPLY</p>
    </section>}
    <button className={`voice-launch${open ? ' active' : ''}`} onClick={() => setOpen(value => !value)} aria-expanded={open} aria-label={open ? 'Close season data assistant' : 'Open season data assistant'}><span className="voice-orb">{open ? '×' : '✳'}</span><span>{open ? 'CLOSE ASSISTANT' : 'ASK THE DATA'}</span></button>
  </>;
}
