export interface Post {
    id: string;
    paper_id: string;
    title: string;
    content_markdown?: string;
    status: 'draft' | 'published';
    slug?: string;
    substack_embed_code?: string;
    created_at?: string;
    published_at?: string;
    tenant_id?: string;
}

export interface AdminPost extends Post {
    has_embed: boolean;
}

export interface PostsResponse {
    posts: Post[];
}

export interface AdminPostsResponse {
    posts: AdminPost[];
}
