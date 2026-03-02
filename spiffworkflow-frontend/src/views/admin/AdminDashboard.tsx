import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Box, Card, CardContent, Typography, Button } from '@mui/material';
import Grid from '@mui/material/Grid';
import { Groups, PendingActions } from '@mui/icons-material';
import HttpService from '../../services/HttpService';
import { setPageTitle } from '../../helpers';

export default function AdminDashboard() {
  const { t } = useTranslation();
  const [groupCount, setGroupCount] = useState<number>(0);
  const [pendingCount, setPendingCount] = useState<number>(0);

  useEffect(() => {
    setPageTitle([t('admin')]);
    HttpService.makeCallToBackend({
      path: '/admin/groups?per_page=1',
      successCallback: (result: any) => {
        setGroupCount(result.pagination.total);
      },
    });
    HttpService.makeCallToBackend({
      path: '/admin/pending-assignments?per_page=1',
      successCallback: (result: any) => {
        setPendingCount(result.pagination.total);
      },
    });
  }, [t]);

  return (
    <>
      <Typography variant="h1">{t('admin')}</Typography>
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Groups color="primary" />
                <Typography variant="h6">{t('admin_groups')}</Typography>
              </Box>
              <Typography variant="h3" sx={{ mt: 1 }}>
                {groupCount}
              </Typography>
              <Button
                component={Link}
                to="/admin/groups"
                variant="outlined"
                size="small"
                sx={{ mt: 1 }}
              >
                {t('admin_manage_groups')}
              </Button>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PendingActions color="warning" />
                <Typography variant="h6">
                  {t('admin_pending_members')}
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ mt: 1 }}>
                {pendingCount}
              </Typography>
              <Button
                component={Link}
                to="/admin/pending"
                variant="outlined"
                size="small"
                sx={{ mt: 1 }}
              >
                {t('admin_view_pending')}
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </>
  );
}
