import React, { useState, useEffect, useRef } from 'react';
import { useExperiment } from './ExperimentContext';

const StageIndicator = ({ 
  stage, 
  icon, 
  label, 
  currentStatus, 
  showProgress = false,
  progress = 0 
}) => {
  // Get the stage times from context
  const { stageTimes } = useExperiment();
  
  // State for tracking elapsed time
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef(null);
  const lastStartTimeRef = useRef(null);

  // Determine if this stage is active or completed
  const isActive = currentStatus === stage;
  const isCompleted = isCompletedStage(stage, currentStatus);
  const stageStartTime = stageTimes[stage];

  // Calculate classes
  let stageClasses = "stage " + stage;
  if (isActive) stageClasses += " active";
  if (isCompleted) stageClasses += " completed";

  // Format progress percentage for display
  const progressPercent = Math.round(progress * 100);

  // Format elapsed time as mm:ss
  const formatTime = (timeInSeconds) => {
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  // Store the stage start time reference
  useEffect(() => {
    if (stageStartTime && stageStartTime !== lastStartTimeRef.current) {
      lastStartTimeRef.current = stageStartTime;
    }
  }, [stageStartTime]);

  // Timer logic
  useEffect(() => {
    // Don't start the timer if we don't have a start time for this stage
    if (!stageStartTime) return;
    
    // If the stage is active or completed, start/update the timer
    if ((isActive || isCompleted) && !timerRef.current) {
      const updateTimer = () => {
        // Always calculate from the original start time to avoid drift
        const now = Date.now();
        const elapsed = (now - stageStartTime) / 1000;
        setElapsedTime(elapsed);
      };
      
      // Update once immediately
      updateTimer();
      
      // Only set an interval if the stage is active (not completed)
      if (isActive) {
        timerRef.current = setInterval(updateTimer, 1000);
      }
    }

    // Stop the timer when the stage is no longer active (but keep the elapsed time)
    if (!isActive && timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    // Cleanup on unmount
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isActive, isCompleted, stageStartTime]);

  // Show timer only if we have a start time for this stage
  const showTimer = stageStartTime && (isActive || isCompleted) && stage !== 'running' && stage !== 'completed';

  return (
    <div className={stageClasses}>
      <div className="stage-icon">{icon}</div>
      <div className="stage-label">{label}</div>
      
      {/* Show timer if stage has started */}
      {showTimer && (
        <div className="stage-timer">{formatTime(elapsedTime)}</div>
      )}
      
      {showProgress && (
        <>
          <div className="progress-bar-container">
            <div 
              className="progress-bar" 
              style={{ width: `${progressPercent}%` }}
            ></div>
          </div>
          <div className="progress-text">{progressPercent}%</div>
        </>
      )}
    </div>
  );
};

// Helper function to determine if a stage is completed
const isCompletedStage = (stage, currentStatus) => {
  const stages = ['loading', 'pipetting', 'running', 'completed'];
  const currentIndex = stages.indexOf(currentStatus);
  const stageIndex = stages.indexOf(stage);
  
  // If current status is completed, all stages are completed
  if (currentStatus === 'completed') {
    return true;
  }
  
  // Otherwise, a stage is completed if its index is less than the current status index
  return stageIndex < currentIndex;
};

export default StageIndicator; 