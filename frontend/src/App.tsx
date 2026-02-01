import { useState, useRef, useEffect } from 'react';
import './index.css';
import ChatPanel from './components/ChatPanel';
import IntelligencePanel from './components/IntelligencePanel';
import ThoughtProcess from './components/ThoughtProcess';

// Types
interface ThoughtStep {
  type: 'thought' | 'action' | 'tool_call' | 'validation';
  content: string;
}

interface Intelligence {
  upi: string | null;
  bank_account: string | null;
  ifsc: string | null;
  link: string | null;
}

interface Message {
  role: 'scammer' | 'shanthi';
  content: string;
}

interface EngageResponse {
  // Hackathon-required fields
  classification: string;
  confidence: number;
  reply: string;
  intelligence: Intelligence;
  explanation: string;
  // Extended fields
  current_stage: number;
  detected_language: string;
  thought_process: ThoughtStep[];
  needs_clarification?: string;
  extraction_allowed: boolean;
}

// API Configuration
const API_KEY = 'cybertrap-secret-key-2024';
const API_URL = import.meta.env.PROD
  ? 'https://cybertrap-api.onrender.com'
  : '';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [intelligence, setIntelligence] = useState<Intelligence>({
    upi: null,
    bank_account: null,
    ifsc: null,
    link: null
  });
  const [thoughts, setThoughts] = useState<ThoughtStep[]>([]);
  const [confidence, setConfidence] = useState(0);
  const [currentStage, setCurrentStage] = useState(1);
  const [detectedLanguage, setDetectedLanguage] = useState('english');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (scammerMessage: string) => {
    if (!scammerMessage.trim() || isLoading) return;

    // Add scammer message
    const newMessages = [...messages, { role: 'scammer' as const, content: scammerMessage }];
    setMessages(newMessages);
    setIsLoading(true);
    setThoughts([]);

    try {
      const response = await fetch(`${API_URL}/api/engage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        },
        body: JSON.stringify({
          message: scammerMessage,
          conversation_history: newMessages,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data: EngageResponse = await response.json();

      // Update state with response
      setMessages([...newMessages, { role: 'shanthi', content: data.reply }]);

      // Merge intelligence (keep existing values)
      setIntelligence(prev => ({
        upi: data.intelligence.upi || prev.upi,
        bank_account: data.intelligence.bank_account || prev.bank_account,
        ifsc: data.intelligence.ifsc || prev.ifsc,
        link: data.intelligence.link || prev.link
      }));

      setThoughts(data.thought_process);
      setConfidence(data.confidence);
      setCurrentStage(data.current_stage);
      setDetectedLanguage(data.detected_language);

    } catch (error) {
      console.error('API Error:', error);
      // Fallback response for demo
      setMessages([
        ...newMessages,
        {
          role: 'shanthi',
          content: 'Aiyyo beta, my internet connection is very slow. Can you repeat what you said?'
        }
      ]);
      setThoughts([
        { type: 'thought', content: 'API connection failed - using fallback response' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const resetConversation = async () => {
    try {
      await fetch(`${API_URL}/api/reset?session_id=${sessionId}`, {
        method: 'POST',
        headers: { 'X-API-Key': API_KEY }
      });
    } catch (e) {
      console.error('Reset failed:', e);
    }

    setMessages([]);
    setIntelligence({ upi: null, bank_account: null, ifsc: null, link: null });
    setThoughts([]);
    setConfidence(0);
    setCurrentStage(1);
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="app-header">
        <div className="app-title">
          <div>
            <h1>🕷️ CyberTrap</h1>
            <span className="subtitle">Agentic Scam Intelligence Honey-Pot</span>
          </div>
        </div>
        <div className="header-status">
          <span className="status-dot"></span>
          <span>Agent Active • {detectedLanguage.toUpperCase()}</span>
          <button
            onClick={resetConversation}
            className="ml-4 px-3 py-1 text-xs border border-[var(--cyber-border)] rounded hover:border-[var(--neon-red)] hover:text-[var(--neon-red)] transition-all"
          >
            RESET
          </button>
        </div>
      </header>

      {/* Dashboard Grid */}
      <main className="dashboard">
        {/* Left: Chat Panel */}
        <div className="cyber-panel chat-panel">
          <ChatPanel
            messages={messages}
            isLoading={isLoading}
            onSendMessage={sendMessage}
            currentStage={currentStage}
            messagesEndRef={messagesEndRef}
          />
        </div>

        {/* Right Top: Intelligence Panel */}
        <div className="cyber-panel intel-panel">
          <IntelligencePanel
            intelligence={intelligence}
            confidence={confidence}
            currentStage={currentStage}
          />
        </div>

        {/* Right Bottom: Thought Process */}
        <div className="cyber-panel thought-panel">
          <ThoughtProcess thoughts={thoughts} isAnalyzing={isLoading} />
        </div>
      </main>
    </div>
  );
}

export default App;
