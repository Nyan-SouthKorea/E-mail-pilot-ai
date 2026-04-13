(function () {
  var shellMode = 'browser_fallback';
  var nativeDialogState = 'checking';
  var detectRetryHandle = null;
  var detectRetryCount = 0;
  var maxDetectRetryCount = 20;
  var tooltipEl = null;
  var tooltipPinned = false;
  var tooltipOwner = null;

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function shellModeLabel(mode) {
    if (mode === 'desktop_window') return '전용 앱 창';
    if (mode === 'browser_fallback') return '브라우저 fallback';
    if (mode === 'headless') return 'headless / smoke';
    return mode || '(미확정)';
  }

  function nativeDialogLabel(state) {
    if (state === 'desktop_ready') return '사용 가능';
    if (state === 'desktop_pending' || state === 'checking') return '연결 확인 중';
    if (state === 'browser_fallback') return '수동 입력 필요';
    if (state === 'desktop_failed') return '연결 실패';
    return state || '(미확정)';
  }

  function jobStatusLabel(status) {
    if (status === 'running') return '진행 중';
    if (status === 'completed') return '완료';
    if (status === 'failed') return '실패';
    if (status === 'partial_success') return '부분 완료';
    if (status === 'idle') return '대기 중';
    if (status === 'no_workspace') return '세이브 미열림';
    return status || '대기 중';
  }

  function nativeDialogMessage(state) {
    if (state === 'desktop_ready') {
      return '전용 창의 파일 탐색기를 바로 사용할 수 있습니다.';
    }
    if (state === 'desktop_pending' || state === 'checking') {
      return '전용 창 연결을 확인하는 중입니다. 찾아보기를 누르면 바로 다시 시도합니다.';
    }
    if (state === 'desktop_failed') {
      return '전용 창 연결이 불안정합니다. 다시 시도하거나 경로를 직접 입력해 주세요.';
    }
    return '이 환경에서는 파일 탐색기를 열 수 없어 경로를 직접 입력해야 합니다.';
  }

  function getPywebviewApi() {
    if (!window.pywebview || !window.pywebview.api) return null;
    return window.pywebview.api;
  }

  function hasReadyPywebviewBridge() {
    var api = getPywebviewApi();
    return !!(
      api &&
      typeof api.dialog_capabilities === 'function' &&
      typeof api.pick_folder === 'function' &&
      typeof api.pick_file === 'function'
    );
  }

  function getTooltipElement() {
    if (tooltipEl) return tooltipEl;
    tooltipEl = document.createElement('div');
    tooltipEl.className = 'tooltip-popover';
    tooltipEl.hidden = true;
    document.body.appendChild(tooltipEl);
    return tooltipEl;
  }

  function positionTooltip(target) {
    var tooltip = getTooltipElement();
    var rect = target.getBoundingClientRect();
    tooltip.style.left = Math.max(12, rect.left + window.scrollX) + 'px';
    tooltip.style.top = (rect.bottom + window.scrollY + 10) + 'px';
  }

  function showTooltip(target, text) {
    if (!text) return;
    var tooltip = getTooltipElement();
    tooltip.innerHTML = escapeHtml(text);
    tooltip.hidden = false;
    tooltipOwner = target;
    positionTooltip(target);
  }

  function hideTooltip(force) {
    if (tooltipPinned && !force) return;
    if (!tooltipEl) return;
    tooltipEl.hidden = true;
    tooltipPinned = false;
    tooltipOwner = null;
  }

  function bindTooltips() {
    document.querySelectorAll('[data-tooltip]').forEach(function (node) {
      if (node.dataset.tooltipBound === 'yes') return;
      node.dataset.tooltipBound = 'yes';
      var text = node.getAttribute('data-tooltip') || '';
      node.addEventListener('mouseenter', function () {
        tooltipPinned = false;
        showTooltip(node, text);
      });
      node.addEventListener('mouseleave', function () {
        hideTooltip(false);
      });
      node.addEventListener('focus', function () {
        tooltipPinned = false;
        showTooltip(node, text);
      });
      node.addEventListener('blur', function () {
        hideTooltip(false);
      });
      node.addEventListener('click', function (event) {
        if (tooltipOwner === node && !tooltipEl.hidden) {
          tooltipPinned = !tooltipPinned;
          if (!tooltipPinned) {
            hideTooltip(true);
          }
        } else {
          tooltipPinned = true;
          showTooltip(node, text);
        }
        if (node.tagName === 'BUTTON' && node.type === 'button') {
          event.preventDefault();
        }
        event.stopPropagation();
      });
    });

    document.addEventListener('click', function (event) {
      if (!tooltipEl || tooltipEl.hidden) return;
      if (tooltipOwner && (tooltipOwner === event.target || tooltipOwner.contains(event.target))) {
        return;
      }
      if (tooltipEl.contains(event.target)) return;
      hideTooltip(true);
    });
    window.addEventListener('resize', function () {
      if (tooltipOwner && tooltipEl && !tooltipEl.hidden) {
        positionTooltip(tooltipOwner);
      }
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
          message: '경로 상태를 확인하지 못했습니다.',
        });
      });
  }

  function bindPathInspection() {
    document.querySelectorAll('[data-inspect-kind]').forEach(function (input) {
      input.addEventListener('change', function () { inspectPathInput(input); });
      input.addEventListener('blur', function () { inspectPathInput(input); });
      if (input.value) inspectPathInput(input);
    });
  }

  function updateSaveFolderPreview() {
    var parentInput = document.getElementById('save_parent_dir');
    var labelInput = document.getElementById('workspace_label');
    var target = document.querySelector('[data-save-folder-preview]');
    if (!parentInput || !labelInput || !target) return;

    var now = new Date();
    var yy = String(now.getFullYear()).slice(-2);
    var mm = String(now.getMonth() + 1).padStart(2, '0');
    var dd = String(now.getDate()).padStart(2, '0');
    var hh = String(now.getHours()).padStart(2, '0');
    var mi = String(now.getMinutes()).padStart(2, '0');
    var label = (labelInput.value || '새 세이브').replace(/[<>:"/\\|?*]/g, ' ').replace(/\s+/g, ' ').trim();
    var folderName = yy + mm + dd + '_' + hh + mi + '_' + (label || '새 세이브');
    target.textContent = '만들어질 세이브 파일 폴더: ' + (parentInput.value || '') + (parentInput.value ? '\\' : '') + folderName;
  }

  function bindSaveFolderPreview() {
    ['save_parent_dir', 'workspace_label'].forEach(function (id) {
      var input = document.getElementById(id);
      if (!input) return;
      input.addEventListener('input', updateSaveFolderPreview);
      input.addEventListener('change', updateSaveFolderPreview);
    });
    updateSaveFolderPreview();
  }

  function bindWizardTabs() {
    var buttons = Array.prototype.slice.call(document.querySelectorAll('[data-wizard-tab]'));
    if (!buttons.length) return;

    function selectWizardTab(tabName) {
      buttons.forEach(function (button) {
        var active = button.dataset.wizardTab === tabName;
        button.classList.toggle('active', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      document.querySelectorAll('[data-wizard-panel]').forEach(function (panel) {
        var active = panel.dataset.wizardPanel === tabName;
        panel.classList.toggle('active', active);
        panel.hidden = !active;
      });
    }

    buttons.forEach(function (button) {
      button.addEventListener('click', function () {
        selectWizardTab(button.dataset.wizardTab || 'open');
      });
    });
  }

  function bindModalButtons() {
    document.querySelectorAll('[data-open-modal]').forEach(function (button) {
      button.addEventListener('click', function () {
        var modal = document.getElementById(button.dataset.openModal || '');
        if (modal && modal.showModal) modal.showModal();
      });
    });
  }

  function openAutoModal() {
    var modalId = document.body.dataset.autoOpenModal || '';
    if (!modalId) return;
    var modal = document.getElementById(modalId);
    if (modal && modal.showModal) modal.showModal();
  }

  function updatePickerButtons() {
    var disableButtons = shellMode === 'headless';
    document.querySelectorAll('[data-picker-target]').forEach(function (button) {
      button.disabled = disableButtons;
      button.classList.toggle('disabled', disableButtons);
      button.setAttribute(
        'data-tooltip',
        disableButtons
          ? 'headless 실행이라 파일 탐색기를 열 수 없습니다.'
          : '파일 탐색기에서 직접 선택합니다.'
      );
    });
    bindTooltips();
  }

  function setNativeDialogState(state, messageOverride) {
    nativeDialogState = state;
    document.body.dataset.nativeDialogState = state;
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
    }, delayMs || 300);
  }

  function detectNativeDialogs() {
    if (shellMode === 'headless') {
      setNativeDialogState('desktop_failed');
      return Promise.resolve(false);
    }
    if (hasReadyPywebviewBridge()) {
      return getPywebviewApi().dialog_capabilities()
        .then(function (payload) {
          if (payload && payload.native_dialog_supported) {
            setNativeDialogState('desktop_ready');
            return true;
          }
          setNativeDialogState(
            'desktop_failed',
            (payload && payload.message) || '전용 창 연결은 되었지만 파일 탐색기를 열 수 없습니다.'
          );
          return false;
        })
        .catch(function () {
          setNativeDialogState('desktop_pending', '전용 창 연결을 다시 확인하고 있습니다.');
          queueNativeDialogDetection(300);
          return false;
        });
    }
    return fetch('/diagnostics/picker-bridge')
      .then(function (response) { return response.json(); })
      .then(function (payload) {
        if (payload && payload.native_dialog_supported) {
          setNativeDialogState('desktop_ready');
          return true;
        }
        detectRetryCount += 1;
        setNativeDialogState(
          'desktop_failed',
          (payload && payload.message) || '파일 탐색기를 열 수 없는 환경입니다. 경로를 직접 입력해 주세요.'
        );
        return false;
      })
      .catch(function () {
        detectRetryCount += 1;
        if (detectRetryCount >= maxDetectRetryCount) {
          setNativeDialogState('desktop_failed', '파일 탐색기 연결을 확인하지 못했습니다. 다시 시도하거나 경로를 직접 입력해 주세요.');
          return false;
        }
        setNativeDialogState('desktop_pending', '파일 탐색기 연결을 다시 확인하고 있습니다.');
        queueNativeDialogDetection(300);
        return false;
      });
  }

  function openNativePicker(button) {
    var targetId = button.dataset.pickerTarget || '';
    var input = document.getElementById(targetId);
    var statusTarget = document.getElementById(button.dataset.statusTarget || '');
    var workspaceRoot = button.dataset.workspaceRoot || document.body.dataset.workspaceRoot || '';

    if (!input) return;
    if (shellMode === 'headless') {
      renderPathStatus(statusTarget, {
        status: 'warn',
        message: '이 환경에서는 파일 탐색기를 열 수 없어 경로를 직접 입력해야 합니다.',
      });
      return;
    }

    renderPathStatus(statusTarget, {
      status: 'quiet',
      message: '파일 탐색기를 여는 중입니다.',
    });
    detectNativeDialogs().finally(function () {
      var pickerKind = button.dataset.pickerKind || 'folder';
      var bridgeApi = hasReadyPywebviewBridge() ? getPywebviewApi() : null;
      var pickerPromise;
      if (bridgeApi) {
        pickerPromise = (
          pickerKind === 'file'
            ? bridgeApi.pick_file(input.value || '', workspaceRoot || '', ['Excel (*.xlsx;*.xlsm;*.xltx;*.xltm)'])
            : bridgeApi.pick_folder(input.value || '', workspaceRoot || '')
        );
      } else {
        var form = new FormData();
        form.append('current_path', input.value || '');
        form.append('workspace_root', workspaceRoot || '');
        pickerPromise = fetch(pickerKind === 'file' ? '/diagnostics/pick-file' : '/diagnostics/pick-folder', {
          method: 'POST',
          body: form,
        }).then(function (response) { return response.json(); });
      }
      pickerPromise
        .then(function (payload) {
          if (payload && payload.ok && payload.path) {
            setNativeDialogState('desktop_ready');
            input.value = payload.path;
            input.dispatchEvent(new Event('change', { bubbles: true }));
            if (targetId === 'save_parent_dir') updateSaveFolderPreview();
            renderPathStatus(statusTarget, {
              status: 'pass',
              message: '선택한 경로를 입력했습니다.',
            });
            return;
          }
          renderPathStatus(statusTarget, {
            status: (payload && payload.error === '선택이 취소되었습니다.') ? 'quiet' : 'warn',
            message: (payload && payload.error) || '전용 창 연결이 아직 준비되지 않았습니다. 다시 시도하거나 경로를 직접 입력해 주세요.',
          });
        })
        .catch(function () {
          renderPathStatus(statusTarget, {
            status: 'fail',
            message: '파일 탐색기를 열지 못했습니다. 다시 시도하거나 경로를 직접 입력해 주세요.',
          });
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
    if (shellMode === 'headless') {
      setNativeDialogState('desktop_failed', 'headless 실행이라 파일 탐색기를 열 수 없습니다.');
      return;
    }
    if (initialState === 'desktop_failed') {
      setNativeDialogState('desktop_failed');
      return;
    }
    setNativeDialogState('desktop_pending');
    queueNativeDialogDetection(180);
  }

  function bindDialogRecheck() {
    document.querySelectorAll('[data-dialog-recheck]').forEach(function (button) {
      button.addEventListener('click', function () {
        detectRetryCount = 0;
        setNativeDialogState('desktop_pending', '전용 창 연결을 다시 확인하고 있습니다.');
        detectNativeDialogs();
      });
    });
  }

  function bindRecentWorkspaceButtons() {
    document.querySelectorAll('[data-recent-workspace]').forEach(function (button) {
      button.addEventListener('click', function () {
        var target = document.getElementById('open_workspace_root');
        var statusTarget = document.getElementById('open-workspace-status');
        if (!target) return;
        target.value = button.dataset.recentWorkspace || '';
        target.dispatchEvent(new Event('change', { bubbles: true }));
        document.querySelectorAll('[data-wizard-tab]').forEach(function (tabButton) {
          if (tabButton.dataset.wizardTab === 'open') {
            tabButton.click();
          }
        });
        if (statusTarget) {
          renderPathStatus(statusTarget, {
            status: 'pass',
            message: '최근 세이브 파일 경로를 채웠습니다. 암호를 확인한 뒤 열어 주세요.',
          });
        }
      });
    });
  }

  function renderJobState(target, payload) {
    if (!target || !payload) return;
    var parts = [];
    if (payload.status) parts.push('<span class="status-pill">' + escapeHtml(jobStatusLabel(payload.status)) + '</span>');
    if (payload.stage_label) parts.push('<span class="status-pill quiet">' + escapeHtml(payload.stage_label) + '</span>');
    if (payload.progress_percent) parts.push('<span class="status-pill quiet">' + escapeHtml(payload.progress_percent) + '%</span>');
    if (payload.message) parts.push('<span class="status-pill">' + escapeHtml(payload.message) + '</span>');
    target.innerHTML = parts.join('');
  }

  function renderJobProgressCard(payload) {
    var card = document.querySelector('[data-job-progress-card]');
    if (!card) return;
    if (!payload || !payload.status || payload.status === 'idle' || payload.status === 'no_workspace') {
      card.hidden = true;
      return;
    }
    card.hidden = false;
    var title = card.querySelector('[data-job-title]');
    var stage = card.querySelector('[data-job-stage]');
    var statusLabel = card.querySelector('[data-job-status-label]');
    var stageLabel = card.querySelector('[data-job-stage-label]');
    var progressLabel = card.querySelector('[data-job-progress-label]');
    var nextAction = card.querySelector('[data-job-next-action]');
    var message = card.querySelector('[data-job-message]');
    var details = card.querySelector('[data-job-details]');
    var fill = card.querySelector('[data-job-progress-fill]');
    var featureLabel = payload.feature_id === 'mailbox.connection_check'
      ? '계정 연결 확인'
      : (payload.feature_id === 'runtime.workspace.sync.quick_smoke'
        ? '빠른 테스트 동기화'
        : (payload.feature_id === 'runtime.workspace.sync'
          ? '전체 동기화'
          : '작업 진행 상태'));

    if (title) title.textContent = featureLabel;
    if (stage) stage.textContent = payload.stage_label || payload.status || '대기 중';
    if (statusLabel) statusLabel.textContent = jobStatusLabel(payload.status);
    if (stageLabel) stageLabel.textContent = payload.stage_label || payload.stage_id || '-';
    if (progressLabel) progressLabel.textContent = String(payload.progress_percent || 0) + '%';
    if (nextAction) nextAction.textContent = payload.next_action || '표시할 내용이 없습니다.';
    if (message) {
      message.textContent = payload.message || '';
      message.className = 'field-status ' + (
        payload.status === 'completed' ? 'pass' :
          payload.status === 'partial_success' ? 'warn' :
            payload.status === 'failed' ? 'fail' : 'quiet'
      );
    }
    if (fill) fill.style.width = String(payload.progress_percent || 0) + '%';
    if (details) {
      var detailItems = Array.isArray(payload.details) ? payload.details : [];
      details.innerHTML = detailItems.map(function (item) {
        return '<li>' + escapeHtml(item) + '</li>';
      }).join('');
      details.hidden = detailItems.length === 0;
    }
  }

  function pollJobState() {
    var target = document.querySelector('[data-job-status]');
    fetch('/jobs/current')
      .then(function (response) { return response.json(); })
      .then(function (payload) {
        if (target) renderJobState(target, payload);
        renderJobProgressCard(payload);
      })
      .catch(function () {
        if (target) {
          renderJobState(target, {
            status: 'failed',
            message: '작업 상태를 읽지 못했습니다.',
          });
        }
        renderJobProgressCard({
          status: 'failed',
          message: '작업 상태를 읽지 못했습니다.',
          stage_label: '실패',
          progress_percent: 100,
          details: ['잠시 후 새로고침하거나 다시 시도해 주세요.'],
        });
      });
  }

  function initializeUi() {
    bindTooltips();
    bindPathInspection();
    bindNativePickerButtons();
    bindModalButtons();
    bindDialogRecheck();
    bindWizardTabs();
    bindRecentWorkspaceButtons();
    bindSaveFolderPreview();
    initializeShellContext();
    openAutoModal();
    pollJobState();
    window.setInterval(pollJobState, 1500);
  }

  document.addEventListener('DOMContentLoaded', initializeUi);
  window.addEventListener('pywebviewready', function () {
    detectRetryCount = 0;
    detectNativeDialogs();
  });
})();
