"use client";

import { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

type Message = {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
};

type Conversation = {
  id: string;
  title: string;
  is_pinned: boolean;
  project_id: string | null;
  created_at: string;
  updated_at: string;
};

type Project = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
};

type ConversationDetail = Conversation & {
  messages: Message[];
};

type ConversationsContextType = {
  conversations: Conversation[];
  projects: Project[];
  currentConversation: ConversationDetail | null;
  isLoading: boolean;
  error: string | null;
  fetchConversations: () => Promise<void>;
  fetchProjects: () => Promise<void>;
  fetchConversation: (id: string) => Promise<void>;
  createConversation: (title: string, project_id?: string) => Promise<string>;
  updateConversation: (id: string, data: { title?: string, is_pinned?: boolean, project_id?: string | null }) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  createProject: (name: string, description?: string) => Promise<string>;
  deleteProject: (id: string) => Promise<void>;
  clearCurrentConversation: () => void;
};

const ConversationsContext = createContext<ConversationsContextType | undefined>(undefined);

export const ConversationsProvider = ({ children }: { children: ReactNode }) => {
  const { token, isAuthenticated } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentConversation, setCurrentConversation] = useState<ConversationDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Set up axios authorization header for all requests
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Fetch conversations when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchConversations();
      fetchProjects();
    } else {
      setConversations([]);
      setProjects([]);
      setCurrentConversation(null);
    }
  }, [isAuthenticated]);

  const fetchConversations = async () => {
    if (!token) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get('http://localhost:8000/conversations/');
      setConversations(response.data);
    } catch (err: any) {
      console.error('Error fetching conversations:', err);
      setError(err.response?.data?.detail || 'Failed to fetch conversations');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchProjects = async () => {
    if (!token) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get('http://localhost:8000/projects/');
      setProjects(response.data);
    } catch (err: any) {
      console.error('Error fetching projects:', err);
      setError(err.response?.data?.detail || 'Failed to fetch projects');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchConversation = async (id: string) => {
    if (!token) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get(`http://localhost:8000/conversations/${id}`);
      setCurrentConversation(response.data);
    } catch (err: any) {
      console.error(`Error fetching conversation ${id}:`, err);
      setError(err.response?.data?.detail || 'Failed to fetch conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const createConversation = async (title: string, project_id?: string): Promise<string> => {
    if (!token) throw new Error('Authentication required');
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:8000/conversations/', {
        title,
        project_id: project_id || null
      });
      
      await fetchConversations(); // Refresh the list
      return response.data.id;
    } catch (err: any) {
      console.error('Error creating conversation:', err);
      setError(err.response?.data?.detail || 'Failed to create conversation');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const updateConversation = async (id: string, data: { title?: string, is_pinned?: boolean, project_id?: string | null }) => {
    if (!token) return;
    
    setIsLoading(true);
    setError(null);
    try {
      await axios.patch(`http://localhost:8000/conversations/${id}`, data);
      
      // Update local state
      await fetchConversations();
      
      // Update current conversation if it's the one being modified
      if (currentConversation && currentConversation.id === id) {
        await fetchConversation(id);
      }
    } catch (err: any) {
      console.error(`Error updating conversation ${id}:`, err);
      setError(err.response?.data?.detail || 'Failed to update conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteConversation = async (id: string) => {
    if (!token) return;
    
    setIsLoading(true);
    setError(null);
    try {
      await axios.delete(`http://localhost:8000/conversations/${id}`);
      
      // Update local state
      setConversations(conversations.filter(conv => conv.id !== id));
      
      // Clear current conversation if it's the one being deleted
      if (currentConversation && currentConversation.id === id) {
        setCurrentConversation(null);
      }
    } catch (err: any) {
      console.error(`Error deleting conversation ${id}:`, err);
      setError(err.response?.data?.detail || 'Failed to delete conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const createProject = async (name: string, description?: string): Promise<string> => {
    if (!token) throw new Error('Authentication required');
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:8000/projects/', {
        name,
        description: description || null
      });
      
      await fetchProjects(); // Refresh the list
      return response.data.id;
    } catch (err: any) {
      console.error('Error creating project:', err);
      setError(err.response?.data?.detail || 'Failed to create project');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const deleteProject = async (id: string) => {
    if (!token) return;
    
    setIsLoading(true);
    setError(null);
    try {
      await axios.delete(`http://localhost:8000/projects/${id}`);
      
      // Update local state
      setProjects(projects.filter(proj => proj.id !== id));
      await fetchConversations(); // Refresh conversations as their project_id might have changed
    } catch (err: any) {
      console.error(`Error deleting project ${id}:`, err);
      setError(err.response?.data?.detail || 'Failed to delete project');
    } finally {
      setIsLoading(false);
    }
  };

  const clearCurrentConversation = () => {
    setCurrentConversation(null);
  };

  return (
    <ConversationsContext.Provider
      value={{
        conversations,
        projects,
        currentConversation,
        isLoading,
        error,
        fetchConversations,
        fetchProjects,
        fetchConversation,
        createConversation,
        updateConversation,
        deleteConversation,
        createProject,
        deleteProject,
        clearCurrentConversation
      }}
    >
      {children}
    </ConversationsContext.Provider>
  );
};

export const useConversations = () => {
  const context = useContext(ConversationsContext);
  if (context === undefined) {
    throw new Error('useConversations must be used within a ConversationsProvider');
  }
  return context;
};