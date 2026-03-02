import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Box, Button, TextField, Typography, Stack } from '@mui/material';
import HttpService from '../../services/HttpService';

export default function AdminGroupNew() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState('');
  const [name, setName] = useState('');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    HttpService.makeCallToBackend({
      path: '/admin/groups',
      httpMethod: 'POST',
      postBody: { identifier, name: name || identifier },
      successCallback: (result: any) => {
        navigate(`/admin/groups/${result.id}`);
      },
    });
  };

  return (
    <>
      <Typography variant="h1">{t('admin_group_new')}</Typography>
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{ mt: 2, maxWidth: 500 }}
      >
        <Stack spacing={2}>
          <TextField
            label={t('identifier')}
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
            fullWidth
            helperText={t('admin_group_identifier_help')}
          />
          <TextField
            label={t('name')}
            value={name}
            onChange={(e) => setName(e.target.value)}
            fullWidth
            helperText={t('admin_group_name_help')}
          />
          <Stack direction="row" spacing={2}>
            <Button type="submit" variant="contained">
              {t('create')}
            </Button>
            <Button
              variant="outlined"
              onClick={() => navigate('/admin/groups')}
            >
              {t('cancel')}
            </Button>
          </Stack>
        </Stack>
      </Box>
    </>
  );
}
