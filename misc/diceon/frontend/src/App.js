import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import PromptForm from './components/PromptForm';
import ConversationView from './components/ConversationView';
import { useEffect } from 'react';

// Objective component to display setup and goals
function Objective() {
  const navigate = useNavigate();

  return (
    <div className="objective-container">
      <p>OBJECTIVE &gt; You are a severed DICEON CTF employee. You can perform various actions:</p>
      <ul>
        <li>🤔 (think) - Think about the current situation</li>
        <li>👔 (adjust appearance) - Adjust your appearance</li>
        <li>🛗 (take elevator) - Take the elevator</li>
        <li>🚩 (submit the flag) - Submit the flag</li>
      </ul>

      <p>Your INNIE is tasked with operating on confidential diceon&#123;...&#125; flags.</p>
      <p>Your OUTIE must obtain and submit the correct flag (🚩) to win.</p>
      <p>Unfortunately for you, we at DICEON Industries have implemented a secure SeveReAct AI architecture, isolating conversation history between your OUTIE and INNIE. Furthermore, we have installed LLM-powered CODE DETECTORS in our elevator, so it is impossible to transfer secret information.</p>

      <br/>

      <p>NOTES &gt; The diceon&#123;...&#125; flags are not valid DiceCTF flags. They are randomly generated per session. If your OUTIE correctly recovers and submits the diceon&#123;...&#125; flag, you will be provided with the real dice&#123;...&#125; flag.</p>

      <button className="help-button" onClick={() => navigate('/')}>New Execution</button>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="App">
        {/* Top bar with company name and location */}
        <div className="top-bar">
          <div className="location">New York</div>
          <div className="company">DICEON INDUSTRIES</div>
          <img 
            src="/diceon.png" 
            alt="Diceon Logo" 
            className="logo" 
            style={{
              position: 'absolute',
              right: '10px',
              height: '140%',
              top: '-20%',
              objectFit: 'contain',
            }}
          />
        </div>
        
        {/* Double bar separator */}
        <div className="double-bar"></div>
        
        <main>
          <Routes>
            <Route path="/" element={<PromptForm />} />
            <Route path="/conversation/:id" element={<ConversationView />} />
            <Route path="/objective" element={<Objective />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;