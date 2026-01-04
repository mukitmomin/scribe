import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Modal, ConfirmModal } from './Modal';

describe('Modal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
  };

  it('renders when isOpen is true', () => {
    render(<Modal {...defaultProps} title="Test Modal" />);
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<Modal {...defaultProps} isOpen={false} title="Test Modal" />);
    expect(screen.queryByText('Test Modal')).not.toBeInTheDocument();
  });

  it('renders title and description', () => {
    render(
      <Modal
        {...defaultProps}
        title="Test Title"
        description="Test Description"
      />
    );
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
  });

  it('renders children', () => {
    render(
      <Modal {...defaultProps}>
        <div>Child Content</div>
      </Modal>
    );
    expect(screen.getByText('Child Content')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(<Modal {...defaultProps} onClose={onClose} title="Test Modal" />);

    const closeButton = screen.getByRole('button');
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when overlay is clicked if closeOnOverlayClick is true', () => {
    const onClose = vi.fn();
    const { container } = render(
      <Modal {...defaultProps} onClose={onClose} closeOnOverlayClick={true} />
    );

    const overlay = container.querySelector('[class*="overlay"]');
    if (overlay) {
      fireEvent.click(overlay);
      expect(onClose).toHaveBeenCalledTimes(1);
    }
  });

  it('does not call onClose when overlay is clicked if closeOnOverlayClick is false', () => {
    const onClose = vi.fn();
    const { container } = render(
      <Modal {...defaultProps} onClose={onClose} closeOnOverlayClick={false} />
    );

    const overlay = container.querySelector('[class*="overlay"]');
    if (overlay) {
      fireEvent.click(overlay);
      expect(onClose).not.toHaveBeenCalled();
    }
  });

  it('does not call onClose when modal content is clicked', () => {
    const onClose = vi.fn();
    const { container } = render(
      <Modal {...defaultProps} onClose={onClose}>
        <div>Content</div>
      </Modal>
    );

    const modalContent = container.querySelector('[class*="modal"]');
    if (modalContent) {
      fireEvent.click(modalContent);
      expect(onClose).not.toHaveBeenCalled();
    }
  });

  it('hides close button when showCloseButton is false', () => {
    render(
      <Modal {...defaultProps} title="Test Modal" showCloseButton={false} />
    );

    const closeButton = screen.queryByRole('button');
    expect(closeButton).not.toBeInTheDocument();
  });

  it('applies custom maxWidth', () => {
    const { container } = render(
      <Modal {...defaultProps} maxWidth="800px" />
    );

    const modalContent = container.querySelector('[class*="modal"]') as HTMLElement;
    expect(modalContent?.style.maxWidth).toBe('800px');
  });
});

describe('ConfirmModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
  };

  it('renders with default text', () => {
    render(<ConfirmModal {...defaultProps} />);
    expect(screen.getByText('Confirm')).toBeInTheDocument();
    expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument();
    expect(screen.getByText('Confirm')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('renders with custom text', () => {
    render(
      <ConfirmModal
        {...defaultProps}
        title="Delete Item"
        description="This action cannot be undone."
        confirmText="Delete"
        cancelText="Keep"
      />
    );
    expect(screen.getByText('Delete Item')).toBeInTheDocument();
    expect(screen.getByText('This action cannot be undone.')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
    expect(screen.getByText('Keep')).toBeInTheDocument();
  });

  it('calls onConfirm when confirm button is clicked', () => {
    const onConfirm = vi.fn();
    render(<ConfirmModal {...defaultProps} onConfirm={onConfirm} />);

    const confirmButton = screen.getByText('Confirm');
    fireEvent.click(confirmButton);

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when cancel button is clicked', () => {
    const onClose = vi.fn();
    render(<ConfirmModal {...defaultProps} onClose={onClose} />);

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('disables confirm button when isLoading is true', () => {
    render(<ConfirmModal {...defaultProps} isLoading={true} />);

    const confirmButton = screen.getByText('Loading...');
    expect(confirmButton).toBeDisabled();
  });

  it('shows loading text when isLoading is true', () => {
    render(<ConfirmModal {...defaultProps} isLoading={true} />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('applies danger variant styling', () => {
    const { container } = render(
      <ConfirmModal {...defaultProps} variant="danger" />
    );

    const confirmButton = screen.getByText('Confirm');
    expect(confirmButton.className).toContain('dangerButton');
  });

  it('applies default variant styling', () => {
    const { container } = render(
      <ConfirmModal {...defaultProps} variant="default" />
    );

    const confirmButton = screen.getByText('Confirm');
    expect(confirmButton.className).toContain('confirmButton');
  });
});
