"use client";

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Filter, RefreshCw, Terminal, Cpu, Eye, Bot, Layers, Bookmark, Loader2 } from 'lucide-react';
import styles from './Research.module.css';
import type { Paper } from '@scribe/types';

export default function ResearchPage() {
    const [standardResults, setStandardResults] = useState<Paper[]>([]);
    const [agenticResults, setAgenticResults] = useState<Paper[]>([]);
    const [bookmarks, setBookmarks] = useState<Paper[]>([]);
    const [loading, setLoading] = useState(false);
    const [discovering, setDiscovering] = useState(false);
    const [query, setQuery] = useState('');
    const [searchMode, setSearchMode] = useState<'standard' | 'agentic'>('standard');
    const [activeTopic, setActiveTopic] = useState<string | null>(null);
    const [sortBy, setSortBy] = useState('date');
    const [showBookmarks, setShowBookmarks] = useState(true);
    const [hasSearchedStandard, setHasSearchedStandard] = useState(false);

    const topics = [
        { id: 'LLMs', label: 'LLMs', icon: Terminal },
        { id: 'Agents', label: 'Agents', icon: Bot },
        { id: 'Vision', label: 'Vision', icon: Eye },
        { id: 'Robotics', label: 'Robotics', icon: Cpu },
        { id: 'Reasoning', label: 'Reasoning', icon: Layers },
    ];

    const fetchBookmarks = async () => {
        try {
            const res = await fetch('/api/v1/papers/bookmarks');
            if (res.ok) {
                const data = await res.json();
                setBookmarks(data);
            }
        } catch (e) {
            console.error("Failed to fetch bookmarks");
        }
    };

    const runAgenticSearch = async () => {
        setDiscovering(true);
        try {
            const params = new URLSearchParams();
            if (query) params.append('q', query);

            const res = await fetch(`/api/v1/papers/discover?${params.toString()}`);
            if (res.ok) {
                const data = await res.json();
                setAgenticResults(data);
            }
        } catch (e) {
            console.error("Discovery failed", e);
        } finally {
            setDiscovering(false);
        }
    };

    const runStandardSearch = async (overrideTopic?: string) => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (query) params.append('q', query);
            if (overrideTopic || activeTopic) params.append('topic', overrideTopic || activeTopic || '');
            if (sortBy) params.append('sort', sortBy);

            const res = await fetch(`/api/v1/papers/trending?${params.toString()}`);
            if (res.ok) {
                const data = await res.json();
                setStandardResults(data);
                if (query || overrideTopic || activeTopic) {
                    setHasSearchedStandard(true);
                } else {
                    setHasSearchedStandard(false);
                }
            }
        } catch (error) {
            console.error("Error fetching papers:", error);
        } finally {
            setLoading(false);
        }
    };

    const executeSearch = () => {
        if (searchMode === 'agentic') {
            runAgenticSearch();
        } else {
            runStandardSearch();
        }
    };

    useEffect(() => {
        fetchBookmarks();
        runStandardSearch();
    }, []);

    const handleTopicClick = (topicId: string) => {
        if (searchMode === 'agentic') {
            setSearchMode('standard');
            if (activeTopic === topicId) {
                setActiveTopic(null);
                setQuery('');
                runStandardSearch('');
            } else {
                setActiveTopic(topicId);
                setQuery('');
                runStandardSearch(topicId);
            }
        } else {
            if (activeTopic === topicId) {
                setActiveTopic(null);
                runStandardSearch('');
            } else {
                setActiveTopic(topicId);
                setQuery('');
                runStandardSearch(topicId);
            }
        }
    };

    const toggleBookmark = async (paper: Paper) => {
        const updateList = (list: Paper[]) => list.map(p => p.id === paper.id ? { ...p, is_bookmarked: !p.is_bookmarked } : p);

        setStandardResults(prev => updateList(prev));
        setAgenticResults(prev => updateList(prev));

        const newStatus = !paper.is_bookmarked;
        if (newStatus) {
            setBookmarks(prev => [{ ...paper, is_bookmarked: true }, ...prev]);
        } else {
            setBookmarks(prev => prev.filter(p => p.id !== paper.id));
        }

        try {
            await fetch(`/api/v1/papers/${paper.id}/bookmark`, { method: 'PUT' });
        } catch (e) {
            console.error("Failed to toggle bookmark");
        }
    };

    const displayedPapers = searchMode === 'agentic' ? agenticResults : standardResults;
    const isModeLoading = searchMode === 'agentic' ? discovering : loading;
    const [navigatingTo, setNavigatingTo] = useState<string | null>(null);

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1 className={styles.title}>Research Lab</h1>
                <p style={{ color: 'var(--secondary)', marginTop: '0.5rem' }}>
                    Discover and analyze the latest AI research papers.
                </p>
            </div>

            {bookmarks.length > 0 && (
                <div style={{ marginBottom: '3rem', borderBottom: '1px solid var(--card-border)', paddingBottom: '2rem' }}>
                    <div
                        onClick={() => setShowBookmarks(!showBookmarks)}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', marginBottom: '1rem' }}
                    >
                        <Bookmark size={20} fill="#f59e0b" color="#f59e0b" />
                        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, margin: 0 }}>Saved Papers ({bookmarks.length})</h2>
                        <span style={{ fontSize: '0.8rem', color: 'var(--secondary)' }}>{showBookmarks ? 'Hide' : 'Show'}</span>
                    </div>

                    {showBookmarks && (
                        <div className={styles.grid}>
                            {bookmarks.map((paper) => (
                                <PaperCard key={paper.id} paper={paper} onBookmark={() => toggleBookmark(paper)} navigatingTo={navigatingTo} onNavigate={setNavigatingTo} />
                            ))}
                        </div>
                    )}
                </div>
            )}

            <div className={styles.controls} style={{ marginBottom: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <div style={{ position: 'relative', flex: 1, display: 'flex', gap: '0.5rem' }}>
                        <div style={{
                            display: 'flex',
                            background: 'var(--card-bg)',
                            border: '1px solid var(--card-border)',
                            borderRadius: '8px',
                            padding: '4px',
                            gap: '4px'
                        }}>
                            <button
                                onClick={() => setSearchMode('standard')}
                                title="Standard Search"
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    padding: '0.4rem',
                                    borderRadius: '6px',
                                    border: 'none',
                                    background: searchMode === 'standard' ? 'rgba(var(--primary-rgb), 0.1)' : 'transparent',
                                    color: searchMode === 'standard' ? 'var(--primary)' : 'var(--secondary)',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s'
                                }}
                            >
                                <Search size={18} />
                            </button>
                            <button
                                onClick={() => setSearchMode('agentic')}
                                title="Agentic Search"
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    padding: '0.4rem',
                                    borderRadius: '6px',
                                    border: 'none',
                                    background: searchMode === 'agentic' ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2))' : 'transparent',
                                    color: searchMode === 'agentic' ? '#a855f7' : 'var(--secondary)',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s'
                                }}
                            >
                                <Bot size={18} />
                            </button>
                        </div>

                        <div style={{ position: 'relative', flex: 1 }}>
                            <input
                                type="text"
                                placeholder={searchMode === 'agentic' ? "Ask the Research Agent..." : "Search papers, ID, or URL..."}
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter') executeSearch(); }}
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    padding: '0.8rem 1rem',
                                    background: 'var(--card-bg)',
                                    border: '1px solid var(--card-border)',
                                    borderRadius: '8px',
                                    color: 'var(--foreground)',
                                    fontSize: '1rem',
                                    outline: 'none'
                                }}
                            />
                        </div>

                        <button
                            onClick={executeSearch}
                            disabled={isModeLoading}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                padding: '0 1.5rem',
                                borderRadius: '8px',
                                background: searchMode === 'agentic' ? 'linear-gradient(135deg, #6366f1, #a855f7)' : 'var(--primary)',
                                color: 'white',
                                border: 'none',
                                fontWeight: 600,
                                cursor: 'pointer',
                                opacity: isModeLoading ? 0.7 : 1,
                                minWidth: '100px',
                                justifyContent: 'center'
                            }}
                        >
                            {isModeLoading ? <RefreshCw size={18} className={styles.spin} /> : (searchMode === 'agentic' ? <Bot size={18} /> : <Search size={18} />)}
                            {isModeLoading ? 'Thinking...' : (searchMode === 'agentic' ? 'Ask' : 'Search')}
                        </button>
                    </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {topics.map(topic => {
                            const Icon = topic.icon;
                            const isActive = activeTopic === topic.id;
                            return (
                                <button
                                    key={topic.id}
                                    onClick={() => handleTopicClick(topic.id)}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.5rem',
                                        padding: '0.4rem 0.8rem',
                                        borderRadius: '999px',
                                        border: `1px solid ${isActive ? 'var(--primary)' : 'var(--card-border)'}`,
                                        background: isActive ? 'rgba(var(--primary-rgb), 0.1)' : 'var(--card-bg)',
                                        color: isActive ? 'var(--primary)' : 'var(--secondary)',
                                        cursor: 'pointer',
                                        fontSize: '0.85rem',
                                        transition: 'all 0.2s ease'
                                    }}
                                >
                                    <Icon size={14} />
                                    {topic.label}
                                </button>
                            );
                        })}
                    </div>

                    <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            padding: '0.4rem',
                            color: 'var(--secondary)',
                            fontSize: '0.9rem',
                            cursor: 'pointer'
                        }}
                    >
                        <option value="date">Newest First</option>
                        <option value="relevance">Most Relevant</option>
                        <option value="lastUpdated">Last Updated</option>
                    </select>
                </div>
            </div>

            {isModeLoading ? (
                <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--secondary)' }}>
                    <RefreshCw size={32} className={styles.spin} style={{ marginBottom: '1rem' }} />
                    <p>{searchMode === 'agentic' ? "Agent is researching..." : "Scanning Arxiv..."}</p>
                </div>
            ) : (
                <div className={styles.grid}>
                    {displayedPapers.length === 0 ? (
                        <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '4rem', color: 'var(--secondary)', border: '1px dashed var(--card-border)', borderRadius: '12px' }}>
                            <p>No papers found.</p>
                        </div>
                    ) : (
                        displayedPapers.map((paper) => (
                            <PaperCard key={paper.id} paper={paper} onBookmark={() => toggleBookmark(paper)} navigatingTo={navigatingTo} onNavigate={setNavigatingTo} />
                        ))
                    )}
                </div>
            )}
        </div>
    );
}

function PaperCard({ paper, onBookmark, navigatingTo, onNavigate }: { paper: Paper, onBookmark: () => void, navigatingTo: string | null, onNavigate: (id: string | null) => void }) {
    const router = useRouter();
    const isLoading = navigatingTo === paper.id;

    const handleOpenTeacher = (e: React.MouseEvent) => {
        e.preventDefault();
        onNavigate(paper.id);
        router.push(`/teacher/${paper.id}`);
    };

    return (
        <div className={styles.card}>
            <div style={{ marginBottom: '0.5rem', fontSize: '0.8rem', color: 'var(--secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <span>{new Date(paper.published_date).toLocaleDateString()}</span>
                    <span>{paper.id}</span>
                </div>
                <button
                    onClick={(e) => { e.preventDefault(); onBookmark(); }}
                    style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '4px' }}
                    title={paper.is_bookmarked ? "Remove Bookmark" : "Bookmark"}
                >
                    <Bookmark size={18} fill={paper.is_bookmarked ? "#f59e0b" : "none"} color={paper.is_bookmarked ? "#f59e0b" : "var(--secondary)"} />
                </button>
            </div>
            <h2 className={styles.paperTitle}>{paper.title}</h2>
            <p className={styles.authors}>{paper.authors.join(', ')}</p>
            <p className={styles.summary}>{paper.summary}</p>
            <button
                onClick={handleOpenTeacher}
                className={styles.button}
                disabled={isLoading || (navigatingTo !== null && navigatingTo !== paper.id)}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    opacity: (navigatingTo !== null && navigatingTo !== paper.id) ? 0.5 : 1,
                    cursor: isLoading ? 'wait' : 'pointer'
                }}
            >
                {isLoading && <Loader2 size={16} className={styles.spin} />}
                {isLoading ? 'Loading...' : 'Open Teacher'}
            </button>
        </div>
    );
}
