import { Box, IconButton, Typography } from '@mui/material';
import { Close } from '@mui/icons-material';
import { Editor } from '@monaco-editor/react';

type PythonEditorPanelProps = {
  content: string;
  onChange: (value: string) => void;
  fileName: string;
  height: number;
  onClose: () => void;
};

export default function PythonEditorPanel({
  content,
  onChange,
  fileName,
  height,
  onClose,
}: PythonEditorPanelProps) {
  return (
    <Box
      sx={{
        height,
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        borderTop: 1,
        borderColor: 'divider',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 1,
          py: 0.5,
          backgroundColor: 'background.paper',
          borderBottom: 1,
          borderColor: 'divider',
          flexShrink: 0,
        }}
      >
        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
          {fileName}
        </Typography>
        <IconButton size="small" onClick={onClose}>
          <Close fontSize="small" />
        </IconButton>
      </Box>
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <Editor
          language="python"
          value={content}
          onChange={(value) => onChange(value || '')}
          options={{
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 13,
            lineNumbers: 'on',
            automaticLayout: true,
          }}
        />
      </Box>
    </Box>
  );
}
