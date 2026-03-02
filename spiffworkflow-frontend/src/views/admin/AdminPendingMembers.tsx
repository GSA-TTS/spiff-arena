import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
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
import PaginationForTable from '../../components/PaginationForTable';
import { getPageInfoFromSearchParams, setPageTitle } from '../../helpers';
import { PaginationObject } from '../../interfaces';

interface PendingAssignment {
  id: number;
  username: string;
  group_id: number;
  group_identifier: string | null;
}

export default function AdminPendingMembers() {
  const [searchParams] = useSearchParams();
  const { t } = useTranslation();
  const [items, setItems] = useState<PendingAssignment[]>([]);
  const [pagination, setPagination] = useState<PaginationObject | null>(null);

  useEffect(() => {
    setPageTitle([t('admin_pending_members')]);
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    HttpService.makeCallToBackend({
      path: `/admin/pending-assignments?page=${page}&per_page=${perPage}`,
      successCallback: (result: any) => {
        setItems(result.results);
        setPagination(result.pagination);
      },
    });
  }, [searchParams, t]);

  const buildTable = () => (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{t('username')}</TableCell>
            <TableCell>{t('admin_group')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.id}>
              <TableCell>{item.username}</TableCell>
              <TableCell>
                {item.group_identifier ? (
                  <Link to={`/admin/groups/${item.group_id}`}>
                    {item.group_identifier}
                  </Link>
                ) : (
                  item.group_id
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    return (
      <>
        <Typography variant="h1">{t('admin_pending_members')}</Typography>
        {items.length > 0 ? (
          <PaginationForTable
            page={page}
            perPage={perPage}
            pagination={pagination as any}
            tableToDisplay={buildTable()}
          />
        ) : (
          <Typography sx={{ mt: 2 }}>
            {t('admin_no_pending_members')}
          </Typography>
        )}
      </>
    );
  }
  return null;
}
