import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import Display from './Display';

function ResponseDisplay({ conversationId, existingSocket = null}) {
  const [responses, setResponses] = useState([]);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!conversationId) return;

    // Use existing socket if provided, otherwise create a new one
    const socket = existingSocket || io();
    
    // Only join the room if we're using a new socket connection
    if (!existingSocket) {
      // Join the conversation room
      socket.emit('join', { conversation_id: conversationId });
    }
    
    // Listen for updates
    const handleUpdate = (data) => {
        console.log(data);
      if (data.conversation_id === conversationId) {
        // Store the full response object including role and side
        setResponses(prev => [...prev, {
          response: data.response,
          response_outie: data.response_outie,
          response_innie: data.response_innie,
          role: data.role,
          side: data.side,
          type: data.type
        }]);
        setIsComplete(data.type === 'done');
      }
    };
    
    socket.on('llm_update', handleUpdate);
    
    // Cleanup
    return () => {
      socket.off('llm_update', handleUpdate);
      
      // Only disconnect if we created a new socket
      if (!existingSocket) {
        socket.disconnect();
      }
    };
  }, [conversationId, existingSocket]);

  // Simplified view for the new UI
    return (
        <Display responses={responses} isComplete={isComplete} />
    );
}

export default ResponseDisplay; 