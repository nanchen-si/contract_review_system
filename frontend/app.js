/* 合同审查审批系统 · 前端应用主控
 * 视图：登录 / 任务 / 规则 / 命中 / 日志
 * 字段命名严格对齐 .spec.md「统一属性命名约定」
 */

(function () {
  "use strict";

  /* ===================== 工具函数 ===================== */
  const $ = function (sel, root) { return (root || document).querySelector(sel); };
  const $$ = function (sel, root) { return Array.from((root || document).querySelectorAll(sel)); };

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "class") node.className = attrs[k];
        else if (k === "style") node.style.cssText = attrs[k];
        else if (k === "html") node.innerHTML = attrs[k];
        else if (k.indexOf("on") === 0) node.addEventListener(k.slice(2), attrs[k]);
        else if (k === "dataset") {
          Object.keys(attrs[k]).forEach(function (dk) {
            node.dataset[dk] = attrs[k][dk];
          });
        } else if (attrs[k] === false || attrs[k] === null || attrs[k] === undefined) {
          /* skip */
        } else {
          node.setAttribute(k, attrs[k]);
        }
      });
    }
    if (children) {
      const list = Array.isArray(children) ? children : [children];
      list.forEach(function (c) {
        if (c === null || c === undefined || c === false) return;
        if (typeof c === "string" || typeof c === "number") {
          node.appendChild(document.createTextNode(String(c)));
        } else {
          node.appendChild(c);
        }
      });
    }
    return node;
  }

  function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function fmtDate(value) {
    if (!value) return "-";
    const d = new Date(value);
    if (isNaN(d.getTime())) return value;
    const pad = function (n) { return n < 10 ? "0" + n : "" + n; };
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) +
      " " + pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
  }

  function riskTag(level) {
    if (!level) return el("span", { class: "tag tag--low" }, "-");
    const cls = level === "high" ? "tag--high" : level === "medium" ? "tag--medium" : "tag--low";
    return el("span", { class: "tag " + cls }, level.toUpperCase());
  }

  function taskStatusTag(status) {
    const cls = "tag--" + status;
    return el("span", { class: "tag " + cls }, status);
  }

  function toast(message, type) {
    const host = $("#toast-host");
    if (!host) return;
    const cls = type === "error" ? "toast--error" : type === "success" ? "toast--success" : "";
    const node = el("div", { class: "toast " + cls }, message);
    host.appendChild(node);
    setTimeout(function () {
      node.style.opacity = "0";
      node.style.transition = "opacity 0.2s ease";
      setTimeout(function () { node.remove(); }, 240);
    }, 3000);
  }
  /* ===================== 路由 / 视图状态 ===================== */
  const VIEWS = ["login", "tasks", "rules", "hits", "logs"];
  const state = {
    view: "login",
    user: null,
    tasks: { items: [], page: 1, size: 20, total: 0, status: "" },
    rules: [],
    hits: { items: [] },
    logs: { items: [], page: 1, size: 20, total: 0 },
    detail: null,
  };

  function setView(view) {
    if (!VIEWS.includes(view)) return;
    state.view = view;
    renderHeader();
    render();
  }

  function render() {
    const main = $("#app-main");
    if (!main) return;
    main.innerHTML = "";
    if (!state.user && state.view !== "login") {
      state.view = "login";
    }
    if (state.view === "login") return renderLogin(main);
    if (state.view === "tasks") return renderTasks(main);
    if (state.view === "rules") return renderRules(main);
    if (state.view === "hits") return renderHits(main);
    if (state.view === "logs") return renderLogs(main);
  }
  /* ===================== 登录视图 ===================== */
  function renderLogin(main) {
    let mode = "login";
    const card = el("div", { class: "login-screen" });

    function buildCard() {
      const wrap = el("div", { class: "login-card" }, [
        el("div", { class: "login-card__eyebrow" }, "Contract Review System"),
        el("h1", null, mode === "login" ? "欢迎回来" : "注册新账号"),
        el("p", null, mode === "login"
          ? "请使用账号与密码登录后台，查看合同审查任务的最新状态。"
          : "注册一个 reviewer 账号；admin 账号已由系统种子提供。"),
        (function () {
          const tabs = el("div", { class: "login-tabs" }, [
            el("button", {
              class: "login-tab" + (mode === "login" ? " is-active" : ""),
              onclick: function () { mode = "login"; refresh(); },
            }, "登录"),
            el("button", {
              class: "login-tab" + (mode === "register" ? " is-active" : ""),
              onclick: function () { mode = "register"; refresh(); },
            }, "注册"),
          ]);
          return tabs;
        })(),
      ]);

      const form = el("form", {
        onsubmit: async function (e) {
          e.preventDefault();
          const username = $("#login-username").value.trim();
          const password = $("#login-password").value;
          if (!username || !password) {
            toast("请填写用户名与密码", "error");
            return;
          }
          try {
            const submitBtn = $("#login-submit");
            submitBtn.disabled = true;
            submitBtn.innerHTML = "<span class=\"loading\"></span> 正在处理…";
            const fn = mode === "login" ? "login" : "register";
            const resp = await CRSApi.auth[fn](username, password);
            if (mode === "register") {
              toast("注册成功，请使用该账号登录", "success");
              mode = "login";
              refresh();
              return;
            }
            CRSApi.setToken(resp.data.token);
            CRSApi.setCurrentUser(await fetchMe(resp.data.token));
            state.user = CRSApi.getCurrentUser();
            toast("登录成功", "success");
            setView("tasks");
          } catch (err) {
            toast(err.message || "登录失败", "error");
          } finally {
            const submitBtn = $("#login-submit");
            if (submitBtn) {
              submitBtn.disabled = false;
              submitBtn.textContent = mode === "login" ? "登录" : "注册";
            }
          }
        },
      });

      form.appendChild(el("div", { class: "field" }, [
        el("label", { class: "field__label", for: "login-username" }, "用户名"),
        el("input", {
          class: "field__input",
          id: "login-username",
          type: "text",
          autocomplete: "username",
          placeholder: "admin / reviewer",
          required: "required",
        }),
      ]));
      form.appendChild(el("div", { class: "field" }, [
        el("label", { class: "field__label", for: "login-password" }, "密码"),
        el("input", {
          class: "field__input",
          id: "login-password",
          type: "password",
          autocomplete: "current-password",
          placeholder: "请输入密码",
          required: "required",
        }),
      ]));
      form.appendChild(el("button", {
        class: "btn btn--primary",
        id: "login-submit",
        type: "submit",
      }, mode === "login" ? "登录" : "注册"));

      wrap.appendChild(form);
      wrap.appendChild(el("div", { class: "login-meta" }, [
        el("div", null, [
          "默认管理员：admin / 123456",
          el("br"),
          "API 基址：" + CRSApi.getBaseUrl(),
        ]),
      ]));
      return wrap;
    }

    let cardInner = buildCard();
    function refresh() {
      const next = buildCard();
      card.replaceChild(next, cardInner);
      cardInner = next;
    }

    card.appendChild(cardInner);
    main.appendChild(card);
  }

  async function fetchMe(token) {
    try {
      const r = await CRSApi.auth.me();
      return r.data;
    } catch (e) {
      // fall back: 解析 token 的 payload 部分
      try {
        const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
        return { id: payload.sub || payload.user_id, username: payload.username || "(未知)", role: payload.role || "reviewer" };
      } catch (_) {
        return { id: 0, username: "(未知)", role: "reviewer" };
      }
    }
  }
  /* ===================== 任务视图 ===================== */
  async function renderTasks(main) {
    const header = el("div", { class: "page-header" }, [
      el("div", null, [
        el("div", { class: "page-header__meta" }, "审批任务 / Approval Tasks"),
        el("h1", { class: "page-header__title" }, [
          "合同审查 ", el("em", null, "审批任务"),
        ]),
        el("div", { class: "page-header__sub" },
          "拉取审批系统的待办合同并依次执行解析、规则审查与回写评论。"),
      ]),
      el("div", { class: "page-header__actions" }, [
        el("button", {
          class: "btn btn--primary",
          onclick: triggerPull,
        }, "拉取待办"),
        el("button", {
          class: "btn",
          onclick: function () { loadTasks(); },
        }, "刷新"),
      ]),
    ]);
    main.appendChild(header);

    const toolbar = el("div", { class: "task-toolbar" });
    const seg = el("div", { class: "seg" });
    const STATUSES = [
      { v: "", label: "全部" },
      { v: "pending", label: "Pending" },
      { v: "parsing", label: "Parsing" },
      { v: "reviewing", label: "Reviewing" },
      { v: "done", label: "Done" },
      { v: "blocked", label: "Blocked" },
    ];
    STATUSES.forEach(function (s) {
      const b = el("button", {
        class: state.tasks.status === s.v ? "is-active" : "",
        onclick: function () {
          state.tasks.status = s.v;
          state.tasks.page = 1;
          loadTasks();
        },
      }, s.label);
      b.dataset.status = s.v;
      seg.appendChild(b);
    });
    toolbar.appendChild(seg);
    toolbar.appendChild(el("div", { class: "spacer" }));
    toolbar.appendChild(el("div", { style: "font-family: var(--font-mono); font-size: 11px; color: var(--ink-mute); letter-spacing: .06em; text-transform: uppercase;" },
      "共 " + state.tasks.total + " 条"));
    main.appendChild(toolbar);

    const host = el("div", { id: "task-list" });
    main.appendChild(host);

    await loadTasks();

    async function loadTasks() {
      host.innerHTML = "";
      host.appendChild(el("div", { class: "panel" }, [
        el("div", { class: "loading" }),
      ]));
      try {
        const params = { page: state.tasks.page, size: state.tasks.size };
        if (state.tasks.status) params.task_status = state.tasks.status;
        const resp = await CRSApi.tasks.list(params);
        state.tasks.items = resp.data.items || [];
        state.tasks.total = resp.data.total || 0;
        // refresh toolbar count
        toolbar.lastChild.textContent = "共 " + state.tasks.total + " 条";
        // refresh seg buttons
        $$("button", seg).forEach(function (b) {
          b.classList.toggle("is-active", b.dataset.status === state.tasks.status);
        });
        renderTaskTable(host);
      } catch (err) {
        host.innerHTML = "";
        host.appendChild(el("div", { class: "empty-state" }, [
          el("h3", null, "加载失败"),
          el("div", null, err.message || "请检查后端服务与登录状态"),
        ]));
      }
    }
  }

  async function triggerPull() {
    try {
      const resp = await CRSApi.tasks.trigger();
      const n = (resp.data || []).length;
      toast("已入队 " + n + " 个新任务", "success");
      if (state.view === "tasks") render();
    } catch (err) {
      toast(err.message || "拉取失败", "error");
    }
  }

  function renderTaskTable(host) {
    host.innerHTML = "";
    if (!state.tasks.items.length) {
      host.appendChild(el("div", { class: "empty-state" }, [
        el("h3", null, "暂无任务"),
        el("div", null, "点击右上角「拉取待办」从审批系统拉入新合同"),
      ]));
      return;
    }
    const wrap = el("div", { class: "table-wrap" });
    const table = el("table", { class: "table" });
    table.appendChild(el("thead", null, el("tr", null, [
      el("th", null, "ID"),
      el("th", null, "审批编号"),
      el("th", null, "标题"),
      el("th", null, "申请人"),
      el("th", null, "任务状态"),
      el("th", null, "回写状态"),
      el("th", null, ""),
    ])));
    const tbody = el("tbody");
    state.tasks.items.forEach(function (task) {
      const tr = el("tr", null, [
        el("td", { class: "mono" }, String(task.id)),
        el("td", { class: "mono" }, task.approval_code),
        el("td", null, task.approval_title),
        el("td", null, task.applicant_name),
        el("td", null, taskStatusTag(task.task_status)),
        el("td", null, el("span", { class: "tag tag--" + task.write_status }, task.write_status)),
        el("td", { class: "actions" }, [
          el("button", {
            class: "btn btn--sm",
            onclick: function () { openTaskDetail(task.id); },
          }, "详情"),
          task.task_status === "blocked" && state.user && state.user.role === "admin"
            ? el("button", {
                class: "btn btn--sm btn--danger",
                onclick: function () { retryTask(task.id); },
              }, "重试")
            : null,
        ]),
      ]);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    host.appendChild(wrap);
    renderPagination(host, state.tasks.page, state.tasks.size, state.tasks.total, function (p) {
      state.tasks.page = p;
      render();
    });
  }
  function renderPagination(host, page, size, total, onChange) {
    const pages = Math.max(1, Math.ceil(total / size));
    const bar = el("div", { style: "display:flex; gap:8px; justify-content:center; align-items:center; margin-top:16px; font-family: var(--font-mono); font-size: 12px; color: var(--ink-mute);" });
    const mkBtn = function (label, p, disabled) {
      return el("button", {
        class: "btn btn--sm",
        disabled: disabled ? "disabled" : false,
        onclick: function () { onChange(p); },
      }, label);
    };
    bar.appendChild(mkBtn("上一页", page - 1, page <= 1));
    bar.appendChild(el("span", null, page + " / " + pages + "  ·  共 " + total + " 条"));
    bar.appendChild(mkBtn("下一页", page + 1, page >= pages));
    host.appendChild(bar);
  }

  async function retryTask(taskId) {
    if (!confirm("确认重试任务 #" + taskId + "？")) return;
    try {
      await CRSApi.tasks.retry(taskId);
      toast("重试已触发", "success");
      render();
    } catch (err) {
      toast(err.message || "重试失败", "error");
    }
  }

  /* ===================== 任务详情抽屉 ===================== */
  async function openTaskDetail(taskId) {
    const mask = el("div", { class: "drawer-mask is-open" });
    const drawer = el("aside", { class: "drawer is-open" });
    mask.appendChild(drawer);
    document.body.appendChild(mask);

    const head = el("div", { class: "drawer__head" }, [
      el("div", null, [
        el("div", { class: "meta" }, "TASK #" + taskId),
        el("h2", null, "加载中…"),
      ]),
      el("button", { class: "drawer__close", onclick: close }, "×"),
    ]);
    drawer.appendChild(head);
    const body = el("div", { class: "drawer__body" });
    drawer.appendChild(body);

    function close() {
      mask.remove();
    }
    mask.addEventListener("click", function (e) {
      if (e.target === mask) close();
    });

    try {
      const resp = await CRSApi.tasks.detail(taskId);
      state.detail = resp.data;
      const d = resp.data;
      head.querySelector("h2").textContent = d.approval_title;
      head.querySelector(".meta").innerHTML = "TASK #" + d.id + "  ·  " +
        escapeHtml(d.approval_code) + "  ·  " +
        d.task_status + " / " + d.write_status;

      // 1. 基本信息
      body.appendChild(buildKVSection("任务概览", [
        ["审批编号", d.approval_code, true],
        ["审批标题", d.approval_title],
        ["申请人", d.applicant_name],
        ["任务状态", d.task_status],
        ["回写状态", d.write_status],
      ]));

      // 2. 附件
      body.appendChild(buildAttachmentsSection(d.attachments || []));

      // 3. 解析结果
      body.appendChild(buildParseSection(d.parse));

      // 4. 命中记录
      body.appendChild(buildHitsSection(d.hits || []));

      // 5. 审查结果
      body.appendChild(buildResultSection(d.result));

      // 6. 运行日志
      body.appendChild(buildLogsSection(d.logs || []));
    } catch (err) {
      body.appendChild(el("div", { class: "empty-state" }, [
        el("h3", null, "加载失败"),
        el("div", null, err.message || "请稍后重试"),
      ]));
    }
  }
  function buildKVSection(title, rows) {
    const sec = el("div", { class: "drawer__section" }, [el("h3", null, title)]);
    const kv = el("dl", { class: "kv" });
    rows.forEach(function (r) {
      const k = r[0], v = r[1], mono = r[2];
      kv.appendChild(el("dt", null, k));
      kv.appendChild(el("dd", null, mono
        ? el("span", { class: "mono" }, v == null ? "-" : v)
        : (v == null ? "-" : v)));
    });
    sec.appendChild(kv);
    return sec;
  }

  function buildAttachmentsSection(list) {
    const sec = el("div", { class: "drawer__section" }, [
      el("h3", null, "附件（" + list.length + "）"),
    ]);
    if (!list.length) {
      sec.appendChild(el("div", { class: "empty-state" }, "暂无附件"));
      return sec;
    }
    const wrap = el("div", { class: "table-wrap" });
    const table = el("table", { class: "table" });
    table.appendChild(el("thead", null, el("tr", null, [
      el("th", null, "ID"),
      el("th", null, "文件名"),
      el("th", null, "类型"),
      el("th", null, "下载状态"),
      el("th", null, "路径"),
    ])));
    const tbody = el("tbody");
    list.forEach(function (a) {
      tbody.appendChild(el("tr", null, [
        el("td", { class: "mono" }, String(a.id)),
        el("td", null, a.file_name),
        el("td", null, el("span", { class: "tag" }, a.file_type)),
        el("td", null, el("span", { class: "tag tag--" + a.download_status }, a.download_status)),
        el("td", { class: "mono", style: "max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" }, a.file_path || "-"),
      ]));
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    sec.appendChild(wrap);
    return sec;
  }

  /* 解析结果：基本信息 8 项 + 条款信息 8 项 */
  const BASIC_FIELDS = [
    "合同标题", "合同编号", "签约主体", "对方名称",
    "金额", "币种", "生效时间", "到期时间",
  ];
  const CLAUSE_FIELDS = [
    "付款条款", "交付条款", "验收条款", "违约条款",
    "保密条款", "数据条款", "知识产权条款", "争议解决条款",
  ];

  function buildHitsSection(hits) {
    const sec = el("div", { class: "drawer__section" }, [
      el("h3", null, "规则命中（" + hits.length + "）"),
    ]);
    if (!hits.length) {
      sec.appendChild(el("div", { class: "empty-state" }, "暂无规则命中"));
      return sec;
    }
    const wrap = el("div", { class: "table-wrap" });
    const table = el("table", { class: "table" });
    table.appendChild(el("thead", null, el("tr", null, [
      el("th", null, "规则"),
      el("th", null, "风险"),
      el("th", null, "证据原文"),
      el("th", null, "证据位置"),
      el("th", null, "状态"),
    ])));
    const tbody = el("tbody");
    hits.forEach(function (h) {
      tbody.appendChild(el("tr", null, [
        el("td", null, [
          el("div", { style: "font-weight: 600;" }, h.rule_name || "(未命名)"),
          el("div", { class: "mono", style: "font-size: 11px; color: var(--ink-mute);" }, "rule_id=" + h.rule_id),
        ]),
        el("td", null, riskTag(h.risk_level)),
        el("td", { style: "max-width: 320px;" }, h.evidence_text || "-"),
        el("td", { class: "mono" }, h.evidence_position || "-"),
        el("td", null, el("span", { class: "tag" }, h.hit_status)),
      ]));
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    sec.appendChild(wrap);
    return sec;
  }

  function buildResultSection(result) {
    const sec = el("div", { class: "drawer__section" }, [
      el("h3", null, "审查结果"),
    ]);
    if (!result) {
      sec.appendChild(el("div", { class: "empty-state" }, "暂无审查结果"));
      return sec;
    }
    const wrap = el("div", null, [
      buildKVSection("结论", [
        ["总风险等级", ""],
      ]),
    ]);
    // 替换最后一行为带 tag
    wrap.firstChild.remove();
    const head = el("div", { class: "drawer__section" }, [
      el("h3", null, "结论"),
      el("dl", { class: "kv" }, [
        el("dt", null, "总风险等级"),
        el("dd", null, riskTag(result.overall_risk_level)),
        el("dt", null, "摘要"),
        el("dd", null, result.summary_text || "-"),
        el("dt", null, "关注点"),
        el("dd", null, result.focus_points_json ? renderFocusPoints(result.focus_points_json) : "-"),
        el("dt", null, "评论"),
        el("dd", { class: "mono" }, result.comment_text || "（未生成）"),
      ]),
    ]);
    sec.appendChild(head);
    return sec;
  }

  function renderFocusPoints(fp) {
    const list = Array.isArray(fp) ? fp : (fp.focus_points || fp.items || []);
    if (!Array.isArray(list) || !list.length) return "-";
    const wrap = el("ul", { style: "padding-left: 18px; margin: 0;" });
    list.forEach(function (item) {
      if (typeof item === "string") {
        wrap.appendChild(el("li", null, item));
      } else if (item && item.description) {
        wrap.appendChild(el("li", null, item.description));
      } else {
        wrap.appendChild(el("li", null, JSON.stringify(item)));
      }
    });
    return wrap;
  }

  function buildLogsSection(logs) {
    const sec = el("div", { class: "drawer__section" }, [
      el("h3", null, "运行日志（最近 " + logs.length + " 条）"),
    ]);
    if (!logs.length) {
      sec.appendChild(el("div", { class: "empty-state" }, "暂无日志"));
      return sec;
    }
    const wrap = el("div", { class: "table-wrap" });
    const table = el("table", { class: "table" });
    table.appendChild(el("thead", null, el("tr", null, [
      el("th", null, "时间"),
      el("th", null, "级别"),
      el("th", null, "类型"),
      el("th", null, "内容"),
    ])));
    const tbody = el("tbody");
    logs.forEach(function (l) {
      tbody.appendChild(el("tr", null, [
        el("td", { class: "mono" }, fmtDate(l.create_time)),
        el("td", null, el("span", { class: "tag" }, l.log_level)),
        el("td", { class: "mono" }, l.log_type),
        el("td", null, l.log_content),
      ]));
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    sec.appendChild(wrap);
    return sec;
  }
  /* ===================== 规则视图 ===================== */
  async function renderRules(main) {
    const isAdmin = state.user && state.user.role === "admin";
    main.appendChild(el("div", { class: "page-header" }, [
      el("div", null, [
        el("div", { class: "page-header__meta" }, "审查规则 / Review Rules"),
        el("h1", { class: "page-header__title" }, [
          "规则 ", el("em", null, "维护"),
        ]),
        el("div", { class: "page-header__sub" },
          "管理 11 条默认审查规则（2.4.6）。增删改操作仅管理员可执行；" +
          "删除为逻辑删除，使用 is_deleted 标记。"),
      ]),
      el("div", { class: "page-header__actions" }, [
        isAdmin ? el("button", {
          class: "btn btn--primary",
          onclick: openRuleForm,
        }, "新增规则") : null,
        el("button", {
          class: "btn",
          onclick: function () { loadRules(); },
        }, "刷新"),
      ]),
    ]));

    const host = el("div", { id: "rules-list" });
    main.appendChild(host);

    await loadRules();

    async function loadRules() {
      host.innerHTML = "";
      host.appendChild(el("div", { class: "panel" }, [el("div", { class: "loading" })]));
      try {
        const resp = await CRSApi.rules.list();
        state.rules = resp.data || [];
        renderRulesTable(host);
      } catch (err) {
        host.innerHTML = "";
        host.appendChild(el("div", { class: "empty-state" }, [
          el("h3", null, "加载失败"),
          el("div", null, err.message || "请检查登录状态"),
        ]));
      }
    }
  }

  function renderRulesTable(host) {
    host.innerHTML = "";
    if (!state.rules.length) {
      host.appendChild(el("div", { class: "empty-state" }, [
        el("h3", null, "暂无规则"),
        el("div", null, "点击右上角「新增规则」或在服务启动时自动注入 11 条默认规则"),
      ]));
      return;
    }
    const isAdmin = state.user && state.user.role === "admin";
    const wrap = el("div", { class: "table-wrap" });
    const table = el("table", { class: "table" });
    table.appendChild(el("thead", null, el("tr", null, [
      el("th", null, "ID"),
      el("th", null, "规则编码"),
      el("th", null, "规则名称"),
      el("th", null, "风险"),
      el("th", null, "状态"),
      el("th", null, "匹配模式"),
      el("th", null, "建议说明"),
      el("th", null, ""),
    ])));
    const tbody = el("tbody");
    state.rules.forEach(function (r) {
      const tr = el("tr", null, [
        el("td", { class: "mono" }, String(r.id)),
        el("td", { class: "mono" }, r.rule_code),
        el("td", null, r.rule_name),
        el("td", null, riskTag(r.risk_level)),
        el("td", null, el("span", { class: "tag tag--" + r.rule_status }, r.rule_status)),
        el("td", { class: "mono" }, r.match_mode),
        el("td", { style: "max-width: 280px; color: var(--ink-soft);" }, r.suggestion_text || "-"),
        el("td", { class: "actions" }, isAdmin ? [
          el("button", {
            class: "btn btn--sm",
            onclick: function () { openRuleForm(r); },
          }, "编辑"),
          el("button", {
            class: "btn btn--sm btn--danger",
            onclick: function () { deleteRule(r); },
          }, "删除"),
        ] : [
          el("span", { class: "mono", style: "color: var(--ink-faint);" }, "只读"),
        ]),
      ]);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    host.appendChild(wrap);
  }

  function openRuleForm(rule) {
    const editing = !!rule;
    const mask = el("div", { class: "modal-mask is-open" });
    const modal = el("div", { class: "modal" }, [
      el("h2", null, editing ? "编辑规则" : "新增规则"),
      el("p", null, "规则字段：rule_code / rule_name / risk_level / rule_status / match_mode / match_text / suggestion_text。"),
    ]);
    const form = el("form", { onsubmit: async function (e) { e.preventDefault(); submitForm(); } });
    function f(id, label, type, value, opts) {
      opts = opts || {};
      const input = opts.textarea
        ? el("textarea", { class: "field__textarea", id: id, rows: 3 })
        : el("input", { class: "field__input", id: id, type: type || "text" });
      if (opts.disabled) input.disabled = "disabled";
      if (value != null) input.value = value;
      if (opts.placeholder) input.placeholder = opts.placeholder;
      return el("div", { class: "field" }, [
        el("label", { class: "field__label", for: id }, label),
        input,
      ]);
    }
    const sel = function (id, label, value, options) {
      const sel = el("select", { class: "field__select", id: id });
      options.forEach(function (o) {
        const opt = el("option", { value: o }, o);
        if (o === value) opt.selected = "selected";
        sel.appendChild(opt);
      });
      return el("div", { class: "field" }, [el("label", { class: "field__label", for: id }, label), sel]);
    };
    const r = rule || {};
    form.appendChild(el("div", { class: "field-row" }, [
      f("rf-code", "rule_code", "text", r.rule_code, { disabled: editing ? "disabled" : "", placeholder: "唯一编码" }),
      f("rf-name", "rule_name", "text", r.rule_name, { placeholder: "规则名称" }),
    ]));
    form.appendChild(el("div", { class: "field-row" }, [
      sel("rf-risk", "risk_level", r.risk_level || "low", ["low", "medium", "high"]),
      sel("rf-status", "rule_status", r.rule_status || "enabled", ["enabled", "disabled"]),
      sel("rf-mode", "match_mode", r.match_mode || "regex", ["regex", "numeric", "llm"]),
    ]));
    form.appendChild(f("rf-match", "match_text", "text", r.match_text, { placeholder: "regex/numeric/llm 提示文本" }));
    form.appendChild(f("rf-suggest", "suggestion_text", "text", r.suggestion_text, { placeholder: "建议说明", textarea: true }));
    const actions = el("div", { class: "actions" }, [
      el("button", { class: "btn", type: "button", onclick: function () { mask.remove(); } }, "取消"),
      el("button", { class: "btn btn--primary", type: "submit" }, editing ? "保存" : "创建"),
    ]);
    form.appendChild(actions);
    modal.appendChild(form);
    mask.appendChild(modal);
    document.body.appendChild(mask);

    async function submitForm() {
      const payload = {
        rule_code: $("#rf-code").value.trim(),
        rule_name: $("#rf-name").value.trim(),
        risk_level: $("#rf-risk").value,
        rule_status: $("#rf-status").value,
        match_mode: $("#rf-mode").value,
        match_text: $("#rf-match").value.trim() || null,
        suggestion_text: $("#rf-suggest").value.trim() || null,
      };
      if (!payload.rule_code || !payload.rule_name) {
        toast("请填写编码与名称", "error");
        return;
      }
      try {
        if (editing) {
          await CRSApi.rules.update(rule.id, payload);
          toast("已更新", "success");
        } else {
          await CRSApi.rules.create(payload);
          toast("已创建", "success");
        }
        mask.remove();
        render();
      } catch (err) {
        toast(err.message || "保存失败", "error");
      }
    }
  }

  async function deleteRule(rule) {
    if (!confirm("逻辑删除规则「" + rule.rule_name + "」？")) return;
    try {
      await CRSApi.rules.remove(rule.id);
      toast("已删除", "success");
      render();
    } catch (err) {
      toast(err.message || "删除失败", "error");
    }
  }
  /* ===================== 命中视图 ===================== */
  async function renderHits(main) {
    main.appendChild(el("div", { class: "page-header" }, [
      el("div", null, [
        el("div", { class: "page-header__meta" }, "规则命中 / Rule Hits"),
        el("h1", { class: "page-header__title" }, [
          "命中 ", el("em", null, "复核"),
        ]),
        el("div", { class: "page-header__sub" },
          "按任务/规则/风险等级筛选命中记录；evidence_position 由 page_no + clause_name 拼接而成。" +
          "confirm / ignore 接口为框架预留，demo 返回「未启用」。"),
      ]),
      el("div", { class: "page-header__actions" }, [
        el("button", {
          class: "btn",
          onclick: function () { loadHits(); },
        }, "刷新"),
      ]),
    ]));

    const toolbar = el("div", { class: "panel" }, [
      el("div", { class: "field-row" }, [
        (function () {
          const input = el("input", {
            class: "field__input",
            id: "hit-task",
            type: "number",
            placeholder: "按任务 ID 筛选",
          });
          return el("div", { class: "field" }, [
            el("label", { class: "field__label", for: "hit-task" }, "Task ID"),
            input,
          ]);
        })(),
        (function () {
          const sel = el("select", { class: "field__select", id: "hit-risk" }, [
            el("option", { value: "" }, "全部风险等级"),
            el("option", { value: "high" }, "HIGH"),
            el("option", { value: "medium" }, "MEDIUM"),
            el("option", { value: "low" }, "LOW"),
          ]);
          return el("div", { class: "field" }, [
            el("label", { class: "field__label", for: "hit-risk" }, "Risk Level"),
            sel,
          ]);
        })(),
        el("div", { class: "field" }, [
          el("label", { class: "field__label" }, "操作"),
          el("button", {
            class: "btn btn--primary",
            onclick: function () { loadHits(); },
          }, "查询"),
        ]),
      ]),
    ]);
    main.appendChild(toolbar);

    const host = el("div", { id: "hits-list" });
    main.appendChild(host);

    await loadHits();

    async function loadHits() {
      host.innerHTML = "";
      host.appendChild(el("div", { class: "panel" }, [el("div", { class: "loading" })]));
      try {
        const params = {};
        const taskVal = $("#hit-task").value.trim();
        if (taskVal) params.task_id = Number(taskVal);
        const riskVal = $("#hit-risk").value;
        if (riskVal) params.risk_level = riskVal;
        const resp = await CRSApi.hits.list(params);
        state.hits.items = resp.data || [];
        renderHitsTable(host);
      } catch (err) {
        host.innerHTML = "";
        host.appendChild(el("div", { class: "empty-state" }, [
          el("h3", null, "加载失败"),
          el("div", null, err.message || "请检查登录状态"),
        ]));
      }
    }
  }

  function renderHitsTable(host) {
    host.innerHTML = "";
    if (!state.hits.items.length) {
      host.appendChild(el("div", { class: "empty-state" }, [
        el("h3", null, "暂无命中"),
        el("div", null, "完成至少一次任务审查后再来查看"),
      ]));
      return;
    }
    const wrap = el("div", { class: "table-wrap" });
    const table = el("table", { class: "table" });
    table.appendChild(el("thead", null, el("tr", null, [
      el("th", null, "ID"),
      el("th", null, "任务"),
      el("th", null, "规则"),
      el("th", null, "风险"),
      el("th", null, "证据原文"),
      el("th", null, "证据位置"),
      el("th", null, "状态"),
      el("th", null, ""),
    ])));
    const tbody = el("tbody");
    state.hits.items.forEach(function (h) {
      const tr = el("tr", null, [
        el("td", { class: "mono" }, String(h.id)),
        el("td", { class: "mono" }, String(h.task_id)),
        el("td", null, h.rule_name),
        el("td", null, riskTag(h.risk_level)),
        el("td", { style: "max-width: 320px;" }, h.evidence_text || "-"),
        el("td", { class: "mono" }, h.evidence_position || "-"),
        el("td", null, el("span", { class: "tag" }, h.hit_status)),
        el("td", { class: "actions" }, [
          el("button", {
            class: "btn btn--sm",
            onclick: function () { hitAction(h.id, "confirm"); },
          }, "确认"),
          el("button", {
            class: "btn btn--sm btn--ghost",
            onclick: function () { hitAction(h.id, "ignore"); },
          }, "忽略"),
        ]),
      ]);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    host.appendChild(wrap);
  }

  async function hitAction(hitId, action) {
    try {
      const resp = action === "confirm"
        ? await CRSApi.hits.confirm(hitId)
        : await CRSApi.hits.ignore(hitId);
      toast(resp.message || "操作成功", "success");
    } catch (err) {
      toast(err.message || "操作失败", "error");
    }
  }
  /* ===================== 日志视图（admin） ===================== */
  async function renderLogs(main) {
    main.appendChild(el("div", { class: "page-header" }, [
      el("div", null, [
        el("div", { class: "page-header__meta" }, "运行日志 / Task Logs"),
        el("h1", { class: "page-header__title" }, [
          "运行 ", el("em", null, "日志"),
        ]),
        el("div", { class: "page-header__sub" },
          "按级别 / 类型 / 任务 ID 检索 task_logs；仅 admin 可访问。"),
      ]),
      el("div", { class: "page-header__actions" }, [
        el("button", {
          class: "btn",
          onclick: function () { loadLogs(); },
        }, "刷新"),
      ]),
    ]));

    const toolbar = el("div", { class: "panel" }, [
      el("div", { class: "field-row" }, [
        (function () {
          const input = el("input", {
            class: "field__input",
            id: "log-task",
            type: "number",
            placeholder: "按任务 ID 筛选",
          });
          return el("div", { class: "field" }, [
            el("label", { class: "field__label", for: "log-task" }, "Task ID"),
            input,
          ]);
        })(),
        (function () {
          const sel = el("select", { class: "field__select", id: "log-level" }, [
            el("option", { value: "" }, "全部级别"),
            el("option", { value: "info" }, "INFO"),
            el("option", { value: "warn" }, "WARN"),
            el("option", { value: "error" }, "ERROR"),
          ]);
          return el("div", { class: "field" }, [
            el("label", { class: "field__label", for: "log-level" }, "Log Level"),
            sel,
          ]);
        })(),
        (function () {
          const sel = el("select", { class: "field__select", id: "log-type" }, [
            el("option", { value: "" }, "全部类型"),
            el("option", { value: "task" }, "task"),
            el("option", { value: "parse" }, "parse"),
            el("option", { value: "review" }, "review"),
            el("option", { value: "writeback" }, "writeback"),
            el("option", { value: "retry" }, "retry"),
          ]);
          return el("div", { class: "field" }, [
            el("label", { class: "field__label", for: "log-type" }, "Log Type"),
            sel,
          ]);
        })(),
        el("div", { class: "field" }, [
          el("label", { class: "field__label" }, "操作"),
          el("button", {
            class: "btn btn--primary",
            onclick: function () { state.logs.page = 1; loadLogs(); },
          }, "查询"),
        ]),
      ]),
    ]);
    main.appendChild(toolbar);

    const host = el("div", { id: "logs-list" });
    main.appendChild(host);

    await loadLogs();

    async function loadLogs() {
      host.innerHTML = "";
      host.appendChild(el("div", { class: "panel" }, [el("div", { class: "loading" })]));
      try {
        const params = { page: state.logs.page, size: state.logs.size };
        const taskVal = $("#log-task").value.trim();
        if (taskVal) params.task_id = Number(taskVal);
        const lv = $("#log-level").value;
        if (lv) params.log_level = lv;
        const ty = $("#log-type").value;
        if (ty) params.log_type = ty;
        const resp = await CRSApi.logs.list(params);
        state.logs.items = resp.data.items || [];
        state.logs.total = resp.data.total || 0;
        renderLogsTable(host);
      } catch (err) {
        host.innerHTML = "";
        host.appendChild(el("div", { class: "empty-state" }, [
          el("h3", null, "加载失败"),
          el("div", null, err.message || "请检查登录状态（仅 admin 可访问）"),
        ]));
      }
    }
  }

  function renderLogsTable(host) {
    host.innerHTML = "";
    if (!state.logs.items.length) {
      host.appendChild(el("div", { class: "empty-state" }, [
        el("h3", null, "暂无日志"),
        el("div", null, "调整筛选条件后再查询"),
      ]));
      return;
    }
    const wrap = el("div", { class: "table-wrap" });
    const table = el("table", { class: "table" });
    table.appendChild(el("thead", null, el("tr", null, [
      el("th", null, "ID"),
      el("th", null, "时间"),
      el("th", null, "任务"),
      el("th", null, "级别"),
      el("th", null, "类型"),
      el("th", null, "内容"),
    ])));
    const tbody = el("tbody");
    state.logs.items.forEach(function (l) {
      tbody.appendChild(el("tr", null, [
        el("td", { class: "mono" }, String(l.id)),
        el("td", { class: "mono" }, fmtDate(l.create_time)),
        el("td", { class: "mono" }, l.task_id == null ? "-" : String(l.task_id)),
        el("td", null, el("span", { class: "tag" }, l.log_level)),
        el("td", { class: "mono" }, l.log_type),
        el("td", null, l.log_content),
      ]));
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    host.appendChild(wrap);
    renderPagination(host, state.logs.page, state.logs.size, state.logs.total, function (p) {
      state.logs.page = p;
      render();
    });
  }
  /* ===================== 头部渲染 ===================== */
  function renderHeader() {
    const header = $("#app-header");
    if (!header) return;
    const isLoggedIn = !!state.user;
    header.innerHTML = "";
    const inner = el("div", { class: "app-header__inner" });

    inner.appendChild(el("a", { class: "brand", href: "#" }, [
      el("div", { class: "brand__mark" }, "合同审查"),
      el("div", { class: "brand__sub" }, "v0.1 · CRS"),
    ]));

    if (isLoggedIn) {
      const nav = el("nav", { class: "nav" });
      [
        { v: "tasks", label: "任务" },
        { v: "rules", label: "规则" },
        { v: "hits", label: "命中" },
      ].forEach(function (item) {
        if (state.user.role === "admin") {
          nav.appendChild(el("button", {
            class: "nav__item" + (state.view === item.v ? " is-active" : ""),
            dataset: { view: item.v },
            onclick: function () { setView(item.v); },
          }, item.label));
        } else if (item.v !== "hits") {
          nav.appendChild(el("button", {
            class: "nav__item" + (state.view === item.v ? " is-active" : ""),
            dataset: { view: item.v },
            onclick: function () { setView(item.v); },
          }, item.label));
        }
      });
      if (state.user.role === "admin") {
        nav.appendChild(el("button", {
          class: "nav__item" + (state.view === "logs" ? " is-active" : ""),
          dataset: { view: "logs" },
          onclick: function () { setView("logs"); },
        }, "日志"));
      }
      inner.appendChild(nav);
    }

    const actions = el("div", { class: "header-actions" });
    if (isLoggedIn) {
      actions.appendChild(el("span", { class: "who" }, [
        el("strong", null, state.user.username),
        " · " + state.user.role,
      ]));
      actions.appendChild(el("button", {
        class: "btn btn--sm btn--ghost",
        onclick: function () { setApiUrl(); },
      }, "API"));
      actions.appendChild(el("button", {
        class: "btn btn--sm",
        onclick: logout,
      }, "退出"));
    } else {
      actions.appendChild(el("span", { class: "who" }, "未登录"));
    }
    inner.appendChild(actions);
    header.appendChild(inner);
  }

  function setApiUrl() {
    const url = prompt("后端 API 基址", CRSApi.getBaseUrl());
    if (url && url.trim()) {
      CRSApi.setBaseUrl(url.trim());
      toast("已切换为 " + CRSApi.getBaseUrl(), "success");
      render();
    }
  }

  function logout() {
    CRSApi.clearAuth();
    state.user = null;
    setView("login");
  }

  /* ===================== 健康检查 ===================== */
  async function pingHealth() {
    try {
      const r = await CRSApi.health();
      const footer = $("#app-footer");
      if (footer) {
        footer.innerHTML = "服务正常  ·  " + CRSApi.getBaseUrl() + "  ·  " +
          "状态 " + (r.status || "ok");
      }
    } catch (e) {
      const footer = $("#app-footer");
      if (footer) {
        footer.innerHTML = "后端不可达  ·  " + CRSApi.getBaseUrl() + "  ·  " +
          (e.message || "请检查服务是否启动");
      }
    }
  }

  /* ===================== 入口 ===================== */
  async function bootstrap() {
    CRSApi.initBaseUrl();
    const token = CRSApi.getToken();
    if (token) {
      try {
        state.user = await fetchMe(token);
        CRSApi.setCurrentUser(state.user);
        setView("tasks");
      } catch (e) {
        CRSApi.clearAuth();
        setView("login");
      }
    } else {
      setView("login");
    }
    renderHeader();
    pingHealth();
    setInterval(pingHealth, 30000);
  }

  document.addEventListener("DOMContentLoaded", bootstrap);
  window.CRSApp = { setView: setView, state: state };
  /* 解析结果：基本信息 8 项 + 条款信息 8 项
   * 兼容两种持久化形态：
   *  A. 扁平 dict：basic_info_json = {name: value,...}，
   *               clause_info_json = {name: {raw_text, page_no, extract_status?, structured?},...}
   *  B. 数组结构：basic_info_json = {fields:[{field_name, field_value, raw_text, page_no, extract_status}]}
   *               clause_info_json = {clauses:[...]}
   */
  function buildParseSection(parse) {
    const sec = el("div", { class: "drawer__section" }, [
      el("h3", null, "解析结果（" + (parse ? parse.parse_status : "无") + "）"),
    ]);
    if (!parse) {
      sec.appendChild(el("div", { class: "empty-state" }, "暂无解析结果"));
      return sec;
    }
    if (parse.parse_error) {
      sec.appendChild(el("div", { style: "background: var(--vermilion-soft); color: var(--vermilion); padding: 10px 12px; border-radius: var(--radius); font-family: var(--font-mono); font-size: 12px; margin-bottom: 12px;" },
        "解析异常：" + parse.parse_error));
    }
    const basic = parse.basic_info_json || {};
    const clauses = parse.clause_info_json || {};
    sec.appendChild(renderBasicGrid(basic));
    sec.appendChild(renderClauseGrid(clauses));
    return sec;
  }

  function renderBasicGrid(basic) {
    const wrap = el("div", { style: "margin-top: 12px;" }, [
      el("div", { style: "font-family: var(--font-mono); font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-mute); margin-bottom: 8px;" }, "基本信息"),
    ]);
    const grid = el("div", { class: "field-grid" });
    const entries = extractEntries(basic);
    BASIC_FIELDS.forEach(function (name) {
      const entry = entries[name] || null;
      grid.appendChild(renderBasicCard(name, entry));
    });
    wrap.appendChild(grid);
    return wrap;
  }

  function renderClauseGrid(clauses) {
    const wrap = el("div", { style: "margin-top: 18px;" }, [
      el("div", { style: "font-family: var(--font-mono); font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-mute); margin-bottom: 8px;" }, "条款信息"),
    ]);
    const grid = el("div", { class: "field-grid" });
    const entries = extractEntries(clauses);
    CLAUSE_FIELDS.forEach(function (name) {
      const entry = entries[name] || null;
      grid.appendChild(renderClauseCard(name, entry));
    });
    wrap.appendChild(grid);
    return wrap;
  }

  /* 从 basic_info_json / clause_info_json 提取 name -> {value, raw_text, page_no, extract_status, structured} */
  function extractEntries(payload) {
    const map = {};
    if (!payload || typeof payload !== "object") return map;
    // 形态 A：扁平 {name: value} 或 {name: {raw_text, page_no}}
    if (!payload.fields && !payload.clauses && !payload.items) {
      Object.keys(payload).forEach(function (k) {
        const v = payload[k];
        if (v && typeof v === "object" && !Array.isArray(v) && ("raw_text" in v || "page_no" in v)) {
          map[k] = {
            value: v.field_value || v.value || "",
            raw_text: v.raw_text || "",
            page_no: v.page_no || 0,
            extract_status: v.extract_status || (v.raw_text ? "extracted" : "missing"),
            structured: v.structured || null,
          };
        } else {
          map[k] = {
            value: v == null ? "" : (typeof v === "object" ? JSON.stringify(v) : String(v)),
            raw_text: "",
            page_no: 0,
            extract_status: v ? "extracted" : "missing",
            structured: null,
          };
        }
      });
      return map;
    }
    // 形态 B：{fields:[{field_name,...}]} 或 {clauses:[...]} 或 {items:[...]}
    const list = payload.fields || payload.clauses || payload.items || [];
    list.forEach(function (item) {
      if (!item) return;
      const name = item.field_name || item.clause_name || item.name;
      if (!name) return;
      map[name] = {
        value: item.field_value || item.value || "",
        raw_text: item.raw_text || "",
        page_no: item.page_no || 0,
        extract_status: item.extract_status || (item.raw_text || item.field_value ? "extracted" : "missing"),
        structured: item.structured || null,
      };
    });
    return map;
  }

  function renderBasicCard(name, entry) {
    const card = el("div", { class: "field-card" });
    card.appendChild(el("div", { class: "field-card__label" }, name));
    if (entry && entry.value) {
      card.appendChild(el("div", { class: "field-card__value" }, entry.value));
    } else {
      card.appendChild(el("div", { class: "field-card__value is-missing" }, "未提取"));
    }
    const meta = el("div", { class: "field-card__meta" });
    meta.appendChild(el("span", null, "P" + (entry ? entry.page_no || "-" : "-")));
    meta.appendChild(el("span", null, entry ? (entry.extract_status || (entry.value ? "extracted" : "missing")) : "missing"));
    card.appendChild(meta);
    if (entry && entry.raw_text && entry.raw_text !== entry.value) {
      card.appendChild(el("div", { class: "field-card__raw" }, entry.raw_text));
    }
    return card;
  }

  function renderClauseCard(name, entry) {
    const card = el("div", { class: "field-card" });
    card.appendChild(el("div", { class: "field-card__label" }, name));
    if (entry && entry.raw_text) {
      card.appendChild(el("div", { class: "field-card__value" }, entry.raw_text));
    } else {
      card.appendChild(el("div", { class: "field-card__value is-missing" }, "未提取"));
    }
    const meta = el("div", { class: "field-card__meta" });
    meta.appendChild(el("span", null, "P" + (entry ? entry.page_no || "-" : "-")));
    meta.appendChild(el("span", null, entry ? (entry.extract_status || (entry.raw_text ? "extracted" : "missing")) : "missing"));
    card.appendChild(meta);
    if (entry && entry.structured) {
      card.appendChild(el("div", { class: "field-card__raw" }, "结构化要点：" + JSON.stringify(entry.structured)));
    }
    return card;
  }
})();
