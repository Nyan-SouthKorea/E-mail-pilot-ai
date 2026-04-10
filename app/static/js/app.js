(function () {
  var shellMode = 'browser_fallback';
  var nativeDialogState = 'checking';
  var detectRetryHandle = null;
  var detectRetryCount = 0;
  var maxDetectRetryCount = 30;

  function renderJobState(target, payload) {
    if (!target || !payload) return;
    var parts = [];
    parts.push('<span class="status-pill">상태: ' + (payload.status || 'unknown') + '</span>');
    if (payload.feature_id) {
      parts.push('<span class="status-pill mono">feature: ' + payload.feature_id + '</span>');
    }
    if (payload.message) {
      parts.push('<span class="status-pill">' + payload.message + '</span>');
    }
    target.innerHTML = parts.join('');
  }

  function pollJobState() {
    var target = document.querySelector('[data-job-status]');
    if (!target) return;
    fetch('/jobs/current')
      .then(function (response) { return response.json(); })
      .then(function (payload) { renderJobState(target, payload); })
      .catch(function () {
        renderJobState(target, {
          status: 'failed',
          message: '작업 상태를 읽지 못했다.',
        });
      });
  }

  function shellModeLabel(mode) {
    if (mode === 'desktop_window') return '전용 앱 창';
    if (mode === 'browser_fallback') return '로컬 브라우저 fallback';
    if (mode === 'headless') return 'headless / smoke';
    return mode || '(미확정)';
  }

  function nativeDialogLabel(state) {
    if (state === 'desktop_ready') return '사용 가능';
    if (state === 'desktop_pending' || state === 'checking') return '전용 창 연결 확인 중';
    if (state === 'browser_fallback') return '브라우저 fallback';
    if (state === 'desktop_failed') return '전용 창 연결 실패';
    return state || '(미확정)';
  }

  function nativeDialogMessage(state) {
    if (state === 'desktop_ready') {
      return '현재 환경: 앱 전용 네이티브 파일 탐색기를 사용할 수 있습니다.';
    }
    if (state === 'desktop_pending' || state === 'checking') {
      return '현재 환경: 앱 전용 창 연결 확인 중입니다.';
    }
    if (state === 'desktop_failed') {
      return '현재 환경: 전용 창 연결이 불안정합니다. 직접 경로 입력으로 진행하거나 앱을 다시 실행해 주세요.';
    }
    return '현재 환경: 브라우저 fallback이므로 직접 경로를 입력해야 합니다.';
  }

  function ensurePywebviewApi() {
    return !!(window.pywebview && window.pywebview.api);
  }

  function updatePickerButtons() {
    var ready = nativeDialogState === 'desktop_ready';
    document.querySelectorAll('[data-picker-target]').forEach(function (button) {
      if (!button.dataset.defaultLabel) {
        button.dataset.defaultLabel = button.textContent;
      }
      button.disabled = !ready;
      button.textContent = (nativeDialogState === 'desktop_pending' || nativeDialogState === 'checking')
        ? '연결 확인 중'
        : button.dataset.defaultLabel;
    });
  }

  function setNativeDialogState(state, messageOverride) {
    nativeDialogState = state;
    document.body.dataset.nativeDialogState = state;
    document.body.dataset.nativeDialog =
      state === 'desktop_ready' ? 'yes' : (
        state === 'desktop_pending' || state === 'checking' ? 'pending' : 'no'
      );

    document.querySelectorAll('[data-dialog-mode]').forEach(function (node) {
      node.textContent = messageOverride || nativeDialogMessage(state);
      node.classList.toggle('danger', state === 'browser_fallback' || state === 'desktop_failed');
    });
    document.querySelectorAll('[data-shell-mode-value]').forEach(function (node) {
      node.textContent = shellModeLabel(shellMode);
    });
    document.querySelectorAll('[data-native-dialog-state-value]').forEach(function (node) {
      node.textContent = nativeDialogLabel(state);
    });
    updatePickerButtons();
  }

  function queueNativeDialogDetection(delayMs) {
    if (shellMode !== 'desktop_window' || nativeDialogState === 'desktop_ready') return;
    if (detectRetryHandle) return;
    detectRetryHandle = window.setTimeout(function () {
      detectRetryHandle = null;
      detectNativeDialogs();
    }, delayMs || 350);
  }

  function detectNativeDialogs() {
    if (shellMode === 'browser_fallback') {
      setNativeDialogState('browser_fallback');
      return Promise.resolve(false);
    }
    if (shellMode !== 'desktop_window') {
      setNativeDialogState('desktop_failed');
      return Promise.resolve(false);
    }
    if (!ensurePywebviewApi() || !window.pywebview.api.dialog_capabilities) {
      detectRetryCount += 1;
      if (detectRetryCount >= maxDetectRetryCount) {
        setNativeDialogState(
          'desktop_failed',
          '현재 환경: 전용 창 연결이 지연되고 있습니다. 앱을 다시 실행하거나 공식 실행 파일 경로를 확인해 주세요.'
        );
        return Promise.resolve(false);
      }
      setNativeDialogState('desktop_pending');
      queueNativeDialogDetection(400);
      return Promise.resolve(false);
    }
    return window.pywebview.api.dialog_capabilities()
      .then(function (payload) {
        if (payload && payload.native_dialog) {
          setNativeDialogState('desktop_ready');
          return true;
        }
        setNativeDialogState(
          'desktop_failed',
          '현재 환경: 전용 창과 파일 탐색기 연결에 실패했습니다. 직접 경로 입력으로 진행하거나 앱을 다시 실행해 주세요.'
        );
        return false;
      })
      .catch(function () {
        detectRetryCount += 1;
        if (detectRetryCount >= maxDetectRetryCount) {
          setNativeDialogState(
            'desktop_failed',
            '현재 환경: 전용 창과 파일 탐색기 연결에 실패했습니다. 직접 경로 입력으로 진행하거나 앱을 다시 실행해 주세요.'
          );
          return false;
        }
        setNativeDialogState('desktop_pending');
        queueNativeDialogDetection(400);
        return false;
      });
  }

  function renderPathStatus(target, payload) {
    if (!target) return;
    var status = payload && payload.status ? payload.status : 'warn';
    target.className = 'field-status ' + status;
    target.textContent = payload && payload.message
      ? payload.message
      : '경로 상태를 확인하지 못했습니다.';
  }

  function inspectPathInput(input) {
    if (!input || !input.dataset.inspectKind) return;
    var target = document.getElementById(input.dataset.statusTarget || '');
    var workspaceRoot = input.dataset.workspaceRoot || document.body.dataset.workspaceRoot || '';
    var params = new URLSearchParams({
      path_text: input.value || '',
      selection_kind: input.dataset.inspectKind,
    });
    if (workspaceRoot) {
      params.set('workspace_root', workspaceRoot);
    }
    fetch('/workspace/inspect-path?' + params.toString())
      .then(function (response) { return response.json(); })
      .then(function (payload) { renderPathStatus(target, payload); })
      .catch(function () {
        renderPathStatus(target, {
          status: 'fail',
          message: '경로 검사 중 오류가 발생했습니다.',
        });
      });
  }

  function bindPathInspection() {
    document.querySelectorAll('[data-inspect-kind]').forEach(function (input) {
      input.addEventListener('change', function () { inspectPathInput(input); });
      input.addEventListener('blur', function () { inspectPathInput(input); });
      if (input.value) {
        inspectPathInput(input);
      }
    });
  }

  function openNativePicker(button) {
    var targetId = button.dataset.pickerTarget || '';
    var input = document.getElementById(targetId);
    var statusTarget = document.getElementById(button.dataset.statusTarget || '');
    var workspaceRoot = button.dataset.workspaceRoot || document.body.dataset.workspaceRoot || '';

    if (!input) return;
    if (nativeDialogState === 'desktop_pending' || nativeDialogState === 'checking') {
      detectNativeDialogs().then(function (ready) {
        if (!ready) {
          renderPathStatus(statusTarget, {
            status: 'warn',
            message: '전용 창 연결을 확인하는 중입니다. 잠시 후 다시 시도해 주세요.',
          });
        }
      });
      return;
    }
    if (nativeDialogState === 'browser_fallback') {
      renderPathStatus(statusTarget, {
        status: 'warn',
        message: '이 환경에서는 직접 경로를 입력해야 합니다. Windows 앱 전용 창에서만 파일 탐색기가 열립니다.',
      });
      return;
    }
    if (nativeDialogState === 'desktop_failed' || !ensurePywebviewApi()) {
      renderPathStatus(statusTarget, {
        status: 'warn',
        message: '전용 창 연결이 실패했습니다. 직접 경로 입력으로 진행하거나 앱을 다시 실행해 주세요.',
      });
      return;
    }

    var pickerKind = button.dataset.pickerKind || 'folder';
    var promise;
    if (pickerKind === 'file') {
      promise = window.pywebview.api.pick_file(
        input.value || '',
        workspaceRoot,
        ['Excel (*.xlsx;*.xlsm;*.xltx;*.xltm)']
      );
    } else {
      promise = window.pywebview.api.pick_folder(input.value || '', workspaceRoot);
    }

    promise
      .then(function (payload) {
        if (payload && payload.ok && payload.path) {
          input.value = payload.path;
          input.dispatchEvent(new Event('change', { bubbles: true }));
          return;
        }
        renderPathStatus(statusTarget, {
          status: 'warn',
          message: payload && payload.error ? payload.error : '경로 선택이 취소되었습니다.',
        });
      })
      .catch(function (error) {
        renderPathStatus(statusTarget, {
          status: 'fail',
          message: '파일 탐색기를 열지 못했습니다: ' + error,
        });
      });
  }

  function bindNativePickerButtons() {
    document.querySelectorAll('[data-picker-target]').forEach(function (button) {
      button.addEventListener('click', function () {
        openNativePicker(button);
      });
    });
  }

  function initializeShellContext() {
    shellMode = document.body.dataset.shellMode || 'browser_fallback';
    var initialState = document.body.dataset.nativeDialogState || 'checking';
    if (shellMode === 'browser_fallback') {
      setNativeDialogState('browser_fallback');
      return;
    }
    if (shellMode === 'headless') {
      setNativeDialogState('desktop_failed', '현재 환경: headless 실행이라 파일 탐색기를 열 수 없습니다.');
      return;
    }
    if (initialState === 'desktop_ready') {
      setNativeDialogState('desktop_ready');
      return;
    }
    if (initialState === 'desktop_failed') {
      setNativeDialogState('desktop_failed');
      return;
    }
    setNativeDialogState('desktop_pending');
    queueNativeDialogDetection(200);
  }

  function initializeUi() {
    pollJobState();
    window.setInterval(pollJobState, 2500);
    bindPathInspection();
    bindNativePickerButtons();
    initializeShellContext();
  }

  document.addEventListener('DOMContentLoaded', initializeUi);
  window.addEventListener('pywebviewready', function () {
    detectRetryCount = 0;
    detectNativeDialogs();
  });
})();
