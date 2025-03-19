"use client";

import { useState } from 'react';
import ChatInterface from '../components/ChatInterface';
import SearchInterface from '../components/SearchInterface';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'chat' | 'search'>('chat');

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 lg:p-12">
      <div className="w-full max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">Anthropic-OpenAI Agent</h1>
        
        {/* Tab navigation */}
        <div className="flex justify-center mb-8">
          <div className="border-b border-gray-200 w-full max-w-md">
            <nav className="flex -mb-px justify-center" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('chat')}
                className={`w-1/2 py-3 px-4 text-center border-b-2 font-medium text-sm ${activeTab === 'chat' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              >
                Chat
              </button>
              <button
                onClick={() => setActiveTab('search')}
                className={`w-1/2 py-3 px-4 text-center border-b-2 font-medium text-sm ${activeTab === 'search' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              >
                Search
              </button>
            </nav>
          </div>
        </div>
        
        {/* Tab content */}
        <div className="w-full">
          {activeTab === 'chat' ? (
            <ChatInterface />
          ) : (
            <SearchInterface />
          )}
        </div>
      </div>
    </main>
  );
}
