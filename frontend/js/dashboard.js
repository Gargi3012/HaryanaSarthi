const API_BASE = window.location.origin;

document.addEventListener('DOMContentLoaded', async () => {
  // Global Chart Defaults
  Chart.defaults.font.family = "'Outfit', sans-serif";
  Chart.defaults.color = '#64748b';

  let colleges = 100;
  let scholarships = 1652;
  let internships = 1000;
  let jobs_exams = 50000;
  let schemes = 115;
  let totalOpps = colleges + scholarships + internships + jobs_exams + schemes;

  try {
    const res = await fetch(`${API_BASE}/stats`);
    if (res.ok) {
      const data = await res.json();
      colleges = data.colleges || 0;
      jobs_exams = data.jobs_exams || 0;
      scholarships = data.scholarships || 0;
      internships = data.internships || 0;
      schemes = data.schemes || 0;
      totalOpps = colleges + scholarships + internships + jobs_exams + schemes;
    }
  } catch (err) {
    console.error("Failed to fetch live stats, using fallback defaults:", err);
  }

  // Update Overview Metrics
  document.getElementById('metric-opps').innerText = totalOpps.toLocaleString();
  document.getElementById('metric-users').innerText = "3"; // Seeded users
  document.getElementById('metric-apps').innerText = "12";  // Sample applications count
  document.getElementById('metric-rate').innerText = "85%";

  // 2. Opportunities Distribution (Pie Chart)
  const oppsDistCtx = document.getElementById('oppsDistChart').getContext('2d');
  new Chart(oppsDistCtx, {
    type: 'pie',
    data: {
      labels: ['Colleges', 'Scholarships', 'Internships', 'Jobs & Exams', 'Schemes'],
      datasets: [{
        data: [colleges, scholarships, internships, jobs_exams, schemes],
        backgroundColor: [
          '#16a34a', '#0ea5e9', '#f59e0b', '#8b5cf6', '#14b8a6'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });

  // 3. Popular vs Less Explored Opportunities (Horizontal Bar Chart)
  const engagementCtx = document.getElementById('engagementChart').getContext('2d');
  new Chart(engagementCtx, {
    type: 'bar',
    data: {
      labels: ['Top College A', 'Post Matric Scholarship', 'Data Analyst Intern', 'State Job X', 'Exam Y', 'Scheme Z (Low)', 'Local Intern (Low)', 'Agri Scheme (Lowest)'],
      datasets: [{
        label: 'Engagement (Views/Applications)',
        data: [15000, 12000, 10500, 9000, 8000, 1200, 800, 300],
        backgroundColor: (ctx) => {
          const value = ctx.raw || 0;
          return value < 2000 ? '#ef4444' : '#16a34a';
        },
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false } },
        y: { grid: { display: false } }
      },
      plugins: { legend: { display: false } }
    }
  });

  // 4. Eligibility Insights (Doughnut Chart)
  const elighCtx = document.getElementById('eligibilityChart').getContext('2d');
  new Chart(elighCtx, {
    type: 'doughnut',
    data: {
      labels: ['Highly Eligible', 'Eligible', 'Partially Eligible'],
      datasets: [{
        data: [45, 35, 20],
        backgroundColor: ['#16a34a', '#ca8a04', '#e11d48'],
        borderWidth: 0,
        cutout: '70%'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom' } }
    }
  });

  // 5. User Segmentation (Bar Chart - Categories by Income grouped)
  const userSegmentCtx = document.getElementById('userSegmentChart').getContext('2d');
  new Chart(userSegmentCtx, {
    type: 'bar',
    data: {
      labels: ['General', 'SC', 'ST', 'OBC', 'EWS'],
      datasets: [{
        label: 'Users',
        data: [12000, 18000, 5000, 15000, 8000],
        backgroundColor: '#3b82f6',
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false } },
        y: { grid: { borderDash: [4, 4] } }
      }
    }
  });

  // 6. Region Insights - Haryana vs India (Line or Bar)
  const regionCtx = document.getElementById('regionChart').getContext('2d');
  new Chart(regionCtx, {
    type: 'line',
    data: {
      labels: ['Gurugram', 'Faridabad', 'Ambala', 'Rohtak', 'Hisar', 'Sirsa', 'Nuh'],
      datasets: [{
        label: 'Demand/Traffic',
        data: [18000, 15000, 9000, 7000, 6000, 2000, 800],
        borderColor: '#16a34a',
        backgroundColor: 'rgba(22, 163, 74, 0.1)',
        tension: 0.4,
        fill: true,
        pointBackgroundColor: '#16a34a'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, grid: { borderDash: [4, 4] } }
      }
    }
  });

  // 7. Sector Insights (Radar or Bar Chart)
  const sectorCtx = document.getElementById('sectorChart').getContext('2d');
  new Chart(sectorCtx, {
    type: 'polarArea',
    data: {
      labels: ['IT', 'Healthcare', 'Agriculture', 'Finance', 'Education', 'Manufacturing'],
      datasets: [{
        data: [25, 18, 5, 12, 20, 10],
        backgroundColor: [
          'rgba(59, 130, 246, 0.7)',
          'rgba(16, 185, 129, 0.7)',
          'rgba(245, 158, 11, 0.7)',
          'rgba(139, 92, 246, 0.7)',
          'rgba(236, 72, 153, 0.7)',
          'rgba(100, 116, 139, 0.7)'
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'right' } }
    }
  });

});
