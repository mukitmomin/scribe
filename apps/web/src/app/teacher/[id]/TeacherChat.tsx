'use client';
import { useChat } from '@ai-sdk/react';
import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import styles from './Teacher.module.css';
import { LoadingDots } from '@scribe/ui';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Trash2, Plus, MessageSquare, FileText, PanelLeft, PanelLeftClose, Settings, ExternalLink, Maximize2, Minimize2 } from 'lucide-react';
import type { ChatSession, Post } from '@scribe/types';

interface TeacherChatProps {
    paperId: string;
    initialSessions: ChatSession[];
    initialSessionId: string | null;
    initialMessages: any[];
    initialPosts: Post[];
    onOpenDraft?: (postId: string) => void;
    onDraftCreated?: (post: Post) => void;
    isPdfCollapsed?: boolean;
    onTogglePdf?: () => void;
}

export function TeacherChat({ paperId, initialSessions, initialSessionId, initialMessages, initialPosts, onOpenDraft, onDraftCreated, isPdfCollapsed, onTogglePdf }: TeacherChatProps) {
    const [input, setInput] = useState('');
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [sessions, setSessions] = useState<ChatSession[]>(initialSessions);
    const [posts, setPosts] = useState<Post[]>(initialPosts || []);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(initialSessionId);
    const activeSessionIdRef = useRef<string | null>(initialSessionId);
    const router = useRouter();

    useEffect(() => {
        activeSessionIdRef.current = currentSessionId;
    }, [currentSessionId]);

    useEffect(() => {
        if (initialPosts) setPosts(initialPosts);
    }, [initialPosts]);

    const messagesEndRef = useRef<HTMLDivElement>(null);

    const { messages, append, isLoading, setMessages } = useChat({
        id: currentSessionId ? `teacher-${currentSessionId}` : `teacher-${paperId}`,
        api: '/api/v1/chat',
        streamProtocol: 'data',
        onError: (error: Error) => console.error("Chat error", error)
    } as any);

    const refreshSessions = useCallback(async () => {
        try {
            const res = await fetch(`/api/v1/chat/sessions/${paperId}`);
            if (res.ok) {
                const data = await res.json();
                setSessions(data.sessions || []);
            }
        } catch (e) {
            console.error("Failed to refresh sessions", e);
        }
    }, [paperId]);

    const handleNewChat = async () => {
        try {
            const res = await fetch('/api/v1/chat/session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ paper_id: paperId })
            });
            if (res.ok) {
                const newSession = await res.json();
                setCurrentSessionId(newSession.id);
                activeSessionIdRef.current = newSession.id;
                setMessages([]);
                await refreshSessions();
                setIsDrawerOpen(false);
            }
        } catch (e) {
            console.error("Failed to create new session", e);
        }
    };

    useEffect(() => {
        const loadSessionMessages = async () => {
            if (!currentSessionId) {
                setMessages([]);
                return;
            }
            try {
                const res = await fetch(`/api/v1/chat/session/${currentSessionId}`);
                if (res.ok) {
                    const data = await res.json();
                    setMessages(data.messages || []);
                }
            } catch (e) {
                console.error("Failed to load session messages", e);
            }
        };
        loadSessionMessages();
    }, [currentSessionId, setMessages]);

    const handleSwitchSession = (sessionId: string) => {
        if (sessionId === currentSessionId) return;
        isSwitchingSessionRef.current = true;
        setCurrentSessionId(sessionId);
        activeSessionIdRef.current = sessionId;
    };

    const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);

    const handleGenerateDraft = async () => {
        if (!currentSessionId || isGeneratingDraft) return;
        setIsGeneratingDraft(true);
        try {
            const res = await fetch('/api/v1/scribe/draft', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ paper_id: paperId, session_id: currentSessionId })
            });
            if (res.ok) {
                const data = await res.json();
                if (onDraftCreated) {
                    onDraftCreated({ ...data, id: data.post_id, title: 'Deep Dive: ...' } as any);
                } else {
                    router.push(`/scribe/${data.post_id}`);
                }
            }
        } catch (e) {
            console.error("Failed to generate draft", e);
            alert("Failed to generate draft.");
        } finally {
            setIsGeneratingDraft(false);
        }
    };

    const handleDeleteSession = async () => {
        if (!currentSessionId) return;
        if (!confirm("Are you sure you want to delete this chat?")) return;
        try {
            await fetch(`/api/v1/chat/session/${currentSessionId}`, { method: 'DELETE' });
            await refreshSessions();
            const remainingSessions = sessions.filter(s => s.id !== currentSessionId);
            if (remainingSessions.length > 0) {
                handleSwitchSession(remainingSessions[0].id);
            } else {
                setCurrentSessionId(null);
                activeSessionIdRef.current = null;
                setMessages([]);
            }
        } catch (e) {
            console.error("Failed to delete session", e);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput('');

        let targetSessionId = activeSessionIdRef.current;
        if (!targetSessionId) {
            try {
                const res = await fetch('/api/v1/chat/session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ paper_id: paperId })
                });
                if (res.ok) {
                    const newSession = await res.json();
                    targetSessionId = newSession.id;
                    activeSessionIdRef.current = newSession.id;
                    setCurrentSessionId(newSession.id);
                    setTimeout(refreshSessions, 2000);
                }
            } catch (e) {
                console.error("Failed to create session", e);
                return;
            }
        }

        // API route extracts only the new message from the full history
        append({ role: 'user', content: userMessage }, { body: { sessionId: targetSessionId, paperId: paperId } });
        setTimeout(refreshSessions, 2000);
    };

    const isSwitchingSessionRef = useRef(false);

    useEffect(() => {
        if (messages.length > 0) {
            const behavior = isSwitchingSessionRef.current ? 'auto' : 'smooth';
            isSwitchingSessionRef.current = false;
            messagesEndRef.current?.scrollIntoView({ behavior, block: 'nearest' });
        }
    }, [messages]);

    return (
        <div className={styles.chatWrapper}>
            <div className={styles.middleArea}>
                <div className={`${styles.actionDrawer} ${isDrawerOpen ? styles.drawerOpen : styles.drawerClosed}`}>
                    <div className={`${styles.sidebarRail} ${isDrawerOpen ? styles.railHidden : ''}`}>
                        <button className={styles.railButton} onClick={() => setIsDrawerOpen(true)} title="Expand Menu">
                            <PanelLeft size={20} />
                        </button>
                        <button className={styles.railButton} onClick={handleNewChat} title="New Chat">
                            <Plus size={20} />
                        </button>
                        <div className={styles.settingsWrapper}>
                            <button className={styles.railButton} onClick={() => setIsSettingsOpen(!isSettingsOpen)} title="Settings">
                                <Settings size={20} />
                            </button>
                            {isSettingsOpen && (
                                <div className={styles.settingsMenu}>
                                    {onTogglePdf && (
                                        <button className={styles.settingsMenuItem} onClick={() => { onTogglePdf(); setIsSettingsOpen(false); }}>
                                            {isPdfCollapsed ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                                            <span>{isPdfCollapsed ? "Show PDF" : "Maximize Chat"}</span>
                                        </button>
                                    )}
                                    <a href={`https://arxiv.org/pdf/${paperId}.pdf`} target="_blank" rel="noopener noreferrer" className={styles.settingsMenuItem}>
                                        <ExternalLink size={16} />
                                        <span>Open PDF</span>
                                    </a>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className={`${styles.drawerContent} ${isDrawerOpen ? styles.contentVisible : ''}`}>
                        <div className={styles.drawerHeader}>
                            <span className={styles.drawerTitle}>Teacher</span>
                            <button className={styles.iconButton} onClick={() => setIsDrawerOpen(false)} title="Collapse Menu">
                                <PanelLeftClose size={18} />
                            </button>
                        </div>
                        <button onClick={handleNewChat} className={styles.newChatButton}>
                            <Plus size={16} /> <span>New Chat</span>
                        </button>
                        <div className={styles.sessionsList}>
                            <div className={styles.sessionsHeader}>Chats</div>
                            {sessions.length === 0 ? (
                                <div className={styles.noSessions}>No conversations yet</div>
                            ) : (
                                sessions.map(session => (
                                    <button key={session.id} className={`${styles.sessionItem} ${session.id === currentSessionId ? styles.sessionActive : ''}`} onClick={() => handleSwitchSession(session.id)}>
                                        <MessageSquare size={14} />
                                        <span className={styles.sessionTitle}>{session.title}</span>
                                    </button>
                                ))
                            )}
                            <div className={styles.sessionsHeader} style={{ marginTop: '1rem', borderTop: '1px solid var(--card-border)' }}>Saved Drafts</div>
                            {posts.length === 0 ? (
                                <div className={styles.noSessions}>No drafts yet</div>
                            ) : (
                                posts.map(post => (
                                    <button key={post.id} className={styles.sessionItem} onClick={() => onOpenDraft ? onOpenDraft(post.id) : router.push(`/scribe/${post.id}`)}>
                                        <FileText size={14} />
                                        <span className={styles.sessionTitle}>{post.title || 'Untitled Draft'}</span>
                                    </button>
                                ))
                            )}
                        </div>
                        <div className={styles.drawerFooter}>
                            {currentSessionId && (
                                <>
                                    <button onClick={handleGenerateDraft} className={styles.generateDraftButton} disabled={isGeneratingDraft}>
                                        <FileText size={16} />
                                        <span>{isGeneratingDraft ? 'Generating...' : 'Generate Draft'}</span>
                                    </button>
                                    <button onClick={handleDeleteSession} className={styles.deleteSessionButton}>
                                        <Trash2 size={16} /> <span>Delete Chat</span>
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                <div className={`${styles.messagesArea} ${isPdfCollapsed ? styles.messagesAreaFull : ''}`}>
                    {messages.length === 0 && (
                        <div className={styles.emptyState}>
                            <p>Ask a question about the paper to get started.</p>
                        </div>
                    )}
                    {messages.map(m => (
                        <div key={m.id} className={`${styles.messageRow} ${m.role === 'user' ? styles.userRow : styles.teacherRow}`}>
                            <div className={`${styles.messageBubble} ${m.role === 'user' ? styles.userBubble : styles.teacherBubble}`}>
                                <div className={styles.roleLabel}>{m.role === 'assistant' ? 'Teacher' : 'You'}</div>
                                <div className={styles.messageContent}>
                                    {m.parts ? (
                                        m.parts.map((part: { type: string; text?: string }, i: number) => part.type === 'text' && (
                                            <ReactMarkdown key={i} remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
                                                {part.text || ''}
                                            </ReactMarkdown>
                                        ))
                                    ) : (
                                        <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
                                            {(m as any).content || ''}
                                        </ReactMarkdown>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className={`${styles.messageRow} ${styles.teacherRow}`}>
                            <div className={`${styles.messageBubble} ${styles.teacherBubble}`}>
                                <div className={styles.roleLabel}>Teacher</div>
                                <LoadingDots />
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            <div className={isPdfCollapsed ? styles.inputAreaFloating : styles.inputArea}>
                <form onSubmit={handleSubmit} className={styles.inputForm}>
                    <input value={input} onChange={(e) => setInput(e.target.value)} className={styles.input} placeholder="Ask about the paper..." disabled={isLoading} />
                    <button type="submit" className={styles.sendButton} disabled={isLoading || !input.trim()}>Send</button>
                </form>
            </div>

            {isGeneratingDraft && (
                <div className={styles.loadingOverlay}>
                    <div className={styles.loadingSpinner} />
                    <div className={styles.loadingText}>Generating your blog post...</div>
                </div>
            )}
        </div>
    );
}
