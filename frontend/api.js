/* 后端接口客户端：所有调用走同源反代或直连 baseUrl，统一返回 ApiResponse。
 * 字段命名严格对齐 .spec.md「统一属性命名约定」与 app/schemas 的 Pydantic 模型。
 */

(function (global) {
  'use strict';

  const DEFAULT_BASE_URL = 'http://127.0.0.1:8000';
  const TOKEN_KEY = 'crs.token';
  const USER_KEY = 'crs.user';

  const state = { baseUrl: DEFAULT_BASE_URL };

  function setBaseUrl(url) {
    state.baseUrl = String(url || DEFAULT_BASE_URL).replace(/\/+$/, '');
    try { localStorage.setItem('crs.baseUrl', state.baseUrl); } catch (e) {}
  }

  function initBaseUrl() {
    try {
      const cached = localStorage.getItem('crs.baseUrl');
      if (cached) state.baseUrl = cached;
    } catch (e) {}
  }

  function getToken() {
    try { return localStorage.getItem(TOKEN_KEY) || ''; } catch (e) { return ''; }
  }

  function setToken(token) {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token);
      else localStorage.removeItem(TOKEN_KEY);
    } catch (e) {}
  }

  function getCurrentUser() {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  }

  function setCurrentUser(user) {
    try {
      if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
      else localStorage.removeItem(USER_KEY);
    } catch (e) {}
  }

  function clearAuth() { setToken(''); setCurrentUser(null); }

  async function request(method, path, options) {
    options = options || {};
    const query = options.query || null;
    const body = options.body;
    const withAuth = options.auth !== false;
    let url = state.baseUrl + path;
    if (query) {
      const qs = Object.keys(query)
        .filter(function (k) {
          const v = query[k];
          return v !== undefined && v !== null && v !== '';
        })
        .map(function (k) { return encodeURIComponent(k) + '=' + encodeURIComponent(query[k]); })
        .join('&');
      if (qs) url += (url.indexOf('?') >= 0 ? '&' : '?') + qs;
    }
    const headers = { Accept: 'application/json' };
    if (body !== undefined && body !== null) headers['Content-Type'] = 'application/json';
    if (withAuth) {
      const token = getToken();
      if (token) headers['Authorization'] = 'Bearer ' + token;
    }
    const init = { method: method, headers: headers };
    if (body !== undefined && body !== null) init.body = JSON.stringify(body);
    const res = await fetch(url, init);
    const text = await res.text();
    let payload = null;
    if (text) {
      try { payload = JSON.parse(text); }
      catch (e) { throw new Error('响应不是合法 JSON：' + text.slice(0, 200)); }
    }
    if (!res.ok) {
      const msg = (payload && payload.message) || ('HTTP ' + res.status);
      const err = new Error(msg);
      err.status = res.status;
      err.payload = payload;
      throw err;
    }
    return payload;
  }

  const authApi = {
    register: function (username, password) {
      return request('POST', '/api/auth/register',
        { body: { username: username, password: password }, auth: false });
    },
    login: function (username, password) {
      return request('POST', '/api/auth/login',
        { body: { username: username, password: password }, auth: false });
    },
    me: function () { return request('GET', '/api/auth/me'); },
  };

  const taskApi = {
    trigger: function () { return request('POST', '/api/tasks/trigger'); },
    list: function (params) { return request('GET', '/api/tasks', { query: params || {} }); },
    detail: function (taskId) { return request('GET', '/api/tasks/' + taskId); },
    retry: function (taskId) { return request('POST', '/api/tasks/' + taskId + '/retry'); },
  };

  const ruleApi = {
    list: function () { return request('GET', '/api/rules'); },
    create: function (payload) { return request('POST', '/api/rules', { body: payload }); },
    update: function (ruleId, payload) { return request('PUT', '/api/rules/' + ruleId, { body: payload }); },
    remove: function (ruleId) { return request('DELETE', '/api/rules/' + ruleId); },
  };

  const hitApi = {
    list: function (params) { return request('GET', '/api/hits', { query: params || {} }); },
    confirm: function (hitId) { return request('POST', '/api/hits/' + hitId + '/confirm'); },
    ignore: function (hitId) { return request('POST', '/api/hits/' + hitId + '/ignore'); },
  };

  const logApi = {
    list: function (params) { return request('GET', '/api/logs', { query: params || {} }); },
  };

  function health() { return request('GET', '/api/health', { auth: false }); }

  global.CRSApi = {
    setBaseUrl: setBaseUrl,
    initBaseUrl: initBaseUrl,
    getBaseUrl: function () { return state.baseUrl; },
    getToken: getToken,
    setToken: setToken,
    getCurrentUser: getCurrentUser,
    setCurrentUser: setCurrentUser,
    clearAuth: clearAuth,
    auth: authApi,
    tasks: taskApi,
    rules: ruleApi,
    hits: hitApi,
    logs: logApi,
    health: health,
  };
})(window);
