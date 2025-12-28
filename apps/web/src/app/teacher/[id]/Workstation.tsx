'use client';
import { useState } from 'react';
import { TeacherChat } from './TeacherChat';
import { ScribeEditor } from '../../scribe/[id]/ScribeEditor';
import styles from './Teacher.module.css';

interface WorkstationProps {
    paperId: string;
    initialSessions: any[];
    initialSessionId: string | null;
    initialMessages: any[];
    initialPosts: any[];
}

export function Workstation({
    paperId,
    initialSessions,
    initialSessionId,
    initialMessages,
    initialPosts
}: WorkstationProps) {
    const [view, setView] = useState<'chat' | 'scribe'>('chat');
    const [activePostId, setActivePostId] = useState<string | null>(null);
    const [posts, setPosts] = useState(initialPosts);
    const [isPdfCollapsed, setIsPdfCollapsed] = useState(false);

    const handleOpenDraft = (postId: string) => {
        setActivePostId(postId);
        setView('scribe');
    };

    const handleCreateDraft = (postData: any) => {
        setPosts(prev => [postData, ...prev]);
        setActivePostId(postData.id || postData.post_id);
        setView('scribe');
    };

    const handleBackToChat = () => {
        setActivePostId(null);
        setView('chat');
    };

    return (
        <div
            className={styles.container}
            style={{
                gridTemplateColumns: isPdfCollapsed ? '0px 1fr' : '1fr 1fr',
                transition: 'grid-template-columns 0.3s ease'
            }}
        >
            <div className={styles.pdfContainer}>
                <iframe
                    src={`https://arxiv.org/pdf/${paperId}.pdf`}
                    className={styles.pdfFrame}
                    title="PDF Viewer"
                />
            </div>

            <div className={styles.chatContainer}>
                <div style={{ display: view === 'chat' ? 'flex' : 'none', height: '100%', flexDirection: 'column' }}>
                    <TeacherChat
                        paperId={paperId}
                        initialSessions={initialSessions}
                        initialSessionId={initialSessionId}
                        initialMessages={initialMessages}
                        initialPosts={posts}
                        onOpenDraft={handleOpenDraft}
                        onDraftCreated={handleCreateDraft}
                        isPdfCollapsed={isPdfCollapsed}
                        onTogglePdf={() => setIsPdfCollapsed(!isPdfCollapsed)}
                    />
                </div>

                {view === 'scribe' && activePostId && (
                    <ScribeEditorWrapper postId={activePostId} onBack={handleBackToChat} />
                )}
            </div>
        </div>
    );
}

function ScribeEditorWrapper({ postId, onBack }: { postId: string, onBack: () => void }) {
    const [post, setPost] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useState(() => {
        fetch(`/api/v1/scribe/post/${postId}`)
            .then(res => res.json())
            .then(data => {
                setPost(data);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    });

    if (loading) return <div className={styles.emptyState}>Loading draft...</div>;
    if (!post) return <div className={styles.emptyState}>Failed to load draft</div>;

    return <ScribeEditor initialPost={post} onBack={onBack} />;
}
