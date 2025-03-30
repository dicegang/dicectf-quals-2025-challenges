const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));

// Get list of available experiments
app.get('/api/experiments', (req, res) => {
  // Check if experiments directory exists, create if not
  const experimentsDir = path.join(__dirname, '..', 'biosim', 'experiments');
//   if (!fs.existsSync(experimentsDir)) {
//     fs.mkdirSync(experimentsDir, { recursive: true });
    
//     // Create a sample experiment file if none exist
//     const sampleExperiment = {
//       "name": "sample_experiment",
//       "description": "A sample experiment"
//     };
    
//     fs.writeFileSync(
//       path.join(experimentsDir, 'sample.json'),
//       JSON.stringify(sampleExperiment, null, 2)
//     );
//   }

  // Read experiment files
  const files = fs.readdirSync(experimentsDir)
    .filter(file => file.endsWith('.json'))
    .map(file => {
      const filePath = path.join(experimentsDir, file);
      try {
        const content = fs.readFileSync(filePath, 'utf8');
        const experiment = JSON.parse(content);
        return {
          id: file.replace('.json', ''),
          name: experiment.name || file.replace('.json', ''),
          description: experiment.description || ''
        };
      } catch (error) {
        return {
          id: file.replace('.json', ''),
          name: file.replace('.json', ''),
          description: 'Error reading experiment details'
        };
      }
    });

  res.json(files);
});

// Run experiment
app.post('/api/run', (req, res) => {
  const { experiment, input } = req.body;
  
  if (!experiment) {
    return res.status(400).json({ error: 'Experiment ID is required' });
  }
  
  // Generate a unique ID for this run
  const runId = Date.now().toString();
  
  // Send immediate response
  res.json({ runId });
  
  // Use socket.io to send progress updates to the client
  io.on('connection', (socket) => {
    console.log('Client connected');
    
    // Handle disconnection
    socket.on('disconnect', () => {
      console.log('Client disconnected');
    });
  });
  
  // Encode input as base64 if provided
  const inputB64 = input ? Buffer.from(input).toString('base64') : '';
  
  // Path to the biosim directory (which is next to bioweb)
  const biosimDir = path.join(__dirname, '..', 'biosim');
  
  // Construct the command
  const cmd = 'python3';
  const args = [
    path.join(biosimDir, 'run.py'),
    '--experiment',
    `biosim/experiments/${experiment}.json`,
    '--input_b64',
    inputB64
  ];
  
  console.log(`Running command: ${cmd} ${args.join(' ')}`);
  
  // Spawn the Python process
  const pythonProcess = spawn(cmd, args, {
    cwd: path.join(__dirname, '..') // Run from the project root
  });
  
  // Listen for data from the Python process
  pythonProcess.stdout.on('data', (data) => {
    const lines = data.toString().trim().split('\n');
    
    lines.forEach(line => {
      if (line.trim()) {
        try {
          const update = JSON.parse(line);
          // Broadcast the update to all connected clients
          io.emit(`experiment-update-${runId}`, update);
          console.log('Update:', update);
        } catch (error) {
          console.error('Error parsing JSON:', error, line);
        }
      }
    });
  });
  
  // Handle errors
  pythonProcess.stderr.on('data', (data) => {
    console.error(`stderr: ${data}`);
    io.emit(`experiment-error-${runId}`, { error: data.toString() });
  });
  
  // Handle process completion
  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    if (code !== 0) {
      io.emit(`experiment-error-${runId}`, { error: `Process exited with code ${code}` });
    }
  });
});

// Catch-all route to serve the main HTML file
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start the server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 