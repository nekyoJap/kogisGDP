/**
 * predictions.js - AI予想JSON読み込み・表示ロジック
 *
 * GitHub Pages 上で predictions/ ディレクトリの JSON を fetch して表示する。
 * 全データ取得は静的ファイルサーバーのみで完結（サーバーサイド不要）。
 */

(function () {
  'use strict';

  // GitHub Pages のベース URL を動的に検出
  const BASE_PATH = (() => {
    const loc = window.location;
    // GitHub Pages: https://user.github.io/repo/
    // ローカル: http://localhost:8080/ または file:///...
    const path = loc.pathname;
    // /docs/ は GitHub Pages の設定によって含まれない場合がある
    const segments = path.split('/').filter(Boolean);
    // repo名を含むパスを構築
    if (loc.hostname.endsWith('github.io') && segments.length >= 1) {
      return `/${segments[0]}/docs/predictions`;
    }
    // ローカル開発時
    return './predictions';
  })();

  // 車番 → 色クラス
  const CAR_CLASS = {
    1: 'car-1', 2: 'car-2', 3: 'car-3',
    4: 'car-4', 5: 'car-5', 6: 'car-6',
    7: 'car-7', 8: 'car-8', 9: 'car-9',
  };

  // グレード → CSSクラス
  const GRADE_CLASS = {
    GP: 'grade-gp', GI: 'grade-gi', GII: 'grade-gii',
    GIII: 'grade-giii', FI: 'grade-fi', FII: 'grade-fii',
  };

  // JST の今日の日付 (YYYY-MM-DD)
  function getTodayJST() {
    const now = new Date();
    const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
    return jst.toISOString().split('T')[0];
  }

  // 日付文字列を ±N 日移動する
  function shiftDate(dateStr, days) {
    const d = new Date(dateStr + 'T00:00:00+09:00');
    d.setDate(d.getDate() + days);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  // summary.json を取得する
  async function fetchSummary(dateStr) {
    const url = `${BASE_PATH}/${dateStr}/summary.json?v=${Date.now()}`;
    try {
      const res = await fetch(url);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  // レース予想 JSON を取得する
  async function fetchPrediction(dateStr, venueCode, raceNumber) {
    const padded = String(raceNumber).padStart(2, '0');
    const url = `${BASE_PATH}/${dateStr}/${venueCode}_${padded}.json`;
    try {
      const res = await fetch(url);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  // 車番バッジ HTML
  function carBadge(num) {
    const cls = CAR_CLASS[num] || '';
    return `<span class="car-num ${cls}">${num}</span>`;
  }

  // 信頼度バーのクラスを決定
  function confClass(value) {
    if (value >= 0.7) return 'high';
    if (value >= 0.5) return 'mid';
    return 'low';
  }

  // 3連単コンボを文字列に変換（例: "2-1-5"）
  function comboStr(arr) {
    return arr.join('-');
  }

  // レースカードの HTML を生成する
  function buildRaceCard(data) {
    const pred = data.prediction || {};
    const grade = data.grade || '';
    const gradeCls = GRADE_CLASS[grade] || 'grade-fi';
    const confidence = typeof pred.confidence === 'number' ? pred.confidence : 0.5;
    const confPct = Math.round(confidence * 100);

    // TOP3
    const top3 = Array.isArray(pred.top3) ? pred.top3 : [];
    const top3Html = top3.map((n, i) => {
      const sep = i < top3.length - 1 ? '<span class="top3-sep">→</span>' : '';
      return carBadge(n) + sep;
    }).join('');

    // ライン構成
    const formations = Array.isArray(pred.formation) ? pred.formation : [];
    const formationHtml = formations.map(f =>
      `<p>${escapeHtml(f)}</p>`
    ).join('');

    // 3連単
    const sanrentan = pred.recommended_bets?.sanrentan || [];
    const wide = pred.recommended_bets?.wide || [];

    const santanRows = sanrentan.slice(0, 16).map(combo =>
      `<div class="bet-line">
        <span class="bet-type">3連単</span>
        <div class="bet-combo">
          ${combo.map(n => `<span class="bet-combo-item">${carBadge(n)}</span>`).join('<span style="color:var(--color-text-muted);padding:0 2px">-</span>')}
        </div>
       </div>`
    ).join('');

    const wideRows = wide.slice(0, 3).map(combo =>
      `<div class="bet-line">
        <span class="bet-type">ワイド</span>
        <div class="bet-combo">
          ${combo.map(n => `<span class="bet-combo-item">${carBadge(n)}</span>`).join('<span style="color:var(--color-text-muted);padding:0 2px">-</span>')}
        </div>
       </div>`
    ).join('');

    const reasoning = escapeHtml(pred.reasoning || '');

    return `
      <div class="race-card">
        <div class="card-header">
          <span class="grade-badge ${gradeCls}">${grade}</span>
          <span class="venue-name">${escapeHtml(data.venue || '')}</span>
          <span class="race-num">${data.race_number || ''}R</span>
        </div>
        <div class="card-body">
          <div class="top3-row">
            <span class="top3-label">予想</span>
            <div class="top3-numbers">${top3Html}</div>
          </div>
          ${formationHtml ? `<div class="formation">${formationHtml}</div>` : ''}
          <div class="confidence-row">
            <span class="confidence-label">信頼度</span>
            <div class="confidence-bar-wrap">
              <div class="confidence-bar-fill ${confClass(confidence)}" style="width:${confPct}%"></div>
            </div>
            <span class="confidence-value">${confPct}%</span>
          </div>
          ${(sanrentan.length || wide.length) ? `
          <div class="bets-section">
            <div class="bets-title">推奨買い目 <span class="bet-count">${sanrentan.length}点</span></div>
            ${santanRows}
            ${wideRows}
          </div>` : ''}
          ${reasoning ? `
          <details class="reasoning-details">
            <summary>予想根拠</summary>
            <div class="reasoning-text">${reasoning}</div>
          </details>` : ''}
        </div>
      </div>`;
  }

  // エラーカードの HTML
  function buildErrorCard(venueCode, raceNumber) {
    return `
      <div class="race-card error-card">
        <div class="card-header">
          <span class="grade-badge" style="background:#555">?</span>
          <span class="venue-name">${escapeHtml(venueCode)}</span>
          <span class="race-num">${raceNumber}R</span>
        </div>
        <div class="card-body">
          <div class="status-msg" style="padding:20px 0">予想を生成できませんでした</div>
        </div>
      </div>`;
  }

  // HTML エスケープ
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // メイン描画処理
  async function renderDate(dateStr) {
    const cardsEl = document.getElementById('race-cards');
    const tabsEl = document.getElementById('venue-tabs');
    const statusEl = document.getElementById('status-msg');

    // ローディング表示
    cardsEl.innerHTML = '';
    tabsEl.innerHTML = '';
    statusEl.innerHTML = '<span class="loading-spinner"></span>データを読み込み中...';
    statusEl.style.display = 'block';

    const summary = await fetchSummary(dateStr);
    if (!summary) {
      statusEl.innerHTML = `
        <span class="status-icon">📭</span>
        ${escapeHtml(dateStr)} の予想データはまだ準備中です。<br>
        毎朝 7:00 頃に自動生成されます。`;
      return;
    }

    statusEl.style.display = 'none';

    const venues = summary.venues || [];
    if (!venues.length) {
      statusEl.innerHTML = '<span class="status-icon">🏁</span>本日は開催なしです。';
      statusEl.style.display = 'block';
      return;
    }

    // 開催場タブを生成
    let firstVenueCode = null;
    venues.forEach((venue, idx) => {
      if (!firstVenueCode) firstVenueCode = venue.code;
      const tab = document.createElement('button');
      tab.className = 'venue-tab' + (idx === 0 ? ' active' : '');
      tab.textContent = venue.name || venue.code;
      tab.dataset.code = venue.code;
      tab.addEventListener('click', () => switchVenue(venue.code));
      tabsEl.appendChild(tab);
    });

    // 全レース予想を並行取得
    const allPromises = venues.flatMap(venue =>
      (venue.races || []).map(raceNum =>
        fetchPrediction(dateStr, venue.code, raceNum)
          .then(data => ({ venue, raceNum, data }))
      )
    );
    const results = await Promise.allSettled(allPromises);

    // カードを DOM に追加（venue ごとに data-venue 付与）
    results.forEach(r => {
      if (r.status !== 'fulfilled') return;
      const { venue, raceNum, data } = r.value;
      const el = document.createElement('div');
      el.dataset.venue = venue.code;
      if (data && !data.error) {
        el.innerHTML = buildRaceCard(data);
      } else {
        el.innerHTML = buildErrorCard(venue.code, raceNum);
      }
      cardsEl.appendChild(el);
    });

    // 最初の開催場を表示
    if (firstVenueCode) switchVenue(firstVenueCode);
  }

  // 開催場切り替え
  function switchVenue(venueCode) {
    // タブのアクティブ切り替え
    document.querySelectorAll('.venue-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.code === venueCode);
    });

    // カードの表示切り替え
    document.querySelectorAll('#race-cards > div[data-venue]').forEach(el => {
      el.style.display = el.dataset.venue === venueCode ? '' : 'none';
    });
  }

  // 初期化
  document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('date-input');
    const prevBtn = document.getElementById('date-prev');
    const nextBtn = document.getElementById('date-next');

    const today = getTodayJST();
    dateInput.value = today;
    dateInput.max = today;

    renderDate(today);

    dateInput.addEventListener('change', () => {
      if (dateInput.value) renderDate(dateInput.value);
    });

    prevBtn.addEventListener('click', () => {
      const newDate = shiftDate(dateInput.value, -1);
      dateInput.value = newDate;
      renderDate(newDate);
    });

    nextBtn.addEventListener('click', () => {
      const newDate = shiftDate(dateInput.value, 1);
      if (newDate <= today) {
        dateInput.value = newDate;
        renderDate(newDate);
      }
    });
  });
})();
