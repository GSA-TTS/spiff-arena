import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Paper,
} from '@mui/material';
import HttpService from '../../services/HttpService';
import UserSearch from '../../components/UserSearch';
import { User } from '../../interfaces';
import { setPageTitle } from '../../helpers';

interface HumanTaskOwner {
  id: number;
  username: string;
}

interface LaneGroup {
  id: number;
  identifier: string;
}

interface AdminHumanTask {
  id: number;
  task_guid: string;
  task_name: string;
  task_title: string | null;
  task_type: string;
  task_status: string;
  completed: boolean;
  lane_name: string | null;
  lane_group: LaneGroup | null;
  potential_owners: HumanTaskOwner[];
  completed_by: HumanTaskOwner | null;
}

interface ProcessInstanceInfo {
  id: number;
  status: string;
  process_model_identifier: string;
  process_model_display_name: string;
}

interface GroupOption {
  id: number;
  identifier: string;
}

export default function AdminProcessInstanceTasks() {
  const params = useParams();
  const { t } = useTranslation();
  const [tasks, setTasks] = useState<AdminHumanTask[]>([]);
  const [processInstance, setProcessInstance] =
    useState<ProcessInstanceInfo | null>(null);
  const [reassignDialogTask, setReassignDialogTask] =
    useState<AdminHumanTask | null>(null);
  const [selectedUsers, setSelectedUsers] = useState<User[]>([]);
  const [replaceOwners, setReplaceOwners] = useState(true);
  const [laneDialogTask, setLaneDialogTask] = useState<AdminHumanTask | null>(
    null,
  );
  const [groups, setGroups] = useState<GroupOption[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<number | ''>('');
  const [applyToAllInLane, setApplyToAllInLane] = useState(false);

  const loadTasks = useCallback(() => {
    HttpService.makeCallToBackend({
      path: `/admin/process-instances/${params.process_instance_id}/tasks`,
      successCallback: (result: any) => {
        setTasks(result.results);
        setProcessInstance(result.process_instance);
      },
    });
  }, [params.process_instance_id]);

  useEffect(() => {
    loadTasks();
    HttpService.makeCallToBackend({
      path: '/admin/groups?per_page=1000',
      successCallback: (result: any) => {
        setGroups(
          result.results.map((g: any) => ({
            id: g.id,
            identifier: g.identifier,
          })),
        );
      },
    });
  }, [loadTasks]);

  useEffect(() => {
    if (processInstance) {
      setPageTitle([
        t('admin'),
        t('admin_manage_tasks'),
        `#${processInstance.id}`,
      ]);
    }
  }, [processInstance, t]);

  const handleReassign = () => {
    if (!reassignDialogTask || selectedUsers.length === 0) {
      return;
    }
    const endpoint = replaceOwners ? 'reassign' : 'add-owners';
    HttpService.makeCallToBackend({
      path: `/admin/tasks/${reassignDialogTask.id}/${endpoint}`,
      httpMethod: 'PUT',
      postBody: { user_ids: selectedUsers.map((u) => u.id) },
      successCallback: () => {
        setReassignDialogTask(null);
        setSelectedUsers([]);
        loadTasks();
      },
    });
  };

  const handleLaneReassign = () => {
    if (!laneDialogTask || !selectedGroupId) {
      return;
    }

    if (applyToAllInLane && laneDialogTask.lane_name) {
      HttpService.makeCallToBackend({
        path: `/admin/process-instances/${params.process_instance_id}/lane-reassign`,
        httpMethod: 'PUT',
        postBody: {
          lane_name: laneDialogTask.lane_name,
          group_id: selectedGroupId,
        },
        successCallback: () => {
          setLaneDialogTask(null);
          loadTasks();
        },
      });
    } else {
      HttpService.makeCallToBackend({
        path: `/admin/tasks/${laneDialogTask.id}/lane-reassign`,
        httpMethod: 'PUT',
        postBody: { group_id: selectedGroupId },
        successCallback: () => {
          setLaneDialogTask(null);
          loadTasks();
        },
      });
    }
  };

  if (!processInstance) {
    return null;
  }

  return (
    <>
      <Typography variant="h1">{t('admin_manage_tasks')}</Typography>
      <Box sx={{ mb: 2 }}>
        <Typography variant="body1">
          {t('admin_process_instance')}: #{processInstance.id} -{' '}
          {processInstance.process_model_display_name}
        </Typography>
        <Chip label={processInstance.status} size="small" sx={{ mt: 0.5 }} />
      </Box>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t('admin_task_name')}</TableCell>
              <TableCell>{t('admin_lane')}</TableCell>
              <TableCell>{t('status')}</TableCell>
              <TableCell>{t('admin_potential_owners')}</TableCell>
              <TableCell>{t('admin_completed_by')}</TableCell>
              <TableCell>{t('actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map((task) => (
              <TableRow key={task.id}>
                <TableCell>{task.task_title || task.task_name}</TableCell>
                <TableCell>
                  {task.lane_name && (
                    <Stack direction="row" spacing={0.5} alignItems="center">
                      <span>{task.lane_name}</span>
                      {task.lane_group && (
                        <Chip
                          label={task.lane_group.identifier}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Stack>
                  )}
                </TableCell>
                <TableCell>
                  <Chip
                    label={task.completed ? 'completed' : task.task_status}
                    color={task.completed ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {task.potential_owners.map((o) => o.username).join(', ')}
                </TableCell>
                <TableCell>
                  {task.completed_by ? task.completed_by.username : '-'}
                </TableCell>
                <TableCell>
                  {!task.completed && (
                    <Stack direction="row" spacing={1}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => setReassignDialogTask(task)}
                      >
                        {t('admin_reassign')}
                      </Button>
                      {task.lane_name && (
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => {
                            setLaneDialogTask(task);
                            setSelectedGroupId(
                              task.lane_group ? task.lane_group.id : '',
                            );
                          }}
                        >
                          {t('admin_change_lane')}
                        </Button>
                      )}
                    </Stack>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog
        open={!!reassignDialogTask}
        onClose={() => setReassignDialogTask(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{t('admin_reassign')}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 1 }}>
            <UserSearch
              onSelectedUser={(user: User | null) => {
                if (user) {
                  setSelectedUsers((prev) => [...prev, user]);
                }
              }}
              label={t('admin_search_user')}
            />
            {selectedUsers.length > 0 && (
              <Box sx={{ mt: 1 }}>
                {selectedUsers.map((u) => (
                  <Chip
                    key={u.id}
                    label={u.username}
                    onDelete={() =>
                      setSelectedUsers((prev) =>
                        prev.filter((p) => p.id !== u.id),
                      )
                    }
                    sx={{ mr: 0.5, mb: 0.5 }}
                  />
                ))}
              </Box>
            )}
            <FormControlLabel
              control={
                <Checkbox
                  checked={replaceOwners}
                  onChange={(e) => setReplaceOwners(e.target.checked)}
                />
              }
              label={t('admin_replace_owners')}
              sx={{ mt: 1 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReassignDialogTask(null)}>
            {t('cancel')}
          </Button>
          <Button variant="contained" onClick={handleReassign}>
            {t('admin_reassign')}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={!!laneDialogTask}
        onClose={() => setLaneDialogTask(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{t('admin_change_lane')}</DialogTitle>
        <DialogContent>
          <FormControl fullWidth size="small" sx={{ mt: 1 }}>
            <InputLabel>{t('admin_select_group')}</InputLabel>
            <Select
              value={selectedGroupId}
              label={t('admin_select_group')}
              onChange={(e) => setSelectedGroupId(e.target.value as number)}
            >
              {groups.map((g) => (
                <MenuItem key={g.id} value={g.id}>
                  {g.identifier}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {laneDialogTask?.lane_name && (
            <FormControlLabel
              control={
                <Checkbox
                  checked={applyToAllInLane}
                  onChange={(e) => setApplyToAllInLane(e.target.checked)}
                />
              }
              label={t('admin_apply_to_all_in_lane')}
              sx={{ mt: 1 }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLaneDialogTask(null)}>{t('cancel')}</Button>
          <Button variant="contained" onClick={handleLaneReassign}>
            {t('admin_change_lane')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
