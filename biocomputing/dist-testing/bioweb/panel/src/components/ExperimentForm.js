import React, { useEffect } from 'react';
import { useExperiment } from './ExperimentContext';

const ExperimentForm = () => {
  const {
    experiments,
    selectedExperiment,
    input,
    isFormEnabled,
    setSelectedExperiment,
    setInput,
    fetchExperiments,
    runExperiment
  } = useExperiment();

  // Fetch experiments when component mounts
  useEffect(() => {
    fetchExperiments();
  }, []); // Empty dependency array ensures it only runs once on mount

  return (
    <div className="experiment-form">
      <div className="form-group">
        <label>Эксперимент:</label>
        <div className="experiment-radio-group">
          {experiments.map(experiment => (
            <div 
              key={experiment.id} 
              className={`experiment-option ${selectedExperiment === experiment.id ? 'selected' : ''}`}
              onClick={() => isFormEnabled && setSelectedExperiment(experiment.id)}
              title={experiment.description}
            >
              <input
                type="radio"
                id={`experiment-${experiment.id}`}
                name="experiment"
                value={experiment.id}
                checked={selectedExperiment === experiment.id}
                onChange={() => {}} // Handled by onClick on parent div
                disabled={!isFormEnabled}
              />
              <div className="experiment-details">
                <div className="experiment-name">{experiment.name}</div>
                <div className="experiment-meta">
                  <div className="experiment-model">
                    <span className="meta-label">модель:</span> {experiment.model}
                  </div>
                  <div className="experiment-duration">
                    <span className="meta-label">время:</span> {experiment.expected_duration}с
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="form-group">
        <label htmlFor="experiment-input">Данные (необязательно):</label>
        <textarea
          id="experiment-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Введите данные для эксперимента"
          disabled={!isFormEnabled}
        />
      </div>
      
      <button
        onClick={runExperiment}
        disabled={!isFormEnabled || !selectedExperiment}
      >
        Запустить эксперимент
      </button>
    </div>
  );
};

export default ExperimentForm; 