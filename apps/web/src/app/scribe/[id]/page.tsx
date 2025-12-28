import { ScribeEditor } from './ScribeEditor';
import styles from '../../teacher/[id]/Teacher.module.css';
import { getBackendUrl } from '@/lib/config';

async function getPost(postId: string) {
    try {
        const res = await fetch(getBackendUrl(`/api/v1/scribe/post/${postId}`), { cache: 'no-store' });
        if (!res.ok) {
            if (res.status === 404) return null;
            throw new Error(`Failed to fetch post: ${res.status}`);
        }
        return await res.json();
    } catch (error) {
        console.error("Failed to fetch post:", error);
        return null;
    }
}

export default async function ScribePage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    const post = await getPost(id);

    if (!post) {
        return (
            <div className={styles.container} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className={styles.emptyState}>Post not found</div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.pdfContainer}>
                <iframe
                    src={`https://arxiv.org/pdf/${post.paper_id}.pdf`}
                    className={styles.pdfFrame}
                    title="PDF Viewer"
                    style={{ background: 'white' }}
                />
            </div>
            <div className={styles.chatContainer}>
                <ScribeEditor initialPost={post} />
            </div>
        </div>
    );
}
