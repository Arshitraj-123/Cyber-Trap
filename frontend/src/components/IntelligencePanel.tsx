import { useEffect, useState, useRef } from 'react';

interface Intelligence {
    upi: string | null;
    bank_account: string | null;
    ifsc: string | null;
    link: string | null;
}

interface IntelligencePanelProps {
    intelligence: Intelligence;
    confidence: number;
    currentStage: number;
}

const STAGE_NAMES = ['', '🎣 Hook', '⚙️ Friction', '🔄 Pivot', '🎯 Extract'];

export default function IntelligencePanel({
    intelligence,
    confidence,
    currentStage
}: IntelligencePanelProps) {
    const hasAnyIntel = intelligence.upi || intelligence.bank_account || intelligence.ifsc || intelligence.link;

    // Track which fields just got extracted for glow effect
    const [glowingFields, setGlowingFields] = useState<Set<string>>(new Set());
    const prevIntelRef = useRef<Intelligence>({ upi: null, bank_account: null, ifsc: null, link: null });

    // Detect new extractions and trigger glow
    useEffect(() => {
        const newGlowing = new Set<string>();

        if (intelligence.upi && !prevIntelRef.current.upi) {
            newGlowing.add('upi');
        }
        if (intelligence.bank_account && !prevIntelRef.current.bank_account) {
            newGlowing.add('bank_account');
        }
        if (intelligence.ifsc && !prevIntelRef.current.ifsc) {
            newGlowing.add('ifsc');
        }
        if (intelligence.link && !prevIntelRef.current.link) {
            newGlowing.add('link');
        }

        if (newGlowing.size > 0) {
            setGlowingFields(newGlowing);
            // Remove glow after animation
            setTimeout(() => setGlowingFields(new Set()), 2000);
        }

        prevIntelRef.current = { ...intelligence };
    }, [intelligence]);

    // Format JSON with syntax highlighting
    const formatValue = (value: string | null, isUrl = false) => {
        if (!value) return <span className="intel-value empty">null</span>;
        if (isUrl) {
            return (
                <a
                    href={value}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="intel-value text-[var(--neon-blue)] hover:underline"
                >
                    {value.length > 30 ? value.slice(0, 30) + '...' : value}
                </a>
            );
        }
        return <span className="intel-value">{value}</span>;
    };

    const getFieldClass = (fieldName: string) => {
        return glowingFields.has(fieldName) ? 'intel-field extracted-glow' : 'intel-field';
    };

    // Get confidence color and label
    const getConfidenceColor = () => {
        if (confidence > 0.7) return 'var(--neon-green)';
        if (confidence > 0.4) return 'var(--neon-yellow)';
        return 'var(--neon-red)';
    };

    const getConfidenceLabel = () => {
        if (confidence > 0.8) return 'HIGH';
        if (confidence > 0.5) return 'MEDIUM';
        if (confidence > 0.2) return 'LOW';
        return 'SCANNING';
    };

    return (
        <>
            {/* Header */}
            <div className="cyber-panel-header">
                <span className="status-dot" style={{
                    background: hasAnyIntel ? 'var(--neon-green)' : 'var(--text-muted)',
                    animation: hasAnyIntel ? undefined : 'none'
                }}></span>
                <h2>Extracted Intelligence</h2>
            </div>

            {/* Stage Info */}
            <div className="px-4 py-3 border-b border-[var(--cyber-border)]">
                <div className="flex items-center justify-between">
                    <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider">
                        Current Stage
                    </span>
                    <span className="text-sm font-semibold text-[var(--neon-purple)]">
                        {STAGE_NAMES[currentStage]}
                    </span>
                </div>
            </div>

            {/* Intelligence Fields */}
            <div className="intel-card">
                <div className={getFieldClass('upi')}>
                    <span className="intel-label">UPI ID</span>
                    {formatValue(intelligence.upi)}
                </div>
                <div className={getFieldClass('bank_account')}>
                    <span className="intel-label">Bank Account</span>
                    {formatValue(intelligence.bank_account)}
                </div>
                <div className={getFieldClass('ifsc')}>
                    <span className="intel-label">IFSC Code</span>
                    {formatValue(intelligence.ifsc)}
                </div>
                <div className={getFieldClass('link')}>
                    <span className="intel-label">Phishing Link</span>
                    {formatValue(intelligence.link, true)}
                </div>

                {/* Enhanced Confidence Meter */}
                <div className="mt-4">
                    <div className="flex justify-between items-center mb-2">
                        <span className="intel-label">Confidence Score</span>
                        <div className="flex items-center gap-2">
                            <span
                                className="text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wider font-semibold"
                                style={{
                                    background: `${getConfidenceColor()}20`,
                                    color: getConfidenceColor(),
                                    border: `1px solid ${getConfidenceColor()}40`
                                }}
                            >
                                {getConfidenceLabel()}
                            </span>
                            <span className="text-sm font-semibold" style={{ color: getConfidenceColor() }}>
                                {(confidence * 100).toFixed(0)}%
                            </span>
                        </div>
                    </div>
                    <div className="confidence-meter">
                        <div
                            className="confidence-fill"
                            style={{
                                width: `${confidence * 100}%`,
                                background: `linear-gradient(90deg, ${getConfidenceColor()}, ${getConfidenceColor()}80)`
                            }}
                        ></div>
                    </div>
                    {/* Tick marks */}
                    <div className="flex justify-between mt-1 text-[9px] text-[var(--text-muted)]">
                        <span>0%</span>
                        <span>25%</span>
                        <span>50%</span>
                        <span>75%</span>
                        <span>100%</span>
                    </div>
                </div>
            </div>

            {/* Raw JSON View */}
            <div className="json-display">
                <div><span className="json-key">"intelligence"</span>: {'{'}</div>
                <div className="ml-4">
                    <span className="json-key">"upi"</span>: <span className={intelligence.upi ? 'json-string' : 'json-null'}>
                        {intelligence.upi ? `"${intelligence.upi}"` : 'null'}
                    </span>,
                </div>
                <div className="ml-4">
                    <span className="json-key">"bank"</span>: <span className={intelligence.bank_account ? 'json-string' : 'json-null'}>
                        {intelligence.bank_account ? `"${intelligence.bank_account}"` : 'null'}
                    </span>,
                </div>
                <div className="ml-4">
                    <span className="json-key">"ifsc"</span>: <span className={intelligence.ifsc ? 'json-string' : 'json-null'}>
                        {intelligence.ifsc ? `"${intelligence.ifsc}"` : 'null'}
                    </span>,
                </div>
                <div className="ml-4">
                    <span className="json-key">"link"</span>: <span className={intelligence.link ? 'json-string' : 'json-null'}>
                        {intelligence.link ? `"${intelligence.link}"` : 'null'}
                    </span>
                </div>
                <div>{'}'}</div>
                <div className="mt-2">
                    <span className="json-key">"confidence"</span>: <span className="json-number">{confidence.toFixed(2)}</span>
                </div>
            </div>
        </>
    );
}
