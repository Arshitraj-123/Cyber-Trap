import { useState } from 'react';

interface Message {
    role: 'scammer' | 'shanthi';
    content: string;
}

interface ChatPanelProps {
    messages: Message[];
    isLoading: boolean;
    onSendMessage: (message: string) => void;
    currentStage: number;
    messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

const STAGE_NAMES = ['', 'Hook', 'Friction', 'Pivot', 'Extract'];

export default function ChatPanel({
    messages,
    isLoading,
    onSendMessage,
    currentStage,
    messagesEndRef
}: ChatPanelProps) {
    const [input, setInput] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim() && !isLoading) {
            onSendMessage(input);
            setInput('');
        }
    };

    return (
        <>
            {/* Header */}
            <div className="cyber-panel-header">
                <span className="status-dot"></span>
                <h2>Scammer Chat</h2>
                <div className="ml-auto stage-indicator">
                    {[1, 2, 3, 4].map(stage => (
                        <div
                            key={stage}
                            className={`stage-dot ${stage === currentStage ? 'active' : ''} ${stage < currentStage ? 'complete' : ''}`}
                            title={STAGE_NAMES[stage]}
                        >
                            {stage}
                        </div>
                    ))}
                </div>
            </div>

            {/* Messages */}
            <div className="chat-container">
                {messages.length === 0 && (
                    <div className="text-center text-[var(--text-muted)] py-12">
                        <div className="text-4xl mb-4">🎭</div>
                        <p className="text-sm">Paste a scammer message to start the trap</p>
                        <p className="text-xs mt-2 opacity-50">Mrs. Shanthi is ready and waiting...</p>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={`message ${msg.role === 'scammer' ? 'message-scammer' : 'message-agent'}`}
                    >
                        <div className="message-label">
                            {msg.role === 'scammer' ? '⚠️ Scammer' : '🎭 Mrs. Shanthi'}
                        </div>
                        <div>{msg.content}</div>
                    </div>
                ))}

                {isLoading && (
                    <div className="message message-agent">
                        <div className="message-label">🎭 Mrs. Shanthi</div>
                        <div className="typing-indicator">
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="chat-input-area">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmit(e);
                        }
                    }}
                    placeholder="Paste scammer message here..."
                    className="chat-input"
                    rows={2}
                    disabled={isLoading}
                />
                <button
                    type="submit"
                    className="send-btn"
                    disabled={isLoading || !input.trim()}
                >
                    {isLoading ? '...' : 'Send'}
                </button>
            </form>
        </>
    );
}
