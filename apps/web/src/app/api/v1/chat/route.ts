export const runtime = 'edge';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(req: Request) {
  const body = await req.json();

  // Extract only the new message (last message in array) to send to backend
  // This prevents sending entire chat history with every request
  const messages = body.messages || [];
  const newMessage = messages.length > 0 ? messages[messages.length - 1] : null;

  // Transform request to send only new message + session context
  const backendRequest = {
    sessionId: body.sessionId,
    paperId: body.paperId,
    message: newMessage,
  };

  const response = await fetch(`${BACKEND_URL}/api/v1/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(backendRequest),
  });

  // Return the streaming response directly without buffering
  return new Response(response.body, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'x-vercel-ai-data-stream': 'v1',
    },
  });
}
