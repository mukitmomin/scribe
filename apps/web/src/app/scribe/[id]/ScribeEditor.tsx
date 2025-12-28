'use client';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import styles from '../../teacher/[id]/Teacher.module.css';
import { Save, ArrowLeft, Send, Trash2, Columns } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { ConfirmModal } from '@scribe/ui';

interface Post {
    id: string;
    paper_id: string;
    title: string;
    content_markdown?: string;
    status: string;
    slug?: string;
    substack_embed_code?: string;
}

interface ScribeEditorProps {
    initialPost: Post;
    onBack?: () => void;
}

export function ScribeEditor({ initialPost, onBack }: ScribeEditorProps) {
    const [content, setContent] = useState(initialPost.content_markdown || '');
    const [title, setTitle] = useState(initialPost.title || '');
    const [slug, setSlug] = useState(initialPost.slug || '');
    const [substackEmbedCode, setSubstackEmbedCode] = useState(initialPost.substack_embed_code || '');
    const [status, setStatus] = useState(initialPost.status || 'draft');
    const [isSaving, setIsSaving] = useState(false);
    const [activeTab, setActiveTab] = useState<'write' | 'preview' | 'split'>('write');
    const [showPubDetails, setShowPubDetails] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const router = useRouter();

    const handleBack = () => {
        if (onBack) onBack();
        else router.push(`/teacher/${initialPost.paper_id}`);
    };

    const handleSave = async (targetStatus?: string) => {
        setIsSaving(true);
        const finalStatus = targetStatus || status;
        try {
            const res = await fetch(`/api/v1/scribe/post/${initialPost.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, slug, substack_embed_code: substackEmbedCode, content_markdown: content, status: finalStatus })
            });
            if (res.ok) setStatus(finalStatus);
        } catch (e) {
            console.error("Failed to save", e);
            alert("Failed to save post");
        } finally {
            setIsSaving(false);
        }
    };

    const handlePublish = () => {
        if (confirm("Publish this post to your blog?")) handleSave('published');
    };

    const confirmDiscard = async () => {
        setIsSaving(true);
        try {
            const res = await fetch(`/api/v1/scribe/post/${initialPost.id}`, { method: 'DELETE' });
            if (res.ok) handleBack();
        } catch (e) {
            console.error("Failed to discard", e);
            alert("Failed to discard draft");
            setIsSaving(false);
            setShowDeleteModal(false);
        }
    };

    return (
        <div className={styles.chatWrapper} style={{ background: 'var(--background)' }}>
            <div style={{ padding: '1rem', borderBottom: '1px solid var(--card-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(0,0,0,0.2)' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <button onClick={handleBack} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'transparent', border: 'none', color: 'var(--secondary)', cursor: 'pointer', fontSize: '0.9rem' }}>
                        <ArrowLeft size={16} /> Back to Paper
                    </button>
                    <div style={{ display: 'flex', background: 'var(--card-bg)', borderRadius: '6px', padding: '2px' }}>
                        <button onClick={() => setActiveTab('write')} style={{ padding: '0.4rem 1rem', border: 'none', background: activeTab === 'write' ? 'var(--primary)' : 'transparent', color: activeTab === 'write' ? 'white' : 'var(--secondary)', borderRadius: '4px', cursor: 'pointer', fontWeight: 500, fontSize: '0.9rem' }}>Write</button>
                        <button onClick={() => setActiveTab('split')} style={{ padding: '0.4rem 1rem', border: 'none', background: activeTab === 'split' ? 'var(--primary)' : 'transparent', color: activeTab === 'split' ? 'white' : 'var(--secondary)', borderRadius: '4px', cursor: 'pointer', fontWeight: 500, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Columns size={14} /></button>
                        <button onClick={() => setActiveTab('preview')} style={{ padding: '0.4rem 1rem', border: 'none', background: activeTab === 'preview' ? 'var(--primary)' : 'transparent', color: activeTab === 'preview' ? 'white' : 'var(--secondary)', borderRadius: '4px', cursor: 'pointer', fontWeight: 500, fontSize: '0.9rem' }}>Preview</button>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <div style={{ padding: '0.25rem 0.75rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', background: status === 'published' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.1)', color: status === 'published' ? '#10b981' : 'var(--secondary)', border: `1px solid ${status === 'published' ? '#059669' : 'transparent'}`, marginRight: '0.5rem' }}>
                        {status === 'published' ? 'Published' : 'Draft'}
                    </div>
                    <button onClick={() => setShowDeleteModal(true)} disabled={isSaving} style={{ height: '36px', background: 'transparent', border: '1px solid var(--card-border)', color: 'var(--secondary)', padding: '0 0.75rem', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                        <Trash2 size={16} />
                    </button>
                    <button onClick={() => handleSave()} disabled={isSaving} style={{ height: '36px', background: 'transparent', border: '1px solid var(--card-border)', color: 'var(--foreground)', padding: '0 1rem', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
                        <Save size={16} /> Save
                    </button>
                    <button onClick={handlePublish} disabled={isSaving || status === 'published'} style={{ height: '36px', background: 'var(--primary)', color: 'white', padding: '0 1rem', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, border: 'none', opacity: status === 'published' ? 0.8 : 1 }}>
                        <Send size={16} /> {status === 'published' ? 'Published' : 'Publish'}
                    </button>
                </div>
            </div>

            <div style={{ padding: '0.5rem 1.5rem' }}>
                <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Post Title" style={{ width: '100%', background: 'transparent', border: 'none', fontSize: '1.5rem', fontWeight: 700, color: 'var(--foreground)', outline: 'none', marginBottom: '0.5rem' }} />
                <button onClick={() => setShowPubDetails(!showPubDetails)} style={{ background: 'transparent', border: 'none', color: 'var(--secondary)', fontSize: '0.8rem', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}>
                    {showPubDetails ? 'Hide' : 'Show'} Publication Details
                </button>
                {showPubDetails && (
                    <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--secondary)', marginBottom: '0.3rem' }}>URL Slug</label>
                            <input value={slug} onChange={e => setSlug(e.target.value)} placeholder="my-awesome-post" style={{ width: '100%', padding: '0.5rem', background: 'var(--card-bg)', border: '1px solid var(--card-border)', color: 'var(--foreground)', borderRadius: '4px' }} />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--secondary)', marginBottom: '0.3rem' }}>Substack Embed Code</label>
                            <textarea value={substackEmbedCode} onChange={e => setSubstackEmbedCode(e.target.value)} placeholder="<iframe src='...' ...></iframe>" style={{ width: '100%', height: '80px', padding: '0.5rem', background: 'var(--card-bg)', border: '1px solid var(--card-border)', color: 'var(--foreground)', borderRadius: '4px', fontFamily: 'monospace', fontSize: '0.8rem' }} />
                        </div>
                    </div>
                )}
            </div>

            <div style={{ flex: 1, display: 'flex', flexDirection: 'row', overflow: 'hidden' }}>
                {(activeTab === 'write' || activeTab === 'split') && (
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: activeTab === 'split' ? '1px solid var(--card-border)' : 'none', overflowY: 'auto' }}>
                        <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="Start writing your blog post..." style={{ flex: 1, width: '100%', background: 'transparent', border: 'none', padding: '1rem 1.5rem', fontSize: '1rem', lineHeight: '1.6', color: 'var(--foreground)', resize: 'none', outline: 'none', fontFamily: 'inherit', minHeight: '100%' }} spellCheck={false} />
                    </div>
                )}
                {(activeTab === 'preview' || activeTab === 'split') && (
                    <div style={{ flex: 1, overflowY: 'auto', background: activeTab === 'split' ? 'rgba(0,0,0,0.2)' : 'transparent' }}>
                        <div className={styles.messageContent} style={{ padding: '1rem 1.5rem', maxWidth: '800px', margin: '0 auto' }}>
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                        </div>
                    </div>
                )}
            </div>

            <ConfirmModal isOpen={showDeleteModal} onClose={() => setShowDeleteModal(false)} onConfirm={confirmDiscard} title="Discard Draft?" description="Are you sure you want to discard this draft? This action cannot be undone." confirmText="Discard" variant="danger" isLoading={isSaving} />
        </div>
    );
}
