import { useState, useEffect, useCallback } from 'react';
import HttpService from '../services/HttpService';

export type NavigationItem = {
  task_guid: string;
  task_name: string;
  task_title: string;
  task_type: string;
  completed: boolean;
  is_current: boolean;
  has_snapshot: boolean;
};

type UseTaskNavigationResult = {
  canGoBack: boolean;
  canGoForward: boolean;
  goBack: () => Promise<string | null>;
  goForward: (formData: any) => Promise<any>;
  loading: boolean;
  navigationItems: NavigationItem[];
};

export default function useTaskNavigation(
  processInstanceId: number | undefined,
  currentTaskGuid: string | undefined,
): UseTaskNavigationResult {
  const [navigationItems, setNavigationItems] = useState<NavigationItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!processInstanceId) {
      return;
    }

    HttpService.makeCallToBackend({
      path: `/tasks/${processInstanceId}/navigation-history`,
      successCallback: (result: any) => {
        setNavigationItems(result.navigation_items || []);
      },
    });
  }, [processInstanceId, currentTaskGuid]);

  const currentIndex = navigationItems.findIndex(
    (item) => item.task_guid === currentTaskGuid,
  );

  const canGoBack = currentIndex > 0;

  // canGoForward: there are snapshots for tasks after the current position
  const canGoForward = navigationItems.some(
    (item, index) => index > currentIndex && item.has_snapshot,
  );

  const goBack = useCallback(async (): Promise<string | null> => {
    if (!canGoBack || !processInstanceId) {
      return null;
    }

    const previousItem = navigationItems[currentIndex - 1];
    if (!previousItem) {
      return null;
    }

    setLoading(true);
    return new Promise<string | null>((resolve) => {
      HttpService.makeCallToBackend({
        path: `/tasks/${processInstanceId}/navigate-back/${previousItem.task_guid}`,
        httpMethod: 'POST',
        successCallback: (result: any) => {
          setLoading(false);
          resolve(result.task_guid || null);
        },
        failureCallback: () => {
          setLoading(false);
          resolve(null);
        },
      });
    });
  }, [canGoBack, processInstanceId, navigationItems, currentIndex]);

  const goForward = useCallback(
    async (formData: any): Promise<any> => {
      if (!processInstanceId) {
        return null;
      }

      setLoading(true);
      return new Promise<any>((resolve) => {
        HttpService.makeCallToBackend({
          path: `/tasks/${processInstanceId}/navigate-forward`,
          httpMethod: 'POST',
          postBody: formData,
          successCallback: (result: any) => {
            setLoading(false);
            resolve(result);
          },
          failureCallback: () => {
            setLoading(false);
            resolve(null);
          },
        });
      });
    },
    [processInstanceId],
  );

  return {
    canGoBack,
    canGoForward,
    goBack,
    goForward,
    loading,
    navigationItems,
  };
}
