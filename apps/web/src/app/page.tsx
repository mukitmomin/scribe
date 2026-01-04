import Link from 'next/link';
import { BookOpen, MessageSquare, FileText, Sparkles, Search, Zap } from 'lucide-react';
import styles from './page.module.css';

export default function LandingPage() {
  return (
    <div className={styles.container}>
      <div className={styles.hero}>
        <h1 className={styles.title}>Scribe</h1>
        <p className={styles.subtitle}>
          Your AI-powered research assistant for discovering, understanding, and sharing academic papers.
          Turn complex research into clear insights with the help of AI.
        </p>
        <div className={styles.ctaButtons}>
          <Link href="/research" className={styles.primaryCta}>
            Start Researching
          </Link>
          <Link href="/dashboard" className={styles.secondaryCta}>
            View Dashboard
          </Link>
        </div>
      </div>

      <div className={styles.features}>
        <div className={styles.featureCard}>
          <div className={styles.featureIcon}>
            <Search size={24} />
          </div>
          <h3 className={styles.featureTitle}>Discover Papers</h3>
          <p className={styles.featureDescription}>
            Search through millions of academic papers on arXiv with standard keyword search
            or let our AI agent discover relevant research for you.
          </p>
        </div>

        <div className={styles.featureCard}>
          <div className={styles.featureIcon}>
            <MessageSquare size={24} />
          </div>
          <h3 className={styles.featureTitle}>Learn with AI Teacher</h3>
          <p className={styles.featureDescription}>
            Chat with an AI that understands the paper deeply. Ask questions, request
            explanations, and get mathematical derivations step-by-step.
          </p>
        </div>

        <div className={styles.featureCard}>
          <div className={styles.featureIcon}>
            <FileText size={24} />
          </div>
          <h3 className={styles.featureTitle}>Generate Blog Drafts</h3>
          <p className={styles.featureDescription}>
            Turn your learning sessions into polished blog posts automatically. Share your
            insights with the world effortlessly.
          </p>
        </div>




      </div>

      <div className={styles.footer}>
        <p>&copy; 2025 Scribe. All Rights Reserved.</p>
      </div>
    </div>
  );
}
