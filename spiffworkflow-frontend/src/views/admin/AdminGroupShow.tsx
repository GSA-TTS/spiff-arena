import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Button,
  IconButton,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Typography,
  Paper,
  Chip,
} from '@mui/material';
import { Delete } from '@mui/icons-material';
import HttpService from '../../services/HttpService';
import UserSearch from '../../components/UserSearch';
import { setPageTitle } from '../../helpers';
import { User } from '../../interfaces';
import ConfirmButton from '../../components/ConfirmButton';
import AdminGroupPermissions from './AdminGroupPermissions';

interface GroupMember {
  id: number;
  username: string;
  email: string | null;
  assignment_id: number;
  annotation: string | null;
}

interface PendingMember {
  id: number;
  username: string;
}

interface GroupDetail {
  id: number;
  identifier: string;
  name: string;
  source_is_open_id: boolean;
  member_count: number;
  pending_count: number;
  members: GroupMember[];
  pending: PendingMember[];
}

export default function AdminGroupShow() {
  const params = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [group, setGroup] = useState<GroupDetail | null>(null);
  const [tabIndex, setTabIndex] = useState(0);
  const [emailInput, setEmailInput] = useState('');
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [editingAnnotation, setEditingAnnotation] = useState<number | null>(
    null,
  );
  const [annotationInput, setAnnotationInput] = useState('');

  const loadGroup = useCallback(() => {
    HttpService.makeCallToBackend({
      path: `/admin/groups/${params.group_id}`,
      successCallback: (result: GroupDetail) => {
        setGroup(result);
        setNameInput(result.name);
      },
    });
  }, [params.group_id]);

  useEffect(() => {
    loadGroup();
  }, [loadGroup]);

  useEffect(() => {
    if (group) {
      setPageTitle([t('admin_groups'), group.name]);
    }
  }, [group, t]);

  const handleAddUserBySearch = (user: User | null) => {
    if (user && group) {
      HttpService.makeCallToBackend({
        path: `/admin/groups/${group.id}/members`,
        httpMethod: 'POST',
        postBody: { usernames: [user.username] },
        successCallback: () => loadGroup(),
      });
    }
  };

  const handleAddByEmail = () => {
    if (emailInput.trim() && group) {
      HttpService.makeCallToBackend({
        path: `/admin/groups/${group.id}/members`,
        httpMethod: 'POST',
        postBody: { usernames: [emailInput.trim()] },
        successCallback: () => {
          setEmailInput('');
          loadGroup();
        },
      });
    }
  };

  const handleCsvUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0] && group) {
      const formData = new FormData();
      formData.append('file', event.target.files[0]);
      HttpService.makeCallToBackend({
        path: `/admin/groups/${group.id}/members/csv`,
        httpMethod: 'POST',
        postBody: formData,
        successCallback: () => loadGroup(),
      });
    }
  };

  const handleRemoveMember = (userId: number) => {
    if (group) {
      HttpService.makeCallToBackend({
        path: `/admin/groups/${group.id}/members/${userId}`,
        httpMethod: 'DELETE',
        successCallback: () => loadGroup(),
      });
    }
  };

  const handleRemovePending = (waitingId: number) => {
    if (group) {
      HttpService.makeCallToBackend({
        path: `/admin/groups/${group.id}/pending/${waitingId}`,
        httpMethod: 'DELETE',
        successCallback: () => loadGroup(),
      });
    }
  };

  const handleUpdateName = () => {
    if (group) {
      HttpService.makeCallToBackend({
        path: `/admin/groups/${group.id}`,
        httpMethod: 'PUT',
        postBody: { name: nameInput },
        successCallback: () => {
          setEditingName(false);
          loadGroup();
        },
      });
    }
  };

  const handleDeleteGroup = () => {
    if (group) {
      HttpService.makeCallToBackend({
        path: `/admin/groups/${group.id}`,
        httpMethod: 'DELETE',
        successCallback: () => navigate('/admin/groups'),
      });
    }
  };

  const handleSaveAnnotation = (userId: number) => {
    if (group) {
      HttpService.makeCallToBackend({
        path: `/admin/groups/${group.id}/members/${userId}/annotation`,
        httpMethod: 'PUT',
        postBody: { annotation: annotationInput },
        successCallback: () => {
          setEditingAnnotation(null);
          loadGroup();
        },
      });
    }
  };

  if (!group) {
    return null;
  }

  const membersTab = (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>
        {t('admin_add_members')}
      </Typography>
      <Stack spacing={2} sx={{ maxWidth: 500 }}>
        <UserSearch
          onSelectedUser={handleAddUserBySearch}
          label={t('admin_search_user')}
        />
        <Stack direction="row" spacing={1}>
          <TextField
            label={t('admin_add_by_email')}
            value={emailInput}
            onChange={(e) => setEmailInput(e.target.value)}
            size="small"
            fullWidth
          />
          <Button variant="outlined" onClick={handleAddByEmail}>
            {t('add_button')}
          </Button>
        </Stack>
        <Button variant="outlined" component="label" size="small">
          {t('admin_upload_csv')}
          <input type="file" accept=".csv" hidden onChange={handleCsvUpload} />
        </Button>
      </Stack>

      <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
        {t('admin_group_members')} ({group.members.length})
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t('username')}</TableCell>
              <TableCell>{t('email')}</TableCell>
              <TableCell>{t('admin_annotation')}</TableCell>
              <TableCell>{t('actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {group.members.map((member) => (
              <TableRow key={member.id}>
                <TableCell>{member.username}</TableCell>
                <TableCell>{member.email}</TableCell>
                <TableCell
                  onClick={() => {
                    setEditingAnnotation(member.id);
                    setAnnotationInput(member.annotation || '');
                  }}
                  sx={{ cursor: 'pointer', minWidth: 150 }}
                >
                  {editingAnnotation === member.id ? (
                    <TextField
                      value={annotationInput}
                      onChange={(e) => setAnnotationInput(e.target.value)}
                      onBlur={() => handleSaveAnnotation(member.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleSaveAnnotation(member.id);
                        }
                      }}
                      size="small"
                      autoFocus
                      fullWidth
                    />
                  ) : (
                    member.annotation || '-'
                  )}
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleRemoveMember(member.id)}
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {group.pending.length > 0 && (
        <>
          <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
            {t('admin_pending_members')} ({group.pending.length})
          </Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t('username')}</TableCell>
                  <TableCell>{t('admin_member_pending')}</TableCell>
                  <TableCell>{t('actions')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {group.pending.map((pending) => (
                  <TableRow key={pending.id}>
                    <TableCell>{pending.username}</TableCell>
                    <TableCell>
                      <Chip
                        label={t('admin_member_pending')}
                        color="warning"
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => handleRemovePending(pending.id)}
                      >
                        <Delete fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  );

  return (
    <>
      <Stack direction="row" alignItems="center" spacing={2}>
        {editingName ? (
          <Stack direction="row" spacing={1} alignItems="center">
            <TextField
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              size="small"
            />
            <Button onClick={handleUpdateName} variant="contained" size="small">
              {t('save')}
            </Button>
            <Button onClick={() => setEditingName(false)} size="small">
              {t('cancel')}
            </Button>
          </Stack>
        ) : (
          <Typography
            variant="h1"
            onClick={() => setEditingName(true)}
            sx={{ cursor: 'pointer' }}
          >
            {group.name}
          </Typography>
        )}
        <Chip label={group.identifier} size="small" variant="outlined" />
      </Stack>

      <Box sx={{ mt: 1, mb: 2 }}>
        {!group.source_is_open_id && (
          <ConfirmButton
            onConfirmation={handleDeleteGroup}
            buttonLabel={t('admin_delete_group')}
            description={t('admin_delete_group_confirm')}
          />
        )}
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabIndex} onChange={(_, v) => setTabIndex(v)}>
          <Tab label={t('admin_group_members')} />
          <Tab label={t('admin_group_permissions')} />
        </Tabs>
      </Box>

      {tabIndex === 0 && membersTab}
      {tabIndex === 1 && <AdminGroupPermissions groupId={group.id} />}
    </>
  );
}
