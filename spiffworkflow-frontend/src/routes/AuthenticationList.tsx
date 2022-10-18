import { useContext, useEffect, useState } from 'react';
import { Table } from 'react-bootstrap';
import ErrorContext from '../contexts/ErrorContext';
import { AuthenticationItem } from '../interfaces';
import HttpService from '../services/HttpService';

export default function AuthenticationList() {
  const setErrorMessage = (useContext as any)(ErrorContext)[1];

  const [authenticationList, setAuthenticationList] = useState<
    AuthenticationItem[] | null
  >(null);
  const [connectProxyBaseUrl, setConnectProxyBaseUrl] = useState<string | null>(
    null
  );

  useEffect(() => {
    const processResult = (result: any) => {
      setAuthenticationList(result.results);
      setConnectProxyBaseUrl(result.connector_proxy_base_url);
    };
    HttpService.makeCallToBackend({
      path: `/authentications`,
      successCallback: processResult,
      failureCallback: setErrorMessage,
    });
  }, [setErrorMessage]);

  const buildTable = () => {
    if (authenticationList) {
      const rows = authenticationList.map((row) => {
        return (
          <tr key={row.id}>
            <td>
              <a
                data-qa="authentication-create-link"
                href={`${connectProxyBaseUrl}/v1/auths/${row.id}`}
              >
                {row.id}
              </a>
            </td>
          </tr>
        );
      });
      return (
        <Table striped bordered>
          <thead>
            <tr>
              <th>ID</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </Table>
      );
    }
    return null;
  };

  if (authenticationList) {
    return <>{buildTable()}</>;
  }

  return <main />;
}
