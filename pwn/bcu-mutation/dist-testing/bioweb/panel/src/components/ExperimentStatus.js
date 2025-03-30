import React from 'react';
import { useExperiment } from './ExperimentContext';
import StageIndicator from './StageIndicator';

const ExperimentStatus = () => {
  const { status, output, error, progress, runId } = useExperiment();

  // Only show the status section if we're not in the idle state
  if (status === 'idle') {
    return null;
  }

  return (
    <div>
      <h2>Статус эксперимента</h2>
      
      <div className="progress-container">
        <div className="progress-stages">
          <StageIndicator 
            stage="loading" 
            icon="🧬"
            label="Booting CPU" 
            currentStatus={status}
          />
          <div className="stage-connector"></div>
          
          <StageIndicator 
            stage="pipetting" 
            icon="🧪"
            label="Pipetting" 
            currentStatus={status}
          />
          <div className="stage-connector"></div>
          
          <StageIndicator 
            stage="running" 
            icon="🔬" 
            label="Running" 
            currentStatus={status}
            showProgress={true}
            progress={progress}
          />
          <div className="stage-connector"></div>
          
          <StageIndicator 
            stage="completed" 
            icon="✅" 
            label="Completed" 
            currentStatus={status}
          />
        </div>
      </div>
      
      {output && (
        <div className="output-container">
          <h3>Результат эксперимента:</h3>
          <pre>{output}</pre>
        </div>
      )}

      {status === 'completed' && (
        <div className="output-container">
          <a href={`/results/${runId}`}>{`/results/${runId}`}</a>
        </div>
      )}
      
      {error && (
        <div className="error-container">
          <h3>Ошибка:</h3>
          <pre>{error}</pre>
        </div>
      )}
    </div>
  );
};

export default ExperimentStatus; 