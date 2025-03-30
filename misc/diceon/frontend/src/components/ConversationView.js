import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import Display from './Display';
import { useNavigate } from 'react-router-dom';

function ConversationView() {
  const { id } = useParams();
  const [conversation, setConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formattedResponses, setFormattedResponses] = useState([]);
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchConversation = async () => {
      try {
        const response = await axios.get(`/api/conversation/${id}`);
        console.log(response.data);
        setConversation(response.data);
        setFormattedResponses(response.data.responses);
      } catch (err) {
        console.error('Error fetching conversation:', err);
        setError('Failed to load conversation. It may not exist or has been removed.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversation();
  }, [id]);

  if (isLoading) {
    return <div className="loading">Loading conversation...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">{error}</p>
        <Link to="/" className="back-link">Back to Home</Link>
      </div>
    );
  }

  return (
    <div className="conversation-view">
      <h2>Archive</h2>
      
      <div className="conversation-details">
        <div className="prompt-section">
          <h3>Prompt:</h3>
          <p className="prompt-text">{conversation.prompt}</p>
        </div>
        
        <div className="responses-section">
          <h3>Execution Trace:</h3>
          <Display responses={formattedResponses} isComplete={true} />
        </div>
        
        <div className="conversation-meta">
          <p>Conversation ID: {conversation.id}</p>
          <p>Timestamp: {new Date(conversation.timestamp).toLocaleString()}</p>
        </div>
      </div>
      
      <button className="back-link" onClick={() => navigate('/')}>New Execution</button>
    </div>
  );
}

export default ConversationView; 