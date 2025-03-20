"use client";

import { useState } from 'react';
import { useConversations } from '../context/ConversationsContext';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
  const { 
    conversations, 
    projects, 
    fetchConversation, 
    createConversation, 
    updateConversation,
    deleteConversation,
    createProject,
    deleteProject,
    currentConversation,
    clearCurrentConversation
  } = useConversations();
  
  const { user, logout } = useAuth();
  
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [showPinned, setShowPinned] = useState<boolean>(false);
  const [newConvTitle, setNewConvTitle] = useState<string>('');
  const [newProjectName, setNewProjectName] = useState<string>('');
  const [newProjectDesc, setNewProjectDesc] = useState<string>('');
  const [showProjectForm, setShowProjectForm] = useState<boolean>(false);
  
  // Filter conversations based on selection
  const filteredConversations = conversations.filter(conv => {
    if (showPinned) return conv.is_pinned;
    if (selectedProjectId !== null) return conv.project_id === selectedProjectId;
    return true;
  });
  
  const handleNewConversation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newConvTitle) return;
    
    try {
      const id = await createConversation(newConvTitle, selectedProjectId || undefined);
      setNewConvTitle('');
      // Open the new conversation
      await fetchConversation(id);
    } catch (err) {
      console.error("Failed to create conversation:", err);
    }
  };
  
  const handleNewProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName) return;
    
    try {
      await createProject(newProjectName, newProjectDesc || undefined);
      setNewProjectName('');
      setNewProjectDesc('');
      setShowProjectForm(false);
    } catch (err) {
      console.error("Failed to create project:", err);
    }
  };
  
  const handleTogglePin = async (id: number, isPinned: boolean) => {
    await updateConversation(id, { is_pinned: !isPinned });
  };
  
  const handleSelectConversation = (id: number) => {
    fetchConversation(id);
  };
  
  const handleNewChat = () => {
    clearCurrentConversation();
  };
  
  return (
    <div className="h-full w-64 bg-gray-900 text-white flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Anthropic Chat</h2>
        </div>
        
        <button 
          onClick={handleNewChat}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md mb-4"
        >
          New Chat
        </button>
        
        <div className="flex mt-2 space-x-2">
          <button
            onClick={() => { setSelectedProjectId(null); setShowPinned(false); }}
            className={`px-3 py-1 rounded-md ${!selectedProjectId && !showPinned ? 'bg-gray-700' : 'bg-gray-800 hover:bg-gray-700'}`}
          >
            All
          </button>
          <button
            onClick={() => { setShowPinned(true); setSelectedProjectId(null); }}
            className={`px-3 py-1 rounded-md ${showPinned ? 'bg-gray-700' : 'bg-gray-800 hover:bg-gray-700'}`}
          >
            Pinned
          </button>
        </div>
      </div>
      
      {/* Projects Section */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-semibold">Projects</h3>
          <button 
            onClick={() => setShowProjectForm(!showProjectForm)}
            className="text-gray-400 hover:text-white"
          >
            {showProjectForm ? '×' : '+'}
          </button>
        </div>
        
        {showProjectForm && (
          <form onSubmit={handleNewProject} className="mb-3">
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="Project name"
              className="w-full p-2 bg-gray-800 rounded-md mb-2 text-sm"
            />
            <input
              type="text"
              value={newProjectDesc}
              onChange={(e) => setNewProjectDesc(e.target.value)}
              placeholder="Description (optional)"
              className="w-full p-2 bg-gray-800 rounded-md mb-2 text-sm"
            />
            <button 
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 py-1 px-3 rounded-md text-sm"
            >
              Create Project
            </button>
          </form>
        )}
        
        <div className="space-y-1 max-h-40 overflow-y-auto">
          {projects.map(project => (
            <div key={project.id} className="flex justify-between items-center">
              <button
                onClick={() => { setSelectedProjectId(project.id); setShowPinned(false); }}
                className={`text-sm py-1 px-2 rounded-md flex-grow text-left ${selectedProjectId === project.id ? 'bg-gray-700' : 'hover:bg-gray-800'}`}
                title={project.description || ''}
              >
                {project.name}
              </button>
              <button
                onClick={() => deleteProject(project.id)}
                className="text-gray-500 hover:text-red-500 ml-2"
                title="Delete project"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>
      
      {/* Conversations Section */}
      <div className="flex-grow p-4 overflow-hidden flex flex-col">
        <div className="mb-3">
          <form onSubmit={handleNewConversation} className="flex items-center">
            <input
              type="text"
              value={newConvTitle}
              onChange={(e) => setNewConvTitle(e.target.value)}
              placeholder="New conversation title"
              className="flex-grow p-2 bg-gray-800 rounded-l-md"
            />
            <button 
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 py-2 px-3 rounded-r-md"
            >
              +
            </button>
          </form>
        </div>
        
        <div className="overflow-y-auto flex-grow">
          <h3 className="font-semibold mb-2">
            {showPinned 
              ? 'Pinned Conversations' 
              : selectedProjectId !== null 
                ? `Project: ${projects.find(p => p.id === selectedProjectId)?.name}` 
                : 'All Conversations'}
          </h3>
          
          {filteredConversations.length === 0 ? (
            <p className="text-gray-500 text-sm">No conversations found</p>
          ) : (
            <div className="space-y-1">
              {filteredConversations.map(conv => (
                <div 
                  key={conv.id} 
                  className={`p-2 rounded-md flex justify-between items-center ${currentConversation?.id === conv.id ? 'bg-gray-700' : 'hover:bg-gray-800'}`}
                >
                  <button
                    onClick={() => handleSelectConversation(conv.id)}
                    className="flex-grow text-left truncate"
                  >
                    {conv.title}
                  </button>
                  <div className="flex space-x-1">
                    <button
                      onClick={() => handleTogglePin(conv.id, conv.is_pinned)}
                      className={`${conv.is_pinned ? 'text-yellow-400' : 'text-gray-500 hover:text-yellow-400'}`}
                      title={conv.is_pinned ? "Unpin" : "Pin"}
                    >
                      {conv.is_pinned ? '★' : '☆'}
                    </button>
                    <button
                      onClick={() => deleteConversation(conv.id)}
                      className="text-gray-500 hover:text-red-500"
                      title="Delete"
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* User Section */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center justify-between">
          <div className="truncate">
            <div className="font-medium">{user?.username}</div>
            <div className="text-gray-400 text-xs truncate">{user?.email}</div>
          </div>
          <button
            onClick={logout}
            className="text-gray-400 hover:text-white text-sm"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;