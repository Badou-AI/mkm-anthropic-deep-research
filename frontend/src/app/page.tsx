"use client";

import { useState, useEffect } from 'react';
import ChatInterface from '../components/ChatInterface';
import SearchInterface from '../components/SearchInterface';
import Sidebar from '../components/Sidebar';
import AuthForms from '../components/AuthForms';
import { useAuth } from '../context/AuthContext';

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<'chat' | 'search'>('chat');
  
  // If loading, show a simple loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  // If not authenticated, show login/register form
  if (!isAuthenticated) {
    return <AuthForms />;
  }
  
  // Main application with sidebar and content
  return (
    <main className="flex min-h-screen">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content */}
      <div className="flex-1 p-6 overflow-hidden">
        {/* Tab navigation */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('chat')}
                className={`mr-8 py-3 px-1 text-center border-b-2 font-medium text-sm ${activeTab === 'chat' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              >
                Chat
              </button>
              <button
                onClick={() => setActiveTab('search')}
                className={`mr-8 py-3 px-1 text-center border-b-2 font-medium text-sm ${activeTab === 'search' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              >
                Search
              </button>
            </nav>
          </div>
        </div>
        
        {/* Tab content */}
        <div className="h-[calc(100vh-10rem)]">
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