import Link from 'next/link'

export default function Home() {
  return (
    <main className="container" style={{ paddingTop: 40 }}>
      <h1>Welcome to Think-Inspire</h1>
      <p>Go to <Link href="/chat">Chat</Link></p>
    </main>
  )
}