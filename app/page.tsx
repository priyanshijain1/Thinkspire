import Link from 'next/link'

export default function Home() {
  return (
    <main className="container" style={{ paddingTop: 40 }}>
      <h1>Welcome to the Think-Inspire App</h1>
      <p>Open the chat interface to converse with the AI solver.</p>
      <p>
        <Link href="/chat">Go to Chat</Link>
      </p>
    </main>
  )
}
