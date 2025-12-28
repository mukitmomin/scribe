export interface Paper {
    id: string;
    title: string;
    authors: string[];
    summary: string;
    published_date: string;
    pdf_url: string;
    status: string;
    is_bookmarked?: boolean;
    tenant_id?: string;
}
