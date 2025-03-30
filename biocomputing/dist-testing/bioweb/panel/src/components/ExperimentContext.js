import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import io from 'socket.io-client';
import { API_ENDPOINT } from '../App';

// Create context
const ExperimentContext = createContext();

// Create provider component
export const ExperimentProvider = ({ children }) => {
  // State variables
  const [experiments, setExperiments] = useState([]);
  const [selectedExperiment, setSelectedExperiment] = useState('');
  const [input, setInput] = useState('');
  const [status, setStatus] = useState('idle'); // idle, loading, pipetting, running, completed
  const [progress, setProgress] = useState(0);
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [runId, setRunId] = useState(null);
  const [isFormEnabled, setIsFormEnabled] = useState(true);
  const [socket, setSocket] = useState(null);
  const [stageTimes, setStageTimes] = useState({
    loading: null,
    pipetting: null,
    running: null,
    completed: null
  });

  // Initialize socket connection
  useEffect(() => {
    // Connect to the socket server using API_ENDPOINT
    console.log('Connecting to Socket.IO server at:', API_ENDPOINT);
    const newSocket = io(API_ENDPOINT);
    
    newSocket.on('connect', () => {
      console.log('Socket.IO connected successfully!');
    });
    
    newSocket.on('connect_error', (error) => {
      console.error('Socket.IO connection error:', error);
    });

    setSocket(newSocket);

    return () => {
      if (newSocket) {
        console.log('Disconnecting from Socket.IO server');
        newSocket.disconnect();
      }
    };
  }, []);

  // Update stage times when status changes
  useEffect(() => {
    if (status !== 'idle' && !stageTimes[status]) {
      setStageTimes(prevTimes => ({
        ...prevTimes,
        [status]: Date.now()
      }));
    }
  }, [status]);

  // Set up socket listeners when runId changes
  useEffect(() => {
    if (!socket) return;

    console.log(`Setting up listeners for experiment run: ${runId}`);

    const handleUpdate = (update) => {
      console.log('Update received:', update);
      
      // Update the status only if it's different and not just a progress update
      if (update.status && update.status !== status) {
        setStatus(update.status);
      }
      
      // Update progress if available
      if (update.progress !== undefined) {
        setProgress(update.progress);
      }
      
      // If completed, show the output
      if (update.status === 'completed' && update.output) {
        // Clean up the output (remove null bytes and other non-printable characters)
        const cleanOutput = update.output.replace(/\u0000/g, '').trim();
        setOutput(cleanOutput);
        
        // Re-enable the form after completion
        setIsFormEnabled(true);
      }
    };

    const handleError = (error) => {
      console.error('Experiment error:', error);
      setError(error.error || 'An error occurred during the experiment');
      setIsFormEnabled(true);
    };

    socket.on('run_starting', (data) => {
      console.log('Run starting:', data);
      setStatus('loading');
      setProgress(0);
      setRunId(data.run_id);
      // Record the start time for the loading stage
      setStageTimes(prevTimes => ({
        ...prevTimes,
        loading: Date.now()
      }));
    });

    socket.on('experiment_update', (data) => {
      console.log('Run update:', data);

      if (data.status === 'running') {
        // Extract the new status from update if available, otherwise use 'running'
        const newStatus = data.update?.status || 'running';
        
        // Only update stage times if this is an actual stage transition
        // If it's just a progress update for the running stage, don't change the status or times
        if (newStatus !== status) {
          // Record the start time for the new stage
          setStageTimes(prevTimes => ({
            ...prevTimes,
            [newStatus]: Date.now()
          }));
          setStatus(newStatus);
        }
        
        // Always update with the latest data
        handleUpdate(data.update);
      } else if (data.status === 'error') {
        setStatus('error');
        handleError(data.error);
      }
    });
  }, [socket]);

  // Reset the status and output display
  const resetStatus = useCallback(() => {
    setStatus('idle');
    setProgress(0);
    setOutput('');
    setError('');
    setStageTimes({
      loading: null,
      pipetting: null,
      running: null,
      completed: null
    });
  }, []);

  // Fetch available experiments
  const fetchExperiments = useCallback(async () => {
    try {
      console.log('Fetching available experiments...');
      const response = await fetch(`${API_ENDPOINT}/api/experiments`);
      const data = await response.json();
      console.log('Experiments received:', data);
      setExperiments(data);
    } catch (error) {
      console.error('Error fetching experiments:', error);
      setError('Failed to load experiments. Please refresh the page.');
    }
  }, []);

  // Run the selected experiment
  const runExperiment = useCallback(async () => {
    if (!selectedExperiment) {
      alert('Please select an experiment to run.');
      return;
    }

    console.log(`Running experiment: ${selectedExperiment}`);
    
    // Disable form
    setIsFormEnabled(false);

    // Reset status
    resetStatus();
    setStatus('loading');

    // Send request to run experiment
    socket.emit('run_experiment', {
      experiment: selectedExperiment,
      input: input
    });
  }, [selectedExperiment, input, resetStatus]);

  // Provide the context value
  const contextValue = {
    experiments,
    selectedExperiment,
    input,
    status,
    progress,
    output,
    error,
    isFormEnabled,
    stageTimes,
    runId,
    setSelectedExperiment,
    setInput,
    fetchExperiments,
    runExperiment,
    resetStatus
  };

  return (
    <ExperimentContext.Provider value={contextValue}>
      {children}
    </ExperimentContext.Provider>
  );
};

// Custom hook to use the experiment context
export const useExperiment = () => {
  const context = useContext(ExperimentContext);
  if (!context) {
    throw new Error('useExperiment must be used within an ExperimentProvider');
  }
  return context;
}; 