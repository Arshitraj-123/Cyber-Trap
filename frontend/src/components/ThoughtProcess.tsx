interface ThoughtStep {
    type: 'thought' | 'action' | 'tool_call' | 'validation';
    content: string;
}

interface ThoughtProcessProps {
    thoughts: ThoughtStep[];
    isAnalyzing?: boolean;
}

const TYPE_ICONS: Record<string, string> = {
    thought: '💭',
    action: '⚡',
    tool_call: '🔧',
    validation: '✓'
};

const TYPE_LABELS: Record<string, string> = {
    thought: 'Reasoning',
    action: 'Action',
    tool_call: 'Stealth Tool',
    validation: 'Validation'
};

export default function ThoughtProcess({ thoughts, isAnalyzing = false }: ThoughtProcessProps) {
    return (
        <>
            {/* Header */}
            <div className="cyber-panel-header">
                <span
                    className={`status-dot ${isAnalyzing ? 'analyzing' : ''}`}
                    style={{
                        background: isAnalyzing ? 'var(--neon-purple)' :
                            thoughts.length > 0 ? 'var(--neon-purple)' : 'var(--text-muted)',
                    }}
                ></span>
                <h2>Agent Thought Process</h2>
                <span className="ml-auto text-xs text-[var(--text-muted)]">
                    {isAnalyzing ? (
                        <span className="analyzing-text">ANALYZING...</span>
                    ) : (
                        `${thoughts.length} steps`
                    )}
                </span>
            </div>

            {/* Thoughts */}
            <div className="thought-container">
                {/* Analyzing Animation */}
                {isAnalyzing && (
                    <div className="scanning-animation">
                        <div className="scanner-line"></div>
                        <div className="scanning-content">
                            <div className="scanning-icon">🔍</div>
                            <div className="scanning-text-container">
                                <div className="text-sm font-semibold text-[var(--neon-purple)]">
                                    Analyzing Message...
                                </div>
                                <div className="scanning-dots">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                        <div className="scanning-tasks">
                            <div className="scanning-task active">
                                <span className="task-dot"></span>
                                Detecting language pattern
                            </div>
                            <div className="scanning-task">
                                <span className="task-dot"></span>
                                Identifying scam vectors
                            </div>
                            <div className="scanning-task">
                                <span className="task-dot"></span>
                                Extracting intelligence
                            </div>
                            <div className="scanning-task">
                                <span className="task-dot"></span>
                                Generating response
                            </div>
                        </div>
                    </div>
                )}

                {/* Empty State */}
                {!isAnalyzing && thoughts.length === 0 && (
                    <div className="text-center text-[var(--text-muted)] py-6 text-sm">
                        <span className="opacity-50">Waiting for agent activity...</span>
                    </div>
                )}

                {/* Thought Steps */}
                {!isAnalyzing && thoughts.map((step, i) => (
                    <div key={i} className="thought-step">
                        <div className={`thought-icon ${step.type}`}>
                            {TYPE_ICONS[step.type] || '?'}
                        </div>
                        <div>
                            <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">
                                {TYPE_LABELS[step.type] || step.type}
                            </div>
                            <div className="thought-content">
                                {step.content}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </>
    );
}
