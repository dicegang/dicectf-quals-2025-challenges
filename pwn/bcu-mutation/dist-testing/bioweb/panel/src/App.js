import React from 'react';
import './App.css';
import ExperimentForm from './components/ExperimentForm';
import ExperimentStatus from './components/ExperimentStatus';
import { ExperimentProvider } from './components/ExperimentContext';
import { BrowserRouter as Router, Route, Routes, useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';

const ExperimentResult = () => {
  const { runId } = useParams();

  const [result, setResult] = useState(null);

  useEffect(() => {
    fetch(`/api/results/${runId}`)
      .then(res => res.json())
      .then(setResult);
  }, [runId]);

  if (!result) {
    return <div>Loading...</div>;
  }

  // Style for console output
  const consoleStyle = {
    backgroundColor: '#1e1c1c',
    color: '#bf3030',
    fontFamily: '"Courier New", monospace',
    padding: '20px',
    borderRadius: '0',
    whiteSpace: 'pre-wrap',
    overflowX: 'auto',
    maxWidth: '100%',
    margin: '20px 0',
    border: '2px solid #5e4c4c',
    boxShadow: '0 0 10px rgba(0, 0, 0, 0.5) inset'
  };

  // Format the result data for console display
  const formatConsoleOutput = () => {
    return `<span style="color: #aa8c7c;">ID:</span> ${result.id}
<span style="color: #aa8c7c;">Created At:</span> ${result.created_at}
<span style="color: #aa8c7c;">Experiment Name:</span> ${result.experiment_name}
<span style="color: #aa8c7c;">Input Data:</span> <span style="color: #bf3030; font-weight: bold;">REDACTED</span>
<span style="color: #aa8c7c;">Output Data:</span> ${result.output_data}`;
  };

  return (
    <div>
      <a href={`/`} className="back-link">← Назад</a>
      <div 
        style={consoleStyle}
        dangerouslySetInnerHTML={{ __html: formatConsoleOutput() }}
      />
    </div>
  );
}

function App() {
  return (
    <div className="container">
      <h1>BCU-8 Control Interface</h1>
      
      <Router>
        <Routes>
          <Route path="/" element={<ExperimentProvider>
            <ExperimentForm />
            <ExperimentStatus />
          </ExperimentProvider>} />
          <Route path="/results/:runId" element={<ExperimentResult />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App; 