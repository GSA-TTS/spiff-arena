import { useState, useCallback, useRef } from 'react';

type ScriptSlot = 'pre' | 'post' | 'script';

interface CodeModuleFunction {
  elementId: string;
  type: ScriptSlot;
  name: string;
  docstring: string;
  body: string;
}

export interface UseCodeModuleManagerReturn {
  codeModuleContent: string;
  isDirty: boolean;
  onTaskAdded: (elementId: string, elementType: string) => void;
  onTaskRemoved: (elementId: string) => void;
  onTaskTypeChanged: (
    elementId: string,
    oldType: string,
    newType: string,
  ) => void;
  loadContent: (content: string) => void;
  setRawContent: (content: string) => void;
  markSaved: () => void;
  reconcile: (tasks: { id: string; type: string }[]) => void;
}

const SCRIPT_TASK_TYPE = 'bpmn:ScriptTask';

const TASK_TYPES_WITH_SCRIPTS = new Set([
  'bpmn:Task',
  'bpmn:UserTask',
  'bpmn:ManualTask',
  SCRIPT_TASK_TYPE,
  'bpmn:ServiceTask',
  'bpmn:SendTask',
  'bpmn:ReceiveTask',
  'bpmn:BusinessRuleTask',
  'bpmn:CallActivity',
  'bpmn:SubProcess',
]);

// Matches managed function definitions like: def Activity_0qpzdpu_pre(
const MANAGED_FUNC_PATTERN = /^def (\w+)_(pre|post|script)\(\s*\):\s*$/;

function isTaskType(elementType: string): boolean {
  return TASK_TYPES_WITH_SCRIPTS.has(elementType);
}

function createFunctionStub(
  elementId: string,
  type: 'pre' | 'post' | 'script',
): CodeModuleFunction {
  const name = `${elementId}_${type}`;
  const typeLabel =
    type === 'script'
      ? 'Main script'
      : `${type.charAt(0).toUpperCase() + type.slice(1)}-script`;
  return {
    elementId,
    type,
    name,
    docstring: `"""${typeLabel} for ${elementId}."""`,
    body: '    pass',
  };
}

function renderFunction(fn: CodeModuleFunction): string {
  return `def ${fn.name}():\n    ${fn.docstring}\n${fn.body}`;
}

function renderContent(
  header: string,
  functions: CodeModuleFunction[],
): string {
  const parts: string[] = [];
  if (header.trim()) {
    parts.push(header.trimEnd());
  }
  for (const fn of functions) {
    parts.push(renderFunction(fn));
  }
  if (parts.length === 0) {
    return '';
  }
  return `${parts.join('\n\n\n')}\n`;
}

/**
 * Parse a Python code module into header + managed functions.
 * Functions matching `def {id}_{pre|post|script}():` are "managed".
 * Everything else is preserved in the header.
 */
function parseContent(content: string): {
  header: string;
  functions: CodeModuleFunction[];
} {
  if (!content.trim()) {
    return { header: '', functions: [] };
  }

  const lines = content.split('\n');
  const functions: CodeModuleFunction[] = [];
  const headerLines: string[] = [];
  let i = 0;

  while (i < lines.length) {
    const match = lines[i].match(MANAGED_FUNC_PATTERN);
    if (match) {
      const elementId = match[1];
      const type = match[2] as 'pre' | 'post' | 'script';
      const name = `${elementId}_${type}`;
      i += 1; // move past def line

      // Collect docstring
      let docstring = '';
      if (i < lines.length && lines[i].trim().startsWith('"""')) {
        const docLine = lines[i].trim();
        if (docLine.endsWith('"""') && docLine.length > 3) {
          // Single-line docstring
          docstring = lines[i].trimStart();
          i += 1;
        } else {
          // Multi-line docstring
          const docLines = [lines[i]];
          i += 1;
          while (i < lines.length && !lines[i].trim().endsWith('"""')) {
            docLines.push(lines[i]);
            i += 1;
          }
          if (i < lines.length) {
            docLines.push(lines[i]);
            i += 1;
          }
          docstring = docLines.map((l) => l.trimStart()).join('\n');
        }
      }

      // Collect body (indented lines until next def or blank line followed by non-indented)
      const bodyLines: string[] = [];
      while (i < lines.length) {
        const line = lines[i];
        // Stop at next function definition or end of indented block
        if (
          line.match(/^def \w/) ||
          (line.trim() === '' &&
            i + 1 < lines.length &&
            lines[i + 1].match(/^def \w/))
        ) {
          // Skip trailing blank lines
          break;
        }
        if (
          line.trim() === '' &&
          i + 1 < lines.length &&
          !lines[i + 1].startsWith(' ') &&
          !lines[i + 1].startsWith('\t') &&
          lines[i + 1].trim() !== ''
        ) {
          break;
        }
        bodyLines.push(line);
        i += 1;
      }

      // Skip trailing blank lines between functions
      while (i < lines.length && lines[i].trim() === '') {
        i += 1;
      }

      const body = bodyLines.length > 0 ? bodyLines.join('\n') : '    pass';

      functions.push({
        elementId,
        type,
        name,
        docstring:
          docstring ||
          `"""${type.charAt(0).toUpperCase() + type.slice(1)}-script for ${elementId}."""`,
        body: body.trimEnd() || '    pass',
      });
    } else {
      headerLines.push(lines[i]);
      i += 1;
    }
  }

  // Trim trailing blank lines from header
  while (
    headerLines.length > 0 &&
    headerLines[headerLines.length - 1].trim() === ''
  ) {
    headerLines.pop();
  }

  return {
    header: headerLines.join('\n'),
    functions,
  };
}

export function useCodeModuleManager(): UseCodeModuleManagerReturn {
  const [header, setHeader] = useState('');
  const [functions, setFunctions] = useState<CodeModuleFunction[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const loadedRef = useRef(false);

  const codeModuleContent = renderContent(header, functions);

  const loadContent = useCallback((content: string) => {
    const parsed = parseContent(content);
    setHeader(parsed.header);
    setFunctions(parsed.functions);
    setIsDirty(false);
    loadedRef.current = true;
  }, []);

  const setRawContent = useCallback((content: string) => {
    const parsed = parseContent(content);
    setHeader(parsed.header);
    setFunctions(parsed.functions);
    setIsDirty(true);
  }, []);

  const markSaved = useCallback(() => {
    setIsDirty(false);
  }, []);

  const onTaskAdded = useCallback((elementId: string, elementType: string) => {
    if (!isTaskType(elementType)) {
      return;
    }

    setFunctions((prev) => {
      const existingIds = new Set(prev.map((f) => `${f.elementId}_${f.type}`));
      const newFunctions: CodeModuleFunction[] = [];

      if (!existingIds.has(`${elementId}_pre`)) {
        newFunctions.push(createFunctionStub(elementId, 'pre'));
      }
      if (!existingIds.has(`${elementId}_post`)) {
        newFunctions.push(createFunctionStub(elementId, 'post'));
      }
      if (
        elementType === SCRIPT_TASK_TYPE &&
        !existingIds.has(`${elementId}_script`)
      ) {
        newFunctions.push(createFunctionStub(elementId, 'script'));
      }

      if (newFunctions.length === 0) {
        return prev;
      }
      return [...prev, ...newFunctions];
    });
    setIsDirty(true);
  }, []);

  const onTaskRemoved = useCallback((elementId: string) => {
    setFunctions((prev) => {
      const filtered = prev.filter((f) => f.elementId !== elementId);
      if (filtered.length === prev.length) {
        return prev;
      }
      return filtered;
    });
    setIsDirty(true);
  }, []);

  const onTaskTypeChanged = useCallback(
    (elementId: string, oldType: string, newType: string) => {
      setFunctions((prev) => {
        const updated = [...prev];
        let changed = false;

        if (oldType !== SCRIPT_TASK_TYPE && newType === SCRIPT_TASK_TYPE) {
          // Add script function stub
          if (
            !updated.some(
              (f) => f.elementId === elementId && f.type === 'script',
            )
          ) {
            // Insert after the pre function for this element, or at the end
            const preIdx = updated.findIndex(
              (f) => f.elementId === elementId && f.type === 'pre',
            );
            const insertIdx = preIdx >= 0 ? preIdx + 1 : updated.length;
            updated.splice(
              insertIdx,
              0,
              createFunctionStub(elementId, 'script'),
            );
            changed = true;
          }
        } else if (
          oldType === SCRIPT_TASK_TYPE &&
          newType !== SCRIPT_TASK_TYPE
        ) {
          // Remove script function stub
          const scriptIdx = updated.findIndex(
            (f) => f.elementId === elementId && f.type === 'script',
          );
          if (scriptIdx >= 0) {
            updated.splice(scriptIdx, 1);
            changed = true;
          }
        }

        if (!changed) {
          return prev;
        }
        return updated;
      });
      setIsDirty(true);
    },
    [],
  );

  const reconcile = useCallback((tasks: { id: string; type: string }[]) => {
    setFunctions((prev) => {
      const updated = [...prev];
      let changed = false;
      const existingIds = new Set(
        updated.map((f) => `${f.elementId}_${f.type}`),
      );
      const taskIdSet = new Set(tasks.map((t) => t.id));

      // Add missing stubs for tasks in BPMN
      for (const task of tasks) {
        if (!isTaskType(task.type)) {
          continue;
        }

        if (!existingIds.has(`${task.id}_pre`)) {
          updated.push(createFunctionStub(task.id, 'pre'));
          changed = true;
        }
        if (!existingIds.has(`${task.id}_post`)) {
          updated.push(createFunctionStub(task.id, 'post'));
          changed = true;
        }
        if (
          task.type === 'bpmn:ScriptTask' &&
          !existingIds.has(`${task.id}_script`)
        ) {
          updated.push(createFunctionStub(task.id, 'script'));
          changed = true;
        }
      }

      // Remove orphaned functions (element no longer in BPMN)
      const beforeLen = updated.length;
      const filtered = updated.filter((f) => taskIdSet.has(f.elementId));
      if (filtered.length !== beforeLen) {
        changed = true;
      }

      if (!changed) {
        return prev;
      }
      return filtered.length !== beforeLen ? filtered : updated;
    });
    setIsDirty(true);
  }, []);

  return {
    codeModuleContent,
    isDirty,
    onTaskAdded,
    onTaskRemoved,
    onTaskTypeChanged,
    loadContent,
    setRawContent,
    markSaved,
    reconcile,
  };
}
