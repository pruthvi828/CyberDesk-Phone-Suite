// Phone Cleaner & Safe Backup Client Controller
let currentMode = "adb"; // 'adb' or 'folder'
let deviceData = null;
let scanData = null;
let currentCategoryFiles = [];
let currentCategoryKey = "";
let selectedFilePaths = new Set();
let socket = null;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  initWebSocket();
  refreshDeviceStatus();
  setInterval(pollMigrationStatus, 1500);
});

async function pollMigrationStatus() {
  try {
    const res = await fetch("/api/migration/status");
    const data = await res.json();
    const card = document.getElementById("liveMigrationCard");
    
    if (data && (data.status === "in_progress" || data.status === "completed" || data.processed_files > 0 || data.done_count > 0)) {
      card.style.display = "block";
      const percent = data.percent !== undefined ? data.percent : (data.total_files ? Math.round((data.processed_files / data.total_files) * 100) : 0);
      const processed = data.processed_files !== undefined ? data.processed_files : (data.done_count || 0);
      const total = data.total_files !== undefined ? data.total_files : (data.total_count || 126);
      const pending = data.pending_files !== undefined ? data.pending_files : Math.max(0, total - processed);
      const transGb = data.transferred_bytes ? (data.transferred_bytes / (1024**3)).toFixed(2) : (data.done_gb || "0.00");
      const totGb = data.total_bytes ? (data.total_bytes / (1024**3)).toFixed(2) : (data.total_gb || "11.12");

      const speedText = data.speed_mb_s ? ` | ⚡ <b>${data.speed_mb_s} MB/s</b>` : "";
      const etaText = data.eta ? ` | ⏳ ETA: <b>${data.eta}</b>` : "";

      document.getElementById("liveMigrationFill").style.width = `${percent}%`;
      document.getElementById("liveMigrationPctText").textContent = `${percent}% Complete (${processed}/${total})`;
      document.getElementById("liveMigrationStats").innerHTML = `Transferred: <b>${processed}</b> videos (${transGb} GB / ${totGb} GB)${speedText}`;
      document.getElementById("liveMigrationRemaining").innerHTML = `<b>${pending}</b> videos pending${etaText}`;

      if (data.current_file) {
        document.getElementById("liveMigrationSub").innerHTML = `<b>Current:</b> <code style="color:#38bdf8;">${data.current_file}</code>`;
      }

      if (data.status === "completed" || pending === 0) {
        document.getElementById("liveMigrationSub").innerHTML = `<span style="color: var(--success); font-weight: 600;">🎉 All videos successfully moved to Pen Drive & deleted from phone!</span>`;
        document.getElementById("liveMigrationPctText").textContent = `100% Done`;
      }
    }
  } catch (e) {
    // Ignore polling errors
  }
}

// WebSocket Connection
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log("WebSocket connected.");
  };

  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      handleWebSocketMessage(msg);
    } catch (e) {
      console.error("WS Parse error:", e);
    }
  };

  socket.onclose = () => {
    console.log("WebSocket disconnected, reconnecting in 3s...");
    setTimeout(initWebSocket, 3000);
  };
}

function handleWebSocketMessage(msg) {
  if (msg.type === "progress") {
    updateProgressUI(msg.status, msg.percent);
  } else if (msg.type === "scan_complete") {
    closeModal("progressModal");
    scanData = msg.data;
    renderScanResults(msg.data);
  } else if (msg.type === "backup_complete") {
    showOperationComplete("Backup Complete", `Successfully backed up ${msg.data.successful_count} files (${msg.data.total_formatted}) to:<br><code>${msg.data.backup_dir}</code>`);
  } else if (msg.type === "clean_complete") {
    if (msg.data.dry_run) {
      renderDryRunPreview(msg.data);
    } else {
      showOperationComplete("Cleanup Complete", `Successfully cleaned ${msg.data.deleted_count} unwanted files.<br><b>Freed Space: ${msg.data.freed_formatted}</b>`);
      // Refresh scan summary
      fetchScanResults();
      refreshDeviceStatus();
    }
  } else if (msg.type === "error") {
    alert("Error: " + msg.message);
    closeModal("progressModal");
  }
}

// Mode Selection
function setMode(mode) {
  currentMode = mode;
  document.getElementById("tabAdb").classList.toggle("active", mode === "adb");
  document.getElementById("tabWireless").classList.toggle("active", mode === "wireless");
  document.getElementById("tabFolder").classList.toggle("active", mode === "folder");

  document.getElementById("wirelessBanner").style.display = mode === "wireless" ? "flex" : "none";
  document.getElementById("folderInputGroup").style.display = mode === "folder" ? "block" : "none";

  if (mode === "folder") {
    document.getElementById("deviceModel").textContent = "Local Folder / Mounted USB Mode";
    document.getElementById("deviceStatusPill").className = "status-pill ready";
    document.getElementById("deviceStatusText").textContent = "Folder Mode Ready";
    document.getElementById("deviceBrandBadge").style.display = "none";
    document.getElementById("deviceMeta").innerHTML = "<span>Select folder or drive on your PC</span>";
  } else {
    refreshDeviceStatus();
  }
}

async function pairWirelessDevice() {
  const address = document.getElementById("wirelessPairAddress").value.trim();
  const code = document.getElementById("wirelessPairCode").value.trim();

  if (!address || !code) {
    alert("Please enter both the IP:Port and 6-digit pairing code from your phone screen.");
    return;
  }

  showProgressModal("Pairing Wireless Device...", `Pairing with ${address}...`);

  try {
    const res = await fetch("/api/device/pair-wireless", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address, code })
    });
    const data = await res.json();
    closeModal("progressModal");

    if (data.success) {
      alert("🎉 Successfully paired with your phone!");
      refreshDeviceStatus();
    } else {
      alert("Pairing failed: " + data.message);
    }
  } catch (e) {
    alert("Error pairing: " + e);
    closeModal("progressModal");
  }
}

async function connectWirelessDevice() {
  const address = document.getElementById("wirelessConnectAddress").value.trim();
  if (!address) {
    alert("Please enter the IP:Port from the Wireless Debugging screen on your phone.");
    return;
  }

  showProgressModal("Connecting to Phone...", `Connecting to ${address}...`);

  try {
    const res = await fetch("/api/device/connect-wireless", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address })
    });
    const data = await res.json();
    closeModal("progressModal");

    if (data.success) {
      alert("🎉 Connected to your phone!");
      refreshDeviceStatus();
    } else {
      alert("Connection failed: " + data.message);
    }
  } catch (e) {
    alert("Error connecting: " + e);
    closeModal("progressModal");
  }
}

// Device Status
async function refreshDeviceStatus() {
  if (currentMode !== "adb") return;

  try {
    const res = await fetch("/api/device/status");
    const data = await res.json();
    deviceData = data;

    const pill = document.getElementById("deviceStatusPill");
    const text = document.getElementById("deviceStatusText");
    const model = document.getElementById("deviceModel");
    const badge = document.getElementById("deviceBrandBadge");
    const meta = document.getElementById("deviceMeta");
    const storageWrapper = document.getElementById("storageBarWrapper");

    if (data.default_backup_dir) {
      document.getElementById("backupDestinationInput").value = data.default_backup_dir;
    }

    if (data.active_device && data.active_device.connected) {
      const dev = data.active_device;
      pill.className = "status-pill ready";
      text.textContent = "USB Connected (Ready)";
      model.textContent = `${dev.brand} ${dev.model}`;
      badge.textContent = dev.brand;
      badge.style.display = "inline-block";

      meta.innerHTML = `
        <span><i class="bi bi-battery-charging"></i> Battery: ${dev.battery}%</span>
        <span><i class="bi bi-android2"></i> Android ${dev.android_version}</span>
        <span><i class="bi bi-hash"></i> ID: ${dev.id}</span>
      `;

      if (dev.storage && dev.storage.total_bytes > 0) {
        storageWrapper.style.display = "block";
        const totalGb = (dev.storage.total_bytes / (1024 ** 3)).toFixed(1);
        const usedGb = (dev.storage.used_bytes / (1024 ** 3)).toFixed(1);
        const freeGb = (dev.storage.free_bytes / (1024 ** 3)).toFixed(1);

        document.getElementById("storageStatsText").textContent = `${usedGb} GB used / ${totalGb} GB (${freeGb} GB free)`;
        document.getElementById("storageFill").style.width = `${dev.storage.used_percent}%`;
      }
    } else if (data.active_device && data.active_device.state === "unauthorized") {
      pill.className = "status-pill unauthorized";
      text.textContent = "Unauthorized USB";
      model.textContent = "Phone Detected - Action Needed";
      meta.innerHTML = `<span style="color: var(--warning);"><i class="bi bi-exclamation-triangle"></i> Check your phone screen & tap 'Allow USB Debugging'</span>`;
    } else {
      pill.className = "status-pill disconnected";
      text.textContent = "No Device Detected";
      model.textContent = "Connect Phone via USB Cable";
      meta.innerHTML = "<span>Follow steps in the banner above</span>";
      badge.style.display = "none";
      storageWrapper.style.display = "none";
    }
  } catch (err) {
    console.error("Status fetch error:", err);
  }
}

// Trigger Scan
async function triggerScan() {
  const payload = { mode: currentMode };
  if (currentMode === "folder") {
    const path = document.getElementById("customFolderPath").value.trim();
    if (!path) {
      alert("Please enter a local or mounted folder path to scan.");
      return;
    }
    payload.folder_path = path;
  }

  showProgressModal("Scanning Phone Storage...", "Starting deep storage scan...");

  try {
    const res = await fetch("/api/scan/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      alert("Scan failed: " + (err.detail || "Unknown error"));
      closeModal("progressModal");
    }
  } catch (e) {
    alert("Scan request failed: " + e);
    closeModal("progressModal");
  }
}

async function fetchScanResults() {
  try {
    const res = await fetch("/api/scan/results");
    const data = await res.json();
    if (data.scanned) {
      scanData = data.summary;
      renderScanResults(data.summary);
    }
  } catch (e) {
    console.error("Fetch scan results error:", e);
  }
}

// Render Results
function renderScanResults(summary) {
  document.getElementById("actionPanel").style.display = "grid";
  document.getElementById("categoriesSection").style.display = "block";

  document.getElementById("totalScannedSummary").textContent = `${summary.total_files} files found (${summary.total_formatted})`;

  const grid = document.getElementById("categoriesGrid");
  grid.innerHTML = "";

  const cats = summary.categories;
  for (const [key, cat] of Object.entries(cats)) {
    if (cat.count === 0) continue;

    const isCleanTarget = cat.default_checked_clean;
    const isKeepTarget = cat.default_checked_backup;

    const card = document.createElement("div");
    card.className = `category-card ${isCleanTarget ? 'target-clean' : (isKeepTarget ? 'target-keep' : '')}`;
    card.onclick = () => openCategoryModal(key, cat.label);

    card.innerHTML = `
      <div class="category-top">
        <div class="cat-title-wrap">
          <div class="cat-icon-box ${cat.badge_color}">
            <i class="bi bi-${cat.icon}"></i>
          </div>
          <div>
            <div class="cat-name">${cat.label}</div>
            <div style="font-size: 11px; color: var(--text-muted);">${cat.description}</div>
          </div>
        </div>
      </div>

      <div class="cat-stats">
        <div class="cat-count">${cat.count.toLocaleString()} <span style="font-size: 12px; font-weight: 400; color: var(--text-muted);">files</span></div>
        <div class="cat-bytes">${cat.bytes_formatted}</div>
      </div>

      <div class="cat-footer">
        <span class="action-badge ${isCleanTarget ? 'badge-clean' : (isKeepTarget ? 'badge-keep' : 'badge-clean')}">
          ${cat.action}
        </span>
        <span style="font-size: 12px; color: var(--accent-primary); font-weight: 600;">
          Inspect <i class="bi bi-chevron-right"></i>
        </span>
      </div>
    `;

    grid.appendChild(card);
  }
}

// View Mode & Gallery Controller
let currentViewMode = "gallery";
let currentLightboxIndex = 0;

function setViewMode(mode) {
  currentViewMode = mode;
  document.getElementById("btnViewGallery").classList.toggle("active", mode === "gallery");
  document.getElementById("btnViewTable").classList.toggle("active", mode === "table");

  document.getElementById("modalGalleryGrid").style.display = mode === "gallery" ? "grid" : "none";
  document.getElementById("modalTableViewWrapper").style.display = mode === "table" ? "block" : "none";
}

// Category Detail Modal
async function openCategoryModal(categoryKey, label) {
  currentCategoryKey = categoryKey;
  selectedFilePaths.clear();
  updateSelectedCountUI();

  document.getElementById("modalCategoryTitle").textContent = label;
  document.getElementById("modalCategorySubtitle").textContent = "Loading files...";

  // Default to gallery view for photos/videos/screenshots, table for docs
  const isMediaCat = ["camera_media", "screenshots", "other_images", "other_videos"].includes(categoryKey);
  setViewMode(isMediaCat ? "gallery" : "table");

  openModal("fileModal");

  try {
    const res = await fetch(`/api/scan/category/${categoryKey}`);
    const data = await res.json();
    currentCategoryFiles = data.files;
    document.getElementById("modalCategorySubtitle").textContent = `${data.count} files (${data.bytes_formatted})`;
    
    renderModalFileList(currentCategoryFiles);
    renderModalGallery(currentCategoryFiles);
  } catch (e) {
    alert("Failed to load category files: " + e);
  }
}

function isImageOrVideo(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const isImg = ['jpg', 'jpeg', 'png', 'webp', 'heic', 'bmp', 'gif'].includes(ext);
  const isVid = ['mp4', 'mkv', 'mov', '3gp', 'webm', 'avi', 'm4v'].includes(ext);
  return { isImg, isVid, isMedia: isImg || isVid };
}

function renderModalGallery(files) {
  const grid = document.getElementById("modalGalleryGrid");
  grid.innerHTML = "";

  files.slice(0, 300).forEach((f, index) => {
    const { isImg, isVid } = isImageOrVideo(f.filename);
    const item = document.createElement("div");
    item.className = "gallery-item";
    item.id = `gallery-item-${index}`;

    const previewUrl = `/api/media/preview?path=${encodeURIComponent(f.path)}`;

    item.innerHTML = `
      <input type="checkbox" class="gallery-checkbox" data-path="${f.path}" ${selectedFilePaths.has(f.path) ? 'checked' : ''} onclick="event.stopPropagation(); toggleFileSelection('${f.path}', this.checked, ${index})">
      ${isVid ? `
        <video class="gallery-thumb" src="${previewUrl}#t=0.5" preload="metadata" muted></video>
        <div class="gallery-play-icon"><i class="bi bi-play-circle-fill"></i></div>
      ` : (isImg ? `
        <img class="gallery-thumb" src="${previewUrl}" loading="lazy" alt="${f.filename}">
      ` : `
        <div style="display:flex; height:100%; align-items:center; justify-content:center; flex-direction:column; padding:8px; text-align:center;">
          <i class="bi bi-file-earmark-text" style="font-size:28px; color:var(--text-muted);"></i>
          <span style="font-size:11px; margin-top:4px; word-break:break-all;">${f.filename}</span>
        </div>
      `)}
      <div class="gallery-badge">${f.size_str}</div>
    `;

    item.onclick = () => openLightbox(index);
    grid.appendChild(item);
  });
}

function renderModalFileList(files) {
  const tbody = document.getElementById("modalFileListBody");
  tbody.innerHTML = "";

  files.forEach((f, idx) => {
    const isChecked = selectedFilePaths.has(f.path);
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>
        <input type="checkbox" data-path="${f.path}" ${isChecked ? 'checked' : ''} onchange="toggleFileSelection('${f.path}', this.checked, ${idx})">
      </td>
      <td class="file-name-cell">
        <div style="font-weight: 500; cursor:pointer;" onclick="openLightbox(${idx})">${f.filename}</div>
        <div class="file-path-sub">${f.path}</div>
      </td>
      <td>${f.size_str}</td>
      <td>
        <span class="action-badge ${f.badge_color === 'success' ? 'badge-keep' : 'badge-clean'}">${f.recommendation}</span>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function toggleFileSelection(path, isChecked, index) {
  if (isChecked) {
    selectedFilePaths.add(path);
  } else {
    selectedFilePaths.delete(path);
  }
  
  if (index !== undefined) {
    const gItem = document.getElementById(`gallery-item-${index}`);
    if (gItem) gItem.classList.toggle("selected", isChecked);
  }
  updateSelectedCountUI();
}

function toggleSelectAllModal(checked) {
  selectedFilePaths.clear();
  const checkboxes = document.querySelectorAll("#fileModal input[type='checkbox']");
  checkboxes.forEach((cb) => {
    cb.checked = checked;
    const path = cb.getAttribute("data-path");
    if (path && checked) selectedFilePaths.add(path);
  });

  document.querySelectorAll(".gallery-item").forEach(item => {
    item.classList.toggle("selected", checked);
  });

  updateSelectedCountUI();
}

function updateSelectedCountUI() {
  const count = selectedFilePaths.size;
  const btn = document.getElementById("btnDeleteSelectedModal");
  document.getElementById("modalSelectedCount").textContent = count;
  btn.style.display = count > 0 ? "inline-flex" : "none";
}

function filterModalFiles() {
  const q = document.getElementById("fileSearchInput").value.toLowerCase();
  const filtered = currentCategoryFiles.filter(f => f.filename.toLowerCase().includes(q) || f.path.toLowerCase().includes(q));
  renderModalFileList(filtered);
  renderModalGallery(filtered);
}

// Lightbox Viewer
function openLightbox(index) {
  currentLightboxIndex = index;
  const f = currentCategoryFiles[index];
  if (!f) return;

  const { isImg, isVid } = isImageOrVideo(f.filename);
  const previewUrl = `/api/media/preview?path=${encodeURIComponent(f.path)}`;
  const container = document.getElementById("lightboxMediaContainer");
  
  document.getElementById("lightboxFileTitle").textContent = `${f.filename} (${f.size_str})`;

  if (isVid) {
    container.innerHTML = `<video class="lightbox-video" src="${previewUrl}" controls autoplay></video>`;
  } else if (isImg) {
    container.innerHTML = `<img class="lightbox-img" src="${previewUrl}" alt="${f.filename}">`;
  } else {
    container.innerHTML = `
      <div style="background:#1e293b; padding:40px; border-radius:14px; text-align:center;">
        <i class="bi bi-file-earmark-text" style="font-size:48px; color:var(--accent-primary);"></i>
        <h4 style="margin-top:12px;">${f.filename}</h4>
        <p style="color:var(--text-muted); font-size:13px; margin-top:4px;">${f.path}</p>
        <p style="font-size:14px; margin-top:8px;">Size: ${f.size_str}</p>
      </div>
    `;
  }

  document.getElementById("lightboxModal").classList.add("show");
}

function closeLightbox() {
  const container = document.getElementById("lightboxMediaContainer");
  const vid = container.querySelector("video");
  if (vid) vid.pause();
  document.getElementById("lightboxModal").classList.remove("show");
}

function navLightbox(step) {
  const nextIdx = currentLightboxIndex + step;
  if (nextIdx >= 0 && nextIdx < currentCategoryFiles.length) {
    openLightbox(nextIdx);
  }
}

async function deleteCurrentLightboxItem() {
  const f = currentCategoryFiles[currentLightboxIndex];
  if (!f) return;

  if (!confirm(`Are you sure you want to delete "${f.filename}" from your phone?`)) return;

  try {
    const res = await fetch("/api/clean", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_paths: [f.path], dry_run: false })
    });
    const data = await res.json();
    if (data.success) {
      currentCategoryFiles.splice(currentLightboxIndex, 1);
      renderModalFileList(currentCategoryFiles);
      renderModalGallery(currentCategoryFiles);
      if (currentCategoryFiles.length > 0) {
        openLightbox(Math.min(currentLightboxIndex, currentCategoryFiles.length - 1));
      } else {
        closeLightbox();
      }
      refreshDeviceStatus();
    }
  } catch (e) {
    alert("Delete failed: " + e);
  }
}

async function deleteSelectedInModal() {
  const count = selectedFilePaths.size;
  if (count === 0) return;

  if (!confirm(`Are you sure you want to permanently delete these ${count} selected files from your phone?`)) return;

  showProgressModal("Deleting Selected Files...", `Deleting ${count} files from phone...`);

  try {
    const res = await fetch("/api/clean", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_paths: Array.from(selectedFilePaths), dry_run: false })
    });
    const data = await res.json();
    closeModal("progressModal");

    if (data.success) {
      alert(`✅ Deleted ${data.result.deleted_count} files from your phone!`);
      // Reload current category
      openCategoryModal(currentCategoryKey, document.getElementById("modalCategoryTitle").textContent);
      fetchScanResults();
      refreshDeviceStatus();
    }
  } catch (e) {
    alert("Delete failed: " + e);
    closeModal("progressModal");
  }
}

// Backup Operation
async function startBackup() {
  if (!scanData) {
    alert("Please scan phone first.");
    return;
  }

  const dest = document.getElementById("backupDestinationInput").value.trim();
  if (!dest) {
    alert("Please provide a backup destination path on your PC.");
    return;
  }

  // Backup recommended categories
  const categoriesToBackup = ["important_docs", "messaging_docs", "camera_media", "audio_music"];
  showProgressModal("Backing Up Important Documents & Media...", "Starting safe copy to PC...");

  try {
    const res = await fetch("/api/backup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        category_keys: categoriesToBackup,
        destination: dest
      })
    });
    if (!res.ok) {
      const err = await res.json();
      alert("Backup error: " + (err.detail || "Unknown"));
      closeModal("progressModal");
    }
  } catch (e) {
    alert("Backup request error: " + e);
    closeModal("progressModal");
  }
}

// Clean Operations (Dry Run & Execution)
async function previewClean() {
  if (!scanData) {
    alert("Please scan phone first.");
    return;
  }

  const cleanCategories = ["screenshots", "junk_cache", "apks"];
  showProgressModal("Analyzing Files to Clean...", "Calculating space savings...");

  try {
    const res = await fetch("/api/clean", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        category_keys: cleanCategories,
        dry_run: true
      })
    });
    const data = await res.json();
    closeModal("progressModal");

    if (data.result) {
      renderDryRunPreview(data.result);
    }
  } catch (e) {
    alert("Preview clean error: " + e);
    closeModal("progressModal");
  }
}

function renderDryRunPreview(dryRunResult) {
  document.getElementById("cleanPreviewSummary").textContent = `${dryRunResult.total_target_files} files selected | Freeing ${dryRunResult.freed_formatted}`;
  
  const tbody = document.getElementById("cleanPreviewListBody");
  tbody.innerHTML = "";

  const previewList = dryRunResult.preview_files || [];
  previewList.slice(0, 100).forEach(f => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-weight: 500;">${f.filename}</td>
      <td class="file-path-sub">${f.path}</td>
      <td>${f.size_str}</td>
    `;
    tbody.appendChild(tr);
  });

  if (previewList.length > 100) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="3" style="text-align:center; color:var(--text-muted);">+ ${previewList.length - 100} more files...</td>`;
    tbody.appendChild(tr);
  }

  openModal("cleanConfirmModal");
}

async function executeClean() {
  closeModal("cleanConfirmModal");
  showProgressModal("Cleaning Unwanted Files...", "Deleting screenshots and junk files...");

  const cleanCategories = ["screenshots", "junk_cache", "apks"];
  try {
    const res = await fetch("/api/clean", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        category_keys: cleanCategories,
        dry_run: false
      })
    });
    if (!res.ok) {
      const err = await res.json();
      alert("Clean execution error: " + (err.detail || "Unknown"));
      closeModal("progressModal");
    }
  } catch (e) {
    alert("Clean request error: " + e);
    closeModal("progressModal");
  }
}

// Modal Helpers
function openModal(id) {
  document.getElementById(id).classList.add("show");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("show");
}

function showProgressModal(title, initialStatus) {
  document.getElementById("progressModalTitle").textContent = title;
  document.getElementById("progressStatusText").textContent = initialStatus;
  document.getElementById("liveProgressBarFill").style.width = "0%";
  document.getElementById("liveLogBox").innerHTML = `[${new Date().toLocaleTimeString()}] ${initialStatus}`;
  document.getElementById("progressModalFooter").style.display = "none";
  openModal("progressModal");
}

function updateProgressUI(status, percent) {
  document.getElementById("progressStatusText").textContent = status;
  document.getElementById("liveProgressBarFill").style.width = `${percent}%`;
  
  const logBox = document.getElementById("liveLogBox");
  const newLine = document.createElement("div");
  newLine.textContent = `[${percent}%] ${status}`;
  logBox.appendChild(newLine);
  logBox.scrollTop = logBox.scrollHeight;
}

function showOperationComplete(title, htmlMessage) {
  document.getElementById("progressModalTitle").textContent = title;
  document.getElementById("progressStatusText").innerHTML = `<span style="color: var(--success); font-weight:600;"><i class="bi bi-check-circle-fill"></i> Done</span>`;
  document.getElementById("liveProgressBarFill").style.width = "100%";
  
  const logBox = document.getElementById("liveLogBox");
  logBox.innerHTML = `<div style="color: #6ee7b7; padding: 4px 0;">${htmlMessage}</div>`;
  document.getElementById("progressModalFooter").style.display = "block";
}

async function triggerAutoContribute() {
  showProgressModal("Autonomous Open-Source Dispatch", "Scouting unassigned open-source issues...");
  updateProgressUI("Authenticating via GitHub OAuth Bridge...", 15);

  try {
    const res = await fetch("/api/auto-contribute/run", { method: "POST" });
    const data = await res.json();

    if (data.success && data.result) {
      const pr = data.result;
      const html = `
        <div style="background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); border-radius: 8px; padding: 12px; margin-top: 8px;">
          <h4 style="color: #34d399; margin: 0 0 6px 0; font-size: 15px;"><i class="bi bi-patch-check-fill"></i> Pull Request Successfully Submitted!</h4>
          <p style="margin: 0 0 8px 0; font-size: 13px;">Target: <b>${pr.repo}</b> (${pr.topic})</p>
          <a href="${pr.pr_url}" target="_blank" class="btn btn-success btn-sm" style="display: inline-flex; align-items: center; gap: 6px; text-decoration: none; font-weight: 600;">
            <i class="bi bi-box-arrow-up-right"></i> View PR #${pr.pr_number} on GitHub ↗
          </a>
        </div>
      `;
      showOperationComplete("Contribution Dispatched!", html);
    } else {
      showOperationComplete("Status", `<span style="color: #f87171;">${data.error || data.message || "No pending unassigned issues."}</span>`);
    }
  } catch (err) {
    showOperationComplete("Failed", `<span style="color: #f87171;">Error: ${err.message}</span>`);
  }
}
