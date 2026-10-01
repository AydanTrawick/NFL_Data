import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

const requests = new Map<string, { count: number; until: number }>();

export async function POST(req: NextRequest) {
  const key = process.env.ELEVENLABS_API_KEY;
  const voiceId = process.env.ELEVENLABS_VOICE_ID;
  if (!key || !voiceId) return NextResponse.json({ error: 'Voice replies need ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID configured by the site owner.' }, { status: 503 });
  try {
    const rawText = (await req.json()).text;
    if (typeof rawText !== 'string' || rawText.length > 2500) return NextResponse.json({ error: 'Voice reply text must be between 1 and 2,500 characters.' }, { status: 400 });
    const text = rawText.replace(/\*/g, '').trim();
    if (!text) return NextResponse.json({ error: 'Voice reply text must be between 1 and 2,500 characters.' }, { status: 400 });
    const ip = req.headers.get('x-forwarded-for')?.split(',')[0] || 'local';
    const now = Date.now();
    for (const [address, value] of requests) if (value.until < now) requests.delete(address);
    const rate = requests.get(ip) || { count: 0, until: now + 60_000 };
    if (++rate.count > 15) return NextResponse.json({ error: 'Voice is busy. Wait a minute before asking again.' }, { status: 429 });
    requests.set(ip, rate);

    const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${encodeURIComponent(voiceId)}?output_format=mp3_44100_128`, {
      method: 'POST',
      headers: { 'xi-api-key': key, 'Content-Type': 'application/json', Accept: 'audio/mpeg' },
      body: JSON.stringify({ text: text.trim(), model_id: process.env.ELEVENLABS_MODEL_ID || 'eleven_multilingual_v2' }),
      signal: AbortSignal.timeout(20_000),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      const message = response.status === 401 || response.status === 403 ? 'ElevenLabs rejected the voice credentials. Check the API key and voice ID.' : response.status === 429 ? 'ElevenLabs voice quota or rate limit reached.' : 'ElevenLabs could not generate the voice reply.';
      console.error('ElevenLabs speech request failed:', response.status, detail.detail?.status || detail.detail?.message || 'provider error');
      return NextResponse.json({ error: message }, { status: response.status === 429 ? 429 : 502 });
    }
    return new NextResponse(await response.arrayBuffer(), { headers: { 'Content-Type': 'audio/mpeg', 'Cache-Control': 'no-store' } });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error && error.name === 'TimeoutError' ? 'Voice generation took too long. Try again.' : 'Unable to generate a voice reply.' }, { status: 502 });
  }
}
