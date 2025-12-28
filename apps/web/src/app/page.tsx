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

        <div className={styles.featureCard}>
          <div className={styles.featureIcon}>
            <Sparkles size={24} />
          </div>
          <h3 className={styles.featureTitle}>AI-Powered Discovery</h3>
          <p className={styles.featureDescription}>
            Our agentic search understands your research intent and finds papers that truly 
            matter to your work.
          </p>
        </div>

        <div className={styles.featureCard}>
          <div className={styles.featureIcon}>
            <BookOpen size={24} />
          </div>
          <h3 className={styles.featureTitle}>Bookmark & Organize</h3>
          <p className={styles.featureDescription}>
            Save papers you care about, organize your research sessions, and never lose 
            track of important insights.
          </p>
        </div>

        <div className={styles.featureCard}>
          <div className={styles.featureIcon}>
            <Zap size={24} />
          </div>
          <h3 className={styles.featureTitle}>Streaming Responses</h3>
          <p className={styles.featureDescription}>
            Get real-time AI responses that stream as they're generated. No waiting around 
            for answers to complex questions.
          </p>
        </div>
      </div>

      <div className={styles.howItWorks}>
        <h2 className={styles.sectionTitle}>How It Works</h2>
        <div className={styles.steps}>
          <div className={styles.step}>
            <div className={styles.stepNumber}>1</div>
            <h3 className={styles.stepTitle}>Find Papers</h3>
            <p className={styles.stepDescription}>
              Search or discover research papers using our AI-powered search
            </p>
          </div>

          <div className={styles.step}>
            <div className={styles.stepNumber}>2</div>
            <h3 className={styles.stepTitle}>Learn Deeply</h3>
            <p className={styles.stepDescription}>
              Chat with the AI Teacher to understand complex concepts and methods
            </p>
          </div>

          <div className={styles.step}>
            <div className={styles.stepNumber}>3</div>
            <h3 className={styles.stepTitle}>Share Insights</h3>
            <p className={styles.stepDescription}>
              Generate and publish blog posts to share what you've learned
            </p>
          </div>
        </div>
      </div>

      <div className={styles.footer}>
        <p>&copy; 2025 Scribe. All Rights Reserved.</p>
      </div>
    </div>
  );
}
