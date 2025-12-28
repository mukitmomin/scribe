"use client";
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowLeft, Edit, Code, MoreHorizontal, Trash2 } from 'lucide-react';
import { ConfirmModal, Modal, modalStyles } from '@scribe/ui';
import type { AdminPost } from '@scribe/types';

export default function AdminDashboard() {
    const [posts, setPosts] = useState<AdminPost[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedPostId, setSelectedPostId] = useState<string | null>(null);
    const [openActionMenuId, setOpenActionMenuId] = useState<string | null>(null);
    const [postToDelete, setPostToDelete] = useState<string | null>(null);

    useEffect(() => { fetchPosts(); }, []);

    useEffect(() => {
        const handleClickOutside = () => setOpenActionMenuId(null);
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, []);

    const fetchPosts = async () => {
        try {
            const res = await fetch('/api/v1/scribe/admin/posts');
            if (res.ok) {
                const data = await res.json();
                setPosts(data.posts);
            }
        } catch (e) {
            console.error("Failed to fetch posts", e);
        } finally {
            setLoading(false);
        }
    };

    const confirmDelete = async () => {
        if (!postToDelete) return;
        try {
            const res = await fetch(`/api/v1/scribe/post/${postToDelete}`, { method: 'DELETE' });
            if (res.ok) {
                fetchPosts();
                setPostToDelete(null);
            } else {
                alert("Failed to delete post");
            }
        } catch (e) {
            console.error("Failed to delete", e);
        }
    };

    const toggleActionMenu = (e: React.MouseEvent, postId: string) => {
        e.preventDefault();
        e.stopPropagation();
        e.nativeEvent.stopImmediatePropagation();
        setOpenActionMenuId(openActionMenuId === postId ? null : postId);
    };

    return (
        <div style={{ padding: 'calc(60px + 2rem) 2rem 2rem', maxWidth: '1200px', margin: '0 auto', color: 'var(--foreground)' }}>
            <div style={{ marginBottom: '2rem' }}>
                <Link href="/" style={{ color: 'var(--secondary)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <ArrowLeft size={16} /> Back to Research
                </Link>
                <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>Publisher Dashboard</h1>
                <p style={{ color: 'var(--secondary)' }}>Manage draft posts and publications.</p>
            </div>

            {loading ? (
                <div>Loading posts...</div>
            ) : (
                <div style={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)', borderRadius: '12px', minHeight: '400px' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead style={{ background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--card-border)' }}>
                            <tr>
                                <th style={{ padding: '1rem', color: 'var(--secondary)', fontWeight: 600 }}>Title</th>
                                <th style={{ padding: '1rem', color: 'var(--secondary)', fontWeight: 600 }}>Status</th>
                                <th style={{ padding: '1rem', color: 'var(--secondary)', fontWeight: 600 }}>Embed?</th>
                                <th style={{ padding: '1rem', color: 'var(--secondary)', fontWeight: 600 }}>Date</th>
                                <th style={{ padding: '1rem', color: 'var(--secondary)', fontWeight: 600, textAlign: 'right', width: '80px' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {posts.length === 0 ? (
                                <tr><td colSpan={5} style={{ padding: '2rem', textAlign: 'center', color: 'var(--secondary)' }}>No posts found.</td></tr>
                            ) : (
                                posts.map(post => (
                                    <tr key={post.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '1rem' }}>
                                            <div style={{ fontWeight: 600 }}>{post.title}</div>
                                            <div style={{ fontSize: '0.8rem', color: 'var(--secondary)' }}>ID: {post.id.substring(0, 8)}...</div>
                                        </td>
                                        <td style={{ padding: '1rem' }}>
                                            <span style={{ padding: '0.25rem 0.5rem', borderRadius: '999px', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', background: post.status === 'published' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.05)', color: post.status === 'published' ? '#10b981' : 'var(--secondary)', border: `1px solid ${post.status === 'published' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.1)'}` }}>
                                                {post.status}
                                            </span>
                                        </td>
                                        <td style={{ padding: '1rem' }}>
                                            {post.has_embed ? <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.8rem' }}><Code size={14} /> Active</span> : <span style={{ color: 'var(--secondary)', fontSize: '0.8rem' }}>-</span>}
                                        </td>
                                        <td style={{ padding: '1rem', fontSize: '0.9rem', color: 'var(--secondary)' }}>
                                            {post.published_at ? new Date(post.published_at).toLocaleDateString() : (post.created_at ? new Date(post.created_at).toLocaleDateString() : '-')}
                                        </td>
                                        <td style={{ padding: '1rem', textAlign: 'right', position: 'relative' }}>
                                            <button onClick={(e) => toggleActionMenu(e, post.id)} style={{ padding: '0.5rem', background: 'transparent', border: 'none', color: 'var(--secondary)', cursor: 'pointer', borderRadius: '4px' }}>
                                                <MoreHorizontal size={20} />
                                            </button>
                                            {openActionMenuId === post.id && (
                                                <div onClick={(e) => e.stopPropagation()} style={{ position: 'absolute', right: '1rem', top: '3rem', background: '#1a1a1a', border: '1px solid var(--card-border)', borderRadius: '8px', zIndex: 50, width: '160px', boxShadow: '0 4px 20px rgba(0,0,0,0.5)', overflow: 'hidden', textAlign: 'left' }}>
                                                    <Link href={`/scribe/${post.id}`} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.8rem 1rem', color: 'var(--foreground)', textDecoration: 'none', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.9rem' }}>
                                                        <Edit size={16} /> Open Editor
                                                    </Link>
                                                    <button onClick={() => { setPostToDelete(post.id); setOpenActionMenuId(null); }} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.8rem 1rem', background: 'rgba(239, 68, 68, 0.1)', border: 'none', color: '#ef4444', cursor: 'pointer', textAlign: 'left', fontSize: '0.9rem' }}>
                                                        <Trash2 size={16} /> Delete
                                                    </button>
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            <ConfirmModal isOpen={!!postToDelete} onClose={() => setPostToDelete(null)} onConfirm={confirmDelete} title="Delete Post?" description="Are you sure you want to delete this post? This action cannot be undone." confirmText="Delete" variant="danger" />
        </div>
    );
}
