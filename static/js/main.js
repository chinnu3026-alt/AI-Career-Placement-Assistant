document.addEventListener('DOMContentLoaded', function () {
    // -------------------------------------------------------------
    // Global Theme Toggle Functionality
    // -------------------------------------------------------------
    const themeBtn = document.getElementById('theme-toggle-btn');
    const themeIcon = document.getElementById('theme-toggle-icon');
    
    function updateThemeUI(theme) {
        if (theme === 'light') {
            if (themeIcon) {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            }
        } else {
            if (themeIcon) {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        }
    }
    
    const currentTheme = localStorage.getItem('theme') || 'dark';
    updateThemeUI(currentTheme);
    
    if (themeBtn) {
        themeBtn.addEventListener('click', function() {
            const activeTheme = document.documentElement.getAttribute('data-theme') || 'dark';
            const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeUI(newTheme);
        });
    }

    // -------------------------------------------------------------
    // Global Company Logo Fallback Generator (Gradients + Letter)
    // -------------------------------------------------------------
    window.getCompanyLogoFallback = function (companyName, size = 'normal') {
        const name = companyName || 'Company';
        const words = name.replace(/[^a-zA-Z0-9 ]/g, '').split(/\s+/).filter(Boolean);
        let initials = '';
        if (words.length >= 2) {
            initials = (words[0].charAt(0) + words[1].charAt(0) + (words[2] ? words[2].charAt(0) : '')).toUpperCase();
        } else {
            const clean = name.replace(/[^a-zA-Z0-9]/g, '');
            initials = clean.length > 3 ? clean.substring(0, 3).toUpperCase() : clean.toUpperCase();
        }
        if (!initials) initials = 'CO';

        const gradients = [
            ["#4F46E5", "#06B6D4"],
            ["#3B82F6", "#8B5CF6"],
            ["#10B981", "#059669"],
            ["#EC4899", "#F43F5E"],
            ["#F59E0B", "#D97706"],
            ["#6366F1", "#A855F7"],
            ["#0ea5e9", "#2563eb"],
            ["#84cc16", "#10b981"],
            ["#f43f5e", "#b91c1c"],
            ["#14b8a6", "#0d9488"]
        ];
        
        let hash = 0;
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }
        const index = Math.abs(hash) % gradients.length;
        const [c1, c2] = gradients[index];
        const shapeStyle = Math.abs(hash) % 4;
        
        let shapes = '';
        if (shapeStyle === 0) {
            shapes = `<polygon points="50,15 80,32 80,68 50,85 20,68 20,32" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linejoin="round" opacity="0.25" />`;
        } else if (shapeStyle === 1) {
            shapes = `<polygon points="50,20 80,50 50,80 20,50" fill="none" stroke="#FFFFFF" stroke-width="3" opacity="0.25" />
                      <polygon points="50,35 65,50 50,65 35,50" fill="#FFFFFF" opacity="0.15" />`;
        } else if (shapeStyle === 2) {
            shapes = `<circle cx="42" cy="50" r="22" fill="#FFFFFF" opacity="0.2" />
                      <circle cx="58" cy="50" r="22" fill="#FFFFFF" opacity="0.2" />`;
        } else {
            shapes = `<path d="M 25,50 C 25,35 40,35 50,50 C 60,65 75,65 75,50 C 75,35 60,35 50,50 C 40,65 25,65 25,50 Z" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" opacity="0.25" />`;
        }

        return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" style="width: 100%; height: 100%; display: block; border-radius: 4px;">
            <defs>
                <linearGradient id="fallback_grad_${Math.abs(hash)}" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="${c1}" />
                    <stop offset="100%" stop-color="${c2}" />
                </linearGradient>
            </defs>
            <rect width="100" height="100" fill="url(#fallback_grad_${Math.abs(hash)})" rx="24" />
            ${shapes}
            <text x="50" y="54" dominant-baseline="middle" text-anchor="middle" font-family="'Outfit', sans-serif" font-size="28" font-weight="900" fill="#FFFFFF">${initials}</text>
        </svg>`;
    };

    window.getRealCompanyLogo = function (companyName, originalUrl) {
        if (!companyName) return originalUrl;
        const key = companyName.toLowerCase().replace(/[^a-z0-9]/g, '');
        return `/static/images/companies/${key}.svg`;
    };

    // -------------------------------------------------------------
    // Debounce helper
    // -------------------------------------------------------------
    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }

    // -------------------------------------------------------------
    // Auto-fade flash alerts
    // -------------------------------------------------------------
    const alerts = document.querySelectorAll('.alert-custom');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(function () {
                alert.remove();
            }, 600);
        }, 5000);
    });

    // -------------------------------------------------------------
    // SPA View Router - Sidebar links toggle panels
    // -------------------------------------------------------------
    window.activateDashboardView = function (viewId) {
        // Toggle active class on sidebar links
        const links = document.querySelectorAll('.sidebar-link');
        links.forEach(l => {
            if (l.getAttribute('data-tab') === viewId) {
                l.classList.add('active');
            } else {
                l.classList.remove('active');
            }
        });
        
        // Hide/Show panels
        const panels = document.querySelectorAll('.dashboard-view-panel');
        panels.forEach(p => {
            if (p.id === viewId) {
                p.style.display = 'block';
            } else {
                p.style.display = 'none';
            }
        });
        
        // Scroll to top of main workspace body
        const mainBody = document.querySelector('.main-dashboard-body');
        if (mainBody) mainBody.scrollTop = 0;
    };

    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const tabId = this.getAttribute('data-tab');
            
            // Map sub-tabs or helper clicks back to core views
            if (tabId === 'view-readiness-details' || tabId === 'view-gap-analysis' || tabId === 'view-roadmap-weeks') {
                // If company readiness / gap / learning roadmap clicked but no company selected, redirect to explorer
                const emptyDetail = document.getElementById('company-detail-empty-state');
                if (emptyDetail && emptyDetail.style.display !== 'none') {
                    alert('Please select a target company first to analyze readiness, gaps, and roadmap!');
                    activateDashboardView('view-dream-company');
                    return;
                }
            }
            
            activateDashboardView(tabId);
            
            if (tabId === 'view-ai-career-intelligence') {
                loadAICareerIntelligence();
            }
            
            // Close mobile offcanvas if open
            const offcanvasEl = document.getElementById('sidebarOffcanvas');
            if (offcanvasEl && window.bootstrap) {
                const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
                if (bsOffcanvas) bsOffcanvas.hide();
            }
        });
    });

    // -------------------------------------------------------------
    // Bookmarked Companies Engine (Local Storage)
    // -------------------------------------------------------------
    window.toggleBookmarkCompany = function (companyName, city, type, package_range) {
        fetch('/api/saved-companies')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const isSaved = data.companies.some(c => c.name.toLowerCase() === companyName.toLowerCase() && c.city.toLowerCase() === city.toLowerCase());
                    const formData = new FormData();
                    formData.append('company_name', companyName);
                    formData.append('city', city);
                    if (isSaved) {
                        fetch('/api/saved-companies/delete', { method: 'POST', body: formData })
                            .then(res => res.json())
                            .then(() => {
                                updateBookmarkUI(companyName, city);
                                renderSavedCompaniesList();
                            });
                    } else {
                        fetch('/api/saved-companies/add', { method: 'POST', body: formData })
                            .then(res => res.json())
                            .then(() => {
                                updateBookmarkUI(companyName, city);
                                renderSavedCompaniesList();
                            });
                    }
                }
            });
    };

    window.updateBookmarkUI = function (companyName, city) {
        fetch('/api/saved-companies')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const isBookmarked = data.companies.some(c => c.name.toLowerCase() === companyName.toLowerCase() && c.city.toLowerCase() === city.toLowerCase());
                    const btn = document.getElementById('btn-bookmark-company');
                    if (btn) {
                        const icon = btn.querySelector('i');
                        if (icon) {
                            if (isBookmarked) {
                                icon.className = 'fa-solid fa-bookmark text-info';
                            } else {
                                icon.className = 'fa-regular fa-bookmark';
                            }
                        }
                    }
                    const badge = document.getElementById('saved-companies-badge');
                    if (badge) badge.innerText = data.companies.length;
                }
            });
    };

    window.renderSavedCompaniesList = function () {
        const grid = document.getElementById('saved-companies-grid');
        if (!grid) return;
        
        fetch('/api/saved-companies')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    grid.innerHTML = '';
                    if (data.companies.length > 0) {
                        data.companies.forEach(comp => {
                            const realLogoUrl = window.getRealCompanyLogo(comp.name, comp.logo_url);
                     const logoHtml = `<div class="company-logo-wrapper">${realLogoUrl ? `<img src="${realLogoUrl}" class="company-logo-img" onerror="this.onerror=null; this.outerHTML=window.getCompanyLogoFallback('${comp.name.replace(/'/g, "\\'")}');" alt="${comp.name}">` : window.getCompanyLogoFallback(comp.name)}</div>`;
                            
                            const rawPkg = comp.package_range || '5-12 LPA';
                            const cleanPkg = rawPkg.toString().toLowerCase().includes('lpa') 
                                ? rawPkg.toString().replace(/lpa/i, '').trim() 
                                : rawPkg.toString().trim();

                            grid.innerHTML += `
                                <div class="col-md-4 col-sm-6">
                                    <div class="glass-card p-3">
                                        <div class="d-flex justify-content-between align-items-start mb-2">
                                            <div class="p-2 bg-dark rounded border border-secondary" style="display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; overflow: hidden; padding: 2px !important;">
                                                ${logoHtml}
                                            </div>
                                            <button type="button" class="btn btn-glass p-1 border-0 text-danger" onclick="toggleBookmarkCompany('${comp.name.replace(/'/g, "\\'")}', '${comp.city.replace(/'/g, "\\'")}')">
                                                <i class="fa-solid fa-trash-can"></i>
                                            </button>
                                        </div>
                                        <h5 class="fs-7 text-white fw-bold mb-1">${comp.name}</h5>
                                        <p class="text-secondary-custom fs-9 mb-2"><i class="fa-solid fa-location-dot me-1"></i>${comp.city}</p>
                                        <div class="d-flex justify-content-between align-items-center border-top border-secondary pt-2 mt-2">
                                            <span class="fs-9 text-gradient-green font-bold">₹ ${cleanPkg} LPA</span>
                                            <button class="btn btn-premium btn-xs px-2 py-1 fs-9" onclick="activateDreamCompanyTab('${comp.name.replace(/'/g, "\\'")}', '${comp.city.replace(/'/g, "\\'")}')">Open</button>
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                    } else {
                        grid.innerHTML = '<div class="col-12 text-muted fs-8 text-center py-4">No bookmarked companies listed. Bookmark target companies in the Dream Company explorer.</div>';
                    }
                }
            });
    };

    window.activateDreamCompanyTab = function (name, city) {
        activateDashboardView('view-dream-company');
        selectDashboardCompany(name, city);
    };

    // 2. Application Tracker APIs integration
    window.addSelectedCompanyToTracker = function () {
        const select = document.getElementById('detail-tracker-status');
        if (!select) return;
        const status = select.value;
        if (status === 'none') return;
        
        const companyName = document.getElementById('detail-company-name').innerText;
        const city = document.getElementById('detail-company-location').innerText;
        const type = document.getElementById('detail-company-type').innerText;
        
        const formData = new FormData();
        formData.append('company_name', companyName);
        formData.append('city', city);
        formData.append('type', type);
        formData.append('status', status);
        
        fetch('/api/tracked-applications/save', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    select.value = 'none';
                    renderTrackerBoard();
                    alert(`Application for ${companyName} marked as: ${status}`);
                }
            });
    };

    window.renderTrackerBoard = function () {
        fetch('/api/tracked-applications')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const list = data.applications;
                    const cols = {
                        'Applied': document.getElementById('tracker-applied-cards'),
                        'Interview Scheduled': document.getElementById('tracker-interview-cards'),
                        'Rejected': document.getElementById('tracker-rejected-cards'),
                        'Selected': document.getElementById('tracker-selected-cards')
                    };
                    
                    const counters = {
                        'Applied': document.getElementById('tracker-count-applied'),
                        'Interview Scheduled': document.getElementById('tracker-count-interview'),
                        'Rejected': document.getElementById('tracker-count-rejected'),
                        'Selected': document.getElementById('tracker-count-selected')
                    };
                    
                    Object.keys(cols).forEach(k => { if (cols[k]) cols[k].innerHTML = ''; });
                    Object.keys(counters).forEach(k => { if (counters[k]) counters[k].innerText = '0'; });
                    
                    let cardCount = 0;
                    list.forEach(app => {
                        const col = cols[app.status];
                        if (col) {
                            cardCount++;
                            counters[app.status].innerText = parseInt(counters[app.status].innerText) + 1;
                            
                            const card = document.createElement('div');
                            card.className = 'dashboard-list-item p-2.5 mb-2 d-flex flex-column align-items-start gap-1.5';
                            card.style.background = 'var(--bg-card)';
                            card.innerHTML = `
                                <div class="d-flex justify-content-between align-items-start w-100">
                                    <span class="fs-8 text-white fw-bold">${app.name}</span>
                                    <button class="btn p-0 border-0 text-danger fs-9" onclick="deleteTrackedApplication('${app.name.replace(/'/g, "\\'")}', '${app.city.replace(/'/g, "\\'")}')"><i class="fa-solid fa-trash-can"></i></button>
                                </div>
                                <span class="badge bg-secondary fs-9" style="font-size: 0.65rem !important;">${app.city} &bull; ${app.type}</span>
                                <div class="d-flex gap-1 mt-1 w-100">
                                    <select class="form-select fs-9 py-0.5" onchange="moveApplicationStatus('${app.name.replace(/'/g, "\\'")}', '${app.city.replace(/'/g, "\\'")}', '${app.type.replace(/'/g, "\\'")}', this.value)" style="height: 24px; font-size: 11px !important;">
                                        <option value="Applied" ${app.status === 'Applied' ? 'selected' : ''}>Applied</option>
                                        <option value="Interview Scheduled" ${app.status === 'Interview Scheduled' ? 'selected' : ''}>Interview</option>
                                        <option value="Rejected" ${app.status === 'Rejected' ? 'selected' : ''}>Rejected</option>
                                        <option value="Selected" ${app.status === 'Selected' ? 'selected' : ''}>Selected</option>
                                    </select>
                                </div>
                            `;
                            col.appendChild(card);
                        }
                    });
                    
                    const badge = document.getElementById('tracker-badge-counter');
                    if (badge) badge.innerText = cardCount;
                }
            });
    };

    window.deleteTrackedApplication = function (companyName, city) {
        const formData = new FormData();
        formData.append('company_name', companyName);
        formData.append('city', city);
        fetch('/api/tracked-applications/delete', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(() => renderTrackerBoard());
    };

    window.moveApplicationStatus = function (companyName, city, type, newStatus) {
        const formData = new FormData();
        formData.append('company_name', companyName);
        formData.append('city', city);
        formData.append('type', type);
        formData.append('status', newStatus);
        fetch('/api/tracked-applications/save', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(() => renderTrackerBoard());
    };

    // 3. Placement Calendar Schedules
    const calendarForm = document.getElementById('add-event-form');
    if (calendarForm) {
        calendarForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(calendarForm);
            fetch('/api/calendar-events/add', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        calendarForm.reset();
                        renderCalendarEvents();
                    } else {
                        alert(data.message);
                    }
                });
        });
    }

    window.renderCalendarEvents = function () {
        const container = document.getElementById('calendar-events-list');
        if (!container) return;
        
        fetch('/api/calendar-events')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    container.innerHTML = '';
                    if (data.events.length > 0) {
                        data.events.forEach(evt => {
                            container.innerHTML += `
                                <div class="dashboard-list-item">
                                    <div>
                                        <h5 class="fs-8 text-white fw-bold mb-0.5">${evt.title}</h5>
                                        <p class="text-secondary mb-0.5 fs-9"><i class="fa-regular fa-calendar me-1"></i>${evt.date}</p>
                                        <p class="text-muted mb-0 fs-9">${evt.description || 'No additional description.'}</p>
                                    </div>
                                    <button class="btn p-0 border-0 text-danger fs-9" onclick="deleteCalendarEvent('${evt.id}')">
                                        <i class="fa-solid fa-trash-can"></i>
                                    </button>
                                </div>
                            `;
                        });
                    } else {
                        container.innerHTML = '<p class="text-muted fs-8">No scheduled events found.</p>';
                    }
                }
            });
    };

    window.deleteCalendarEvent = function (id) {
        const formData = new FormData();
        formData.append('event_id', id);
        fetch('/api/calendar-events/delete', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(() => renderCalendarEvents());
    };

    // 4. Coding Progress
    const codingForm = document.getElementById('add-coding-form');
    if (codingForm) {
        codingForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(codingForm);
            fetch('/api/coding-progress/save', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        codingForm.reset();
                        renderCodingProgress();
                    } else {
                        alert(data.message);
                    }
                });
        });
    }

    window.renderCodingProgress = function () {
        const container = document.getElementById('coding-progress-cards');
        if (!container) return;
        
        fetch('/api/coding-progress')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    container.innerHTML = '';
                    if (data.progress.length > 0) {
                        data.progress.forEach(p => {
                            let icon = '<i class="fa-solid fa-code text-info fs-4"></i>';
                            if (p.platform.toLowerCase() === 'leetcode') {
                                icon = '<i class="fa-solid fa-cubes text-warning fs-4"></i>';
                            } else if (p.platform.toLowerCase() === 'hackerrank') {
                                icon = '<i class="fa-brands fa-hackerrank text-success fs-4"></i>';
                            }
                            const percent = Math.min(100, Math.round((p.problems_solved / 500) * 100));
                            
                            container.innerHTML += `
                                <div class="col-6">
                                    <div class="glass-card p-3 d-flex flex-column justify-content-between h-100">
                                        <div class="d-flex justify-content-between align-items-center mb-2">
                                            <div class="d-flex align-items-center gap-2">
                                                ${icon}
                                                <span class="fs-8 text-white fw-bold">${p.platform}</span>
                                            </div>
                                            <button class="btn p-0 border-0 text-danger fs-9" onclick="deleteCodingProgress('${p.id}')"><i class="fa-solid fa-trash-can"></i></button>
                                        </div>
                                        <div class="mb-2">
                                            <span class="fs-7 text-gradient-green font-bold">${p.problems_solved}</span> Solved
                                            <p class="mb-0 text-muted fs-9">Rating: ${p.rating || 'N/A'}</p>
                                        </div>
                                        <div class="progress" style="height: 4px; background: rgba(255,255,255,0.05); border-radius: 4px;">
                                            <div class="progress-bar bg-success" role="progressbar" style="width: ${percent}%;"></div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                    } else {
                        container.innerHTML = '<div class="col-12 text-muted fs-8 text-center py-4">No coding platform metrics logged.</div>';
                    }
                }
            });
    };

    window.deleteCodingProgress = function (id) {
        const formData = new FormData();
        formData.append('progress_id', id);
        fetch('/api/coding-progress/delete', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(() => renderCodingProgress());
    };

    // 5. Recruiter Evaluations
    const evalForm = document.getElementById('add-eval-form');
    if (evalForm) {
        evalForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(evalForm);
            fetch('/api/recruiter-evaluations/add', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        evalForm.reset();
                        renderRecruiterEvaluations();
                    } else {
                        alert(data.message);
                    }
                });
        });
    }

    window.renderRecruiterEvaluations = function () {
        const container = document.getElementById('recruiter-evals-list');
        if (!container) return;
        
        fetch('/api/recruiter-evaluations')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    container.innerHTML = '';
                    if (data.evaluations.length > 0) {
                        data.evaluations.forEach(ev => {
                            let stars = '';
                            for (let i = 1; i <= 5; i++) {
                                if (i <= ev.rating) {
                                    stars += '<i class="fa-solid fa-star text-warning me-0.5"></i>';
                                } else {
                                    stars += '<i class="fa-regular fa-star text-muted me-0.5"></i>';
                                }
                            }
                            container.innerHTML += `
                                <div class="dashboard-list-item flex-column align-items-start gap-1">
                                    <div class="d-flex justify-content-between align-items-center w-100 mb-1">
                                        <h5 class="fs-8 text-white fw-bold mb-0">${ev.company}</h5>
                                        <div>${stars}</div>
                                    </div>
                                    <p class="text-secondary mb-1 fs-9">Evaluator: <strong class="text-white">${ev.evaluator}</strong></p>
                                    <p class="text-muted mb-0 fs-9">${ev.comments || 'No comment details logged.'}</p>
                                </div>
                            `;
                        });
                    } else {
                        container.innerHTML = '<p class="text-muted fs-8">No evaluations logged yet.</p>';
                    }
                }
            });
    };

    // -------------------------------------------------------------
    // Profile, Skills, Certs, Projects AJAX CRUD
    // -------------------------------------------------------------
    const profileForm = document.getElementById('profile-cgpa-form');
    if (profileForm) {
        profileForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            fetch('/api/update-profile', { method: 'POST', body: formData })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error updating profile:', error);
                alert('An error occurred. Please try again.');
            });
        });
    }

    const skillForm = document.getElementById('add-skill-form');
    if (skillForm) {
        skillForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            fetch('/api/add-skill', { method: 'POST', body: formData })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error adding skill:', error);
            });
        });
    }

    window.deleteSkill = function (skillId) {
        if (!confirm('Are you sure you want to remove this skill?')) return;
        const formData = new FormData();
        formData.append('skill_id', skillId);
        fetch('/api/delete-skill', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert(data.message);
            }
        });
    };

    const certForm = document.getElementById('add-cert-form');
    if (certForm) {
        certForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            fetch('/api/add-certification', { method: 'POST', body: formData })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert(data.message);
                }
            });
        });
    }

    window.deleteCertification = function (certId) {
        if (!confirm('Are you sure you want to remove this certification?')) return;
        const formData = new FormData();
        formData.append('cert_id', certId);
        fetch('/api/delete-certification', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert(data.message);
            }
        });
    };

    const projectForm = document.getElementById('add-project-form');
    if (projectForm) {
        projectForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            fetch('/api/add-project', { method: 'POST', body: formData })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert(data.message);
                }
            });
        });
    }

    window.deleteProject = function (projectId) {
        if (!confirm('Are you sure you want to remove this project?')) return;
        const formData = new FormData();
        formData.append('project_id', projectId);
        fetch('/api/delete-project', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert(data.message);
            }
        });
    };

    // -------------------------------------------------------------
    // Dream Company Filter, Search and Render Deck Grid
    // -------------------------------------------------------------
    let roadmapRadarChartInstance = null;
    let roadmapBarChartInstance = null;
    let placementChartInstance = null;

    window.fetchAndRenderCompanies = function () {
        const branchSelect = document.getElementById('roadmap-branch-select');
        const citySelect = document.getElementById('roadmap-city-select');
        const typeSelect = document.getElementById('company-type-select');
        
        const branch = branchSelect ? branchSelect.value : 'CSE';
        const city = citySelect ? citySelect.value : 'Bangalore';
        const type = typeSelect ? typeSelect.value : 'All Types';
        
        const overlay = document.getElementById('companies-loading-overlay');
        if (overlay) overlay.classList.add('active');
        
        const formData = new FormData();
        formData.append('branch', branch);
        formData.append('city', city);
        formData.append('type', type);
        
        fetch('/api/roadmap/companies-by-filter', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (overlay) overlay.classList.remove('active');
            if (data.success) {
                window.filteredCompaniesList = data.companies;
                renderCompaniesView(data.companies);
            }
        })
        .catch(err => {
            if (overlay) overlay.classList.remove('active');
            console.error('Error fetching default companies:', err);
        });
    };

    const cityForm = document.getElementById('roadmap-city-form');
    if (cityForm) {
        cityForm.addEventListener('submit', function (e) {
            e.preventDefault();
            fetchAndRenderCompanies();
        });
    }

    const resetFiltersBtn = document.getElementById('btn-reset-filters');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function () {
            const branchSelect = document.getElementById('roadmap-branch-select');
            const citySelect = document.getElementById('roadmap-city-select');
            const typeSelect = document.getElementById('company-type-select');
            const searchInput = document.getElementById('company-search-input');
            
            if (branchSelect) branchSelect.value = 'CSE';
            if (citySelect) citySelect.value = 'Bangalore';
            if (typeSelect) typeSelect.value = 'All Types';
            if (searchInput) searchInput.value = '';
            
            document.querySelectorAll('.quick-tab-pill').forEach(p => {
                if (p.getAttribute('data-category') === 'All Companies') {
                    p.classList.add('active');
                } else {
                    p.classList.remove('active');
                }
            });
            
            fetchAndRenderCompanies();
        });
    }

    window.resetSearchQuery = function () {
        const searchInput = document.getElementById('company-search-input');
        if (searchInput) {
            searchInput.value = '';
            renderCompaniesTable(window.filteredCompaniesList || [], 1);
        }
    };

    // Quick tab pills categories filter
    document.querySelectorAll('.quick-tab-pill').forEach(pill => {
        pill.addEventListener('click', function () {
            document.querySelectorAll('.quick-tab-pill').forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            
            const category = this.getAttribute('data-category');
            
            // Set type selector value to match tab click and re-trigger fetch
            const typeSelect = document.getElementById('company-type-select');
            if (typeSelect) {
                if (category === 'All (245+)' || category === 'All Companies') {
                    typeSelect.value = 'All Types';
                } else {
                    typeSelect.value = category;
                }
            }
            fetchAndRenderCompanies();
        });
    });

    // Render Cards recommendations & paginated table rows
    window.renderCompaniesView = function (companies) {
        const slider = document.getElementById('companies-cards-slider');
        if (slider) {
            slider.innerHTML = '';
            // Display top 5 highest matching score companies
            const top5 = companies.slice(0, 5);
            if (top5.length > 0) {
                top5.forEach(comp => {
                    let badgeClass = 'badge-product';
                    if (comp.type === 'Service Based') {
                        badgeClass = 'badge-service';
                    } else if (comp.type === 'Startups' || comp.type === 'Startup') {
                        badgeClass = 'badge-startup';
                    } else if (comp.type === 'FinTech') {
                        badgeClass = 'badge-fintech';
                    } else if (comp.type === 'AI Companies') {
                        badgeClass = 'badge-ai';
                    } else if (comp.type === 'Cybersecurity') {
                        badgeClass = 'badge-cyber';
                    } else if (comp.type === 'Government') {
                        badgeClass = 'badge-gov';
                    } else if (comp.type === 'Core Engineering') {
                        badgeClass = 'badge-core';
                    } else if (comp.type === 'MNC') {
                        badgeClass = 'badge-mnc';
                    }
                    
                    const realLogoUrl = window.getRealCompanyLogo(comp.name, comp.logo_url);
                    const logoHtml = `<div class="company-logo-wrapper">${realLogoUrl ? `<img src="${realLogoUrl}" class="company-logo-img" onerror="this.onerror=null; this.outerHTML=window.getCompanyLogoFallback('${comp.name.replace(/'/g, "\\'")}');" alt="${comp.name}">` : window.getCompanyLogoFallback(comp.name)}</div>`;
                    
                    const card = document.createElement('div');
                    card.className = 'company-slider-card';
                    card.onclick = () => selectDashboardCompany(comp.name, comp.city);
                    const rawPkg = comp.package_range || '5-12 LPA';
                    const cleanPkg = rawPkg.toString().toLowerCase().includes('lpa') 
                        ? rawPkg.toString().replace(/lpa/i, '').trim() 
                        : rawPkg.toString().trim();

                    card.innerHTML = `
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <div class="p-2 bg-dark rounded border border-secondary" style="display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; overflow: hidden; padding: 2px !important; border-color: var(--border-color) !important;">
                                ${logoHtml}
                            </div>
                            <span class="badge py-1 px-2.5 fs-9 ${badgeClass}">${comp.type}</span>
                        </div>
                        <div class="mb-3">
                            <h3 class="fs-7 text-white fw-bold mb-1.5 text-truncate" style="font-size: 16px !important;">${comp.name}</h3>
                            <p class="text-secondary mb-1 fs-9"><i class="fa-solid fa-location-dot me-1 text-muted"></i>${comp.city}</p>
                            <p class="fs-8 text-gradient-green font-bold mb-0">₹ ${cleanPkg} LPA</p>
                        </div>
                        
                        <div class="border-top border-secondary pt-2.5 mt-auto" style="border-color: var(--border-color) !important;">
                            <div class="d-flex justify-content-between align-items-center fs-9 mb-1.5 text-secondary">
                                <span>Match Score</span>
                                <span class="text-white font-bold">${comp.match_score}%</span>
                            </div>
                            <div class="progress" style="height: 6px; background: rgba(255,255,255,0.05); border-radius: 4px;">
                                <div class="progress-bar bg-info" role="progressbar" style="width: ${comp.match_score}%;"></div>
                            </div>
                        </div>
                    `;
                    slider.appendChild(card);
                });
            } else {
                slider.innerHTML = '<div class="col-12 text-muted fs-8 text-center py-3">No matching companies found.</div>';
            }
        }
        
        // Render search filter input handler dynamically on results
        const searchInput = document.getElementById('company-search-input');
        if (searchInput) {
            searchInput.oninput = debounce(function () {
                const query = this.value.toLowerCase().trim();
                const filtered = (window.filteredCompaniesList || []).filter(c => c.name.toLowerCase().includes(query));
                renderCompaniesTable(filtered, 1);
            }, 250);
        }
        
        renderCompaniesTable(companies, 1);
    };

    window.renderCompaniesTable = function (companies, page) {
        const tbody = document.getElementById('companies-table-body');
        if (!tbody) return;
        tbody.innerHTML = '';
        
        const pageSize = 10;
        const total = companies.length;
        const pagesCount = Math.ceil(total / pageSize);
        
        const start = total > 0 ? (page - 1) * pageSize + 1 : 0;
        const end = Math.min(total, page * pageSize);
        const label = document.getElementById('table-results-label');
        if (label) label.innerText = `Showing ${start} - ${end} of ${total} companies`;
        
        const counterBtn = document.getElementById('all-companies-counter-btn');
        if (counterBtn) counterBtn.innerText = `All Companies (${total})`;
        
        const paginated = companies.slice((page - 1) * pageSize, page * pageSize);
        
        if (paginated.length > 0) {
            paginated.forEach(comp => {
                const realLogoUrl = window.getRealCompanyLogo(comp.name, comp.logo_url);
                const logoHtml = `<div class="company-logo-wrapper-small me-2">${realLogoUrl ? `<img src="${realLogoUrl}" class="company-logo-img-small" onerror="this.onerror=null; this.outerHTML=window.getCompanyLogoFallback('${comp.name.replace(/'/g, "\\'")}', 'small');" alt="${comp.name}">` : window.getCompanyLogoFallback(comp.name, 'small')}</div>`;
                
                const rawPkg = comp.package_range || '5-12 LPA';
                const cleanPkg = rawPkg.toString().toLowerCase().includes('lpa') 
                    ? rawPkg.toString().replace(/lpa/i, '').trim() 
                    : rawPkg.toString().trim();

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><div class="d-flex align-items-center">${logoHtml}<span class="fw-bold">${comp.name}</span></div></td>
                    <td>${comp.type}</td>
                    <td>${comp.city}</td>
                    <td class="text-gradient-green font-bold">₹ ${cleanPkg} LPA</td>
                    <td>
                        <span class="badge ${comp.match_score >= 80 ? 'bg-success' : 'bg-info'} py-1 px-2.5" style="border-radius: 20px;">
                            ${comp.match_score}% Match
                        </span>
                    </td>
                    <td>
                        <button type="button" class="btn btn-premium btn-xs py-1 px-2 fs-9" onclick="selectDashboardCompany('${comp.name.replace(/'/g, "\\'")}', '${comp.city.replace(/'/g, "\\'")}')">
                            View Roadmap
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6">
                        <div class="empty-state-container border-0 py-3">
                            <div class="empty-state-icon" style="width: 48px; height: 48px; font-size: 1.5rem; margin-bottom: 8px;"><i class="fa-solid fa-magnifying-glass text-muted"></i></div>
                            <h5 class="empty-state-title fs-8 mb-1">No Matching Companies</h5>
                            <p class="empty-state-desc fs-9 mb-2">Try adjusting your keyword query or search terms.</p>
                            <button type="button" class="btn btn-glass btn-xs px-2.5 py-1" onclick="resetSearchQuery()">Clear Search</button>
                        </div>
                    </td>
                </tr>
            `;
        }
        
        // Render pagination controls
        const pagesContainer = document.getElementById('table-pagination-controls');
        if (pagesContainer) {
            pagesContainer.innerHTML = '';
            if (pagesCount > 1) {
                const prev = document.createElement('button');
                prev.className = 'pagination-page-btn';
                prev.innerHTML = '&lt;';
                prev.disabled = (page === 1);
                prev.onclick = () => renderCompaniesTable(companies, page - 1);
                pagesContainer.appendChild(prev);
                
                const maxVisible = 5;
                let startPage = Math.max(1, page - 2);
                let endPage = Math.min(pagesCount, startPage + maxVisible - 1);
                if (endPage - startPage < maxVisible - 1) {
                    startPage = Math.max(1, endPage - maxVisible + 1);
                }
                
                for (let p = startPage; p <= endPage; p++) {
                    const btn = document.createElement('button');
                    btn.className = `pagination-page-btn ${p === page ? 'active' : ''}`;
                    btn.innerText = p;
                    btn.onclick = () => renderCompaniesTable(companies, p);
                    pagesContainer.appendChild(btn);
                }
                
                const next = document.createElement('button');
                next.className = 'pagination-page-btn';
                next.innerHTML = '&gt;';
                next.disabled = (page === pagesCount);
                next.onclick = () => renderCompaniesTable(companies, page + 1);
                pagesContainer.appendChild(next);
            }
        }
    };

    window.selectDashboardCompany = function (company, city) {
        const formData = new FormData();
        formData.append('company', company);
        formData.append('city', city);
        
        fetch('/api/roadmap/set-dream-company', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                loadRoadmapAnalysis();
            } else {
                alert(data.message);
            }
        })
        .catch(err => {
            console.error('Error selecting company:', err);
        });
    };

    // -------------------------------------------------------------
    // Selected Company Roadmap Analytics details injection
    // -------------------------------------------------------------
    window.updateRoadmapProgress = function (companyName) {
        const checkboxes = document.querySelectorAll('.roadmap-week-checkbox');
        const checked = document.querySelectorAll('.roadmap-week-checkbox:checked');
        const total = checkboxes.length;
        const count = checked.length;
        
        let pct = 0;
        if (total > 0) {
            pct = Math.round((count / total) * 100);
        } else {
            pct = 100;
        }
        
        // Update both accordion bars
        const bars = [document.getElementById('roadmap-progress-bar'), document.getElementById('roadmap-view-progress-bar')];
        const texts = [document.getElementById('roadmap-progress-text'), document.getElementById('roadmap-view-progress-text')];
        
        bars.forEach(bar => { if (bar) bar.style.width = `${pct}%`; });
        texts.forEach(text => { if (text) text.innerText = `${pct}% Completed (${count}/${total} Weeks)`; });
        
        // Save state to localStorage
        checkboxes.forEach((cb, idx) => {
            localStorage.setItem(`roadmap-week-check-${companyName}-${idx}`, cb.checked);
        });
    };

    window.loadRoadmapAnalysis = function () {
        fetch('/api/roadmap/analysis')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Display Filled Detail state
                document.getElementById('company-detail-empty-state').style.display = 'none';
                document.getElementById('company-detail-filled-state').style.display = 'block';
                
                // Populate right blueprint panel
                document.getElementById('detail-company-name').innerText = data.company_name;
                document.getElementById('detail-company-type').innerText = data.type;
                document.getElementById('detail-company-location').innerText = data.city;
                document.getElementById('detail-company-cgpa').innerText = `${parseFloat(data.expected_cgpa).toFixed(2)}+`;
                
                const rawPkg = data.package_range || '5-12 LPA';
                const cleanPkg = rawPkg.toString().toLowerCase().includes('lpa') 
                    ? rawPkg.toString().replace(/lpa/i, '').trim() 
                    : rawPkg.toString().trim();
                document.getElementById('detail-company-package').innerText = `₹ ${cleanPkg} LPA`;

                // Dynamic Logo for detail panel
                const logoContainer = document.getElementById('detail-company-logo');
                if (logoContainer) {
                    logoContainer.style.display = 'flex';
                    logoContainer.style.alignItems = 'center';
                    logoContainer.style.justifyContent = 'center';
                    logoContainer.style.width = '44px';
                    logoContainer.style.height = '44px';
                    logoContainer.style.overflow = 'hidden';
                    logoContainer.style.padding = '2px';
                    const realLogoUrl = window.getRealCompanyLogo(data.company_name, data.logo_url);
                    logoContainer.innerHTML = realLogoUrl 
                        ? `<img src="${realLogoUrl}" class="company-logo-img" onerror="this.onerror=null; this.outerHTML=window.getCompanyLogoFallback('${data.company_name.replace(/'/g, "\\'")}');" alt="${data.company_name}">` 
                        : window.getCompanyLogoFallback(data.company_name);
                }
                
                // Add remaining details
                document.getElementById('detail-company-hq').innerText = data.hq || '-';
                document.getElementById('detail-company-blr-office').innerText = data.bangalore_office || 'N/A';
                document.getElementById('detail-company-employees').innerText = data.employee_count || '-';
                document.getElementById('detail-company-industry').innerText = data.industry || '-';
                document.getElementById('detail-company-founded').innerText = data.founded_year || '-';
                document.getElementById('detail-company-description').innerText = data.description || 'No description available.';
                document.getElementById('detail-company-hiring-process').innerText = data.hiring_process || 'N/A';
                
                // Websites and Careers buttons
                const websiteBtn = document.getElementById('detail-company-website-btn');
                if (websiteBtn) {
                    websiteBtn.href = data.website || '#';
                    websiteBtn.style.pointerEvents = data.website ? 'auto' : 'none';
                    websiteBtn.style.opacity = data.website ? '1' : '0.5';
                }
                const careersBtn = document.getElementById('detail-company-careers-btn');
                if (careersBtn) {
                    careersBtn.href = data.careers_page || '#';
                    careersBtn.style.pointerEvents = data.careers_page ? 'auto' : 'none';
                    careersBtn.style.opacity = data.careers_page ? '1' : '0.5';
                }
                
                // Mapped lists
                const techList = document.getElementById('detail-company-tech-list');
                techList.innerHTML = '';
                data.tech_skills.split(',').forEach(s => {
                    if (s.trim()) {
                        techList.innerHTML += `<span class="badge bg-dark border border-secondary text-secondary-custom py-1.5 px-2 fs-9">${s.trim()}</span>`;
                    }
                });

                const certList = document.getElementById('detail-company-certs-list');
                certList.innerHTML = '';
                data.pref_certs.split(',').forEach(c => {
                    if (c.trim()) {
                        certList.innerHTML += `<span class="badge bg-dark border border-secondary text-secondary-custom py-1.5 px-2 fs-9">${c.trim()}</span>`;
                    }
                });

                const projList = document.getElementById('detail-company-projects-list');
                projList.innerHTML = '';
                data.pref_projects.split(',').forEach(p => {
                    if (p.trim()) {
                        projList.innerHTML += `<li>${p.trim()}</li>`;
                    }
                });

                // Detail dial match
                document.getElementById('detail-company-score-val').innerText = `${data.skill_match_pct}%`;
                const dial = document.getElementById('detail-company-score-dial');
                if (dial) {
                    dial.style.background = `conic-gradient(var(--accent-blue) ${data.skill_match_pct}%, rgba(34, 211, 238, 0.1) ${data.skill_match_pct}%)`;
                }
                const matchQuality = document.getElementById('detail-company-match-quality');
                if (matchQuality) {
                    if (data.skill_match_pct >= 90) {
                        matchQuality.innerText = 'Excellent Match';
                        matchQuality.className = 'fs-9 text-gradient-green font-bold d-block';
                    } else if (data.skill_match_pct >= 75) {
                        matchQuality.innerText = 'Good Match';
                        matchQuality.className = 'fs-9 text-info font-bold d-block';
                    } else {
                        matchQuality.innerText = 'Needs Upskilling';
                        matchQuality.className = 'fs-9 text-danger font-bold d-block';
                    }
                }

                // Bind View Roadmap triggers
                document.getElementById('btn-view-roadmap-trigger').onclick = function () {
                    activateDashboardView('view-roadmap-weeks');
                };

                // Bind bookmark button toggle
                document.getElementById('btn-bookmark-company').onclick = function () {
                    toggleBookmarkCompany(data.company_name, data.city, data.type, data.package_range);
                };
                updateBookmarkUI(data.company_name, data.city);

                // Populate the pop-up modal fields as well
                const modal = document.getElementById('company-detail-modal');
                if (modal) {
                    document.getElementById('modal-company-title').innerText = data.company_name;
                    document.getElementById('modal-company-type').innerText = data.type;
                    document.getElementById('modal-company-location').innerText = data.city;
                    document.getElementById('modal-company-cgpa').innerText = `${parseFloat(data.expected_cgpa).toFixed(2)}+`;
                    
                    const rawPkgModal = data.package_range || '5-12 LPA';
                    const cleanPkgModal = rawPkgModal.toString().toLowerCase().includes('lpa') 
                        ? rawPkgModal.toString().replace(/lpa/i, '').trim() 
                        : rawPkgModal.toString().trim();
                    document.getElementById('modal-company-package').innerText = `₹ ${cleanPkgModal} LPA`;

                    // Modal Logo
                    const modalLogo = document.getElementById('modal-company-logo');
                    if (modalLogo) {
                        const realLogoUrl = window.getRealCompanyLogo(data.company_name, data.logo_url);
                        modalLogo.innerHTML = realLogoUrl 
                            ? `<img src="${realLogoUrl}" class="company-logo-img" onerror="this.onerror=null; this.outerHTML=window.getCompanyLogoFallback('${data.company_name.replace(/'/g, "\\'")}');" alt="${data.company_name}">` 
                            : window.getCompanyLogoFallback(data.company_name);
                    }
                    
                    document.getElementById('modal-company-hq').innerText = data.hq || '-';
                    document.getElementById('modal-company-employees').innerText = data.employee_count || '-';
                    document.getElementById('modal-company-industry').innerText = data.industry || '-';
                    document.getElementById('modal-company-founded').innerText = data.founded_year || '-';
                    document.getElementById('modal-company-description').innerText = data.description || 'No description available.';
                    document.getElementById('modal-company-hiring-process').innerText = data.hiring_process || 'N/A';
                    
                    // Websites and Careers buttons
                    const modalWebsiteBtn = document.getElementById('modal-company-website-btn');
                    if (modalWebsiteBtn) {
                        modalWebsiteBtn.href = data.website || '#';
                        modalWebsiteBtn.style.pointerEvents = data.website ? 'auto' : 'none';
                        modalWebsiteBtn.style.opacity = data.website ? '1' : '0.5';
                    }
                    const modalCareersBtn = document.getElementById('modal-company-careers-btn');
                    if (modalCareersBtn) {
                        modalCareersBtn.href = data.careers_page || '#';
                        modalCareersBtn.style.pointerEvents = data.careers_page ? 'auto' : 'none';
                        modalCareersBtn.style.opacity = data.careers_page ? '1' : '0.5';
                    }
                    
                    // Mapped lists in modal
                    const modalTechList = document.getElementById('modal-company-tech-list');
                    modalTechList.innerHTML = '';
                    data.tech_skills.split(',').forEach(s => {
                        if (s.trim()) {
                            modalTechList.innerHTML += `<span class="badge bg-dark border border-secondary text-secondary-custom py-1.5 px-2 fs-9">${s.trim()}</span>`;
                        }
                    });

                    const modalCertList = document.getElementById('modal-company-certs-list');
                    modalCertList.innerHTML = '';
                    data.pref_certs.split(',').forEach(c => {
                        if (c.trim()) {
                            modalCertList.innerHTML += `<span class="badge bg-dark border border-secondary text-secondary-custom py-1.5 px-2 fs-9">${c.trim()}</span>`;
                        }
                    });

                    const modalProjList = document.getElementById('modal-company-projects-list');
                    modalProjList.innerHTML = '';
                    data.pref_projects.split(',').forEach(p => {
                        if (p.trim()) {
                            modalProjList.innerHTML += `<li>${p.trim()}</li>`;
                        }
                    });

                    // Modal match dial
                    document.getElementById('modal-company-score-val').innerText = `${data.skill_match_pct}%`;
                    const modalDial = document.getElementById('modal-company-score-dial');
                    if (modalDial) {
                        modalDial.style.background = `conic-gradient(var(--accent-blue) ${data.skill_match_pct}%, rgba(34, 211, 238, 0.1) ${data.skill_match_pct}%)`;
                    }
                    const modalMatchQuality = document.getElementById('modal-company-match-quality');
                    if (modalMatchQuality) {
                        if (data.skill_match_pct >= 90) {
                            modalMatchQuality.innerText = 'Excellent Match';
                            modalMatchQuality.className = 'fs-9 text-gradient-green font-bold d-block';
                        } else if (data.skill_match_pct >= 75) {
                            modalMatchQuality.innerText = 'Good Match';
                            modalMatchQuality.className = 'fs-9 text-info font-bold d-block';
                        } else {
                            modalMatchQuality.innerText = 'Needs Upskilling';
                            modalMatchQuality.className = 'fs-9 text-danger font-bold d-block';
                        }
                    }

                    // Pre-select current tracker status in modal tracker dropdown
                    const modalTrackerSelect = document.getElementById('modal-tracker-status');
                    if (modalTrackerSelect) {
                        modalTrackerSelect.value = 'none'; // reset first
                        fetch('/api/tracked-applications')
                        .then(res => res.json())
                        .then(appData => {
                            if (appData.success) {
                                const activeApp = appData.applications.find(a => a.name.toLowerCase() === data.company_name.toLowerCase() && a.city.toLowerCase() === data.city.toLowerCase());
                                if (activeApp) {
                                    modalTrackerSelect.value = activeApp.status;
                                }
                            }
                        });
                        
                        modalTrackerSelect.onchange = function() {
                            const status = this.value;
                            if (status === 'none') return;
                            const formData = new FormData();
                            formData.append('company_name', data.company_name);
                            formData.append('city', data.city);
                            formData.append('type', data.type);
                            formData.append('status', status);
                            fetch('/api/tracked-applications/save', { method: 'POST', body: formData })
                            .then(res => res.json())
                            .then(trackerResult => {
                                if (trackerResult.success) {
                                    renderTrackerBoard();
                                    alert(`Application status updated to: ${status}`);
                                }
                            });
                        };
                    }

                    // Bind actions for modal footer buttons
                    document.getElementById('modal-view-roadmap-btn').onclick = function () {
                        modal.close();
                        activateDashboardView('view-roadmap-weeks');
                    };

                    const modalBookmarkBtn = document.getElementById('modal-bookmark-btn');
                    if (modalBookmarkBtn) {
                        modalBookmarkBtn.onclick = function() {
                            toggleBookmarkCompany(data.company_name, data.city, data.type, data.package_range);
                            setTimeout(() => {
                                fetch('/api/saved-companies')
                                .then(res => res.json())
                                .then(savedData => {
                                    const isSaved = savedData.companies.some(c => c.name.toLowerCase() === data.company_name.toLowerCase() && c.city.toLowerCase() === data.city.toLowerCase());
                                    const bookmarkIcon = modalBookmarkBtn.querySelector('i');
                                    if (bookmarkIcon) {
                                        bookmarkIcon.className = isSaved ? 'fa-solid fa-bookmark me-1.5' : 'fa-regular fa-bookmark me-1.5';
                                    }
                                });
                            }, 300);
                        };
                        
                        fetch('/api/saved-companies')
                        .then(res => res.json())
                        .then(savedData => {
                            const isSaved = savedData.companies.some(c => c.name.toLowerCase() === data.company_name.toLowerCase() && c.city.toLowerCase() === data.city.toLowerCase());
                            const bookmarkIcon = modalBookmarkBtn.querySelector('i');
                            if (bookmarkIcon) {
                                bookmarkIcon.className = isSaved ? 'fa-solid fa-bookmark me-1.5' : 'fa-regular fa-bookmark me-1.5';
                            }
                        });
                    }

                    modal.showModal();
                }

                // Populate dashboard view elements
                document.getElementById('dashboard-target-name').innerText = data.company_name;
                document.getElementById('dashboard-target-city').innerText = data.city;
                document.getElementById('dashboard-package-range').innerText = `₹ ${cleanPkg} LPA`;
                document.getElementById('dashboard-skills-count').innerText = data.matched_tech.length + data.matched_soft.length;
                document.getElementById('dashboard-missing-count').innerText = data.missing_tech.length + data.missing_soft.length;
                
                const readinessTexts = [document.getElementById('sidebar-readiness-val'), document.getElementById('dashboard-readiness-val'), document.getElementById('readiness-detail-score')];
                readinessTexts.forEach(el => { if (el) el.innerText = `${data.readiness_score}%`; });
                
                // Mapped dashboard dials
                const sideGauge = document.querySelector('.sidebar-widget .score-gauge-blue');
                if (sideGauge) {
                    sideGauge.style.background = `conic-gradient(var(--accent-blue) ${data.readiness_score}%, rgba(34, 211, 238, 0.1) ${data.readiness_score}%)`;
                }

                // Update readiness dashboard panels
                document.getElementById('readiness-detail-match').innerText = `${data.skill_match_pct}%`;
                document.getElementById('readiness-detail-prob').innerText = `${data.placement_probability}%`;
                document.getElementById('readiness-detail-missing').innerText = data.missing_tech.length + data.missing_soft.length;

                // Priority actions checklist
                const priorityList = document.getElementById('dashboard-priority-list');
                if (priorityList) {
                    priorityList.innerHTML = '';
                    if (data.missing_tech.length > 0) {
                        data.missing_tech.forEach(s => {
                            priorityList.innerHTML += `<div class="mb-1.5">&bull; Complete training gap: <strong class="text-white">${s}</strong></div>`;
                        });
                    } else {
                        priorityList.innerHTML = '<div class="text-success fw-bold">✓ Ready! All technical requirements completed.</div>';
                    }
                }

                // Skills Gap Matrix
                const matrixSkills = [document.getElementById('analysis-skills-breakdown'), document.getElementById('gap-skills-breakdown')];
                matrixSkills.forEach(matrix => {
                    if (matrix) {
                        matrix.innerHTML = '';
                        data.matched_tech.forEach(s => {
                            matrix.innerHTML += `<div class="d-flex justify-content-between align-items-center mb-1.5 text-success">
                                <span>✅ ${s} (Technical)</span>
                                <span class="fw-bold">✓</span>
                            </div>`;
                        });
                        data.missing_tech.forEach(s => {
                            matrix.innerHTML += `<div class="d-flex justify-content-between align-items-center mb-2 text-danger">
                                <span>❌ ${s}</span>
                                <button type="button" class="btn btn-premium btn-xs py-0.5 px-2 fs-9 ms-2" style="font-size: 0.7rem;" onclick="addMissingSkill('${s.replace(/'/g, "\\'")}')">
                                    <i class="fa-solid fa-plus me-1"></i>Add
                                </button>
                            </div>`;
                        });
                        data.matched_soft.forEach(s => {
                            matrix.innerHTML += `<div class="d-flex justify-content-between align-items-center mb-1.5 text-success">
                                <span>✅ ${s} (Soft Skill)</span>
                                <span class="fw-bold">✓</span>
                            </div>`;
                        });
                        data.missing_soft.forEach(s => {
                            matrix.innerHTML += `<div class="d-flex justify-content-between align-items-center mb-2 text-danger">
                                <span>❌ ${s} (Soft)</span>
                                <button type="button" class="btn btn-premium btn-xs py-0.5 px-2 fs-9 ms-2" style="font-size: 0.7rem;" onclick="addMissingSkill('${s.replace(/'/g, "\\'")}')">
                                    <i class="fa-solid fa-plus me-1"></i>Add
                                </button>
                            </div>`;
                        });
                    }
                });

                // Credentials checklists
                const checklists = [document.getElementById('analysis-credentials-breakdown'), document.getElementById('gap-credentials-breakdown')];
                checklists.forEach(ch => {
                    if (ch) {
                        ch.innerHTML = '';
                        data.matched_certs.forEach(c => {
                            ch.innerHTML += `<div class="d-flex justify-content-between align-items-center mb-1.5 text-success">
                                <span>✅ ${c} (Cert)</span>
                                <span class="fw-bold">✓</span>
                            </div>`;
                        });
                        data.missing_certs.forEach(c => {
                            ch.innerHTML += `<div class="d-flex justify-content-between align-items-center mb-1.5 text-danger">
                                <span>❌ ${c} (Cert)</span>
                                <span class="fw-bold">✗</span>
                            </div>`;
                        });
                        data.matched_projects.forEach(p => {
                            ch.innerHTML += `<div class="d-flex justify-content-between align-items-center mb-1.5 text-success">
                                <span>✅ ${p} (Project)</span>
                                <span class="fw-bold">✓</span>
                            </div>`;
                        });
                        data.missing_projects.forEach(p => {
                            ch.innerHTML += `<div class="d-flex justify-content-between align-items-center mb-1.5 text-danger">
                                <span>❌ ${p} (Project)</span>
                                <span class="fw-bold">✗</span>
                            </div>`;
                        });
                    }
                });

                // Accordions weeks
                const roadmaps = [document.getElementById('roadmap-weeks-container'), document.getElementById('roadmap-view-weeks-container')];
                roadmaps.forEach(roadmapContainer => {
                    if (roadmapContainer) {
                        roadmapContainer.innerHTML = '';
                        if (data.roadmap.length > 0) {
                            data.roadmap.forEach((item, idx) => {
                                const isChecked = localStorage.getItem(`roadmap-week-check-${data.company_name}-${idx}`) === 'true';
                                const card = document.createElement('div');
                                card.className = 'roadmap-week-card mb-3 p-3';
                                card.innerHTML = `
                                    <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
                                        <div>
                                            <span class="badge bg-primary-subtle text-primary border border-primary-subtle py-1 px-2 fs-9 mb-1.5" style="border-radius: 4px; font-weight: 600;">
                                                ${item.week.toUpperCase()}
                                            </span>
                                            <h5 class="fs-7 text-white fw-bold mb-1">Master ${item.skill}</h5>
                                            <p class="text-muted fs-8 mb-3">Focus on building fundamentals and solving practice problems in ${item.skill}.</p>
                                        </div>
                                        <div class="form-check fs-8 ms-auto">
                                            <input class="form-check-input roadmap-week-checkbox" type="checkbox" id="check-${idx}" ${isChecked ? 'checked' : ''} onchange="updateRoadmapProgress('${data.company_name.replace(/'/g, "\\'")}')">
                                            <label class="form-check-label text-secondary-custom font-semibold" for="check-${idx}">
                                                Mark Done
                                            </label>
                                        </div>
                                    </div>
                                    <div class="d-flex flex-wrap gap-2 mt-2">
                                        <a href="${item.youtube_url}" target="_blank" class="btn btn-glass btn-xs px-2.5 py-1.5 fs-8 text-gradient">
                                            <i class="fa-brands fa-youtube me-1 text-danger"></i>Video Course
                                        </a>
                                        <a href="${item.cert_url}" target="_blank" class="btn btn-glass btn-xs px-2.5 py-1.5 fs-8 text-gradient-green">
                                            <i class="fa-solid fa-graduation-cap me-1 text-success"></i>Free Certificate
                                        </a>
                                        <a href="${item.practice_url}" target="_blank" class="btn btn-glass btn-xs px-2.5 py-1.5 fs-8 text-gradient-purple">
                                            <i class="fa-solid fa-laptop-code me-1 text-info"></i>Practice Platform
                                        </a>
                                    </div>
                                `;
                                roadmapContainer.appendChild(card);
                            });
                        } else {
                            roadmapContainer.innerHTML = `
                                <div class="text-center py-4 bg-dark-subtle border border-secondary-subtle rounded-3">
                                   <i class="fa-solid fa-champagne-glasses text-gradient fs-4 mb-2"></i>
                                   <p class="fs-7 text-white fw-bold mb-1">Congratulations!</p>
                                   <p class="text-muted fs-8 mb-0">You match all requirements for ${data.company_name}!</p>
                                </div>
                            `;
                        }
                    }
                });
                updateRoadmapProgress(data.company_name);
                renderRoadmapCharts(data);
            }
        });
    };

    function renderRoadmapCharts(data) {
        if (typeof Chart === 'undefined') return;
        
        const radarCtx = document.getElementById('roadmapRadarChart') || document.getElementById('detail-roadmapRadarChart');
        if (radarCtx) {
            if (roadmapRadarChartInstance) {
                roadmapRadarChartInstance.destroy();
            }
            
            const labels = ['Tech Match', 'Soft Match', 'GPA Index', 'Certifications', 'Projects Qty'];
            
            const targetTech = data.matched_tech.length + data.missing_tech.length;
            const targetSoft = data.matched_soft.length + data.missing_soft.length;
            const targetCerts = data.matched_certs.length + data.missing_certs.length;
            const targetProj = data.matched_projects.length + data.missing_projects.length;
            
            const normalizedUserValues = [
                targetTech > 0 ? (data.matched_tech.length / targetTech) * 100 : 100,
                targetSoft > 0 ? (data.matched_soft.length / targetSoft) * 100 : 100,
                data.expected_cgpa > 0 ? Math.min(100, (8.5 / data.expected_cgpa) * 100) : 100,
                targetCerts > 0 ? (data.matched_certs.length / targetCerts) * 100 : 100,
                targetProj > 0 ? (data.matched_projects.length / targetProj) * 100 : 100
            ];
            const normalizedTargetValues = [100, 100, 100, 100, 100];
            
            roadmapRadarChartInstance = new Chart(radarCtx, {
                type: 'radar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Your Fit',
                            data: normalizedUserValues,
                            backgroundColor: 'rgba(59, 130, 246, 0.25)',
                            borderColor: '#3b82f6',
                            borderWidth: 2.5,
                            pointBackgroundColor: '#3b82f6',
                            pointHoverBackgroundColor: '#ffffff',
                            pointHoverBorderColor: '#3b82f6'
                        },
                        {
                            label: 'Requirement',
                            data: normalizedTargetValues,
                            backgroundColor: 'rgba(16, 185, 129, 0.03)',
                            borderColor: '#10b981',
                            borderWidth: 1.5,
                            borderDash: [4, 4],
                            pointBackgroundColor: '#10b981'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom',
                            labels: {
                                color: '#cbd5e1',
                                boxWidth: 10,
                                padding: 15,
                                font: { family: "'Outfit', 'Inter', sans-serif", size: 10, weight: '500' }
                            }
                        }
                    },
                    scales: {
                        r: {
                            angleLines: { color: 'rgba(148, 163, 184, 0.15)' },
                            grid: { color: 'rgba(148, 163, 184, 0.12)' },
                            pointLabels: {
                                color: '#cbd5e1',
                                font: { family: "'Outfit', 'Inter', sans-serif", size: 10, weight: '600' }
                            },
                            ticks: { display: false },
                            min: 0,
                            max: 100
                        }
                    }
                }
            });
        }
        
        const barCtx = document.getElementById('roadmapBarChart') || document.getElementById('detail-roadmapBarChart');
        if (barCtx) {
            if (roadmapBarChartInstance) {
                roadmapBarChartInstance.destroy();
            }
            
            const missingTechCount = data.missing_tech.length;
            const missingSoftCount = data.missing_soft.length;
            const missingCertsCount = data.missing_certs.length;
            const missingProjectsCount = data.missing_projects.length;
            
            roadmapBarChartInstance = new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: ['Tech Deficit', 'Soft Deficit', 'Certs Deficit', 'Proj Deficit'],
                    datasets: [{
                        label: 'Missing Count',
                        data: [missingTechCount, missingSoftCount, missingCertsCount, missingProjectsCount],
                        backgroundColor: 'rgba(239, 68, 68, 0.55)',
                        borderColor: '#ef4444',
                        borderWidth: 1.5,
                        borderRadius: 6,
                        barPercentage: 0.55
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: '#94a3b8', font: { family: "'Outfit', 'Inter', sans-serif", size: 10, weight: '500' } }
                        },
                        y: {
                            grid: { color: 'rgba(148, 163, 184, 0.1)' },
                            ticks: { color: '#94a3b8', font: { family: "'Outfit', 'Inter', sans-serif", size: 10 }, stepSize: 1 },
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }

    window.addMissingSkill = function (skillName) {
        const formData = new FormData();
        formData.append('skill_name', skillName);
        formData.append('proficiency', 'Intermediate');

        fetch('/api/add-skill', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert(data.message);
            }
        })
        .catch(err => {
            console.error('Error adding missing skill:', err);
            alert('Could not add skill to profile.');
        });
    };

    // -------------------------------------------------------------
    // Placement Predictor engine
    // -------------------------------------------------------------
    const predictBtn = document.getElementById('btn-predict-placement');
    if (predictBtn) {
        predictBtn.addEventListener('click', function () {
            const loader = document.getElementById('predictor-loader');
            const results = document.getElementById('predictor-results');
            
            if (loader) loader.style.display = 'block';
            if (results) results.style.display = 'none';

            fetch('/api/predict-placement')
            .then(res => res.json())
            .then(data => {
                if (loader) loader.style.display = 'none';
                if (data.success) {
                    if (results) results.style.display = 'block';
                    
                    const scoreGauge = document.getElementById('predict-score-gauge');
                    const scoreVal = document.getElementById('predict-score-val');
                    if (scoreGauge && scoreVal) {
                        scoreVal.innerText = `${data.placement_probability}%`;
                        scoreGauge.style.background = `conic-gradient(var(--accent-blue) ${data.placement_probability}%, rgba(34, 211, 238, 0.1) ${data.placement_probability}%)`;
                    }
                    
                    // Recommendations List
                    const listContainer = document.getElementById('predictor-recommendations-list');
                    if (listContainer) {
                        listContainer.innerHTML = '';
                        data.recommendations.forEach(rec => {
                            listContainer.innerHTML += `<div class="mb-1.5">&bull; ${rec}</div>`;
                        });
                    }
                    
                    // Draw horizontal bar impact weights chart
                    const chartCtx = document.getElementById('placement-breakdown-chart');
                    if (chartCtx) {
                        if (placementChartInstance) {
                            placementChartInstance.destroy();
                        }
                        
                        placementChartInstance = new Chart(chartCtx, {
                            type: 'bar',
                            data: {
                                labels: ['CGPA Weight', 'Skills Factor', 'Projects Volume', 'Certifications'],
                                datasets: [{
                                    data: [data.details.cgpa_impact, data.details.skills_impact, data.details.projects_impact, data.details.certs_impact],
                                    backgroundColor: ['#22d3ee', '#10b981', '#a855f7', '#ec4899'],
                                    borderRadius: 5,
                                    barPercentage: 0.55
                                }]
                            },
                            options: {
                                indexAxis: 'y',
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } },
                                scales: {
                                    x: {
                                        ticks: { color: '#cbd5e1', font: { family: "'Outfit', 'Inter', sans-serif", size: 10 } },
                                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                                    },
                                    y: {
                                        ticks: { color: '#cbd5e1', font: { family: "'Outfit', 'Inter', sans-serif", size: 10, weight: '500' } },
                                        grid: { display: false }
                                    }
                                }
                            }
                        });
                    }
                } else {
                    alert('Could not run prediction.');
                }
            })
            .catch(err => {
                if (loader) loader.style.display = 'none';
                console.error(err);
            });
        });
    }

    // -------------------------------------------------------------
    // AI Resume Analyzer
    // -------------------------------------------------------------
    const dropZone = document.getElementById('resume-drop-zone');
    const fileInput = document.getElementById('resume-file-input');

    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                uploadResumePDF(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                uploadResumePDF(e.target.files[0]);
            }
        });
    }

    function uploadResumePDF(file) {
        const loader = document.getElementById('analyzer-loader');
        const statusText = document.getElementById('loader-status-text');
        const results = document.getElementById('analyzer-results');

        if (loader) loader.style.display = 'block';
        if (statusText) statusText.innerText = 'Extracting PDF strings...';
        if (results) results.style.display = 'none';

        const formData = new FormData();
        formData.append('resume', file);

        fetch('/api/upload-resume', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (statusText) statusText.innerText = 'Auditing keywords checklist...';
                
                setTimeout(() => {
                    if (loader) loader.style.display = 'none';
                    if (results) results.style.display = 'block';

                    const scoreGauge = document.getElementById('resume-score-gauge');
                    const scoreVal = document.getElementById('resume-score-val');
                    if (scoreGauge && scoreVal) {
                        scoreVal.innerText = `${data.ats_score}%`;
                        scoreGauge.style.background = `conic-gradient(var(--accent-blue) ${data.ats_score}%, rgba(34, 211, 238, 0.1) ${data.ats_score}%)`;
                    }
                    
                    // Update dashboard metrics
                    const atsGrade = document.getElementById('dashboard-ats-grade');
                    if (atsGrade) atsGrade.innerText = `${data.ats_score}%`;

                    // Populate Detected
                    const detected = document.getElementById('detected-skills-container');
                    detected.innerHTML = '';
                    data.detected_skills.forEach(s => {
                        detected.innerHTML += `<span class="badge bg-dark border border-secondary text-secondary-custom py-1 px-2 fs-9">${s}</span>`;
                    });

                    // Populate Missing
                    const missing = document.getElementById('missing-skills-container');
                    missing.innerHTML = '';
                    data.missing_skills.forEach(s => {
                        missing.innerHTML += `<span class="badge bg-dark border border-secondary text-danger py-1 px-2 fs-9">${s}</span>`;
                    });

                    // Populate Feedback
                    const feedback = document.getElementById('feedback-list-container');
                    feedback.innerHTML = '';
                    data.suggestions.forEach(s => {
                        feedback.innerHTML += `<div class="mb-1 text-secondary-custom">&bull; ${s}</div>`;
                    });

                }, 800);
            } else {
                if (loader) loader.style.display = 'none';
                alert(data.message || 'Error processing resume.');
            }
        })
        .catch(err => {
            if (loader) loader.style.display = 'none';
            console.error('Error uploading resume:', err);
            alert('An error occurred during resume uploading.');
        });
    }

    // -------------------------------------------------------------
    // Page load initialization (Only execute if on active Dashboard Page)
    // -------------------------------------------------------------
    if (document.body.classList.contains('dashboard-page-active')) {
        // Load default explorer grids
        fetchAndRenderCompanies();
        
        // Set view to default Dashboard
        activateDashboardView('view-dashboard');
        
        // Render bookmark grid and Kanban application tracker board
        renderSavedCompaniesList();
        renderTrackerBoard();
        renderCalendarEvents();
        renderCodingProgress();
        renderRecruiterEvaluations();

        // Check if the student already has a dream company selected to pre-load analysis
        const emptyDetail = document.getElementById('company-detail-empty-state');
        if (emptyDetail) {
            // If there's a pre-selected company (rendered in page from Flask variables)
            const activeCompanyTitle = document.getElementById('analysis-company-title');
            if (activeCompanyTitle && activeCompanyTitle.innerText.trim() !== '') {
                loadRoadmapAnalysis();
            }
        }
    }

    // Fallback for light dismiss on <dialog>
    const compModal = document.getElementById('company-detail-modal');
    if (compModal && !('closedBy' in HTMLDialogElement.prototype)) {
        compModal.addEventListener('click', function(event) {
            if (event.target !== compModal) return;
            const rect = compModal.getBoundingClientRect();
            const isDialogContent = (
                rect.top <= event.clientY &&
                event.clientY <= rect.top + rect.height &&
                rect.left <= event.clientX &&
                event.clientX <= rect.left + rect.width
            );
            if (!isDialogContent) {
                compModal.close();
            }
        });
    }

    // -------------------------------------------------------------
    // Portfolio Contact Form AJAX Submission
    // -------------------------------------------------------------
    const contactForm = document.getElementById('portfolio-contact-form');
    const contactFormWrapper = document.getElementById('contact-form-wrapper');
    const contactSuccessState = document.getElementById('contact-success-state');
    const btnContactSubmit = document.getElementById('btn-contact-submit');
    const contactSubmitSpinner = document.getElementById('contact-submit-spinner');
    const btnContactReset = document.getElementById('btn-contact-reset');

    if (contactForm) {
        contactForm.addEventListener('submit', function (e) {
            e.preventDefault();
            
            // Show loading state
            btnContactSubmit.disabled = true;
            if (contactSubmitSpinner) contactSubmitSpinner.style.display = 'inline-block';
            
            const formData = new FormData(this);
            
            fetch('/api/contact', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Reset loading state
                btnContactSubmit.disabled = false;
                if (contactSubmitSpinner) contactSubmitSpinner.style.display = 'none';
                
                if (data.success) {
                    // Update success message text if customized by backend
                    const successMsgEl = document.getElementById('contact-success-message');
                    if (successMsgEl && data.message) {
                        successMsgEl.innerText = data.message;
                    }
                    
                    // Trigger fade-out on form and fade-in on success
                    if (contactFormWrapper) {
                        contactFormWrapper.style.display = 'none';
                    }
                    if (contactSuccessState) {
                        contactSuccessState.style.display = 'block';
                        contactSuccessState.classList.add('fade-in-up');
                    }
                    
                    // Reset the form fields
                    contactForm.reset();
                } else {
                    alert(data.message || 'An error occurred while sending your message. Please check the fields and try again.');
                }
            })
            .catch(error => {
                console.error('Error submitting contact form:', error);
                btnContactSubmit.disabled = false;
                if (contactSubmitSpinner) contactSubmitSpinner.style.display = 'none';
                alert('A network error occurred. Please check your connection and try again.');
            });
        });
    }

    if (btnContactReset) {
        btnContactReset.addEventListener('click', function () {
            if (contactSuccessState) {
                contactSuccessState.style.display = 'none';
                contactSuccessState.classList.remove('fade-in-up');
            }
            if (contactFormWrapper) {
                contactFormWrapper.style.display = 'block';
                contactFormWrapper.classList.add('fade-in-up');
            }
        });
    }

    let aiChartInstance = null;

    window.reloadAICareerIntelligence = function() {
        loadAICareerIntelligence();
    };

    window.loadAICareerIntelligence = function() {
        const loader = document.getElementById('ai-intelligence-loader');
        const content = document.getElementById('ai-intelligence-console-content');
        
        if (loader) loader.style.display = 'block';
        if (content) content.style.display = 'none';

        fetch('/api/ai-career-intelligence/data')
            .then(res => res.json())
            .then(data => {
                if (loader) loader.style.display = 'none';
                if (content) content.style.display = 'block';

                if (data.success) {
                    // Update mini stats
                    document.getElementById('ai-stat-ats').innerText = data.ats_score + '%';
                    document.getElementById('ai-stat-placement').innerText = data.placement_prediction.score + '%';
                    document.getElementById('ai-stat-skills').innerText = data.skills.length;
                    document.getElementById('ai-stat-cgpa').innerText = data.cgpa.toFixed(2);

                    // ATS Score Gauge
                    document.getElementById('ai-resume-ats-val').innerText = data.ats_score + '%';
                    document.getElementById('ai-resume-filename').innerText = data.filename || 'No file analyzed yet';

                    // Progress Bars
                    document.getElementById('ai-resume-format-percent').innerText = data.resume_strength.formatting + '%';
                    document.getElementById('ai-resume-format-bar').style.width = data.resume_strength.formatting + '%';
                    
                    document.getElementById('ai-resume-density-percent').innerText = data.resume_strength.keyword_density + '%';
                    document.getElementById('ai-resume-density-bar').style.width = data.resume_strength.keyword_density + '%';

                    document.getElementById('ai-resume-section-percent').innerText = data.resume_strength.section_completion + '%';
                    document.getElementById('ai-resume-section-bar').style.width = data.resume_strength.section_completion + '%';

                    // Suggestions Bullet Points
                    const suggsContainer = document.getElementById('ai-resume-suggestions-list');
                    suggsContainer.innerHTML = '';
                    data.resume_strength.suggestions.forEach(sugg => {
                        suggsContainer.innerHTML += `<li><i class="fa-solid fa-chevron-right text-warning me-1.5 fs-10"></i>${sugg}</li>`;
                    });

                    // Suitable Company Placements List
                    const companiesList = document.getElementById('ai-matching-companies-list');
                    companiesList.innerHTML = '';
                    
                    if (data.matching_companies.length === 0) {
                        companiesList.innerHTML = `
                            <div class="col-12 text-center text-secondary-custom py-4">
                                No companies matching your profile yet. Add skills/projects to start matching!
                            </div>`;
                    } else {
                        data.matching_companies.forEach(comp => {
                            const badgeClass = comp.eligible ? 'bg-success-subtle text-success border border-success-subtle' : 'bg-danger-subtle text-danger border border-danger-subtle';
                            const badgeText = comp.eligible ? 'Eligible' : 'Needs CGPA Upgrade';
                            const matchBadgeColor = comp.match_percent >= 80 ? 'text-success' : (comp.match_percent >= 60 ? 'text-info' : 'text-warning');
                            
                            const matchedSkillsBadges = comp.skills_compare.matched.map(s => `<span class="badge bg-success-subtle text-success fs-10 px-2 py-1"><i class="fa-solid fa-check me-1"></i>${s}</span>`).join(' ') || '<span class="text-secondary-custom fs-9">None</span>';
                            const missingSkillsBadges = comp.skills_compare.missing.map(s => `<span class="badge bg-danger-subtle text-danger fs-10 px-2 py-1"><i class="fa-solid fa-xmark me-1"></i>${s}</span>`).join(' ') || '<span class="text-success-custom fs-9">All Matched!</span>';

                            companiesList.innerHTML += `
                                <div class="col-md-6">
                                    <div class="glass-card p-3" style="border: 1px solid rgba(255,255,255,0.06); border-radius: 15px;">
                                        <div class="d-flex justify-content-between align-items-start mb-2 flex-wrap gap-2">
                                            <div class="d-flex gap-2.5">
                                                <div class="company-logo-wrapper" style="width: 38px; height: 38px; padding: 2px;">
                                                    <img src="/static/images/companies/${comp.logo}" class="company-logo-img" alt="${comp.name}">
                                                </div>
                                                <div>
                                                    <h5 class="text-white fs-8 mb-0.5 fw-bold">${comp.name}</h5>
                                                    <span class="fs-9 text-muted d-block">${comp.category} | ${comp.package}</span>
                                                </div>
                                            </div>
                                            <div class="text-end">
                                                <span class="fs-7 fw-black d-block ${matchBadgeColor}">${comp.match_percent}% Match</span>
                                                <span class="badge ${badgeClass} fs-9 py-0.5 px-2 mt-1">${badgeText}</span>
                                            </div>
                                        </div>
                                        
                                        <div class="mt-2.5 border-top border-secondary pt-2.5">
                                            <div class="row g-2">
                                                <div class="col-6">
                                                    <span class="fs-9 text-secondary-custom fw-bold d-block mb-1">Matched Skills:</span>
                                                    <div class="d-flex flex-wrap gap-1">${matchedSkillsBadges}</div>
                                                </div>
                                                <div class="col-6">
                                                    <span class="fs-9 text-secondary-custom fw-bold d-block mb-1">Missing Skills:</span>
                                                    <div class="d-flex flex-wrap gap-1">${missingSkillsBadges}</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                    }

                    // Placement Prediction Gauge & Chart
                    document.getElementById('ai-placement-prob-val').innerText = data.placement_prediction.score + '%';

                    const chartCtx = document.getElementById('ai-readiness-breakdown-chart');
                    if (chartCtx) {
                        if (aiChartInstance) {
                            aiChartInstance.destroy();
                        }
                        aiChartInstance = new Chart(chartCtx, {
                            type: 'bar',
                            data: {
                                labels: ['CGPA Weight', 'Skills Factor', 'Projects Volume', 'Certifications'],
                                datasets: [{
                                    data: [
                                        data.placement_prediction.breakdown.cgpa,
                                        data.placement_prediction.breakdown.skills,
                                        data.placement_prediction.breakdown.projects,
                                        data.placement_prediction.breakdown.certs
                                    ],
                                    backgroundColor: ['#22d3ee', '#10b981', '#a855f7', '#ec4899'],
                                    borderRadius: 5,
                                    barPercentage: 0.55
                                }]
                            },
                            options: {
                                indexAxis: 'y',
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } },
                                scales: {
                                    x: {
                                        ticks: { color: '#cbd5e1', font: { family: "'Outfit', 'Inter', sans-serif", size: 10 } },
                                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                                    },
                                    y: {
                                        ticks: { color: '#cbd5e1', font: { family: "'Outfit', 'Inter', sans-serif", size: 10, weight: '500' } },
                                        grid: { display: false }
                                    }
                                }
                            }
                        });
                    }

                    // Career Roadmap Weeks
                    const roadmapContainer = document.getElementById('ai-roadmap-weeks-list');
                    roadmapContainer.innerHTML = '';
                    data.roadmap.weeks.forEach(w => {
                        roadmapContainer.innerHTML += `
                            <div class="col-md-6">
                                <div class="glass-card p-3.5 h-100" style="border: 1px solid rgba(255,255,255,0.06); border-radius: 15px;">
                                    <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-1">
                                        <span class="badge bg-primary-subtle text-primary py-1 px-2.5 fs-9 fw-bold">WEEK ${w.week}</span>
                                        <span class="fs-9 text-muted font-bold">Preparation Target</span>
                                    </div>
                                    <h5 class="text-white fs-7 mb-2 fw-black">${w.title}</h5>
                                    <p class="fs-8 text-secondary-custom mb-3">${w.goal}</p>
                                    
                                    <div class="bg-dark-subtle p-2.5 rounded border border-secondary" style="border-radius: 10px !important;">
                                        <div class="mb-1.5"><i class="fa-solid fa-book-open text-info me-1.5 fs-9"></i><strong class="fs-9 text-secondary-custom">Resource:</strong> <span class="fs-9 text-secondary-custom">${w.resources}</span></div>
                                        <div><i class="fa-solid fa-square-check text-success me-1.5 fs-9"></i><strong class="fs-9 text-secondary-custom">Action:</strong> <span class="fs-9 text-secondary-custom">${w.action_item}</span></div>
                                    </div>
                                </div>
                            </div>
                        `;
                    });

                    // AI Recommendations
                    const coursesContainer = document.getElementById('ai-recs-courses-container');
                    coursesContainer.innerHTML = '';
                    data.ai_recommendations.courses.forEach(c => {
                        coursesContainer.innerHTML += `
                            <div class="d-flex align-items-center gap-3 p-2.5 rounded bg-dark border border-secondary" style="border-radius: 12px !important;">
                                <div class="fs-5 text-gradient-cyan"><i class="fa-solid fa-circle-play"></i></div>
                                <div>
                                    <span class="fs-8 text-white fw-bold d-block" style="line-height: 1.25;">${c.title}</span>
                                    <span class="fs-9 text-muted d-block mt-0.5">${c.platform}</span>
                                </div>
                            </div>
                        `;
                    });

                    const certsContainer = document.getElementById('ai-recs-certs-container');
                    certsContainer.innerHTML = '';
                    data.ai_recommendations.certs.forEach(crt => {
                        certsContainer.innerHTML += `
                            <div class="d-flex align-items-center gap-3 p-2.5 rounded bg-dark border border-secondary" style="border-radius: 12px !important;">
                                <div class="fs-5 text-warning"><i class="fa-solid fa-certificate"></i></div>
                                <div>
                                    <span class="fs-8 text-white fw-bold d-block" style="line-height: 1.25;">${crt.name}</span>
                                    <span class="fs-9 text-muted d-block mt-0.5">${crt.org}</span>
                                </div>
                            </div>
                        `;
                    });

                    const projectsContainer = document.getElementById('ai-recs-projects-container');
                    projectsContainer.innerHTML = '';
                    data.ai_recommendations.projects.forEach(p => {
                        projectsContainer.innerHTML += `
                            <div class="d-flex align-items-center gap-3 p-2.5 rounded bg-dark border border-secondary" style="border-radius: 12px !important;">
                                <div class="fs-5 text-gradient-purple"><i class="fa-solid fa-folder-open"></i></div>
                                <div>
                                    <span class="fs-8 text-white fw-bold d-block" style="line-height: 1.25;">${p.title}</span>
                                    <span class="fs-9 text-muted d-block mt-0.5">${p.tech}</span>
                                </div>
                            </div>
                        `;
                    });

                } else {
                    alert(data.message || 'Error loading career intelligence metrics.');
                }
            })
            .catch(err => {
                console.error(err);
                if (loader) loader.style.display = 'none';
                alert('Connection failure: unable to sync career intelligence.');
            });
    };
});
