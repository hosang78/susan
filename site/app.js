(function () {
  'use strict';
  var SEAS = ['동해', '서해', '남해', '제주'];
  var state = { data: null, list: [], byId: {}, images: {}, imgExt: 'webp', group: '전체', sea: '전체', q: '', original: null, listScroll: 0 };
  var $ = function (id) { return document.getElementById(id); };
  var view = $('view');

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function getJSON(url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error(url); return r.json(); });
  }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  /* ---------- 그림 자리 ---------- */
  function picHTML(sp, alt) {
    if (state.images[sp.id]) {
      return '<div class="pic"><img src="images/' + esc(sp.id) + '.' + state.imgExt + '" alt="' + esc(alt) + '" loading="lazy" width="480" height="360"></div>';
    }
    return '<div class="pic" aria-hidden="true"><div class="ph">' +
      '<svg width="24" height="20" viewBox="0 0 24 20" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1.5" y="1.5" width="21" height="17" rx="2"></rect><circle cx="8" cy="7" r="2"></circle><path d="M2 16l6-5 4 3 4-4 6 5"></path></svg>' +
      '<span>그림 준비 중</span></div></div>';
  }
  function seasHTML(sea) {
    if (!sea || !sea.length) return '';
    return '<div class="seas">' + sea.map(function (s) { return '<span class="sea" data-s="' + esc(s) + '">' + esc(s) + '</span>'; }).join('') + '</div>';
  }
  function levelHTML(l) {
    var n = l === '상' ? 3 : l === '중' ? 2 : 1;
    return '<span class="level" aria-label="정보 충실도 ' + esc(l) + '">' + [1, 2, 3].map(function (i) { return '<i class="' + (i <= n ? 'on' : '') + '"></i>'; }).join('') + '</span> ' + esc(l);
  }

  /* ---------- 필터 ---------- */
  function norm(s) { return String(s || '').toLowerCase().replace(/\s+/g, ''); }
  function matches(sp) {
    if (state.group !== '전체' && sp.group !== state.group) return false;
    if (state.sea !== '전체' && sp.sea.indexOf(state.sea) < 0 && sp.sea.indexOf('전 연안') < 0) return false;
    if (state.q) {
      var q = norm(state.q);
      var hay = norm([sp.name, sp.kor, sp.sci, sp.sub, sp.fam, sp.group].join('|'));
      if (hay.indexOf(q) < 0) return false;
    }
    return true;
  }

  function renderChips() {
    var groups = ['전체'].concat(state.data.groups);
    $('groups').innerHTML = groups.map(function (g) {
      return '<button type="button" class="chip" data-g="' + esc(g) + '" aria-pressed="' + (state.group === g) + '">' + esc(g) + '</button>';
    }).join('');
    var seaBox = $('seas');
    seaBox.innerHTML = '<span class="chips-label">해역</span>' + ['전체'].concat(SEAS).map(function (s) {
      return '<button type="button" class="chip" data-s="' + esc(s) + '" aria-pressed="' + (state.sea === s) + '">' + esc(s) + '</button>';
    }).join('');
  }

  function renderList() {
    var items = state.list.filter(matches);
    $('count').textContent = items.length === state.list.length ? state.list.length + '종' : state.list.length + '종 중 ' + items.length + '종';
    if (!items.length) {
      view.innerHTML = '<p class="empty">찾는 생물이 없습니다. 이름을 다르게 입력하거나 그룹·해역 선택을 바꿔 보세요.</p>';
      return;
    }
    var html = '', cur = null, buf = [];
    function flush() {
      if (!cur) return;
      html += '<h2 class="group-head"><span>' + esc(cur) + '</span><span>' + buf.length + '종</span></h2><ul class="list">' + buf.join('') + '</ul>';
    }
    items.forEach(function (sp) {
      if (sp.group !== cur) { flush(); cur = sp.group; buf = []; }
      var sub = sp.name !== sp.kor ? '국명 ' + esc(sp.kor) + ' · ' : '';
      buf.push('<li><a class="card" href="#sp-' + esc(sp.id) + '">' + picHTML(sp, sp.name) +
        '<div><div class="t-name">' + esc(sp.name) + '</div>' +
        '<div class="t-sub">' + sub + '<span class="sci">' + esc(sp.sci) + '</span></div>' +
        '<div class="t-intro">' + esc(sp.intro) + '</div>' + seasHTML(sp.sea) + '</div></a></li>');
    });
    flush();
    view.innerHTML = html;
  }

  /* ---------- 상세 ---------- */
  var SECTIONS = [['look', '생김새'], ['life', '사는 곳·생태'], ['breed', '산란·번식 시기'], ['use', '먹는 법·이용'], ['note', '알아두면 좋은 점']];
  function renderDetail(sp) {
    var names = [];
    if (sp.name !== sp.kor) names.push('국명 ' + esc(sp.kor));
    names.push('<span class="sci">' + esc(sp.sci) + '</span>');
    var basis = sp.seaBasis === '지명으로 추정' ? '<span class="hint">(지명 기준 추정)</span>' : '';
    var secs = SECTIONS.filter(function (s) { return sp[s[0]]; }).map(function (s) {
      return '<section class="sec"><h3>' + s[1] + '</h3><p>' + esc(sp[s[0]]) + '</p></section>';
    }).join('');
    var thin = sp.level === '하' ? '<p class="notice">원문에 실린 설명이 적어 일부 항목만 보여 드립니다.</p>' : '';
    view.innerHTML =
      '<article class="detail">' +
      '<button type="button" class="back" id="back"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M15 18l-6-6 6-6"></path></svg>목록</button>' +
      picHTML(sp, sp.name + ' 그림') +
      '<div class="d-head"><h2>' + esc(sp.name) + '</h2><div class="d-names">' + names.join(' · ') + '</div>' +
      '<div class="d-path">' + [sp.group, sp.sub, sp.fam].filter(function (x, i, a) { return x && a.indexOf(x) === i; }).map(esc).join(' › ') + '</div></div>' +
      '<p class="d-intro">' + esc(sp.intro) + '</p>' +
      '<dl class="meta"><dt>국내 해역</dt><dd>' + (sp.sea.length ? seasHTML(sp.sea) + basis : '<span class="hint">원문에 국내 분포 정보 없음</span>') + '</dd>' +
      '<dt>정보 충실도</dt><dd>' + levelHTML(sp.level) + '</dd></dl>' +
      thin + '<div class="sections">' + secs + '</div>' +
      '<button type="button" class="orig-btn" id="origBtn" aria-expanded="false" aria-controls="orig">원문 보기</button>' +
      '<div class="orig" id="orig" hidden></div>' +
      '</article>';
    document.title = sp.name + ' · 해양수산도감';
    $('back').addEventListener('click', function () {
      if (history.length > 1 && state.cameFromList) history.back(); else location.hash = '';
    });
    $('origBtn').addEventListener('click', function () { toggleOriginal(sp); });
  }

  function toggleOriginal(sp) {
    var box = $('orig'), btn = $('origBtn');
    if (!box.hidden) { box.hidden = true; btn.textContent = '원문 보기'; btn.setAttribute('aria-expanded', 'false'); return; }
    box.hidden = false; btn.textContent = '원문 닫기'; btn.setAttribute('aria-expanded', 'true');
    box.innerHTML = '<p class="hint">원문을 불러오는 중입니다.</p>';
    var p = state.original ? Promise.resolve(state.original) : getJSON('data/original.json').then(function (o) { state.original = o; return o; });
    p.then(function (o) {
      var vers = o[sp.id] || [];
      var withText = vers.filter(function (v) { return v.fields.length; });
      if (!withText.length) { box.innerHTML = '<p class="notice">이 종은 원문에 설명 항목이 없습니다. 학명: <span class="sci">' + esc(sp.sci) + '</span></p>'; return; }
      var many = withText.length > 1;
      box.innerHTML = '<p class="hint">국립해양생물자원관 해양생물종정보 서비스의 원문을 고치지 않고 그대로 보여 드립니다.' +
        (many ? ' 같은 종이라도 조회 방식에 따라 내용이 달라 두 가지를 함께 싣습니다.' : '') + '</p>' +
        withText.map(function (v) {
          var label = !many ? '원문' : v.ver === '목록조회본' ? '원문 1 · 목록 조회' : '원문 2 · 종별 조회';
          return '<section class="orig-ver"><h4>' + label + ' · <span class="sci">' + esc(v.sciFull) + '</span></h4><dl>' +
            v.fields.map(function (f) { return '<dt>' + esc(f[0]) + '</dt><dd>' + esc(f[1]) + '</dd>'; }).join('') + '</dl></section>';
        }).join('');
    }).catch(function () {
      box.innerHTML = '<p class="notice">원문을 불러오지 못했습니다. 인터넷 연결을 확인한 뒤 다시 눌러 주세요.</p>';
      btn.textContent = '원문 보기'; btn.setAttribute('aria-expanded', 'false'); setTimeout(function () { box.hidden = true; }, 2500);
    });
  }

  /* ---------- 라우팅 ---------- */
  function route() {
    var h = location.hash.replace('#', '');
    var m = /^sp-(\d+)$/.exec(h);
    if (m && state.byId[m[1]]) {
      state.cameFromList = state.cameFromList || false;
      document.body.setAttribute('data-view', 'detail');
      renderDetail(state.byId[m[1]]);
      window.scrollTo(0, 0);
    } else {
      document.body.setAttribute('data-view', 'list');
      document.title = '해양수산도감';
      renderList();
      window.scrollTo(0, state.listScroll || 0);
    }
  }

  function bind() {
    $('q').addEventListener('input', function (e) {
      state.q = e.target.value.trim();
      if (location.hash) { location.hash = ''; return; }
      renderList();
    });
    $('groups').addEventListener('click', function (e) {
      var b = e.target.closest('[data-g]'); if (!b) return;
      state.group = b.getAttribute('data-g'); store('dogam.group', state.group); renderChips();
      if (location.hash) location.hash = ''; else renderList();
    });
    $('seas').addEventListener('click', function (e) {
      var b = e.target.closest('[data-s]'); if (!b) return;
      state.sea = b.getAttribute('data-s'); store('dogam.sea', state.sea); renderChips();
      if (location.hash) location.hash = ''; else renderList();
    });
    view.addEventListener('click', function (e) {
      if (e.target.closest('.card')) { state.listScroll = window.scrollY; state.cameFromList = true; }
    });
    window.addEventListener('hashchange', function () {
      if (!location.hash) state.cameFromList = false;
      route();
    });
  }

  Promise.all([getJSON('data/species.json'), getJSON('data/images.json').catch(function () { return { ext: 'webp', ids: [] }; })])
    .then(function (res) {
      state.data = res[0];
      state.list = res[0].species;
      state.list.forEach(function (s) { state.byId[s.id] = s; });
      state.imgExt = res[1].ext || 'webp';
      (res[1].ids || []).forEach(function (id) { state.images[id] = true; });
      var g = store('dogam.group'), s = store('dogam.sea');
      if (g && (g === '전체' || state.data.groups.indexOf(g) >= 0)) state.group = g;
      if (s && (s === '전체' || SEAS.indexOf(s) >= 0)) state.sea = s;
      renderChips(); bind(); route();
    })
    .catch(function () {
      view.innerHTML = '<p class="empty">도감 자료를 불러오지 못했습니다. 이 폴더를 웹 서버로 열어 주세요(예: site 폴더에서 <code>python3 -m http.server</code> 실행 후 http://localhost:8000 접속).</p>';
    });
})();
