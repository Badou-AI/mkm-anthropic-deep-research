import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '../context/AuthContext';
import { ConversationsProvider } from '../context/ConversationsContext';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Anthropic Chat UI',
  description: 'A ChatGPT-like interface for the Anthropic-OpenAI agent',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`bg-gray-50 min-h-screen ${inter.className}`}>
        <AuthProvider>
          <ConversationsProvider>
            {children}
          </ConversationsProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
