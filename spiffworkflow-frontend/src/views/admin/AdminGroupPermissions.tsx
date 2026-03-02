import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Button,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Radio,
  RadioGroup,
  FormControlLabel,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Paper,
} from '@mui/material';
import { Delete } from '@mui/icons-material';
import HttpService from '../../services/HttpService';

interface PermissionAssignment {
  id: number;
  permission: string;
  grant_type: string;
  target_uri: string;
}

interface ProcessGroupOption {
  id: string;
  display_name: string;
}

type OwnProps = {
  groupId: number;
};

export default function AdminGroupPermissions({ groupId }: OwnProps) {
  const { t } = useTranslation();
  const [permissions, setPermissions] = useState<PermissionAssignment[]>([]);
  const [newPermission, setNewPermission] = useState('read');
  const [newTargetUri, setNewTargetUri] = useState('');
  const [newGrantType, setNewGrantType] = useState('permit');
  const [processGroups, setProcessGroups] = useState<ProcessGroupOption[]>([]);
  const [selectedPg, setSelectedPg] = useState('');
  const [selectedRole, setSelectedRole] = useState('user');

  const loadPermissions = useCallback(() => {
    HttpService.makeCallToBackend({
      path: `/admin/groups/${groupId}/permissions`,
      successCallback: (result: any) => {
        setPermissions(result.results);
      },
    });
  }, [groupId]);

  useEffect(() => {
    loadPermissions();
    HttpService.makeCallToBackend({
      path: '/admin/process-groups-for-permissions',
      successCallback: (result: any) => {
        setProcessGroups(result.results);
      },
    });
  }, [loadPermissions]);

  const handleAddPermission = () => {
    if (!newTargetUri.trim()) {
      return;
    }
    HttpService.makeCallToBackend({
      path: `/admin/groups/${groupId}/permissions`,
      httpMethod: 'POST',
      postBody: {
        permission: newPermission,
        target_uri: newTargetUri,
        grant_type: newGrantType,
      },
      successCallback: () => {
        setNewTargetUri('');
        loadPermissions();
      },
    });
  };

  const handleDeletePermission = (permissionId: number) => {
    HttpService.makeCallToBackend({
      path: `/admin/groups/${groupId}/permissions/${permissionId}`,
      httpMethod: 'DELETE',
      successCallback: () => loadPermissions(),
    });
  };

  const handleApplyPreset = () => {
    if (!selectedPg) {
      return;
    }
    HttpService.makeCallToBackend({
      path: `/admin/groups/${groupId}/role-preset`,
      httpMethod: 'POST',
      postBody: {
        process_group_identifier: selectedPg,
        role: selectedRole,
      },
      successCallback: () => loadPermissions(),
    });
  };

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>
        {t('admin_quick_associate')}
      </Typography>
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>{t('admin_process_group')}</InputLabel>
          <Select
            value={selectedPg}
            label={t('admin_process_group')}
            onChange={(e) => setSelectedPg(e.target.value)}
          >
            {processGroups.map((pg) => (
              <MenuItem key={pg.id} value={pg.id}>
                {pg.display_name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <RadioGroup
          row
          value={selectedRole}
          onChange={(e) => setSelectedRole(e.target.value)}
        >
          <FormControlLabel
            value="user"
            control={<Radio />}
            label={t('admin_role_user')}
          />
          <FormControlLabel
            value="admin"
            control={<Radio />}
            label={t('admin_role_admin')}
          />
        </RadioGroup>
        <Button variant="contained" size="small" onClick={handleApplyPreset}>
          {t('admin_apply_preset')}
        </Button>
      </Stack>

      <Typography variant="h6" sx={{ mb: 1 }}>
        {t('admin_add_permission')}
      </Typography>
      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>{t('admin_permission_action')}</InputLabel>
          <Select
            value={newPermission}
            label={t('admin_permission_action')}
            onChange={(e) => setNewPermission(e.target.value)}
          >
            <MenuItem value="create">create</MenuItem>
            <MenuItem value="read">read</MenuItem>
            <MenuItem value="update">update</MenuItem>
            <MenuItem value="delete">delete</MenuItem>
          </Select>
        </FormControl>
        <TextField
          label={t('admin_target_uri')}
          value={newTargetUri}
          onChange={(e) => setNewTargetUri(e.target.value)}
          size="small"
          sx={{ minWidth: 250 }}
        />
        <FormControl size="small" sx={{ minWidth: 100 }}>
          <InputLabel>{t('admin_grant_type')}</InputLabel>
          <Select
            value={newGrantType}
            label={t('admin_grant_type')}
            onChange={(e) => setNewGrantType(e.target.value)}
          >
            <MenuItem value="permit">permit</MenuItem>
            <MenuItem value="deny">deny</MenuItem>
          </Select>
        </FormControl>
        <Button variant="outlined" size="small" onClick={handleAddPermission}>
          {t('add_button')}
        </Button>
      </Stack>

      <Typography variant="h6" sx={{ mb: 1 }}>
        {t('admin_current_permissions')}
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t('admin_target_uri')}</TableCell>
              <TableCell>{t('admin_permission_action')}</TableCell>
              <TableCell>{t('admin_grant_type')}</TableCell>
              <TableCell>{t('actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {permissions.map((perm) => (
              <TableRow key={perm.id}>
                <TableCell>{perm.target_uri}</TableCell>
                <TableCell>{perm.permission}</TableCell>
                <TableCell>{perm.grant_type}</TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleDeletePermission(perm.id)}
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
