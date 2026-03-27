const API_BASE = "http://127.0.0.1:8000";

/* ---------------- path helpers ---------------- */

/**
 * Returns a relative path prefix based on how many directory levels
 * deep the current page is from the frontend root.
 * e.g. pages/onboarding/ → "../../", frontend root → ""
 */
function getRoot() {
  const depth = window.location.pathname
    .replace(/\/[^/]*$/, "")  // strip filename
    .split("/")
    .filter(p => p === "pages" || p === "onboarding" || p === "eligibility").length;
  return depth >= 2 ? "../../" : "";
}

/* ---------------- helpers ---------------- */

function getSessionId() {
  return localStorage.getItem("session_id");
}

function setSessionId(id) {
  localStorage.setItem("session_id", id);
}

function getUserId() {
  return localStorage.getItem("user_id");
}

function setUserData(data) {
  if (data.user_id) localStorage.setItem("user_id", data.user_id);
  if (data.name) localStorage.setItem("user_name", data.name);
  if (data.category) localStorage.setItem("user_category", data.category);
}

function getOnboardingData() {
  try {
    return JSON.parse(localStorage.getItem("haryana_onboarding") || "{}");
  } catch {
    return {};
  }
}

function saveOnboardingData(data) {
  localStorage.setItem("haryana_onboarding", JSON.stringify(data));
}

async function apiRequest(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  let data = {};
  try {
    data = await response.json();
  } catch (_) {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || data.message || `Request failed: ${response.status}`);
  }

  return data;
}

/* ---------------- landing ---------------- */

async function startOnboarding() {
  try {
    const data = await apiRequest("/onboarding/session/create", {
      method: "POST"
    });

    if (!data.session_id) {
      throw new Error("Session not created");
    }

    setSessionId(data.session_id);
    localStorage.removeItem("haryana_onboarding");
    window.location.href = "pages/onboarding/onboarding1.html";
  } catch (error) {
    console.error("Backend connection error:", error);
    const msg = document.getElementById("landingMessage");
    if (msg) {
      msg.innerHTML = `<p class="message-error">Unable to start onboarding. Check backend connection.</p>`;
    }
  }
}

/* ---------------- onboarding ---------------- */

function toggleNextButton(grid) {
  const card = grid.closest(".onboarding-card");
  if (!card) return;

  const nextBtn = card.querySelector(".next-btn");
  if (!nextBtn) return;

  const selectedCount = grid.querySelectorAll(".option-card.selected").length;
  nextBtn.disabled = selectedCount === 0;
}

function collectSelectedValues(grid) {
  const values = [...grid.querySelectorAll(".option-card.selected")].map((el) =>
    el.textContent.trim()
  );
  return grid.classList.contains("multi-select") ? values : values[0];
}

function initOptionSelection() {
  const grids = document.querySelectorAll(".option-grid");
  if (!grids.length) return;

  const savedData = getOnboardingData();

  const dynamicGrid = document.getElementById("dynamicOptionsGrid");
  if (dynamicGrid) {
    const userType = savedData.user_type || "General Citizen";
    let options = [];

    if (userType === "Student") {
      options = ["Government Colleges", "Government Internships", "Government Exams", "Government Scholarships"];
    } else if (userType === "Job Seeker") {
      options = ["Government Colleges", "Government Internships", "Government Exams", "Government Scholarships", "Government Jobs", "Government Schemes"];
    } else {
      options = ["Healthcare schemes", "Agriculture schemes", "Women & Child Welfare", "Transport & Public Services", "Housing schemes", "All Schemes"];
    }

    dynamicGrid.innerHTML = options.map(opt => `<button type="button" class="option-card">${opt}</button>`).join("");
  }

  grids.forEach((grid) => {
    const isMulti = grid.classList.contains("multi-select");
    const key = grid.dataset.key;
    const buttons = grid.querySelectorAll(".option-card");

    const saved = savedData[key];
    if (saved) {
      const savedValues = Array.isArray(saved) ? saved : [saved];
      buttons.forEach((btn) => {
        if (savedValues.includes(btn.textContent.trim())) {
          btn.classList.add("selected");
        }
      });
      toggleNextButton(grid);
    }

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        if (isMulti) {
          btn.classList.toggle("selected");
        } else {
          buttons.forEach((b) => b.classList.remove("selected"));
          btn.classList.add("selected");
        }
        toggleNextButton(grid);
      });
    });
  });
}

async function saveOnboardingStep(stepNumber, payload) {
  const sessionId = getSessionId();
  if (!sessionId) throw new Error("Session not found");

  return apiRequest(`/onboarding/session/${sessionId}/save-step`, {
    method: "POST",
    body: JSON.stringify({
      step_number: stepNumber,
      ...payload
    })
  });
}

async function completeOnboarding() {
  const sessionId = getSessionId();
  if (!sessionId) return;

  return apiRequest(`/onboarding/session/${sessionId}/complete`, {
    method: "POST"
  });
}

function initOnboardingNavigation() {
  const nextButtons = document.querySelectorAll(".next-btn");
  const skipButtons = document.querySelectorAll(".skip-btn");

  nextButtons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const step = Number(btn.dataset.step);
      let nextPage = btn.dataset.next;

      const card = btn.closest(".onboarding-card");
      const grid = card ? card.querySelector(".option-grid") : null;
      if (!grid) return;

      const key = grid.dataset.key;
      const selected = collectSelectedValues(grid);

      if (step === 1 && selected === "Job Seeker") {
        nextPage = "onboarding3.html";
      }

      const onboarding = getOnboardingData();
      onboarding[key] = selected;
      onboarding[`step${step}_skipped`] = false;
      saveOnboardingData(onboarding);

      try {
        if (step === 1) {
          await saveOnboardingStep(1, {
            user_type: selected,
            is_skipped: false
          });
        } else if (step === 2) {
          await saveOnboardingStep(2, {
            looking_for: selected,
            is_skipped: false
          });
        } else if (step === 3) {
          await saveOnboardingStep(3, {
            category: selected,
            is_skipped: false
          });
        } else if (step === 4) {
          await saveOnboardingStep(4, {
            location_preference: selected,
            is_skipped: false
          });
          await completeOnboarding();
        }

        window.location.href = nextPage;
      } catch (error) {
        console.error("Next step error:", error);
        alert("Failed to save onboarding step.");
      }
    });
  });

  skipButtons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const step = Number(btn.dataset.step);

      const onboarding = getOnboardingData();
      onboarding[`step${step}_skipped`] = true;
      saveOnboardingData(onboarding);

      try {
        await saveOnboardingStep(step, { is_skipped: true });

        if (step === 1) window.location.href = "onboarding2.html";
        if (step === 2) window.location.href = "onboarding3.html";
        if (step === 3) window.location.href = "onboarding4.html";
        if (step === 4) {
          await completeOnboarding();
          window.location.href = "../../home.html";
        }
      } catch (error) {
        console.error("Skip step error:", error);
        alert("Failed to skip step.");
      }
    });
  });
}

/* ---------------- login ---------------- */

async function loginUser() {
  const userIdInput = document.getElementById("loginUserId");
  const passwordInput = document.getElementById("loginPassword");
  const authMessage = document.getElementById("authMessage");

  if (!userIdInput || !passwordInput) return;

  const user_id = userIdInput.value.trim();
  const password = passwordInput.value.trim();

  if (!user_id || !password) {
    if (authMessage) {
      authMessage.innerHTML = `<p class="message-error">Please enter User ID and password.</p>`;
    }
    return;
  }

  try {
    const data = await apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        user_id,
        password
      })
    });

    setUserData(data);

    if (authMessage) {
      authMessage.innerHTML = `<p class="message-success">Login successful.</p>`;
    }

    const redirectPage = localStorage.getItem("post_login_redirect");
    if (redirectPage) {
      localStorage.removeItem("post_login_redirect");
      setTimeout(() => {
        window.location.href = redirectPage;
      }, 300);
    } else {
      setTimeout(() => {
        window.location.href = getRoot() + "home.html";
      }, 300);
    }
  } catch (error) {
    console.error("Login error:", error);
    if (authMessage) {
      authMessage.innerHTML = `<p class="message-error">Invalid credentials.</p>`;
    }
  }
}

function initLoginForm() {
  const loginBtn = document.getElementById("loginBtn");
  if (!loginBtn) return;
  loginBtn.addEventListener("click", loginUser);
}

/* ---------------- profile autofill ---------------- */

async function loadCommonProfileFields() {
  const userId = getUserId();
  if (!userId) return;

  try {
    const data = await apiRequest(`/user/${userId}`);

    const mappings = {
      readonlyAge: data.age,
      readonlyIncome: data.income,
      readonlyCategory: data.category,
      readonlyGender: data.gender,
      readonlyState: data.state,
      readonlyClass: data.current_class,
      readonlyEducation: data.education,
      readonlyPercentage: data.percentage
    };

    Object.entries(mappings).forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) el.value = value ?? "";
    });
  } catch (error) {
    console.error("Profile load error:", error);
  }
}

/* ---------------- home / opportunities ---------------- */

function initStateMap() {
  const mapSvg = document.querySelector(".haryana-map");
  const mapPaths = document.querySelectorAll(".haryana-map path");
  const mapLabels = document.querySelectorAll(".map-label");
  const tooltip = document.getElementById("districtTooltip");
  if (!mapPaths.length || !tooltip || !mapSvg) return;

  const getDistrictName = (element) => element.getAttribute("title") || element.textContent.trim();
  const getElementPairs = (id) => {
    return {
      path: document.getElementById(id),
      label: document.querySelector(`.map-label[data-id="${id}"]`)
    };
  };

  const handleHoverIn = (id, e) => {
    mapSvg.classList.add("is-hovered");
    const { path, label } = getElementPairs(id);
    if (path) path.classList.add("highlighted");
    if (label) label.classList.add("highlighted");

    const districtName = getDistrictName(path || label);
    tooltip.textContent = `${districtName} Opportunities`;
    tooltip.classList.add("show");
  };

  const handleHoverMove = (e) => {
    const mapRect = mapSvg.getBoundingClientRect();
    tooltip.style.left = `${e.clientX}px`;
    tooltip.style.top = `${e.clientY - 20}px`;
  };

  const handleHoverOut = (id) => {
    mapSvg.classList.remove("is-hovered");
    const { path, label } = getElementPairs(id);
    if (path) path.classList.remove("highlighted");
    if (label) label.classList.remove("highlighted");
    tooltip.classList.remove("show");
  };

  const handleClick = (id) => {
    const { path, label } = getElementPairs(id);
    const districtName = getDistrictName(path || label);
    alert(`Filtering opportunities for ${districtName}. (Connect to backend filter here)`);
  };

  // Attach to path
  mapPaths.forEach((path) => {
    const id = path.getAttribute("id");
    path.addEventListener("mouseenter", (e) => handleHoverIn(id, e));
    path.addEventListener("mousemove", handleHoverMove);
    path.addEventListener("mouseleave", () => handleHoverOut(id));
    path.addEventListener("click", () => handleClick(id));
  });

  // Attach to label
  mapLabels.forEach((label) => {
    const id = label.getAttribute("data-id");
    label.addEventListener("mouseenter", (e) => handleHoverIn(id, e));
    label.addEventListener("mousemove", handleHoverMove);
    label.addEventListener("mouseleave", () => handleHoverOut(id));
    label.addEventListener("click", () => handleClick(id));
  });
}

function initHeroRouting() {
  const exploreBtn = document.querySelector(".hero-actions .btn-primary");
  const aiBtn = document.getElementById("aiEligibilityBtn");
  
  if (!exploreBtn && !aiBtn) return;

  const onboarding = getOnboardingData();
  
  // Mapping logic for AI button
  let targetHref = "opportunities.html"; // Default fallback
  
  const lookingFor = Array.isArray(onboarding.looking_for) 
    ? onboarding.looking_for 
    : (onboarding.looking_for ? [onboarding.looking_for] : []);

  // If exact single match or primary priority
  if (lookingFor.length > 0) {
    const primary = lookingFor[0];
    if (primary === "Government Colleges") targetHref = "pages/eligibility/eligibility_colleges.html";
    else if (primary === "Government Scholarships") targetHref = "pages/eligibility/eligibility_scholarships.html";
    else if (primary === "Government Jobs") targetHref = "pages/eligibility/eligibility_jobs.html";
    else if (primary === "Government Exams") targetHref = "pages/eligibility/eligibility_exams.html";
    else if (primary === "Government Internships") targetHref = "pages/eligibility/eligibility_internships.html";
    else if (
      primary === "Government Schemes" ||
      primary === "Healthcare schemes" ||
      primary === "Agriculture schemes" ||
      primary === "Women & Child Welfare" ||
      primary === "Transport & Public Services" ||
      primary === "Housing schemes" ||
      primary === "All Schemes"
    ) {
      targetHref = "pages/eligibility/eligibility_schemes.html";
    }
  }

  // Explore button just goes straight to Recommended Opportunities
  if (exploreBtn) {
    exploreBtn.href = "opportunities.html";
  }

  // AI Button checks login first and uses mapped targetHref
  if (aiBtn) {
    aiBtn.addEventListener("click", () => {
      const userId = getUserId();
      if (!userId) {
        localStorage.setItem("post_login_redirect", targetHref);
        window.location.href = getRoot() + "auth.html";
        return;
      }
      window.location.href = targetHref;
    });
  }
}

function initNextBestActionAI() {
  document.addEventListener("click", async (event) => {
    const target = event.target.closest(".nba-analyze-btn");
    if (!target) return;

    const container = target.closest(".nba-section");
    const fileInput = container.querySelector(".nba-file-input");
    const resultDiv = container.querySelector(".nba-result");
    const opportunityName = target.getAttribute("data-opp");

    if (!fileInput.files.length) {
      resultDiv.style.display = "block";
      resultDiv.style.color = "#e11d48";
      resultDiv.innerHTML = "Please select a document first.";
      return;
    }

    const file = fileInput.files[0];
    
    // Convert to base64
    const reader = new FileReader();
    reader.onload = async () => {
      const base64Data = reader.result.split(",")[1];
      const mimeType = file.type || "application/pdf";

      target.disabled = true;
      target.textContent = "Analyzing...";
      resultDiv.style.display = "block";
      resultDiv.style.color = "#334155";
      resultDiv.innerHTML = "Processing document with Gemini AI...";

      try {
        const payload = {
          opportunity_name: opportunityName,
          file_name: file.name,
          mime_type: mimeType,
          file_data: base64Data,
          user_id: getUserId()
        };

        const reply = await apiRequest("/chatbot/analyze-document", {
          method: "POST",
          body: JSON.stringify(payload)
        });

        // Parse markdown lists roughly or just output
        resultDiv.style.color = "#16a34a"; // Green for success feedback base
        // But the AI text handles the specific formatting
        let replyText = reply.reply || "Analysis complete.";
        replyText = replyText.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        resultDiv.innerHTML = replyText;
      } catch (err) {
        console.error("NBA Error:", err);
        resultDiv.style.color = "#e11d48";
        resultDiv.innerHTML = "Analysis failed. Please try again.";
      } finally {
        target.disabled = false;
        target.textContent = "Analyze";
      }
    };
    reader.readAsDataURL(file);
  });
}

function attachApplyInterceptors() {
  document.addEventListener("click", (event) => {
    const target = event.target.closest(".apply-login-protected");
    if (!target) return;

    const userId = getUserId();
    if (!userId) {
      event.preventDefault();
      localStorage.setItem("post_login_redirect", getRoot() + "opportunities.html");
      window.location.href = getRoot() + "auth.html";
    }
  });
}

function buildOpportunitySection(title, items, type, fields) {
  if (!items || !items.length) return "";

  const cards = items.map((item) => {
    const lines = fields.map((field) => {
      return `<p><strong>${field.label}:</strong> ${item[field.key] ?? "-"}</p>`;
    }).join("");

    let link = item.apply_link || item.website_url || "#";
    if (link !== "#" && !link.startsWith("http") && !link.startsWith("javascript")) {
      link = "https://" + link;
    }
    const title = item.scholarship_name || item.scheme_name || item.college_name || item.job_title || item.title || "Opportunity";

    // Stable random deadline 1-28 based on title length
    let hash = 0;
    for (let i = 0; i < title.length; i++) hash = ((hash << 5) - hash) + title.charCodeAt(i);
    const daysLeft = (Math.abs(hash) % 28) + 1;
    let deadlineColor = "var(--text-muted)";
    if (daysLeft <= 5) deadlineColor = "#e11d48";
    else if (daysLeft <= 12) deadlineColor = "#ea580c";

    return `
      <div class="result-card">
        <span class="badge">${type}</span>
        ${lines}
        <p style="color: ${deadlineColor}; font-weight: 600; font-size: 13px; margin-top: 8px;">⏳ ${daysLeft} days left to apply</p>
        <a href="${link}" target="_blank" class="btn btn-primary apply-login-protected" style="margin-top: 12px;">Apply Now</a>
        
        <div class="nba-section" style="margin-top: 20px; padding: 16px; background: #f8fafc; border-radius: 12px; border: 1px dashed #cbd5e1;">
          <h4 style="font-size: 14px; margin-bottom: 8px; color: #334155;">✨ Next Best Action AI</h4>
          <p style="font-size: 13px; color: #64748b; margin-bottom: 12px; line-height: 1.4;">Upload a document to see what's missing for <strong>${title}</strong>.</p>
          <div style="display: flex; gap: 8px; align-items: center;">
            <input type="file" class="nba-file-input" style="font-size: 12px; max-width: 180px;" accept=".pdf,.png,.jpg" />
            <button type="button" class="btn btn-primary nba-analyze-btn" style="padding: 6px 12px; font-size: 12px;" data-opp="${title}">Analyze</button>
          </div>
          <div class="nba-result" style="margin-top: 12px; font-size: 13px; font-weight: 500; display: none;"></div>
        </div>
      </div>
    `;
  }).join("");

  return `
    <section class="section-head">
      <h2>${title}</h2>
    </section>
    <div class="result-grid">${cards}</div>
  `;
}

async function loadRecommendedOpportunities() {
  const container = document.getElementById("recommendedResults");
  if (!container) return;

  const onboarding = getOnboardingData();

  try {
    const lookingForMap = {
      "Government Colleges": "college",
      "Government Internships": "internship",
      "Government Exams": "exam",
      "Government Scholarships": "scholarship",
      "Government Jobs": "job",
      "Government Schemes": "scheme",
      "Healthcare schemes": "healthcare",
      "Agriculture schemes": "agriculture",
      "Women & Child Welfare": "women_child",
      "Transport & Public Services": "transport",
      "Housing schemes": "housing",
      "All Schemes": "all"
    };

    const rawLookingFor = Array.isArray(onboarding.looking_for)
      ? onboarding.looking_for
      : (onboarding.looking_for ? [onboarding.looking_for] : []);

    const mappedLookingFor = rawLookingFor.map((val) => lookingForMap[val.trim()] || val.trim());

    const params = new URLSearchParams({
      user_type: onboarding.user_type || "",
      looking_for: mappedLookingFor.join(","),
      category: onboarding.category || "",
      location_preference: onboarding.location_preference || ""
    });

    const data = await apiRequest(`/opportunities/recommended?${params.toString()}`);

    let html = "";
    
    // Fallback logic: If skip was pressed, the backend might return many. We only want best 3.
    const limit = 3;
    const safeSlice = (arr) => (Array.isArray(arr) ? arr.slice(0, limit) : []);

    html += buildOpportunitySection("Government Colleges", safeSlice(data.colleges), "College", [
      { key: "college_name", label: "College" },
      { key: "location", label: "Location" },
      { key: "tuition_fees", label: "Fees" }
    ]);

    html += buildOpportunitySection("Government Scholarships", safeSlice(data.scholarships), "Scholarship", [
      { key: "scholarship_name", label: "Scholarship" },
      { key: "scholarship_type", label: "Type" },
      { key: "annual_scholarship_amount", label: "Amount" }
    ]);

    html += buildOpportunitySection("Government Jobs", safeSlice(data.jobs), "Job", [
      { key: "post_name", label: "Post" },
      { key: "department", label: "Department" },
      { key: "job_location", label: "Location" }
    ]);

    html += buildOpportunitySection("Government Exams", safeSlice(data.exams), "Exam", [
      { key: "exam_name", label: "Exam" },
      { key: "exam_category", label: "Category" },
      { key: "exam_id", label: "Exam ID" }
    ]);

    html += buildOpportunitySection("Government Internships", safeSlice(data.internships), "Internship", [
      { key: "sector", label: "Sector" },
      { key: "location_city", label: "City" },
      { key: "stipend_per_month_inr", label: "Stipend" }
    ]);

    html += buildOpportunitySection("Government Schemes", safeSlice(data.schemes), "Scheme", [
      { key: "scheme_name", label: "Scheme" },
      { key: "ministry", label: "Ministry" },
      { key: "benefits", label: "Benefits" }
    ]);

    container.innerHTML = html || `<p class="muted">No recommendations found yet.</p>`;
  } catch (error) {
    console.error("Recommended opportunities error:", error);
    container.innerHTML = `<p class="muted">Unable to load opportunities.</p>`;
  }
}

/* ---------------- eligibility helpers ---------------- */

function renderResults(containerId, items, fieldMap) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!items || !items.length) {
    container.innerHTML = `<p class="muted">No results found.</p>`;
    return;
  }

  container.innerHTML = items.map((item) => {
    const status = item.eligibility_status || "Recommended";
    let badgeClass = "";
    
    // Assign specific color classes based on the status text
    const lowerStatus = status.toLowerCase();
    if (lowerStatus.includes("highly eligible") || lowerStatus.includes("recommended")) {
      badgeClass = "badge-highly-eligible";
    } else if (lowerStatus.includes("partially eligible")) {
      badgeClass = "badge-partially-eligible";
    } else if (lowerStatus.includes("eligible")) {
      badgeClass = "badge-eligible";
    }

    const rows = fieldMap.map((field) => {
      const value = item[field.key] ?? "-";
      return `<p><strong>${field.label}:</strong> ${value}</p>`;
    }).join("");

    let link = item.apply_link || item.website_url || "#";
    if (link !== "#" && !link.startsWith("http") && !link.startsWith("javascript")) {
      link = "https://" + link;
    }
    const title = item.scholarship_name || item.scheme_name || item.college_name || item.job_title || item.title || "Opportunity";

    let hash = 0;
    for (let i = 0; i < title.length; i++) hash = ((hash << 5) - hash) + title.charCodeAt(i);
    const daysLeft = (Math.abs(hash) % 28) + 1;
    let deadlineColor = "var(--text-muted)";
    if (daysLeft <= 5) deadlineColor = "#e11d48";
    else if (daysLeft <= 12) deadlineColor = "#ea580c";

    return `
      <div class="result-card">
        <span class="badge ${badgeClass}">${status}</span>
        ${rows}
        <p style="color: ${deadlineColor}; font-weight: 600; font-size: 13px; margin-top: 8px;">⏳ ${daysLeft} days left to apply</p>
        <a class="btn btn-primary apply-login-protected" href="${link}" target="_blank" style="margin-top: 12px;">Apply Now</a>
        
        <div class="nba-section" style="margin-top: 20px; padding: 16px; background: #f8fafc; border-radius: 12px; border: 1px dashed #cbd5e1;">
          <h4 style="font-size: 14px; margin-bottom: 8px; color: #334155;">✨ Next Best Action AI</h4>
          <p style="font-size: 13px; color: #64748b; margin-bottom: 12px; line-height: 1.4;">Upload a document to see what's missing for <strong>${title}</strong>.</p>
          <div style="display: flex; gap: 8px; align-items: center;">
            <input type="file" class="nba-file-input" style="font-size: 12px; max-width: 180px;" accept=".pdf,.png,.jpg" />
            <button type="button" class="btn btn-primary nba-analyze-btn" style="padding: 6px 12px; font-size: 12px;" data-opp="${title}">Analyze</button>
          </div>
          <div class="nba-result" style="margin-top: 12px; font-size: 13px; font-weight: 500; display: none;"></div>
        </div>
      </div>
    `;
  }).join("");
}

async function submitEligibility(endpoint, body, containerId, fieldMap) {
  const userId = getUserId();
  if (!userId) {
    localStorage.setItem("post_login_redirect", window.location.pathname.split("/").pop());
    window.location.href = getRoot() + "auth.html";
    return;
  }

  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = `<p class="muted">Checking eligibility...</p>`;

  try {
    const data = await apiRequest(endpoint, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, ...body })
    });

    renderResults(containerId, data.results || [], fieldMap);
  } catch (error) {
    console.error("Eligibility error:", error);
    container.innerHTML = `<p class="muted">Unable to check eligibility right now.</p>`;
  }
}

/* ---------------- forms ---------------- */

function initToggleButtons() {
  const toggleRows = document.querySelectorAll(".toggle-row");
  if (!toggleRows.length) return;

  toggleRows.forEach((row) => {
    const buttons = row.querySelectorAll(".toggle-btn");
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        buttons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
      });
    });
  });
}

function initCollegeForm() {
  const btn = document.getElementById("checkCollegeEligibility");
  if (!btn) return;

  btn.addEventListener("click", () => {
    submitEligibility("/eligibility/colleges", {
      course_offered: document.getElementById("course")?.value || "",
      entrance_exam_required: document.getElementById("entranceExam")?.value || "",
      percentage: Number(document.getElementById("percentage")?.value || 0),
      mode_of_study: document.querySelector("#studyModeToggle .toggle-btn.active")?.dataset.value || "Full Time",
      hostel_required: document.querySelector("#hostelToggle .toggle-btn.active")?.dataset.value || "Yes"
    }, "collegeResults", [
      { key: "college_name", label: "College Name" },
      { key: "location", label: "Location" },
      { key: "affiliated_university", label: "University" },
      { key: "tuition_fees", label: "Tuition Fees" },
      { key: "scholarships_available", label: "Scholarships" }
    ]);
  });
}

function initJobForm() {
  const btn = document.getElementById("checkJobEligibility");
  if (!btn) return;

  btn.addEventListener("click", () => {
    submitEligibility("/eligibility/jobs", {
      exam_name: document.getElementById("jobExamName")?.value || "",
      percentage: Number(document.getElementById("jobPercentage")?.value || 0)
    }, "jobResults", [
      { key: "post_name", label: "Post Name" },
      { key: "department", label: "Department" },
      { key: "job_location", label: "Job Location" }
    ]);
  });
}

function initExamForm() {
  const btn = document.getElementById("checkExamEligibility");
  if (!btn) return;

  btn.addEventListener("click", () => {
    submitEligibility("/eligibility/exams", {
      percentage: Number(document.getElementById("examPercentage")?.value || 0),
      education_required: document.getElementById("educationRequired")?.value || "",
      state: document.getElementById("examState")?.value || "",
      candidate_category: document.getElementById("examCategory")?.value || ""
    }, "examResults", [
      { key: "exam_name", label: "Exam Name" },
      { key: "exam_category", label: "Exam Category" },
      { key: "exam_id", label: "Exam ID" },
      { key: "age_relaxation", label: "Age Relaxation" }
    ]);
  });
}

function initInternshipForm() {
  const btn = document.getElementById("checkInternshipEligibility");
  if (!btn) return;

  btn.addEventListener("click", () => {
    submitEligibility("/eligibility/internships", {
      preferred_sector: document.getElementById("internshipSector")?.value || "",
      internship_mode: document.getElementById("internshipMode")?.value || "",
      preferred_duration: Number(document.getElementById("internshipDuration")?.value || 0),
      percentage: Number(document.getElementById("internshipPercentage")?.value || 0)
    }, "internshipResults", [
      { key: "sector", label: "Sector" },
      { key: "location_city", label: "Location City" },
      { key: "duration", label: "Duration" },
      { key: "stipend_per_month_inr", label: "Monthly Stipend" },
      { key: "mode", label: "Mode" }
    ]);
  });
}

function initScholarshipForm() {
  const btn = document.getElementById("checkScholarshipEligibility");
  if (!btn) return;

  btn.addEventListener("click", () => {
    submitEligibility("/eligibility/scholarships", {
      student_class: document.getElementById("studentClass")?.value || "",
      min_marks_required: Number(document.getElementById("schMarks")?.value || 0),
      eligible_category: document.getElementById("schCategory")?.value || "",
      scholarship_type: document.getElementById("schType")?.value || ""
    }, "scholarshipResults", [
      { key: "scholarship_id", label: "Scholarship ID" },
      { key: "scholarship_name", label: "Scholarship Name" },
      { key: "scholarship_type", label: "Scholarship Type" },
      { key: "annual_scholarship_amount", label: "Annual Amount" },
      { key: "application_deadline", label: "Deadline" },
      { key: "monthly_stipend", label: "Monthly Stipend" },
      { key: "hostel_allowance", label: "Hostel Allowance" }
    ]);
  });
}

function initSchemeForm() {
  const btn = document.getElementById("checkSchemeEligibility");
  if (!btn) return;

  btn.addEventListener("click", () => {
    submitEligibility("/eligibility/schemes", {
      max_age: Number(document.getElementById("schemeAge")?.value || 0),
      category: document.getElementById("schemeCategory")?.value || "",
      gender: document.getElementById("schemeGender")?.value || "",
      states: document.getElementById("schemeState")?.value || ""
    }, "schemeResults", [
      { key: "scheme_id", label: "Scheme ID" },
      { key: "scheme_name", label: "Scheme Name" },
      { key: "ministry", label: "Ministry" },
      { key: "benefits", label: "Benefits" }
    ]);
  });
}

/* ---------------- chatbot ---------------- */

function detectChatMode() {
  const userId = getUserId();
  
  // Rule 1: Not logged in -> general mode (Your Guide)
  if (!userId) {
    return "general"; 
  }

  // Rule 2: Logged in -> Analyze Profile
  const onboarding = getOnboardingData();
  const occ = (onboarding.occupation || "").toLowerCase();
  const lookingFor = Array.isArray(onboarding.looking_for) 
    ? onboarding.looking_for.map(x => (x||"").toLowerCase())
    : [(onboarding.looking_for || "").toLowerCase()];

  const isStudent = occ === "student" || 
    lookingFor.some(item => 
      item.includes("college") || 
      item.includes("scholarship") || 
      item.includes("internship") || 
      item.includes("exam")
    );

  if (isStudent) {
    return "career"; // Career Path AI
  }

  return "life-event"; // Life Event AI
}

function modeTitle(mode) {
  if (mode === "career") return "Career Path AI";
  if (mode === "life-event") return "Life Event AI";
  return "Your Guide";
}

function modePlaceholder(mode) {
  if (mode === "career") return "Ask about exams, colleges, jobs, internships, scholarships...";
  if (mode === "life-event") return "Ask about schemes, farmer support, pension, women welfare...";
  return "Ask anything about HaryanaSarthi...";
}

function endpointForMode(mode) {
  if (mode === "career") return "/chatbot/career";
  if (mode === "life-event") return "/chatbot/life-event";
  return "/chatbot/general";
}

function createChatbotUI() {
  if (document.getElementById("hsChatFab")) return;

  const mode = detectChatMode();

  const fab = document.createElement("button");
  fab.id = "hsChatFab";
  fab.type = "button";
  fab.textContent = "Your Guide";
  Object.assign(fab.style, {
    position: "fixed",
    right: "20px",
    bottom: "20px",
    zIndex: "9999",
    background: "#16a34a",
    color: "#fff",
    border: "none",
    borderRadius: "999px",
    padding: "14px 18px",
    cursor: "pointer",
    boxShadow: "0 10px 20px rgba(0,0,0,0.18)",
    fontWeight: "700"
  });

  const panel = document.createElement("div");
  panel.id = "hsChatPanel";
  panel.innerHTML = `
    <div id="hsChatHeader">
      <div>
        <strong>${modeTitle(mode)}</strong>
        <div style="font-size:12px; opacity:0.8;">Gemini-powered</div>
      </div>
      <button id="hsChatClose" type="button">×</button>
    </div>
    <div id="hsChatMessages">
      <div class="hs-msg bot">Hi! Ask me anything.</div>
    </div>
    <div id="hsChatInputWrap">
      <input id="hsChatInput" type="text" placeholder="${modePlaceholder(mode)}" />
      <button id="hsChatSend" type="button">Send</button>
    </div>
  `;

  Object.assign(panel.style, {
    position: "fixed",
    right: "20px",
    bottom: "78px",
    width: "340px",
    maxWidth: "calc(100vw - 32px)",
    height: "440px",
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: "16px",
    boxShadow: "0 18px 38px rgba(0,0,0,0.16)",
    zIndex: "9999",
    display: "none",
    overflow: "hidden"
  });

  const style = document.createElement("style");
  style.textContent = `
    #hsChatHeader {
      display:flex;
      align-items:center;
      justify-content:space-between;
      padding:14px 16px;
      background:#166534;
      color:white;
    }
    #hsChatClose {
      background:transparent;
      color:white;
      border:none;
      font-size:24px;
      cursor:pointer;
    }
    #hsChatMessages {
      height:320px;
      overflow-y:auto;
      padding:14px;
      background:#f8fafc;
    }
    .hs-msg {
      margin-bottom:10px;
      padding:10px 12px;
      border-radius:12px;
      line-height:1.45;
      max-width:88%;
      white-space:pre-wrap;
      word-break:break-word;
    }
    .hs-msg.bot {
      background:#e2e8f0;
      color:#111827;
    }
    .hs-msg.user {
      background:#dcfce7;
      color:#14532d;
      margin-left:auto;
    }
    #hsChatInputWrap {
      display:flex;
      gap:8px;
      padding:12px;
      border-top:1px solid #e5e7eb;
      background:white;
    }
    #hsChatInput {
      flex:1;
      padding:10px 12px;
      border:1px solid #d1d5db;
      border-radius:10px;
      outline:none;
    }
    #hsChatSend {
      background:#16a34a;
      color:#fff;
      border:none;
      border-radius:10px;
      padding:10px 14px;
      cursor:pointer;
      font-weight:700;
    }
  `;

  document.head.appendChild(style);
  document.body.appendChild(fab);
  document.body.appendChild(panel);

  fab.addEventListener("click", () => {
    panel.style.display = "block";
  });

  panel.querySelector("#hsChatClose").addEventListener("click", () => {
    panel.style.display = "none";
  });

  const sendBtn = panel.querySelector("#hsChatSend");
  const input = panel.querySelector("#hsChatInput");

  async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    const messages = panel.querySelector("#hsChatMessages");
    messages.insertAdjacentHTML("beforeend", `<div class="hs-msg user">${message}</div>`);
    messages.scrollTop = messages.scrollHeight;
    input.value = "";

    messages.insertAdjacentHTML("beforeend", `<div class="hs-msg bot" id="hsTyping">Thinking...</div>`);
    messages.scrollTop = messages.scrollHeight;

    try {
      const data = await apiRequest(endpointForMode(mode), {
        method: "POST",
        body: JSON.stringify({
          message,
          user_id: getUserId(),
          page: window.location.pathname.split("/").pop()
        })
      });

      const typing = document.getElementById("hsTyping");
      if (typing) typing.remove();

      let replyText = data.reply || "No response.";
      replyText = replyText.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
      messages.insertAdjacentHTML("beforeend", `<div class="hs-msg bot">${replyText}</div>`);
      messages.scrollTop = messages.scrollHeight;
    } catch (error) {
      const typing = document.getElementById("hsTyping");
      if (typing) typing.remove();

      messages.insertAdjacentHTML(
        "beforeend",
        `<div class="hs-msg bot">Unable to connect to chatbot right now.</div>`
      );
      messages.scrollTop = messages.scrollHeight;
    }
  }

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
}

function initChatbot() {
  createChatbotUI();
}

function initNavbarAuth() {
  const authLinks = document.querySelectorAll(".auth-link");
  const userId = getUserId();
  
  if (userId && authLinks.length) {
    authLinks.forEach(link => {
      link.href = getRoot() + "profile.html";
      link.textContent = "My Profile";
      // Optional styling tweak for logged in state
      link.style.background = "#0f172a"; 
      link.style.color = "#ffffff";
    });
  }
}

/* ---------------- init ---------------- */

document.addEventListener("DOMContentLoaded", () => {
  initNavbarAuth();
  
  const startBtn = document.getElementById("startBtn");
  if (startBtn) startBtn.addEventListener("click", startOnboarding);

  initOptionSelection();
  initOnboardingNavigation();
  initLoginForm();
  loadCommonProfileFields();
  initStateMap();
  initHeroRouting();
  attachApplyInterceptors();
  initNextBestActionAI();
  initToggleButtons();

  initCollegeForm();
  initJobForm();
  initExamForm();
  initInternshipForm();
  initScholarshipForm();
  initSchemeForm();

  loadRecommendedOpportunities();
  initChatbot();
});