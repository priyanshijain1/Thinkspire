import './globals.css'

export const metadata = {
  title: 'Thinkspire - AI-Powered Thinking Partner',
  description: 'Explore ideas and solve problems with intelligent AI guidance. Think deeper, grow smarter.',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  userScalable: true,
  themeColor: '#1a1a1a',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="bg-[#fafbfc]">
      <body>{children}</body>
    </html>
  )
}
