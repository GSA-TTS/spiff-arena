import { useState } from 'react';
import { useParams } from 'react-router-dom';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { ProcessModel } from '../interfaces';
import ProcessModelForm from '../components/ProcessModelForm';

export default function ProcessModelNew() {
  const params = useParams();
  const [processModel, setProcessModel] = useState<ProcessModel>({
    id: '',
    display_name: '',
    description: '',
    primary_file_name: '',
    files: [],
  });

  return (
    <>
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Process Groups', '/admin'],
          [
            `Process Group: ${params.process_group_id}`,
            `process_group:${params.process_group_id}:link`,
          ],
        ]}
      />
      <h2>Add Process Model</h2>
      <ProcessModelForm
        mode="new"
        processGroupId={params.process_group_id}
        processModel={processModel}
        setProcessModel={setProcessModel}
      />
    </>
  );
}
