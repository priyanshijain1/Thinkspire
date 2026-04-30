import { NextResponse } from 'next/server';

type ReqBody = { message: string };

function generateReply(message: string): string {
  const m = (message || '').toLowerCase();
  if (m.includes('hello') || m.includes('hi')) return 'Hello! How can I assist you today?';
  if (m.includes('how are you')) return 'I am a program, but I am here to help you!';
  if (m.includes('weather')) return 'I don\'t have live weather data right now, but I can show you how to check it.';
  return `You said: "${message}". Tell me more about your goal or question.`;
}

export async function POST(req: Request) {
  try {
    const body: ReqBody = await req.json();
    const message = body?.message ?? '';
    // Simple simulated latency for realism
    await new Promise((resolve) => setTimeout(resolve, 500));
    const reply = generateReply(message);
    return NextResponse.json({ reply });
  } catch (err) {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }
}
