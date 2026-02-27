import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  IconButton,
  List,
  ListItem,
  ListItemText,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { Add, Delete } from '@mui/icons-material';
import HttpService from '../services/HttpService';
import { modifyProcessIdentifierForPathParam } from '../helpers';

type PackageInfo = {
  name: string;
  version: string;
};

type OwnProps = {
  processGroupId: string;
};

export default function ProcessGroupPackages({ processGroupId }: OwnProps) {
  const { t } = useTranslation();
  const [packages, setPackages] = useState<PackageInfo[]>([]);
  const [newPackageName, setNewPackageName] = useState('');
  const [installing, setInstalling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const modifiedGroupId = modifyProcessIdentifierForPathParam(processGroupId);

  const fetchPackages = useCallback(() => {
    HttpService.makeCallToBackend({
      path: `/process-groups/${modifiedGroupId}/packages`,
      successCallback: (result: PackageInfo[]) => {
        setPackages(result);
      },
    });
  }, [modifiedGroupId]);

  useEffect(() => {
    fetchPackages();
  }, [fetchPackages]);

  const handleInstall = () => {
    const packageName = newPackageName.trim();
    if (!packageName) {
      return;
    }

    setInstalling(true);
    setError(null);

    HttpService.makeCallToBackend({
      path: `/process-groups/${modifiedGroupId}/packages`,
      httpMethod: 'POST',
      postBody: { package_name: packageName },
      successCallback: () => {
        setNewPackageName('');
        setInstalling(false);
        fetchPackages();
      },
      failureCallback: (err: any) => {
        setError(err?.message || `Failed to install '${packageName}'`);
        setInstalling(false);
      },
    });
  };

  const handleUninstall = (packageName: string) => {
    HttpService.makeCallToBackend({
      path: `/process-groups/${modifiedGroupId}/packages/${packageName}`,
      httpMethod: 'DELETE',
      successCallback: () => {
        fetchPackages();
      },
    });
  };

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 1 }}>
        {t('packages')}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 1 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 1, mb: 2, alignItems: 'center' }}>
        <TextField
          size="small"
          label={t('package_name')}
          placeholder="e.g. pandas, numpy==1.24.0"
          value={newPackageName}
          onChange={(e) => setNewPackageName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleInstall();
            }
          }}
          disabled={installing}
          sx={{ flexGrow: 1 }}
          data-testid="package-name-input"
          inputProps={{ 'data-testid': 'package-name-input-field' }}
        />
        <Button
          startIcon={installing ? <CircularProgress size={16} /> : <Add />}
          variant="contained"
          size="small"
          onClick={handleInstall}
          disabled={installing || !newPackageName.trim()}
          data-testid="install-package-button"
        >
          {installing ? t('installing') : t('install')}
        </Button>
      </Box>

      {packages.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          {t('no_packages_installed')}
        </Typography>
      ) : (
        <List dense>
          {packages.map((pkg) => (
            <ListItem
              key={pkg.name}
              data-testid={`package-list-item-${pkg.name}`}
              secondaryAction={
                <Tooltip title={t('uninstall')}>
                  <IconButton
                    size="small"
                    onClick={() => handleUninstall(pkg.name)}
                    data-testid={`uninstall-package-button-${pkg.name}`}
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                </Tooltip>
              }
            >
              <ListItemText
                primary={pkg.name}
                secondary={`v${pkg.version}`}
                primaryTypographyProps={{ fontFamily: 'monospace' }}
              />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
}
