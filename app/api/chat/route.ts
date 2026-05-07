import { NextResponse } from 'next/server'

const backendBaseUrl = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const response = await fetch(`${backendBaseUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      cache: 'no-store',
    })

    const text = await response.text()

    if (!response.ok) {
      return NextResponse.json(
        { error: text || `Backend request failed with ${response.status}` },
        { status: response.status }
      )
    }

    return new NextResponse(text, {
      status: response.status,
      headers: { 'Content-Type': 'application/json' },
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
