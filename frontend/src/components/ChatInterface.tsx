"use client";

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

type Message = {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
};

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [wsEnabled, setWsEnabled] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  
  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Connect to WebSocket when enabled
  useEffect(() => {
    if (wsEnabled && !ws.current) {
      connectWebSocket();
    }
    
    return () => {
      ws.current?.close();
    };
  }, [wsEnabled]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  const connectWebSocket = () => {
    // Use window.location to dynamically determine the host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = '8000'; // Backend port
    const socket = new WebSocket(`${protocol}//${host}:${port}/chat/ws`);
    
    socket.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected');
      setError(''); // Clear any previous errors when connected
    };
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'chunk') {
          setStreamingMessage(prev => prev + data.content);
        } else if (data.type === 'stop') {
          setMessages(prev => [...prev, { role: 'assistant', content: streamingMessage }]);
          setStreamingMessage('');
          setIsLoading(false);
        } else if (data.type === 'error') {
          setError(data.message);
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
        setError('Failed to parse WebSocket message');
        setIsLoading(false);
      }
    };
    
    socket.onclose = () => {
      setWsConnected(false);
      ws.current = null;
      console.log('WebSocket disconnected');
    };
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError(`WebSocket connection error: ${error}`);
      setWsConnected(false);
      ws.current = null;
    };
    
    ws.current = socket;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setError('');
    setIsLoading(true);
    
    try {
      if (wsEnabled && wsConnected) {
        // Send via WebSocket for streaming
        ws.current?.send(JSON.stringify({
          messages: [...messages, userMessage],
          model: 'claude-3-7-sonnet-latest',
          max_tokens: 2048,
          system_prompt: 'You are a helpful assistant.'
        }));
      } else {
        // Send via REST API
        const response = await axios.post('http://localhost:8000/chat/', {
          messages: [...messages, userMessage],
          model: 'claude-3-7-sonnet-latest',
          max_tokens: 2048,
          system_prompt: 'You are a helpful assistant.'
        });
        
        const aiResponse = response.data;
        setMessages(prev => [...prev, aiResponse.message]);
        setIsLoading(false);
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full h-[80vh] flex flex-col bg-white rounded-lg shadow-md overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, index) => (
          <div key={index} className={`mb-4 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
            <div
              className={`inline-block max-w-[70%] p-3 rounded-lg ${msg.role === 'user' ? 'bg-blue-100 text-blue-900' : 'bg-gray-100 text-gray-900'}`}
            >
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          </div>
        ))}
        
        {streamingMessage && (
          <div className="mb-4 text-left">
            <div className="inline-block max-w-[70%] p-3 rounded-lg bg-gray-100 text-gray-900">
              <ReactMarkdown>{streamingMessage}</ReactMarkdown>
            </div>
          </div>
        )}
        
        {isLoading && !streamingMessage && (
          <div className="text-center p-2">
            <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-blue-500 border-r-transparent"></div>
          </div>
        )}
        
        {error && <div className="text-red-500 p-2 text-center">{error}</div>}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="border-t border-gray-200 p-4">
        <div className="flex items-center mb-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={wsEnabled}
              onChange={() => setWsEnabled(!wsEnabled)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-600">
              Enable streaming {wsConnected && wsEnabled && '(connected)'}
            </span>
          </label>
        </div>
        
        <form onSubmit={handleSubmit} className="flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 p-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded-r-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-blue-300"
            disabled={isLoading || !input.trim()}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
