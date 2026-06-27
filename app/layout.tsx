import './globals.css'
import ThemeToggle from './ThemeToggle'

export const metadata = {
  title: 'Thinkspire - AI-Powered Thinking Partner',
  description: 'Explore ideas and solve problems with intelligent AI guidance. Think deeper, grow smarter.',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  userScalable: true,
  themeColor: '#3b82f6',
}

const themeScript = `
  (function() {
    try {
      var stored = localStorage.getItem('theme');
      var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      var theme = stored || (prefersDark ? 'dark' : 'light');
      document.documentElement.setAttribute('data-theme', theme);
    } catch(e) {}
  })();
`

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        {children}
        <ThemeToggle />
      </body>
    </html>
  )
}
