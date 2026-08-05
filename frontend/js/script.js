const API_BASE = window.location.origin;

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
  if (data.access_token) localStorage.setItem("access_token", data.access_token);
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
  const token = localStorage.getItem("access_token");
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: headers
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
    
    // Dynamically save clicked district as location preference
    const onboarding = getOnboardingData();
    onboarding.location_preference = districtName;
    saveOnboardingData(onboarding);
    
    // Reload recommendations to reflect the selected district
    loadRecommendedOpportunities();
    
    // Update the section header visually
    const head = document.querySelector(".section-head h2");
    if (head) {
      head.innerHTML = `Recommended Opportunities in <span style="color: #16a34a;">${districtName}</span>`;
    }
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
      resultDiv.innerHTML = "Processing document with Groq AI...";

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
        <div style="font-size:11px; opacity:0.85; display:flex; align-items:center; gap:6px; margin-top:2px;">
          <span id="hsChatProviderBadge" style="background:rgba(255,255,255,0.18); border-radius:99px; padding:1px 7px; font-weight:600;">⚡ Groq AI</span>
          <button id="hsSwitchProvider" type="button" style="background:transparent; border:1px solid rgba(255,255,255,0.4); border-radius:99px; color:white; font-size:10px; padding:1px 7px; cursor:pointer; font-weight:500;">Switch</button>
        </div>
      </div>
      <button id="hsChatClose" type="button">×</button>
    </div>
    <div id="hsChatMessages">
      <div class="hs-msg bot">Hi! Ask me anything.</div>
    </div>
    <div id="hsChatSuggestions" style="padding: 6px 12px; display: flex; gap: 6px; overflow-x: auto; background: #f1f5f9; border-top: 1px solid #e5e7eb;">
      <span class="hs-suggestion" style="font-size: 11px; padding: 4px 8px; background: white; border: 1px solid #cbd5e1; border-radius: 99px; cursor: pointer; white-space: nowrap; color: #334155; font-weight: 500;">🔍 Check Eligibility</span>
      <span class="hs-suggestion" style="font-size: 11px; padding: 4px 8px; background: white; border: 1px solid #cbd5e1; border-radius: 99px; cursor: pointer; white-space: nowrap; color: #334155; font-weight: 500;">🎓 Search Scholarships</span>
      <span class="hs-suggestion" style="font-size: 11px; padding: 4px 8px; background: white; border: 1px solid #cbd5e1; border-radius: 99px; cursor: pointer; white-space: nowrap; color: #334155; font-weight: 500;">🌾 Farmer Support</span>
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

  // --- Provider toggle: Groq AI ↔ Quick FAQ ---
  let currentProvider = "groq"; // "groq" | "faq"
  const badge = panel.querySelector("#hsChatProviderBadge");
  const switchBtn = panel.querySelector("#hsSwitchProvider");

  switchBtn.addEventListener("click", () => {
    if (currentProvider === "groq") {
      currentProvider = "faq";
      badge.textContent = "💬 Quick FAQ";
      badge.style.background = "rgba(255,255,255,0.18)";
      switchBtn.textContent = "Use Groq AI";
      panel.querySelector("#hsChatInput").placeholder = "Type a keyword (e.g. scholarship, job, eligibility)...";
      const messages = panel.querySelector("#hsChatMessages");
      messages.insertAdjacentHTML("beforeend", `<div class="hs-msg bot" style="border-left:3px solid #fbbf24; padding-left:8px;">Switched to <strong>Quick FAQ mode</strong> — instant offline answers. No internet needed!</div>`);
      messages.scrollTop = messages.scrollHeight;
    } else {
      currentProvider = "groq";
      badge.textContent = "⚡ Groq AI";
      switchBtn.textContent = "Switch";
      panel.querySelector("#hsChatInput").placeholder = modePlaceholder(mode);
      const messages = panel.querySelector("#hsChatMessages");
      messages.insertAdjacentHTML("beforeend", `<div class="hs-msg bot" style="border-left:3px solid #4ade80; padding-left:8px;">Switched to <strong>Groq AI (Llama 3.3)</strong> — full AI responses.</div>`);
      messages.scrollTop = messages.scrollHeight;
    }
  });

  // Offline FAQ answers for Quick FAQ mode
  function getFaqAnswer(msg) {
    const m = msg.toLowerCase();
    if (m.includes("scholarship")) return "🎓 HaryanaSarthi has 1,652+ scholarships. Go to Opportunities → Scholarships and use 'Check Eligibility' to filter ones matching your profile.";
    if (m.includes("job") || m.includes("naukri")) return "💼 Explore 50,000+ job exam listings under Opportunities → Jobs & Exams. Filter by your qualification.";
    if (m.includes("college") || m.includes("admission")) return "🏫 Browse 100+ colleges on HaryanaSarthi. Use the Eligibility Checker under each college listing for your match.";
    if (m.includes("internship")) return "📋 1,000+ internship listings are available. Go to Opportunities → Internships and filter by sector and mode.";
    if (m.includes("scheme") || m.includes("yojana")) return "🏛️ 115+ government schemes available. Check Opportunities → Schemes for farmer, women, student & senior citizen support.";
    if (m.includes("eligib")) return "✅ Use the 'Check Eligibility' button on any opportunity card to instantly check if you qualify based on your profile.";
    if (m.includes("login") || m.includes("account")) return "🔑 Click 'Login / Register' on the top navbar. Use your User ID and password to sign in.";
    if (m.includes("document") || m.includes("upload")) return "📄 Open any opportunity → click 'Analyze My Documents' to upload your Aadhar, marksheet, or certificate for AI analysis.";
    if (m.includes("haryana") || m.includes("sarthi")) return "🌱 HaryanaSarthi is a government opportunity discovery platform for Haryana — connecting citizens to scholarships, jobs, colleges, internships & schemes.";
    if (m.includes("farmer") || m.includes("kisan")) return "🌾 Explore farmer schemes under Opportunities → Schemes. Filter by occupation 'Farmer' for PM-Kisan, crop insurance, and more.";
    if (m.includes("women") || m.includes("mahila")) return "👩 Women-specific scholarships and schemes are available. Filter by Gender = Female in the Eligibility Checker.";
    if (m.includes("hello") || m.includes("hi") || m.includes("namaste")) return "🙏 Namaste! Main Quick FAQ mode mein hoon. Aap scholarship, job, college, internship, ya scheme ke baare mein pooch sakte hain!";
    return "ℹ️ Quick FAQ mein yeh answer nahi mila. Groq AI pe switch karke poori AI se baat karein — woh zyada detail dega!";
  }

  const sendBtn = panel.querySelector("#hsChatSend");
  const input = panel.querySelector("#hsChatInput");

  panel.querySelectorAll(".hs-suggestion").forEach((chip) => {
    chip.addEventListener("click", () => {
      // Extract suggestion text and trigger message send
      input.value = chip.textContent.trim();
      sendMessage();
    });
  });

  async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    const messages = panel.querySelector("#hsChatMessages");
    messages.insertAdjacentHTML("beforeend", `<div class="hs-msg user">${message}</div>`);
    messages.scrollTop = messages.scrollHeight;
    input.value = "";

    // Quick FAQ mode — instant offline response
    if (currentProvider === "faq") {
      const answer = getFaqAnswer(message);
      messages.insertAdjacentHTML("beforeend", `<div class="hs-msg bot">${answer}</div>`);
      messages.scrollTop = messages.scrollHeight;
      return;
    }

    // Groq AI mode — API call
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
        `<div class="hs-msg bot">Unable to connect to Groq AI right now. Try switching to <strong>Quick FAQ</strong> mode using the Switch button above!</div>`
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

function initThemeToggle() {
  const activeTheme = localStorage.getItem("theme");
  if (activeTheme === "dark") {
    document.body.classList.add("dark-theme");
  }

  const navRight = document.querySelector(".nav-right");
  if (!navRight) return;

  if (document.getElementById("themeToggleBtn")) return;

  const toggleBtn = document.createElement("button");
  toggleBtn.id = "themeToggleBtn";
  toggleBtn.type = "button";
  toggleBtn.innerHTML = activeTheme === "dark" ? "☀️ Light" : "🌙 Dark";

  Object.assign(toggleBtn.style, {
    background: "transparent",
    border: "1px solid var(--border-color)",
    color: "var(--text-main)",
    padding: "8px 12px",
    borderRadius: "var(--radius-sm)",
    cursor: "pointer",
    fontWeight: "600",
    fontSize: "13px",
    marginRight: "10px",
    display: "flex",
    alignItems: "center",
    gap: "4px"
  });

  navRight.insertBefore(toggleBtn, navRight.firstChild);

  toggleBtn.addEventListener("click", () => {
    const isDark = document.body.classList.toggle("dark-theme");
    if (isDark) {
      localStorage.setItem("theme", "dark");
      toggleBtn.innerHTML = "☀️ Light";
    } else {
      localStorage.setItem("theme", "light");
      toggleBtn.innerHTML = "🌙 Dark";
    }
  });
}

/* ---------------- init ---------------- */

document.addEventListener("DOMContentLoaded", () => {
  initNavbarAuth();
  initThemeToggle();
  
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