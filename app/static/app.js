(function () {
  const API = "";
  let token = localStorage.getItem("hh_token") || "";
  let me = null;
  let stats = null;
  const selected = new Set();

  const $ = (id) => document.getElementById(id);

  function showScreen(name) {
    ["login-screen", "resume-screen", "app-screen"].forEach((id) => {
      $(id).classList.toggle("hidden", id !== name);
    });
  }

  function showToast(msg) {
    const el = $("toast");
    el.textContent = msg;
    el.classList.remove("hidden");
    setTimeout(() => el.classList.add("hidden"), 4000);
  }

  async function api(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(API + path, { ...options, headers, credentials: "include" });
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = { detail: text };
    }
    if (!res.ok) {
      const detail = data?.detail;
      let msg =
        typeof detail === "string"
          ? detail
          : detail?.message || (detail ? JSON.stringify(detail) : res.statusText);
      if (res.status === 500 && msg === "Internal Server Error") {
        msg = "Ошибка сервера. Попробуй 1–2 отклика или повтори через минуту.";
      }
      throw new Error(msg);
    }
    return data;
  }

  function matchClass(score) {
    if (score >= 75) return "match-high";
    if (score >= 50) return "match-mid";
    return "match-low";
  }

  function renderKpis(s) {
    const delta = (v) =>
      v == null ? "" : `<span class="kpi-delta${v < 0 ? " negative" : ""}">${v > 0 ? "+" : ""}${v}%</span>`;
    $("kpi-row").innerHTML = `
      <div class="kpi-card">
        <div class="muted">Новых вакансий</div>
        <div class="value">${s.vacancies_found_today}</div>
        ${delta(s.vacancies_found_delta_pct)}
      </div>
      <div class="kpi-card">
        <div class="muted">Откликов сегодня</div>
        <div class="value">${s.applications_today}</div>
        ${delta(s.applications_delta_pct)}
      </div>
      <div class="kpi-card">
        <div class="muted">Направлений</div>
        <div class="value">${s.active_directions}</div>
        <span class="muted small">Поисков осталось: ${s.searches_left}</span>
      </div>
    `;
  }

  function renderChart(s) {
    const chart = $("daily-chart");
    const max = Math.max(1, ...s.daily_chart.map((d) => d.applications));
    chart.innerHTML = s.daily_chart
      .map((d) => {
        const h = Math.round((d.applications / max) * 100);
        return `<div class="chart-bar-wrap">
          <div class="chart-bar" style="height:${Math.max(h, 4)}%"></div>
          <span class="chart-label">${d.date}</span>
        </div>`;
      })
      .join("");
  }

  function renderProgress(s) {
    $("progress-value").textContent = `${s.progress_percent}%`;
    $("progress-gauge").style.setProperty("--p", s.progress_percent);
    $("progress-caption").textContent = s.progress_label;
    $("applications-left-label").textContent = `Доступно откликов: ${s.applications_left} из ${s.applications_daily_limit}`;
    $("schedule-label").textContent = s.auto_schedule_label;
    $("plan-badge").textContent = s.plan_label;
    document.querySelectorAll(".mode-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.mode === s.apply_mode);
    });
  }

  function renderVacancies(data) {
    const root = $("vacancies-root");
    if (!data.groups?.length || !data.groups[0].vacancies?.length) {
      root.innerHTML = `<div class="empty-state">
        <p>Пока нет вакансий в подборке.</p>
        <button type="button" class="btn btn-primary" id="empty-search">Запустить поиск</button>
      </div>`;
      $("empty-search")?.addEventListener("click", () => {
        $("search-bar").classList.remove("hidden");
        $("search-input").focus();
      });
      return;
    }

    root.innerHTML = data.groups
      .map(
        (g) => `
      <section class="vacancy-section">
        <div class="section-head">
          <h2>${escapeHtml(g.title)}</h2>
          <span class="muted">Найдено: ${g.total} · Доступно откликов: ${data.applications_left}</span>
        </div>
        <div class="vacancy-grid">
          ${g.vacancies.map((v) => vacancyCardHtml(v)).join("")}
        </div>
      </section>`
      )
      .join("");

    root.querySelectorAll("[data-select]").forEach((btn) => {
      btn.addEventListener("click", () => toggleSelect(Number(btn.dataset.select)));
    });
    root.querySelectorAll("[data-open]").forEach((btn) => {
      btn.addEventListener("click", () => window.open(btn.dataset.open, "_blank"));
    });
    updateBatchBar();
  }

  function vacancyCardHtml(v) {
    const sel = selected.has(v.analysis_id);
    return `
      <article class="vacancy-card${sel ? " selected" : ""}" data-id="${v.analysis_id}">
        <div class="vacancy-card-top">
          <span class="muted">${v.source_label}, ${v.posted_label}</span>
          <span class="match-badge ${matchClass(v.match_score)}">${(v.match_score / 10).toFixed(1)}</span>
        </div>
        <h3>${escapeHtml(v.title)}</h3>
        <p class="vacancy-meta">${escapeHtml(v.company)}</p>
        <p class="vacancy-meta">${escapeHtml(v.summary || "").slice(0, 120)}</p>
        <div class="vacancy-actions">
          <button type="button" class="btn btn-ghost btn-sm" data-open="${escapeHtml(v.url)}">Откликнуться</button>
          <button type="button" class="btn btn-outline btn-sm${sel ? " active" : ""}" data-select="${v.analysis_id}">
            ${sel ? "✓ Выбрано" : "Выбрать"}
          </button>
        </div>
      </article>`;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function toggleSelect(id) {
    if (selected.has(id)) selected.delete(id);
    else selected.add(id);
    const card = document.querySelector(`.vacancy-card[data-id="${id}"]`);
    if (card) {
      card.classList.toggle("selected", selected.has(id));
      const btn = card.querySelector("[data-select]");
      if (btn) {
        btn.textContent = selected.has(id) ? "✓ Выбрано" : "Выбрать";
        btn.classList.toggle("active", selected.has(id));
      }
    }
    updateBatchBar();
  }

  function updateBatchBar() {
    const n = selected.size;
    $("batch-count").textContent = `Выбрано ${n}`;
    $("batch-bar").classList.toggle("hidden", n === 0);
  }

  async function loadDashboard() {
    stats = await api("/dashboard/stats");
    me = await api("/web/auth/me");
    renderKpis(stats);
    renderChart(stats);
    renderProgress(stats);
    const vacancies = await api("/dashboard/vacancies");
    renderVacancies(vacancies);
    showScreen("app-screen");
  }

  async function setMode(mode) {
    stats = await api("/dashboard/mode", {
      method: "PATCH",
      body: JSON.stringify({ mode }),
    });
    renderProgress(stats);
    renderKpis(stats);
    showToast(mode === "auto" ? "Режим: автоотклики" : "Режим: полуавто");
  }

  function initTelegramWidget(botUsername) {
    const box = $("telegram-login");
    box.innerHTML = "";
    window.onTelegramAuth = async (user) => {
      try {
        localStorage.removeItem("hh_token");
        token = "";
        const data = await api("/web/auth/telegram", {
          method: "POST",
          body: JSON.stringify(user),
        });
        token = data.access_token;
        if (!token) {
          throw new Error("Сервер не выдал токен");
        }
        localStorage.setItem("hh_token", token);
        me = data;
        if (!data.resume_ready) {
          showScreen("resume-screen");
        } else {
          await loadDashboard();
        }
      } catch (e) {
        localStorage.removeItem("hh_token");
        token = "";
        showToast(e.message || "Ошибка входа");
      }
    };
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", botUsername);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    script.setAttribute("data-request-access", "write");
    box.appendChild(script);
  }

  async function fetchConfig() {
    try {
      const cfg = await api("/web/config");
      return cfg.bot_username || "HHSearchVacanciesBot";
    } catch {
      return "HHSearchVacanciesBot";
    }
  }

  async function bootstrap() {
    const botUsername = await fetchConfig();
    if (!token) {
      showScreen("login-screen");
      initTelegramWidget(botUsername);
      return;
    }
    try {
      me = await api("/web/auth/me");
      if (!me.resume_ready) {
        showScreen("resume-screen");
        return;
      }
      await loadDashboard();
    } catch (e) {
      localStorage.removeItem("hh_token");
      token = "";
      showScreen("login-screen");
      initTelegramWidget(botUsername);
      if (e?.message && !e.message.includes("401")) {
        showToast(e.message);
      }
    }
  }

  $("resume-save")?.addEventListener("click", async () => {
    const text = $("resume-input").value.trim();
    if (text.length < 20) {
      showToast("Минимум 20 символов");
      return;
    }
    try {
      await api("/dashboard/resume", { method: "PUT", body: JSON.stringify({ resume_text: text }) });
      await loadDashboard();
    } catch (e) {
      showToast(e.message);
    }
  });

  $("logout-btn")?.addEventListener("click", async () => {
    await api("/web/auth/logout", { method: "POST" });
    localStorage.removeItem("hh_token");
    token = "";
    location.reload();
  });

  document.querySelectorAll(".mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => setMode(btn.dataset.mode));
  });

  $("refresh-search")?.addEventListener("click", () => {
    $("search-bar").classList.toggle("hidden");
  });

  $("search-cancel")?.addEventListener("click", () => {
    $("search-bar").classList.add("hidden");
  });

  $("search-run")?.addEventListener("click", async () => {
    const text = $("search-input").value.trim();
    if (text.length < 2) {
      showToast("Введи запрос");
      return;
    }
    showToast("Ищем вакансии… 1–3 мин (не закрывай страницу)");
    try {
      const result = await api("/dashboard/search", {
        method: "POST",
        body: JSON.stringify({ text, per_page: 7 }),
      });
      $("search-bar").classList.add("hidden");
      selected.clear();
      const count = result.vacancies?.length ?? 0;
      try {
        await loadDashboard();
        showToast(
          count
            ? `Готово: ${count} вакансий в подборке`
            : "Новых вакансий не нашли — попробуй другой запрос"
        );
      } catch (refreshError) {
        showToast(
          `Поиск сохранён (${count} шт.), но экран не обновился: ${refreshError.message}`
        );
      }
    } catch (e) {
      showToast(e.message || "Ошибка поиска");
    }
  });

  $("batch-send")?.addEventListener("click", async () => {
    if (!selected.size) {
      showToast("Выбери вакансии кнопкой «Выбрать»");
      return;
    }
    showToast("Готовим отклики… (по одному письму, может занять минуту)");
    try {
      const res = await api("/dashboard/applications/batch", {
        method: "POST",
        body: JSON.stringify({ analysis_ids: [...selected] }),
      });
      selected.clear();
      updateBatchBar();
      await loadDashboard();
      showToast(`Готово: ${res.sent} откликов, ошибок: ${res.failed}`);
    } catch (e) {
      showToast(e.message);
    }
  });

  bootstrap();
})();
