import React from 'react';
import { useReveal } from '../hooks/useReveal';

interface RevealProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}

/** Fades + lifts its children into place the first time they scroll into view. */
export const Reveal: React.FC<RevealProps> = ({ children, className = '', delay = 0 }) => {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
      className={`reveal ${visible ? 'in-view' : ''} ${className}`}
    >
      {children}
    </div>
  );
};
