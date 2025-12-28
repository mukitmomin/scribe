import styles from './LoadingDots.module.css';

export function LoadingDots() {
    return (
        <div className={styles.loadingDots}>
            <span className={styles.dot}></span>
            <span className={styles.dot}></span>
            <span className={styles.dot}></span>
        </div>
    );
}
