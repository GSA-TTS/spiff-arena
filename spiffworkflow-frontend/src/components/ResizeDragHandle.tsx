import React, { useCallback, useRef } from 'react';
import { Box } from '@mui/material';

type ResizeDragHandleProps = {
  onResize: (newHeight: number) => void;
  currentHeight: number;
  minHeight?: number;
  maxHeight?: number;
};

export default function ResizeDragHandle({
  onResize,
  currentHeight,
  minHeight = 100,
  maxHeight = 800,
}: ResizeDragHandleProps) {
  const startYRef = useRef(0);
  const startHeightRef = useRef(0);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      const delta = startYRef.current - e.clientY;
      const newHeight = Math.min(
        maxHeight,
        Math.max(minHeight, startHeightRef.current + delta),
      );
      onResize(newHeight);
    },
    [onResize, minHeight, maxHeight],
  );

  const handleMouseUp = useCallback(() => {
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }, [handleMouseMove]);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      startYRef.current = e.clientY;
      startHeightRef.current = currentHeight;
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    },
    [currentHeight, handleMouseMove, handleMouseUp],
  );

  return (
    <Box
      onMouseDown={handleMouseDown}
      sx={{
        height: 6,
        cursor: 'row-resize',
        backgroundColor: 'divider',
        '&:hover': {
          backgroundColor: 'primary.main',
        },
        flexShrink: 0,
      }}
    />
  );
}
