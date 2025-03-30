import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { io } from 'socket.io-client';
import ResponseDisplay from './ResponseDisplay';

function PromptForm() {
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [socket, setSocket] = useState(null);
  const navigate = useNavigate();

  // Initialize socket connection
  useEffect(() => {
    const newSocket = io();
    setSocket(newSocket);

    // Listen for prompt acknowledgment
    newSocket.on('prompt_received', (data) => {
      console.log('Prompt received:', data);
      setConversationId(data.conversation_id);
      setIsLoading(false);
    });

    // Listen for errors
    newSocket.on('error', (data) => {
      setError(data.message || 'An error occurred');
      setIsLoading(false);
    });

    // Cleanup on unmount
    return () => {
      newSocket.disconnect();
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!prompt.trim() || !socket) {
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setConversationId(null);

    console.log('Submitting prompt via socket:', prompt);
    
    // Use socket.io to submit the prompt
    socket.emit('submit_prompt', { prompt });
  };

  const handleViewConversation = () => {
    if (conversationId) {
      navigate(`/conversation/${conversationId}`);
    }
  };

  return (
    <div className="prompt-container">
      <button className="help-button" onClick={() => navigate('/objective')}>Objective</button>

      {/* Simple status indicator */}
      <div className="status ready">READY</div>
      
      {/* Simple prompt interface */}
      <form onSubmit={handleSubmit}>
        <div className="prompt-line">
          <label className="prompt-label">PROMPT &gt;</label>
          <textarea
            id="prompt-input"
            className="prompt-input"
            value={prompt}
            onChange={(e) => {
                setPrompt(e.target.value)
            }}
            onInput={(e) => {
                e.target.style.height = "auto";
                e.target.style.height = (e.target.scrollHeight) + "px";
            }}
            disabled={isLoading}
            autoFocus
          />
        </div>
        
        <button 
          type="submit" 
          className="execute-button"
          disabled={isLoading || !prompt.trim()}
        >
          {isLoading ? 'EXECUTING' : 'EXECUTE'}
          {isLoading && <span className="loading"></span>}
        </button>
      </form>
      
      {/* Error message */}
      {error && <div className="error-message">ERROR: {error}</div>}
      
      {/* Results display */}
      {conversationId && (
        <div className="results-container">
          <ResponseDisplay 
            conversationId={conversationId} 
            existingSocket={socket} 
          />
          
          <button 
            onClick={handleViewConversation} 
            className="archive-link"
          >
            ARCHIVE DATA
          </button>
        </div>
      )}
    </div>
  );
}

export default PromptForm; 