'use client';
import React, { useEffect, useCallback } from 'react';
import { X } from 'lucide-react';
import styles from './Modal.module.css';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    description?: string;
    children?: React.ReactNode;
    showCloseButton?: boolean;
    closeOnOverlayClick?: boolean;
    maxWidth?: string;
}

export function Modal({
    isOpen,
    onClose,
    title,
    description,
    children,
    showCloseButton = true,
    closeOnOverlayClick = true,
    maxWidth = '500px'
}: ModalProps) {
    const handleKeyDown = useCallback((e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose();
    }, [onClose]);

    useEffect(() => {
        if (isOpen) {
            document.addEventListener('keydown', handleKeyDown);
            document.body.style.overflow = 'hidden';
        }
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            document.body.style.overflow = '';
        };
    }, [isOpen, handleKeyDown]);

    if (!isOpen) return null;

    return (
        <div
            className={styles.overlay}
            onClick={closeOnOverlayClick ? onClose : undefined}
        >
            <div
                className={styles.modal}
                style={{ maxWidth }}
                onClick={(e) => e.stopPropagation()}
            >
                {(title || showCloseButton) && (
                    <div className={styles.header}>
                        {title && <h3 className={styles.title}>{title}</h3>}
                        {showCloseButton && (
                            <button className={styles.closeButton} onClick={onClose}>
                                <X size={20} />
                            </button>
                        )}
                    </div>
                )}
                {description && (
                    <p className={styles.description}>{description}</p>
                )}
                {children}
            </div>
        </div>
    );
}

interface ConfirmModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title?: string;
    description?: string;
    confirmText?: string;
    cancelText?: string;
    variant?: 'default' | 'danger';
    isLoading?: boolean;
}

export function ConfirmModal({
    isOpen,
    onClose,
    onConfirm,
    title = 'Confirm',
    description = 'Are you sure you want to proceed?',
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    variant = 'default',
    isLoading = false
}: ConfirmModalProps) {
    return (
        <Modal isOpen={isOpen} onClose={onClose} title={title} description={description} showCloseButton={false}>
            <div className={styles.actions}>
                <button className={styles.cancelButton} onClick={onClose}>
                    {cancelText}
                </button>
                <button
                    className={variant === 'danger' ? styles.dangerButton : styles.confirmButton}
                    onClick={onConfirm}
                    disabled={isLoading}
                >
                    {isLoading ? 'Loading...' : confirmText}
                </button>
            </div>
        </Modal>
    );
}

export { styles as modalStyles };
