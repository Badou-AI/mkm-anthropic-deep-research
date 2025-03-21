"use client";

import { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { FaSearch } from 'react-icons/fa';

type SearchResult = {
  query: string;
  result: string;
};

const SearchInterface = () => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<'simple' | 'deep_iterative'>('simple');
  const [complexity, setComplexity] = useState<'low' | 'medium' | 'high'>('medium');
  const [constraints, setConstraints] = useState('');
  const [maxIterations, setMaxIterations] = useState(3);
  const [results, setResults] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    
    setIsLoading(true);
    setError('');
    setResults([]);
    
    try {
      const response = await axios.post('http://localhost:8000/search/', {
        query,
        search_type: searchType,
        complexity,
        constraints,
        max_iterations: maxIterations
      });
      
      setResults(response.data.results);
    } catch (err: any) {
      console.error('Search error:', err);
      setError(err.response?.data?.detail || 'Failed to perform search. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full bg-white rounded-lg shadow-md overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <form onSubmit={handleSearch}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Query
            </label>
            <div className="relative">
              <textarea
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  // Auto adjust height
                  e.target.style.height = 'auto';
                  e.target.style.height = e.target.scrollHeight + 'px';
                }}
                placeholder="Enter your search query"
                className="w-full p-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none overflow-hidden min-h-[40px]"
                disabled={isLoading}
                rows={1}
                style={{ height: 'auto' }}
              />
              <button
                type="submit"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-blue-600 focus:outline-none disabled:text-gray-300"
                disabled={isLoading || !query.trim()}
              >
                <FaSearch className="w-5 h-5" />
              </button>
            </div>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Type
            </label>
            <div className="flex space-x-4">
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  value="simple"
                  checked={searchType === 'simple'}
                  onChange={() => setSearchType('simple')}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  disabled={isLoading}
                />
                <span className="ml-2 text-sm text-gray-700">Simple</span>
              </label>
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  value="deep_iterative"
                  checked={searchType === 'deep_iterative'}
                  onChange={() => setSearchType('deep_iterative')}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  disabled={isLoading}
                />
                <span className="ml-2 text-sm text-gray-700">Deep Iterative</span>
              </label>
            </div>
          </div>
          
          {searchType === 'deep_iterative' && (
            <>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Complexity
                </label>
                <select
                  value={complexity}
                  onChange={(e) => setComplexity(e.target.value as any)}
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Constraints (optional)
                </label>
                <textarea
                  value={constraints}
                  onChange={(e) => setConstraints(e.target.value)}
                  placeholder="Add any specific constraints for your search"
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[80px]"
                  disabled={isLoading}
                />
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Iterations
                </label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={maxIterations}
                  onChange={(e) => setMaxIterations(parseInt(e.target.value, 10))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                />
              </div>
            </>
          )}
          
          <div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-blue-300"
              disabled={isLoading || !query.trim()}
            >
              {isLoading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </form>
      </div>
      
      <div className="p-4 max-h-[600px] overflow-y-auto">
        <h2 className="text-lg font-semibold mb-4">Search Results</h2>
        
        {isLoading && (
          <div className="flex justify-center items-center p-8">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent"></div>
          </div>
        )}
        
        {error && <div className="text-red-500 p-2 mb-4">{error}</div>}
        
        {!isLoading && results.length === 0 && !error && (
          <div className="text-gray-500 text-center p-4">No results to display</div>
        )}
        
        {results.map((result, index) => (
          <div key={index} className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="prose max-w-none">
              <ReactMarkdown>{result}</ReactMarkdown>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchInterface;
