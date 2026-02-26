import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  List,
  ListItem,
  ListItemText,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { Add, Delete, Edit } from '@mui/icons-material';
import { Editor } from '@monaco-editor/react';
import HttpService from '../services/HttpService';
import { modifyProcessIdentifierForPathParam } from '../helpers';

type GroupScriptFile = {
  name: string;
  file_contents: string;
};

type OwnProps = {
  processGroupId: string;
};

export default function ProcessGroupScripts({ processGroupId }: OwnProps) {
  const { t } = useTranslation();
  const [files, setFiles] = useState<GroupScriptFile[]>([]);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingFile, setEditingFile] = useState<GroupScriptFile | null>(null);
  const [newFileName, setNewFileName] = useState('');
  const [editorContent, setEditorContent] = useState('');
  const [fileNameError, setFileNameError] = useState('');

  const modifiedGroupId = modifyProcessIdentifierForPathParam(processGroupId);

  const fetchFiles = useCallback(() => {
    HttpService.makeCallToBackend({
      path: `/process-groups/${modifiedGroupId}/files`,
      successCallback: (result: GroupScriptFile[]) => {
        setFiles(result);
      },
    });
  }, [modifiedGroupId]);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const handleNewFile = () => {
    setEditingFile(null);
    setNewFileName('');
    setEditorContent('');
    setFileNameError('');
    setEditorOpen(true);
  };

  const handleEditFile = (file: GroupScriptFile) => {
    setEditingFile(file);
    setNewFileName(file.name.replace(/\.py$/, ''));
    setEditorContent(file.file_contents);
    setFileNameError('');
    setEditorOpen(true);
  };

  const handleDeleteFile = (fileName: string) => {
    HttpService.makeCallToBackend({
      path: `/process-groups/${modifiedGroupId}/files/${fileName}`,
      httpMethod: 'DELETE',
      successCallback: () => {
        fetchFiles();
      },
    });
  };

  const handleSave = () => {
    const fileName = editingFile
      ? editingFile.name
      : `${newFileName.trim()}.py`;

    if (!editingFile && !newFileName.trim()) {
      setFileNameError('File name is required');
      return;
    }

    if (!editingFile && !/^[a-z_][a-z0-9_]*$/i.test(newFileName.trim())) {
      setFileNameError(
        'File name must be a valid Python identifier (letters, numbers, underscores)',
      );
      return;
    }

    const blob = new Blob([editorContent], { type: 'text/x-python' });
    const formData = new FormData();
    formData.append('file', blob, fileName);

    const isUpdate = editingFile !== null;
    const path = isUpdate
      ? `/process-groups/${modifiedGroupId}/files/${fileName}`
      : `/process-groups/${modifiedGroupId}/files`;

    HttpService.makeCallToBackend({
      path,
      httpMethod: isUpdate ? 'PUT' : 'POST',
      postBody: formData,
      successCallback: () => {
        setEditorOpen(false);
        fetchFiles();
      },
    });
  };

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 1,
        }}
      >
        <Typography variant="h6">{t('group_scripts')}</Typography>
        <Button startIcon={<Add />} size="small" onClick={handleNewFile}>
          {t('add_script')}
        </Button>
      </Box>
      {files.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          {t('no_group_scripts')}
        </Typography>
      ) : (
        <List dense>
          {files.map((file) => (
            <ListItem
              key={file.name}
              secondaryAction={
                <Box>
                  <Tooltip title={t('edit')}>
                    <IconButton
                      size="small"
                      onClick={() => handleEditFile(file)}
                    >
                      <Edit fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t('delete')}>
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteFile(file.name)}
                    >
                      <Delete fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              }
            >
              <ListItemText
                primary={file.name}
                primaryTypographyProps={{ fontFamily: 'monospace' }}
              />
            </ListItem>
          ))}
        </List>
      )}

      <Dialog
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingFile ? `Edit ${editingFile.name}` : 'New Script'}
        </DialogTitle>
        <DialogContent>
          {!editingFile && (
            <TextField
              autoFocus
              label="File name"
              value={newFileName}
              onChange={(e) => {
                setNewFileName(e.target.value);
                setFileNameError('');
              }}
              error={!!fileNameError}
              helperText={fileNameError || 'Will be saved as <name>.py'}
              fullWidth
              size="small"
              sx={{ mb: 2, mt: 1 }}
            />
          )}
          <Box sx={{ height: 400, border: 1, borderColor: 'divider' }}>
            <Editor
              language="python"
              value={editorContent}
              onChange={(value) => setEditorContent(value || '')}
              options={{
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                fontSize: 13,
                lineNumbers: 'on',
                automaticLayout: true,
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditorOpen(false)}>{t('cancel')}</Button>
          <Button variant="contained" onClick={handleSave}>
            {t('save')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
