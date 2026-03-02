import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Chip,
} from '@mui/material';
import HttpService from '../../services/HttpService';
import PaginationForTable from '../../components/PaginationForTable';
import { getPageInfoFromSearchParams, setPageTitle } from '../../helpers';
import { AdminGroup, PaginationObject } from '../../interfaces';

export default function AdminGroupList() {
  const [searchParams] = useSearchParams();
  const { t } = useTranslation();
  const [groups, setGroups] = useState<AdminGroup[]>([]);
  const [pagination, setPagination] = useState<PaginationObject | null>(null);

  useEffect(() => {
    setPageTitle([t('admin_groups')]);
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    HttpService.makeCallToBackend({
      path: `/admin/groups?page=${page}&per_page=${perPage}`,
      successCallback: (result: any) => {
        setGroups(result.results);
        setPagination(result.pagination);
      },
    });
  }, [searchParams, t]);

  const buildTable = () => {
    const rows = groups.map((group: AdminGroup) => (
      <TableRow key={group.id}>
        <TableCell>
          <Link to={`/admin/groups/${group.id}`}>{group.identifier}</Link>
        </TableCell>
        <TableCell>{group.name}</TableCell>
        <TableCell>{group.member_count}</TableCell>
        <TableCell>
          {group.pending_count > 0 ? (
            <Chip label={group.pending_count} color="warning" size="small" />
          ) : (
            0
          )}
        </TableCell>
        <TableCell>
          {group.source_is_open_id ? (
            <Chip label="OpenID" size="small" />
          ) : null}
        </TableCell>
      </TableRow>
    ));
    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('identifier')}</TableCell>
              <TableCell>{t('name')}</TableCell>
              <TableCell>{t('admin_group_members')}</TableCell>
              <TableCell>{t('admin_pending_members')}</TableCell>
              <TableCell>{t('source')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>{rows}</TableBody>
        </Table>
      </TableContainer>
    );
  };

  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    return (
      <>
        <Typography variant="h1">{t('admin_groups')}</Typography>
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination as any}
          tableToDisplay={buildTable()}
        />
        <Button
          component={Link}
          to="/admin/groups/new"
          variant="contained"
          sx={{ mt: 2 }}
        >
          {t('admin_group_new')}
        </Button>
      </>
    );
  }
  return null;
}
