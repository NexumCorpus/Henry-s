/**
 * Accessibility utilities for better user experience
 */

/**
 * Announces text to screen readers
 */
export const announceToScreenReader = (message: string): void => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.setAttribute('class', 'sr-only');
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

/**
 * Manages focus for better keyboard navigation
 */
export const manageFocus = {
  /**
   * Trap focus within an element
   */
  trapFocus: (element: HTMLElement): (() => void) => {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    element.addEventListener('keydown', handleTabKey);

    // Focus first element
    firstElement?.focus();

    // Return cleanup function
    return () => {
      element.removeEventListener('keydown', handleTabKey);
    };
  },

  /**
   * Save and restore focus
   */
  saveFocus: (): (() => void) => {
    const activeElement = document.activeElement as HTMLElement;
    
    return () => {
      if (activeElement && activeElement.focus) {
        activeElement.focus();
      }
    };
  },
};

/**
 * Check if user prefers reduced motion
 */
export const prefersReducedMotion = (): boolean => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

/**
 * Generate unique IDs for form elements
 */
export const generateId = (prefix: string = 'id'): string => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Keyboard event helpers
 */
export const keyboardHelpers = {
  isEnterKey: (event: KeyboardEvent): boolean => event.key === 'Enter',
  isSpaceKey: (event: KeyboardEvent): boolean => event.key === ' ',
  isEscapeKey: (event: KeyboardEvent): boolean => event.key === 'Escape',
  isArrowKey: (event: KeyboardEvent): boolean => 
    ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key),
};