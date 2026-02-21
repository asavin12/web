import React from 'react';

interface HighlightTextProps {
  text: string;
  highlight: string;
  className?: string;
  highlightClassName?: string;
}

/**
 * Component to highlight search terms in text
 */
export function HighlightText({
  text,
  highlight,
  className = '',
  highlightClassName = 'bg-vintage-tan/30 text-vintage-dark px-0.5 rounded font-medium',
}: HighlightTextProps) {
  if (!highlight.trim()) {
    return <span className={className}>{text}</span>;
  }

  // Escape special regex characters
  const escapedHighlight = highlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  
  // Create regex for case-insensitive matching
  const regex = new RegExp(`(${escapedHighlight})`, 'gi');
  
  // Split text by the highlight pattern
  const parts = text.split(regex);

  return (
    <span className={className}>
      {parts.map((part, index) => {
        // Check if this part matches the highlight (case-insensitive)
        const isHighlight = part.toLowerCase() === highlight.toLowerCase();
        
        if (isHighlight) {
          return (
            <mark key={index} className={highlightClassName}>
              {part}
            </mark>
          );
        }
        
        return <span key={index}>{part}</span>;
      })}
    </span>
  );
}

export default HighlightText;
