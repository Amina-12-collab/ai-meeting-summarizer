function updateGreeting() {
  const hour = new Date().getHours();
  let greeting = "Welcome back";

  if (hour < 12) {
    greeting = "Good morning, welcome back";
  } else if (hour < 17) {
    greeting = "Good afternoon, welcome back";
  } else {
    greeting = "Good evening, welcome back";
  }

  document.getElementById("greetingText").textContent = greeting;
}
const pageTitles = {
    dashboard:  ['Dashboard',    ''],
    upload:     ['Upload Audio', '/ New File'],
    history:    ['History',      '/ All Records'],
    settings:   ['Settings',     '/ Preferences'],
    analytics:  ['Analytics',    '/ Insights'],
    team:       ['Team',         '/ Members']
  };

  let fileCount = 0, summaryCount = 0, actionCount = 0;
  let historyItems = [];

  function showPage(id) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
    const navMap = ['dashboard','upload','history','settings','analytics','team'];
    const navLinks = document.querySelectorAll('nav a');
    const idx = navMap.indexOf(id);
    if (idx >= 0 && navLinks[idx]) navLinks[idx].classList.add('active');
    document.getElementById('headerTitle').textContent = pageTitles[id][0];
    document.getElementById('headerSub').textContent = pageTitles[id][1];
  }

  function openLogin() { document.getElementById('loginModal').classList.add('open'); }
  function closeLogin() { document.getElementById('loginModal').classList.remove('open'); }

  document.getElementById('audioFile').addEventListener('change', function() {
    if (this.files[0]) {
      const f = this.files[0];
      document.getElementById('fileSelected').style.display = 'flex';
      document.getElementById('fileNameDisplay').textContent = f.name;
      document.getElementById('fileSizeDisplay').textContent = (f.size / 1024).toFixed(1) + ' KB';
    }
  });

  const dropZone = document.getElementById('dropZone');
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault(); dropZone.classList.remove('drag-over');
    const f = e.dataTransfer.files[0];
    if (f) {
      document.getElementById('fileSelected').style.display = 'flex';
      document.getElementById('fileNameDisplay').textContent = f.name;
      document.getElementById('fileSizeDisplay').textContent = (f.size/1024).toFixed(1) + ' KB';
    }
  });

  function clearUpload() {
    document.getElementById('audioFile').value = '';
    document.getElementById('fileSelected').style.display = 'none';
    document.getElementById('resultCard').style.display = 'none';
    document.getElementById('progressWrap').style.display = 'none';
  }

  async function uploadAudio() {
    const file = document.getElementById('audioFile').files[0];
    const name = document.getElementById('fileNameDisplay').textContent;
    if (!file && !name) { alert('Please select a file first.'); return; }

    const pw = document.getElementById('progressWrap');
    const bar = document.getElementById('progressBar');
    const lbl = document.getElementById('progressLabel');
    const pct = document.getElementById('progressPct');

    pw.style.display = 'block';
    document.getElementById('resultCard').style.display = 'none';

    const steps = [
      ['Uploading file...', 20],
      ['Transcribing audio...', 45],
      ['Running AI analysis...', 75],
      ['Generating summary...', 95],
      ['Complete!', 100]
    ];

    for (const [msg, p] of steps) {
      lbl.textContent = msg; pct.textContent = p + '%';
      bar.style.width = p + '%';
      await new Promise(r => setTimeout(r, 600));
    }

    await new Promise(r => setTimeout(r, 300));
    pw.style.display = 'none';

    const fname = file ? file.name : name;
    document.getElementById('summaryText').textContent =
      `This meeting covered the project status update for Q2 2026. The team discussed progress on the AI integration module, reviewed pending milestones, and aligned on the delivery timeline. Key challenges around data pipeline latency were acknowledged and assigned for resolution.`;

    document.getElementById('keypointsText').innerHTML = [
      'AI integration module is 70% complete and on track.',
      'Data pipeline latency identified as a critical blocker.',
      'Client demo scheduled for end of April 2026.',
      'Budget review required before next sprint kick-off.',
      'New team member onboarding planned for next week.'
    ].map(p => `<div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid var(--border);font-size:14px;color:var(--text-2)"><span style="color:var(--accent);font-weight:600;margin-top:1px">→</span>${p}</div>`).join('');

    document.getElementById('actionsText').innerHTML = [
      {who:'Ravi', task:'Fix data pipeline latency issue', due:'Apr 18'},
      {who:'Priya', task:'Prepare client demo environment', due:'Apr 22'},
      {who:'Team Lead', task:'Submit budget review document', due:'Apr 20'},
    ].map(a => `<div class="action-item"><div class="action-check"></div><div><span style="font-weight:500">${a.task}</span><br><span style="font-size:12px;color:var(--text-3)">Assigned to ${a.who} · Due ${a.due}</span></div></div>`).join('');

    document.getElementById('decisionsText').innerHTML = [
      'Approved: Go-ahead on Phase 2 development.',
      'Decided: Weekly sync moved to Fridays at 10 AM.',
      'Agreed: Additional QA resource to be allocated.'
    ].map(d => `<div style="display:flex;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);font-size:14px;color:var(--text-2)"><span style="color:var(--success);font-weight:600">✓</span>${d}</div>`).join('');

    document.getElementById('resultCard').style.display = 'block';
    document.getElementById('resultCard').scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    fileCount++; summaryCount++; actionCount += 3;
    document.getElementById('fileCount').textContent = fileCount;
    document.getElementById('summaryCount').textContent = summaryCount;
    document.getElementById('actionCount').textContent = actionCount;
    if (document.getElementById('a-fileCount')) {
      document.getElementById('a-fileCount').textContent = fileCount;
      document.getElementById('a-summaryCount').textContent = summaryCount;
      document.getElementById('a-actionCount').textContent = actionCount;
    }
    renderAnalyticsLog();
    document.getElementById('recentBadge').textContent = fileCount + ' file' + (fileCount > 1 ? 's' : '');

    const now = new Date();
    historyItems.unshift({ name: fname, date: now.toLocaleDateString('en-GB'), size: file ? (file.size/1024).toFixed(1) + ' KB' : '—', status: 'Complete' });
    renderHistory();
    renderRecent();

    [1,2,3,4].forEach(i => document.getElementById('step'+i).classList.add('done'));
  }

  function switchTab(id, el) {
    document.querySelectorAll('.result-tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    ['summary','keypoints','actions','decisions'].forEach(t => {
      document.getElementById('tab-'+t).style.display = t === id ? '' : 'none';
    });
  }

  function renderHistory() {
    const body = document.getElementById('historyBody');
    if (!historyItems.length) {
      body.innerHTML = '<tr><td colspan="5"><div class="empty-state"><p>No history yet.</p></div></td></tr>';
      return;
    }
    body.innerHTML = historyItems.map(h => `
      <tr>
        <td><div style="display:flex;align-items:center;gap:10px">
          <div class="file-icon" style="width:30px;height:30px">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </div>
          <span style="font-weight:500;font-size:13px">${h.name}</span>
        </div></td>
        <td style="color:var(--text-3);font-size:13px">${h.date}</td>
        <td style="color:var(--text-3);font-size:13px">${h.size}</td>
        <td><span class="badge badge-success">${h.status}</span></td>
        <td><span class="action-link" onclick="showPage('upload')">View</span></td>
      </tr>
    `).join('');
  }

  function renderRecent() {
    const el = document.getElementById('recentList');
    el.innerHTML = historyItems.slice(0,4).map(h => `
      <div class="recent-item">
        <div class="file-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
        <div class="recent-info">
          <div class="recent-name">${h.name}</div>
          <div class="recent-meta">${h.date} · ${h.size}</div>
        </div>
        <span class="badge badge-success">${h.status}</span>
      </div>
    `).join('');
  }

  function switchSettingsTab(id, el) {
    document.querySelectorAll('.settings-nav-item').forEach(n => n.classList.remove('active'));
    el.classList.add('active');
    document.querySelectorAll('.settings-section').forEach(s => s.classList.remove('active'));
    document.getElementById('settings-'+id).classList.add('active');
  }

  function copySummary() {
    const t = document.getElementById('summaryText').textContent;
    navigator.clipboard.writeText(t).then(() => alert('Summary copied!'));
  }

  function downloadSummary() {
    const t = document.getElementById('summaryText').textContent;
    const a = document.createElement('a');
    a.href = 'data:text/plain,' + encodeURIComponent(t);
    a.download = 'meeting-summary.txt';
    a.click();
  }

  function renderAnalyticsLog() {
    const el = document.getElementById('analyticsLog');
    if (!el || !historyItems.length) return;
    el.innerHTML = historyItems.map(h => `
      <div style="display:flex;align-items:center;gap:14px;padding:12px 0;border-bottom:1px solid var(--border)">
        <div class="file-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
        <div style="flex:1">
          <div style="font-size:14px;font-weight:500">${h.name}</div>
          <div style="font-size:12px;color:var(--text-3)">${h.date} · ${h.size}</div>
        </div>
        <span class="badge badge-success">${h.status}</span>
        <span style="font-size:12px;color:var(--text-3)">3.1s</span>
      </div>
    `).join('');
  }

  function openInviteModal() {
    document.getElementById('inviteModal').classList.add('open');
  }
  function closeInviteModal() {
    document.getElementById('inviteModal').classList.remove('open');
  }

  // Draw bar chart on analytics page load
  function drawBarChart() {
    const bars = document.getElementById('barChart');
    const labels = document.getElementById('barLabels');
    if (!bars) return;
    const months = ['Nov','Dec','Jan','Feb','Mar','Apr'];
    const vals = [4, 7, 5, 9, 6, fileCount || 3];
    const max = Math.max(...vals);
    bars.innerHTML = vals.map((v,i) => `
      <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px">
        <span style="font-size:11px;color:var(--text-3);font-weight:500">${v}</span>
        <div style="width:100%;background:${i===5?'var(--accent)':'var(--surface-3)'};border-radius:4px 4px 0 0;height:${Math.round((v/max)*100)}px;transition:height 0.4s ease"></div>
      </div>
    `).join('');
    labels.innerHTML = months.map(m => `<span>${m}</span>`).join('');
  }

  // Patch showPage to draw chart when analytics loads
  const _origShowPage = showPage;
  // Already defined above — just call drawBarChart when analytics shown
  document.addEventListener('click', e => {
    if (e.target.closest('[onclick]')) {
      const fn = e.target.closest('[onclick]')?.getAttribute('onclick');
      if (fn && fn.includes('analytics')) setTimeout(drawBarChart, 50);
    }
  });
  updateGreeting();