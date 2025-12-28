import { Workstation } from './Workstation';
import { getBackendUrl } from '@/lib/config';

interface Session {
    id: string;
    title: string;
    created_at: string | null;
    updated_at: string | null;
    message_count: number;
}

async function getSessions(paperId: string): Promise<Session[]> {
    try {
        const res = await fetch(getBackendUrl(`/api/v1/chat/sessions/${paperId}`), { cache: 'no-store' });
        if (!res.ok) return [];
        const data = await res.json();
        return data.sessions || [];
    } catch (error) {
        console.error("Failed to fetch sessions:", error);
        return [];
    }
}

async function getSessionMessages(sessionId: string): Promise<any[]> {
    try {
        const res = await fetch(getBackendUrl(`/api/v1/chat/session/${sessionId}`), { cache: 'no-store' });
        if (!res.ok) return [];
        const data = await res.json();
        return data.messages || [];
    } catch (error) {
        console.error("Failed to fetch session messages:", error);
        return [];
    }
}

async function getPosts(paperId: string): Promise<any[]> {
    try {
        const res = await fetch(getBackendUrl(`/api/v1/scribe/posts/${paperId}`), { cache: 'no-store' });
        if (!res.ok) return [];
        const data = await res.json();
        return data.posts || [];
    } catch (error) {
        console.error("Failed to fetch posts:", error);
        return [];
    }
}

export default async function TeacherRoomPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    const sessions = await getSessions(id);
    const posts = await getPosts(id);

    const currentSession = sessions.length > 0 ? sessions[0] : null;
    const initialMessages = currentSession ? await getSessionMessages(currentSession.id) : [];

    return (
        <Workstation
            paperId={id}
            initialSessions={sessions}
            initialSessionId={currentSession?.id || null}
            initialMessages={initialMessages}
            initialPosts={posts}
        />
    );
}
