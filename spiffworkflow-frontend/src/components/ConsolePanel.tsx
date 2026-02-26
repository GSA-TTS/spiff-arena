import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Box, Button, Typography } from '@mui/material';
import { Delete } from '@mui/icons-material';

type OwnProps = {
  lines: string[];
  onClear: () => void;
};

export default function ConsolePanel({ lines, onClear }: OwnProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const { t } = useTranslation();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines]);

  return (
    <Box
      sx={{
        backgroundColor: '#1e1e1e',
        color: '#d4d4d4',
        fontFamily: 'monospace',
        fontSize: 13,
        maxHeight: 300,
        overflow: 'auto',
        borderRadius: 1,
        mt: 2,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          px: 1.5,
          py: 0.5,
          borderBottom: '1px solid #333',
          position: 'sticky',
          top: 0,
          backgroundColor: '#1e1e1e',
          zIndex: 1,
        }}
      >
        <Typography
          variant="caption"
          sx={{ color: '#888', fontFamily: 'monospace' }}
        >
          {t('console')}
        </Typography>
        <Button
          size="small"
          startIcon={<Delete fontSize="small" />}
          onClick={onClear}
          sx={{ color: '#888', textTransform: 'none', minWidth: 'auto' }}
        >
          {t('clear')}
        </Button>
      </Box>
      <Box
        sx={{ px: 1.5, py: 1, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}
      >
        {lines.length === 0 ? (
          <Typography
            variant="body2"
            sx={{ color: '#666', fontFamily: 'monospace', fontStyle: 'italic' }}
          >
            {t('no_console_output')}
          </Typography>
        ) : (
          lines.map((line, index) => (
            <span key={`console-line-${index}`}>{line}</span>
          ))
        )}
        <div ref={bottomRef} />
      </Box>
    </Box>
  );
}
