(function () {
  var shellMode = 'browser_fallback';
  var nativeDialogState = 'checking';
  var detectRetryHandle = null;
  var detectRetryCount = 0;
  var maxDetectRetryCount = 20;
  var tooltipEl = null;
  var tooltipPinned = false;
  var tooltipOwner = null;
  var toastRoot = null;
  var transientScrollKeyPrefix = 'epa-window-scroll:';

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

  function invokePywebviewPicker(button, input, workspaceRoot) {
    var api = getPywebviewApi();
    if (!api) {
      return Promise.reject(new Error('전용 창 bridge를 아직 찾지 못했습니다.'));
    }
    var pickerKind = button.dataset.pickerKind || 'folder';
    var picker = pickerKind === 'file' ? api.pick_file : api.pick_folder;
    if (typeof picker !== 'function') {
      return Promise.reject(new Error('전용 창 bridge에 파일 탐색기 함수가 아직 준비되지 않았습니다.'));
    }
    return Promise.resolve(
      picker(
        input.value || '',
        workspaceRoot || ''
      )
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

    if (bindTooltips.globalsBound === 'yes') return;
    bindTooltips.globalsBound = 'yes';
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

  function currentWindowScrollKey() {
    return transientScrollKeyPrefix + window.location.pathname;
  }

  function rememberWindowScrollPosition() {
    try {
      window.sessionStorage.setItem(
        currentWindowScrollKey(),
        String(window.scrollY || 0)
      );
    } catch (error) {
    }
  }

  function restoreWindowScrollPosition() {
    try {
      var raw = window.sessionStorage.getItem(currentWindowScrollKey());
      if (!raw) return;
      window.sessionStorage.removeItem(currentWindowScrollKey());
      var scrollTop = parseInt(raw, 10);
      if (!Number.isFinite(scrollTop) || scrollTop <= 0) return;
      restoreWindowScrollTop(scrollTop);
    } catch (error) {
    }
  }

  function restoreWindowScrollTop(scrollTop) {
    if (!Number.isFinite(scrollTop) || scrollTop < 0) return;
    [0, 80, 220, 480, 900].forEach(function (delay) {
      window.setTimeout(function () {
        window.scrollTo(window.scrollX || 0, scrollTop);
      }, delay);
    });
  }

  function getToastRoot() {
    if (toastRoot) return toastRoot;
    toastRoot = document.createElement('div');
    toastRoot.className = 'toast-stack';
    document.body.appendChild(toastRoot);
    return toastRoot;
  }

  function bindPreserveScrollForms() {
    document.querySelectorAll('form[data-preserve-window-scroll]').forEach(function (form) {
      if (form.dataset.preserveScrollBound === 'yes') return;
      form.dataset.preserveScrollBound = 'yes';
      form.addEventListener('submit', function () {
        rememberWindowScrollPosition();
      });
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
      setNativeDialogState('desktop_ready');
      return Promise.resolve(true);
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
    var pywebviewReady = hasReadyPywebviewBridge();
    var pickerKind = button.dataset.pickerKind || 'folder';

    function handlePickerPayload(payload) {
      if (payload && payload.ok && payload.path) {
        setNativeDialogState('desktop_ready');
        input.value = payload.path;
        input.dispatchEvent(new Event('change', { bubbles: true }));
        if (targetId === 'save_parent_dir') updateSaveFolderPreview();
        renderPathStatus(statusTarget, {
          status: 'pass',
          message: '선택한 경로를 입력했습니다.',
        });
        return true;
      }
      renderPathStatus(statusTarget, {
        status: (payload && payload.error === '선택이 취소되었습니다.') ? 'quiet' : 'warn',
        message: (payload && payload.error) || '파일 탐색기를 열지 못했습니다. 다시 시도하거나 경로를 직접 입력해 주세요.',
      });
      return false;
    }

    function invokeServerFallback() {
      detectNativeDialogs().finally(function () {
        var form = new FormData();
        form.append('current_path', input.value || '');
        form.append('workspace_root', workspaceRoot || '');
        fetch(
          pickerKind === 'file' ? '/diagnostics/pick-file' : '/diagnostics/pick-folder',
          {
            method: 'POST',
            body: form,
          }
        )
          .then(function (response) { return response.json(); })
          .then(function (payload) {
            handlePickerPayload(payload);
          })
          .catch(function () {
            setNativeDialogState('desktop_failed', '파일 탐색기를 열지 못했습니다. 다시 시도하거나 경로를 직접 입력해 주세요.');
            renderPathStatus(statusTarget, {
              status: 'fail',
              message: '파일 탐색기를 열지 못했습니다. 다시 시도하거나 경로를 직접 입력해 주세요.',
            });
          });
      });
    }

    if (pywebviewReady) {
      invokePywebviewPicker(button, input, workspaceRoot)
        .then(function (payload) {
          if (handlePickerPayload(payload)) return;
          invokeServerFallback();
        })
        .catch(function () {
          invokeServerFallback();
        });
      return;
    }

    invokeServerFallback();
  }

  function bindNativePickerButtons() {
    document.querySelectorAll('[data-picker-target]').forEach(function (button) {
      if (button.dataset.nativePickerBound === 'yes') return;
      button.dataset.nativePickerBound = 'yes';
      button.addEventListener('click', function () {
        openNativePicker(button);
      });
    });
  }

  function updateSelectedReviewRow(bundleId) {
    document.querySelectorAll('[data-review-row]').forEach(function (row) {
      row.classList.toggle('selected', !!bundleId && row.dataset.bundleId === bundleId);
    });
  }

  function currentReviewUrl() {
    if (document.body.dataset.currentPath === '/review') {
      return window.location.pathname + window.location.search;
    }
    var detailSection = document.querySelector('#review-detail-panel [data-current-review-url]');
    if (detailSection && detailSection.dataset.currentReviewUrl) {
      return detailSection.dataset.currentReviewUrl;
    }
    try {
      var raw = window.sessionStorage.getItem(reviewStateStorageKey());
      if (raw) {
        var payload = JSON.parse(raw);
        if (payload && payload.url) return payload.url;
      }
    } catch (error) {
    }
    return window.location.pathname + window.location.search;
  }

  function reviewStateStorageKey() {
    var workspaceRoot = document.body.dataset.workspaceRoot || '';
    return 'epa-review-state:' + workspaceRoot;
  }

  function reviewListScrollContainer() {
    return document.querySelector('[data-review-list-scroll]');
  }

  function reviewDetailScrollContainer() {
    return document.querySelector('[data-review-detail-scroll]');
  }

  function captureReviewState() {
    if (document.body.dataset.currentPath !== '/review') return;
    try {
      var selectedSection = document.querySelector('#review-detail-panel [data-selected-bundle-id]');
      var activeArtifactTab = document.querySelector('#review-detail-panel [data-review-artifact-tab].active');
      var listScroll = reviewListScrollContainer();
      var detailScroll = reviewDetailScrollContainer();
      var payload = {
        url: currentReviewUrl(),
        listScrollTop: listScroll ? listScroll.scrollTop : 0,
        detailScrollTop: detailScroll ? detailScroll.scrollTop : 0,
        selectedBundleId: selectedSection ? (selectedSection.dataset.selectedBundleId || '') : '',
        artifactKind: activeArtifactTab ? (activeArtifactTab.dataset.reviewUrl || activeArtifactTab.getAttribute('href') || '') : '',
      };
      window.sessionStorage.setItem(reviewStateStorageKey(), JSON.stringify(payload));
    } catch (error) {
    }
  }

  function restoreReviewScrollPosition() {
    if (document.body.dataset.currentPath !== '/review') return;
    try {
      var raw = window.sessionStorage.getItem(reviewStateStorageKey());
      if (!raw) return;
      var payload = JSON.parse(raw);
      window.setTimeout(function () {
        var listScroll = reviewListScrollContainer();
        var detailScroll = reviewDetailScrollContainer();
        if (listScroll && typeof payload.listScrollTop === 'number') {
          listScroll.scrollTop = payload.listScrollTop;
        }
        if (detailScroll && typeof payload.detailScrollTop === 'number') {
          detailScroll.scrollTop = payload.detailScrollTop;
        }
      }, 30);
    } catch (error) {
    }
  }

  function renderReviewDetailError(message) {
    return [
      '<section class="section review-detail-card" data-selected-bundle-id="" data-current-review-url="' + escapeHtml(currentReviewUrl()) + '">',
      '<div class="section-head"><div><div class="eyebrow">상세</div><h2>상세를 불러오지 못했습니다</h2></div></div>',
      '<div class="review-detail-scroll">',
      '<div class="field-status fail">' + escapeHtml(message || '잠시 후 다시 시도해 주세요.') + '</div>',
      '</div>',
      '</section>',
    ].join('');
  }

  function renderReviewDetailLoading(message) {
    return [
      '<section class="section review-detail-card review-detail-loading" data-selected-bundle-id="" data-current-review-url="' + escapeHtml(currentReviewUrl()) + '">',
      '<div class="section-head"><div><div class="eyebrow">상세</div><h2>' + escapeHtml(message || '선택한 메일을 불러오는 중입니다') + '</h2></div></div>',
      '<div class="review-detail-scroll">',
      '<div class="review-loading-bar"></div>',
      '<div class="field-status quiet">왼쪽 목록과 현재 필터 상태는 그대로 유지됩니다.</div>',
      '</div>',
      '</section>',
    ].join('');
  }

  function updateReviewUrl(url) {
    if (!url) return;
    try {
      window.history.replaceState({}, '', url);
    } catch (error) {
    }
  }

  function loadReviewDetail(selectUrl, reviewUrl, bundleId) {
    var panel = document.getElementById('review-detail-panel');
    if (!panel || !selectUrl) return;
    var previousWindowScrollTop = window.scrollY || 0;
    var listScroll = reviewListScrollContainer();
    var detailScroll = reviewDetailScrollContainer();
    var previousListScrollTop = listScroll ? listScroll.scrollTop : 0;
    var previousDetailScrollTop = detailScroll ? detailScroll.scrollTop : 0;
    var hadExistingDetail = !!panel.querySelector('[data-selected-bundle-id], .review-detail-placeholder');
    updateSelectedReviewRow(bundleId || '');
    if (hadExistingDetail) {
      panel.classList.add('review-panel-loading');
      panel.setAttribute('data-loading-text', '선택한 메일을 불러오는 중입니다');
    } else {
      panel.innerHTML = renderReviewDetailLoading('선택한 메일을 불러오는 중입니다');
    }
    fetch(selectUrl, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('상세를 불러오지 못했습니다.');
        }
        return response.text();
      })
      .then(function (html) {
        panel.innerHTML = html;
        panel.classList.remove('review-panel-loading');
        panel.removeAttribute('data-loading-text');
        if (listScroll) {
          listScroll.scrollTop = previousListScrollTop;
        }
        detailScroll = reviewDetailScrollContainer();
        if (detailScroll) {
          detailScroll.scrollTop = 0;
        }
        restoreWindowScrollTop(previousWindowScrollTop);
        if (reviewUrl) {
          updateReviewUrl(reviewUrl);
        }
        bindDynamicUi();
        captureReviewState();
      })
      .catch(function (error) {
        panel.classList.remove('review-panel-loading');
        panel.removeAttribute('data-loading-text');
        if (!hadExistingDetail) {
          panel.innerHTML = renderReviewDetailError(error && error.message ? error.message : '상세를 불러오지 못했습니다.');
        }
        if (listScroll) {
          listScroll.scrollTop = previousListScrollTop;
        }
        detailScroll = reviewDetailScrollContainer();
        if (detailScroll) {
          detailScroll.scrollTop = previousDetailScrollTop;
        }
        restoreWindowScrollTop(previousWindowScrollTop);
        pushTransientBanner('error', error && error.message ? error.message : '상세를 불러오지 못했습니다.');
        bindDynamicUi();
      });
  }

  function pushTransientBanner(kind, text) {
    if (!text) return;
    var root = getToastRoot();
    var banner = document.createElement('div');
    banner.className = 'banner toast-banner ' + (kind === 'error' ? 'error' : 'success');
    banner.textContent = text;
    root.appendChild(banner);
    window.setTimeout(function () {
      banner.classList.add('visible');
    }, 10);
    window.setTimeout(function () {
      banner.classList.remove('visible');
      window.setTimeout(function () {
        if (banner.parentNode) banner.parentNode.removeChild(banner);
      }, 180);
    }, 4000);
  }

  function openRelativeWorkspacePath(relativePath) {
    if (!relativePath) return Promise.resolve();
    if (shellMode !== 'desktop_window') {
      return Promise.reject(new Error('이 기능은 앱 창에서만 파일을 바로 열 수 있습니다. web 검증 모드에서는 새 탭 보기나 다운로드를 사용해 주세요.'));
    }
    var form = new FormData();
    form.append('relative_path', relativePath);
    form.append('return_to', currentReviewUrl());
    return fetch('/actions/open-path', {
      method: 'POST',
      headers: {
        Accept: 'application/json',
      },
      body: form,
    }).then(function (response) {
      return response.json().then(function (payload) {
        if (!response.ok || !payload.ok) {
          throw new Error((payload && payload.error) || '파일을 열지 못했습니다.');
        }
        return payload;
      });
    });
  }

  function openBrowserUrl(url) {
    if (!url) return false;
    var popup = window.open(url, '_blank', 'noopener,noreferrer');
    if (popup) return true;
    try {
      var anchor = document.createElement('a');
      anchor.href = url;
      anchor.target = '_blank';
      anchor.rel = 'noopener noreferrer';
      anchor.style.display = 'none';
      document.body.appendChild(anchor);
      anchor.click();
      window.setTimeout(function () {
        if (anchor.parentNode) anchor.parentNode.removeChild(anchor);
      }, 0);
      return true;
    } catch (error) {
      return false;
    }
  }

  function setReviewExternalStatus(kind, text) {
    var node = document.querySelector('[data-review-external-status]');
    if (!node) return;
    node.className = 'field-status review-external-status ' + (
      kind === 'error' ? 'fail' :
        kind === 'success' ? 'pass' :
          kind === 'warn' ? 'warn' : 'quiet'
    );
    node.textContent = text || '앱 안 미리보기가 기본입니다. 외부 열기가 막히면 이 자리에서 이유를 안내합니다.';
  }

  function openExternalArtifact(button) {
    if (!button) return;
    var label = button.dataset.openLabel || '파일';
    var relativePath = button.dataset.openRelativePath || '';
    var browserUrl = button.dataset.openBrowserUrl || '';

    captureReviewState();
    setReviewExternalStatus('quiet', label + '을(를) 여는 중입니다.');
    if (shellMode === 'desktop_window' && relativePath) {
      openRelativeWorkspacePath(relativePath)
        .then(function () {
          setReviewExternalStatus('success', label + '을(를) Windows 기본 앱으로 열었습니다.');
          pushTransientBanner('success', label + '을(를) 열었습니다.');
        })
        .catch(function (error) {
          if (browserUrl && openBrowserUrl(browserUrl)) {
            setReviewExternalStatus('warn', label + ' 기본 열기가 실패해 브라우저 창으로 대신 열었습니다.');
            pushTransientBanner('success', label + '을(를) 새 창에서 열었습니다.');
            return;
          }
          setReviewExternalStatus('error', error && error.message ? error.message : label + '을(를) 열지 못했습니다.');
          pushTransientBanner('error', error && error.message ? error.message : label + '을(를) 열지 못했습니다.');
        });
      return;
    }
    if (browserUrl) {
      setReviewExternalStatus('success', label + '을(를) 새 탭에서 열고 있습니다.');
      return;
    }
    setReviewExternalStatus('error', label + '을(를) 열 수 있는 경로를 찾지 못했습니다.');
    pushTransientBanner('error', label + '을(를) 열 수 있는 경로를 찾지 못했습니다.');
  }

  function bindBrowserOpenButtons() {
    document.querySelectorAll('[data-open-browser-url]:not([data-open-relative-path])').forEach(function (button) {
      if (button.dataset.openBrowserBound === 'yes') return;
      button.dataset.openBrowserBound = 'yes';
      button.addEventListener('click', function () {
        var opened = openBrowserUrl(button.dataset.openBrowserUrl || '');
        if (opened) {
          pushTransientBanner('success', '새 탭에서 열었습니다.');
        } else {
          pushTransientBanner('error', '브라우저가 새 탭 열기를 차단했습니다. 팝업 차단을 확인해 주세요.');
        }
      });
    });
  }

  function bindOpenRelativePathButtons() {
    document.querySelectorAll('[data-open-relative-path]').forEach(function (button) {
      if (button.dataset.openRelativeBound === 'yes') return;
      button.dataset.openRelativeBound = 'yes';
      button.addEventListener('click', function (event) {
        if (shellMode === 'desktop_window') {
          event.preventDefault();
          openExternalArtifact(button);
          return;
        }
        captureReviewState();
        var label = button.dataset.openLabel || '파일';
        setReviewExternalStatus('success', label + '을(를) 새 탭에서 열고 있습니다.');
        pushTransientBanner('success', label + '을(를) 새 탭에서 열고 있습니다.');
      });
    });
  }

  function bindReviewRowLinks() {
    document.querySelectorAll('.review-row-link').forEach(function (link) {
      if (link.dataset.reviewRowBound === 'yes') return;
      link.dataset.reviewRowBound = 'yes';
      link.addEventListener('click', function (event) {
        event.preventDefault();
        loadReviewDetail(
          link.dataset.selectUrl || '',
          link.dataset.reviewUrl || link.getAttribute('href') || '',
          link.dataset.bundleId || ''
        );
      });
    });
    document.querySelectorAll('#review-detail-panel [data-review-artifact-tab]').forEach(function (link) {
      if (link.dataset.reviewArtifactBound === 'yes') return;
      link.dataset.reviewArtifactBound = 'yes';
      link.addEventListener('click', function (event) {
        event.preventDefault();
        var selectedSection = document.querySelector('#review-detail-panel [data-selected-bundle-id]');
        loadReviewDetail(
          link.dataset.detailUrl || '',
          link.dataset.reviewUrl || link.getAttribute('href') || '',
          selectedSection ? (selectedSection.dataset.selectedBundleId || '') : ''
        );
      });
    });
    document.querySelectorAll('[data-review-row]').forEach(function (row) {
      if (row.dataset.reviewRowClickBound === 'yes') return;
      row.dataset.reviewRowClickBound = 'yes';
      row.addEventListener('click', function (event) {
        if (event.target.closest('a, button, input, select, textarea, form')) return;
        var selectUrl = row.dataset.selectUrl || '';
        var bundleId = row.dataset.bundleId || '';
        if (!selectUrl) return;
        loadReviewDetail(
          selectUrl,
          row.dataset.reviewUrl || currentReviewUrl(),
          bundleId
        );
      });
    });
  }

  function bindReviewScrollState() {
    [reviewListScrollContainer(), reviewDetailScrollContainer()].forEach(function (node) {
      if (!node) return;
      if (node.dataset.reviewScrollBound === 'yes') return;
      node.dataset.reviewScrollBound = 'yes';
      node.addEventListener('scroll', function () {
        captureReviewState();
      }, { passive: true });
    });
  }

  function bindDynamicUi() {
    bindTooltips();
    bindNativePickerButtons();
    bindPreserveScrollForms();
    bindOpenRelativePathButtons();
    bindBrowserOpenButtons();
    bindReviewRowLinks();
    bindReviewScrollState();
    bindRecentRemoveForms();
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

  function bindRecentRemoveForms() {
    document.querySelectorAll('form[data-recent-remove-form]').forEach(function (form) {
      if (form.dataset.recentRemoveBound === 'yes') return;
      form.dataset.recentRemoveBound = 'yes';
      form.addEventListener('submit', function (event) {
        event.preventDefault();
        event.stopPropagation();
        var previousWindowScrollTop = window.scrollY || 0;
        var recentItem = form.closest('.recent-item');
        fetch(form.action, {
          method: 'POST',
          headers: {
            Accept: 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: new FormData(form),
        })
          .then(function (response) { return response.json(); })
          .then(function (payload) {
            if (!payload || !payload.ok) {
              throw new Error((payload && payload.message) || '최근 세이브 파일을 정리하지 못했습니다.');
            }
            if (recentItem) {
              recentItem.remove();
            }
            var recentList = document.querySelector('.recent-list');
            if (recentList && !recentList.children.length) {
              recentList.outerHTML = '<div class="field-status">아직 최근 세이브가 없습니다. 한 번 열거나 만들면 여기에 다시 나타납니다.</div>';
            }
            window.requestAnimationFrame(function () {
              restoreWindowScrollTop(previousWindowScrollTop);
            });
            pushTransientBanner('success', payload.message || '최근 세이브 파일 목록에서 정리했습니다.');
          })
          .catch(function (error) {
            restoreWindowScrollTop(previousWindowScrollTop);
            pushTransientBanner('error', error && error.message ? error.message : '최근 세이브 파일을 정리하지 못했습니다.');
          });
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
    var cards = document.querySelectorAll('[data-job-progress-card]');
    cards.forEach(function (card) {
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
      var stageProgress = card.querySelector('[data-job-stage-progress]');
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
      if (stageProgress) {
        if (payload.stage_progress_total) {
          stageProgress.textContent = String(payload.stage_progress_current || 0) + ' / ' + String(payload.stage_progress_total);
        } else {
          stageProgress.textContent = '표시할 내용이 없습니다.';
        }
      }
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
    });

    var globalBar = document.querySelector('[data-global-job-progress]');
    if (!globalBar) return;
    if (!payload || !payload.status || payload.status === 'idle' || payload.status === 'no_workspace') {
      globalBar.hidden = true;
      return;
    }
    globalBar.hidden = false;
    var titleNode = globalBar.querySelector('[data-global-job-title]');
    var stageNode = globalBar.querySelector('[data-global-job-stage]');
    var countNode = globalBar.querySelector('[data-global-job-count]');
    var noteNode = globalBar.querySelector('[data-global-job-note]');
    var fillNode = globalBar.querySelector('[data-global-job-fill]');
    var detailsNode = globalBar.querySelector('[data-global-job-details]');
    if (titleNode) {
      titleNode.textContent = payload.feature_id === 'mailbox.connection_check'
        ? '계정 연결 확인'
        : (payload.feature_id === 'runtime.workspace.sync.quick_smoke'
          ? '빠른 테스트 동기화'
          : (payload.feature_id === 'runtime.workspace.sync'
            ? '메일 동기화'
            : '작업 진행 상태'));
    }
    if (stageNode) {
      stageNode.textContent = jobStatusLabel(payload.status) + ' · ' + (payload.stage_label || payload.stage_id || '대기 중');
    }
    if (countNode) {
      countNode.textContent = payload.stage_progress_total
        ? String(payload.stage_progress_current || 0) + ' / ' + String(payload.stage_progress_total) + ' · ' + String(payload.progress_percent || 0) + '%'
        : String(payload.progress_percent || 0) + '%';
    }
    if (noteNode) {
      var noteParts = [];
      if (payload.message) noteParts.push(payload.message);
      if (payload.stage_progress_total) {
        noteParts.push('진행 개수 ' + String(payload.stage_progress_current || 0) + ' / ' + String(payload.stage_progress_total));
      }
      if (!noteParts.length && payload.next_action) noteParts.push(payload.next_action);
      noteNode.textContent = noteParts.join(' · ');
    }
    if (fillNode) {
      fillNode.style.width = String(payload.progress_percent || 0) + '%';
    }
    if (detailsNode) {
      var globalDetailItems = Array.isArray(payload.details) ? payload.details.slice(0, 4) : [];
      detailsNode.innerHTML = globalDetailItems.map(function (item) {
        return '<li>' + escapeHtml(item) + '</li>';
      }).join('');
      detailsNode.hidden = globalDetailItems.length === 0;
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
    bindDynamicUi();
    bindPathInspection();
    bindModalButtons();
    bindDialogRecheck();
    bindWizardTabs();
    bindRecentWorkspaceButtons();
    bindSaveFolderPreview();
    initializeShellContext();
    openAutoModal();
    restoreWindowScrollPosition();
    restoreReviewScrollPosition();
    pollJobState();
    window.setInterval(pollJobState, 1500);
    if (document.body.dataset.currentPath === '/review') {
      var selectedSection = document.querySelector('#review-detail-panel [data-selected-bundle-id]');
      if (selectedSection && selectedSection.dataset.selectedBundleId) {
        updateSelectedReviewRow(selectedSection.dataset.selectedBundleId || '');
      } else {
        var firstRowLink = document.querySelector('.review-row-link');
        if (firstRowLink) {
          loadReviewDetail(
            firstRowLink.dataset.selectUrl || '',
            firstRowLink.dataset.reviewUrl || firstRowLink.getAttribute('href') || '',
            firstRowLink.dataset.bundleId || ''
          );
        }
      }
    }
  }

  document.addEventListener('DOMContentLoaded', initializeUi);
  window.addEventListener('pywebviewready', function () {
    detectRetryCount = 0;
    detectNativeDialogs();
  });
  document.body.addEventListener('htmx:afterSwap', function (event) {
    bindDynamicUi();
    var target = event.target;
    if (!target) return;
    if (target.id === 'review-detail-panel') {
      var selectedSection = target.querySelector('[data-selected-bundle-id]');
      if (selectedSection) {
        updateSelectedReviewRow(selectedSection.dataset.selectedBundleId || '');
      }
      captureReviewState();
    }
  });
})();
