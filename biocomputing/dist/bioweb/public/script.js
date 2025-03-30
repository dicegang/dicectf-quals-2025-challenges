document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const experimentSelect = document.getElementById('experiment-select');
    const experimentInput = document.getElementById('experiment-input');
    const runButton = document.getElementById('run-button');
    const experimentStatus = document.getElementById('experiment-status');
    const outputContainer = document.getElementById('output-container');
    const experimentOutput = document.getElementById('experiment-output');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    
    // Socket.io connection
    const socket = io();
    
    // Fetch available experiments
    fetchExperiments();
    
    // Event listeners
    runButton.addEventListener('click', runExperiment);
    
    // Functions
    async function fetchExperiments() {
        try {
            const response = await fetch('/api/experiments');
            const experiments = await response.json();
            
            // Clear existing options (except the default one)
            experimentSelect.innerHTML = '<option value="">-- Select an experiment --</option>';
            
            // Add experiments to the select dropdown
            experiments.forEach(experiment => {
                const option = document.createElement('option');
                option.value = experiment.id;
                option.textContent = experiment.name;
                option.title = experiment.description;
                experimentSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching experiments:', error);
            showError('Failed to load experiments. Please refresh the page.');
        }
    }
    
    async function runExperiment() {
        const selectedExperiment = experimentSelect.value;
        const input = experimentInput.value.trim();
        
        if (!selectedExperiment) {
            alert('Please select an experiment to run.');
            return;
        }
        
        // Disable form
        setFormEnabled(false);
        
        // Reset status display
        resetStatus();
        experimentStatus.classList.remove('hidden');
        
        try {
            // Send request to run experiment
            const response = await fetch('/api/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    experiment: selectedExperiment,
                    input: input
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Listen for updates from the server
                listenForUpdates(data.runId);
            } else {
                showError(data.error || 'Failed to start experiment.');
                setFormEnabled(true);
            }
        } catch (error) {
            console.error('Error running experiment:', error);
            showError('Failed to start experiment. Please try again.');
            setFormEnabled(true);
        }
    }
    
    function listenForUpdates(runId) {
        // Set up listeners for this specific run
        socket.on(`experiment-update-${runId}`, handleExperimentUpdate);
        socket.on(`experiment-error-${runId}`, handleExperimentError);
        
        // Set loading stage active initially
        updateStage('loading');
    }
    
    function handleExperimentUpdate(update) {
        console.log('Update received:', update);
        
        // Update the display based on the status
        updateStage(update.status, update.progress);
        
        // If completed, show the output
        if (update.status === 'completed' && update.output) {
            // Clean up the output (remove null bytes and other non-printable characters)
            const cleanOutput = update.output.replace(/\u0000/g, '').trim();
            experimentOutput.textContent = cleanOutput;
            outputContainer.classList.remove('hidden');
            
            // Re-enable the form after completion
            setFormEnabled(true);
            
            // Remove the event listeners for this run
            socket.off(`experiment-update-${runId}`);
            socket.off(`experiment-error-${runId}`);
        }
    }
    
    function handleExperimentError(error) {
        console.error('Experiment error:', error);
        showError(error.error || 'An error occurred during the experiment.');
        setFormEnabled(true);
    }
    
    function updateStage(status, progress) {
        // Remove active class from all stages
        const stages = document.querySelectorAll('.stage');
        stages.forEach(stage => stage.classList.remove('active'));
        
        // Mark completed stages
        switch (status) {
            case 'completed':
                document.querySelector('.stage.completed').classList.add('active');
                document.querySelector('.stage.running').classList.add('completed');
                document.querySelector('.stage.pipetting').classList.add('completed');
                document.querySelector('.stage.loading').classList.add('completed');
                break;
            case 'running':
                document.querySelector('.stage.running').classList.add('active');
                document.querySelector('.stage.pipetting').classList.add('completed');
                document.querySelector('.stage.loading').classList.add('completed');
                
                // Update progress bar
                if (progress !== undefined) {
                    const progressPercent = Math.round(progress * 100);
                    document.querySelector('.progress-bar').style.width = `${progressPercent}%`;
                    document.querySelector('.progress-text').textContent = `${progressPercent}%`;
                }
                break;
            case 'pipetting':
                document.querySelector('.stage.pipetting').classList.add('active');
                document.querySelector('.stage.loading').classList.add('completed');
                break;
            case 'loading':
            default:
                document.querySelector('.stage.loading').classList.add('active');
                break;
        }
    }
    
    function resetStatus() {
        // Reset progress display
        const stages = document.querySelectorAll('.stage');
        stages.forEach(stage => {
            stage.classList.remove('active');
            stage.classList.remove('completed');
        });
        
        document.querySelector('.progress-bar').style.width = '0%';
        document.querySelector('.progress-text').textContent = '0%';
        
        // Hide output and error containers
        outputContainer.classList.add('hidden');
        errorContainer.classList.add('hidden');
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorContainer.classList.remove('hidden');
    }
    
    function setFormEnabled(enabled) {
        experimentSelect.disabled = !enabled;
        experimentInput.disabled = !enabled;
        runButton.disabled = !enabled;
    }
}); 