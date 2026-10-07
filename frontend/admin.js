// API Base URL
const API_BASE_URL = window.location.origin.includes('localhost') 
    ? 'http://localhost:5000/api' 
    : '/api';


// Add escapeHtml function here
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Rest of your code...

// Check authentication on load
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('adminToken');
    if (!token) {
        showLoginModal();
    } else {
        loadDashboard();
        loadAdminName();
    }
});

// Tab switching
document.querySelectorAll('.admin-nav li').forEach(item => {
    item.addEventListener('click', function() {
        const tabId = this.dataset.tab;
        
        if (tabId === 'logout') {
            logout();
            return;
        }
        
        // Update active tab
        document.querySelectorAll('.admin-nav li').forEach(li => li.classList.remove('active'));
        this.classList.add('active');
        
        // Show corresponding content
        document.querySelectorAll('.admin-tab').forEach(tab => tab.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        
        // Load data for specific tabs
        if (tabId === 'dashboard') {
            loadDashboard();
        } else if (tabId === 'scholarships') {
            loadScholarships();
        } else if (tabId === 'students') {
            loadStudents();
        } else if (tabId === 'campaigns') {
            loadCampaigns();
        } else if (tabId === 'matching') {
            loadScholarshipsForMatching();
        } else if (tabId === 'work-study') {
            loadWorkStudy();
        }
    });
});

// Show Login Modal
function showLoginModal() {
    document.getElementById('login-modal').style.display = 'flex';
}

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});

// Update closeModal function
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}
// Delete Scholarship
async function deleteScholarship(id) {
    if (confirm('Are you sure you want to delete this scholarship?')) {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/scholarships/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': 'Bearer ' + localStorage.getItem('adminToken')
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                showNotification('Scholarship deleted successfully', 'success');
                loadScholarships(); // Reload the list
            } else {
                showNotification('Failed to delete: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error deleting scholarship:', error);
            showNotification('Error deleting scholarship', 'error');
        }
    }
}

// Edit Scholarship
async function editScholarship(id) {
    // For now, just show a notification
    // In a real implementation, you'd open a modal with the scholarship data
    showNotification('Edit functionality coming soon', 'info');
}

// Show Add Work-Study Modal
function showAddWorkStudy() {
    document.getElementById('work-study-modal').style.display = 'flex';
}

// Admin Login Form
document.getElementById('admin-login-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const email = document.getElementById('admin-email').value;
    const password = document.getElementById('admin-password').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        console.log('Login response:', data);
        
        if (data.success) {
            localStorage.setItem('adminToken', data.token);
            localStorage.setItem('adminUser', JSON.stringify(data.user));
            document.getElementById('login-modal').style.display = 'none';
            
            // Load dashboard
            loadDashboard();
            loadAdminName();
            
            showNotification('Login successful!', 'success');
        } else {
            showNotification(data.error || 'Invalid credentials', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Login failed - check console', 'error');
    }
});
// Load Admin Name
function loadAdminName() {
    const user = JSON.parse(localStorage.getItem('adminUser') || '{}');
    document.getElementById('admin-name').textContent = user.name || 'Admin';
}

function logout() {
    // Clear all admin data
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminUser');
    
    // Clear any other stored data
    sessionStorage.clear();
    
    // Show login modal
    showLoginModal();
    
    // Clear dashboard content
    document.getElementById('admin-name').textContent = 'Admin';
    document.getElementById('total-students').textContent = '0';
    document.getElementById('active-scholarships').textContent = '0';
    document.getElementById('active-campaigns').textContent = '0';
    document.getElementById('total-applications').textContent = '0';
    
    showNotification('Logged out successfully', 'success');
    
    // Optional: Redirect to landing page after 2 seconds
    setTimeout(() => {
        if (confirm('Return to home page?')) {
            window.location.href = '/';
        }
    }, 2000);
}

// Load Dashboard
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/dashboard`, {
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('adminToken') }
        });
        const data = await response.json();
        
        if (data.success) {
            // Update stats
            document.getElementById('total-students').textContent = data.stats.total_students || 0;
            document.getElementById('active-scholarships').textContent = data.stats.active_scholarships || 0;
            document.getElementById('active-campaigns').textContent = data.stats.active_campaigns || 0;
            document.getElementById('total-applications').textContent = data.stats.total_applications || 0;
            
            // Display recent applications
            const tbody = document.getElementById('recent-applications');
            if (data.recent_applications && data.recent_applications.length > 0) {
                tbody.innerHTML = data.recent_applications.map(app => `
                    <tr>
                        <td>${app.users?.name || 'Unknown'}</td>
                        <td><span class="status-badge" style="background: #e3f2fd; color: #1976d2;">${app.opportunity_type}</span></td>
                        <td>${app.opportunity_id}</td>
                        <td>${new Date(app.applied_at).toLocaleDateString()}</td>
                        <td><span class="status-badge ${app.status}">${app.status}</span></td>
                        <td><button class="btn-small view" onclick="viewApplication('${app.id}')">View</button></td>
                    </tr>
                `).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No recent applications</td></tr>';
            }
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load Scholarships
async function loadScholarships() {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/scholarships`, {
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('adminToken') }
        });
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('scholarships-list');
            if (data.scholarships && data.scholarships.length > 0) {
                container.innerHTML = data.scholarships.map(s => `
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-award"></i>
                            <span class="status-badge ${s.status}">${s.status}</span>
                        </div>
                        <h3>${s.name}</h3>
                        <p class="provider"><i class="fas fa-building"></i> ${s.provider}</p>
                        <p class="amount">₹${Number(s.amount).toLocaleString()}</p>
                        <p class="deadline"><i class="fas fa-calendar"></i> Deadline: ${new Date(s.deadline).toLocaleDateString()}</p>
                        <p><i class="fas fa-users"></i> ${s.applications_received || 0} applications</p>
                        <div class="card-footer">
                            <button class="btn-small edit" onclick="editScholarship('${s.id}')"><i class="fas fa-edit"></i> Edit</button>
                            <button class="btn-small view" onclick="viewScholarship('${s.id}')"><i class="fas fa-eye"></i> View</button>
                            <button class="btn-small delete" onclick="deleteScholarship('${s.id}')"><i class="fas fa-trash"></i> Delete</button>
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p style="text-align: center; color: #999;">No scholarships found</p>';
            }
        }
    } catch (error) {
        console.error('Error loading scholarships:', error);
    }
}

// Load Work-Study Opportunities
async function loadWorkStudy() {
    try {
        const response = await fetch(`${API_BASE_URL}/work-study/opportunities`);
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('work-study-list');
            if (data.opportunities && data.opportunities.length > 0) {
                container.innerHTML = data.opportunities.map(opp => `
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-briefcase"></i>
                            <span class="status-badge ${opp.status}">${opp.status}</span>
                        </div>
                        <h3>${opp.title}</h3>
                        <p class="provider"><i class="fas fa-building"></i> ${opp.organization}</p>
                        <p class="amount">₹${opp.stipend}/month</p>
                        <p><i class="fas fa-clock"></i> ${opp.hours_per_week} hrs/week • ${opp.duration_months} months</p>
                        <p><i class="fas fa-map-marker-alt"></i> ${opp.remote ? 'Remote' : opp.location || 'On-site'}</p>
                        <p><i class="fas fa-users"></i> ${opp.applicants || 0} applicants</p>
                        <div class="card-footer">
                            <button class="btn-small edit" onclick="editWorkStudy('${opp.id}')"><i class="fas fa-edit"></i> Edit</button>
                            <button class="btn-small view" onclick="viewWorkStudy('${opp.id}')"><i class="fas fa-eye"></i> View</button>
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p style="text-align: center; color: #999;">No work-study opportunities found</p>';
            }
        }
    } catch (error) {
        console.error('Error loading work-study:', error);
    }
}

// admin.js - Fix loadStudents function (REPLACE the existing function)
async function loadStudents() {
    const container = document.getElementById('students-list');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading students...</p></div>';
    
    try {
        const token = localStorage.getItem('adminToken');
        if (!token) {
            showNotification('Please login again', 'error');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/admin/students`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Students data:', data); // Debug log
        
        if (data.success && data.students && data.students.length > 0) {
            container.innerHTML = data.students.map(student => {
                // Get fields directly from student object (not nested in users)
                const name = student.name || 'Unknown';
                const email = student.email || 'No email';
                const course = student.course || 'Not specified';
                const academicScore = student.academic_score || 'N/A';
                const familyIncome = student.family_income || 0;
                const skills = student.skills || [];
                const profileCompleted = student.profile_completed || false;
                
                return `
                    <div class="card student-card">
                        <div class="card-header">
                            <i class="fas fa-user-graduate"></i>
                            <span class="status-badge ${profileCompleted ? 'active' : 'pending'}">
                                ${profileCompleted ? 'Profile Complete' : 'Incomplete'}
                            </span>
                        </div>
                        <h3>${escapeHtml(name)}</h3>
                        <p><i class="fas fa-envelope"></i> ${escapeHtml(email)}</p>
                        <p><i class="fas fa-graduation-cap"></i> ${escapeHtml(course)}</p>
                        <p><i class="fas fa-star"></i> Academic Score: ${academicScore}%</p>
                        <p><i class="fas fa-rupee-sign"></i> Family Income: ₹${Number(familyIncome).toLocaleString()}</p>
                        ${skills.length > 0 ? `<p><i class="fas fa-code"></i> Skills: ${skills.slice(0, 3).join(', ')}${skills.length > 3 ? '...' : ''}</p>` : ''}
                        <div class="card-footer">
                            <button class="btn-small view" onclick="viewStudent(${student.id})">
                                <i class="fas fa-eye"></i> View Profile
                            </button>
                            <button class="btn-small edit" onclick="editStudent(${student.id})">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = '<p class="empty-state"><i class="fas fa-users"></i><br>No students found</p>';
        }
    } catch (error) {
        console.error('Error loading students:', error);
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <p>Failed to load students: ${error.message}</p>
                <button class="btn-primary" onclick="loadStudents()">
                    <i class="fas fa-sync"></i> Retry
                </button>
            </div>
        `;
    }
}

// Load Campaigns
async function loadCampaigns() {
    try {
        const response = await fetch(`${API_BASE_URL}/crowdfunding/campaigns`);
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('campaigns-list');
            if (data.campaigns && data.campaigns.length > 0) {
                container.innerHTML = data.campaigns.map(campaign => {
                    const progress = (campaign.raised_amount / campaign.goal_amount) * 100;
                    return `
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-hand-holding-heart"></i>
                            <span class="status-badge ${campaign.status}">${campaign.status}</span>
                        </div>
                        <h3>${campaign.title}</h3>
                        <p class="provider">By: ${campaign.student_name || 'Unknown'}</p>
                        <div style="background: #e0e0e0; height: 8px; border-radius: 4px; margin: 15px 0;">
                            <div style="width: ${progress}%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 8px; border-radius: 4px;"></div>
                        </div>
                        <p><strong>₹${Number(campaign.raised_amount).toLocaleString()}</strong> raised of ₹${Number(campaign.goal_amount).toLocaleString()}</p>
                        <p><i class="fas fa-users"></i> ${campaign.donors?.length || 0} donors</p>
                        <p><i class="fas fa-calendar"></i> Deadline: ${new Date(campaign.deadline).toLocaleDateString()}</p>
                        <div class="card-footer">
                            <button class="btn-small view" onclick="viewCampaign('${campaign.id}')"><i class="fas fa-eye"></i> View</button>
                        </div>
                    </div>
                `}).join('');
            } else {
                container.innerHTML = '<p style="text-align: center; color: #999;">No campaigns found</p>';
            }
        }
    } catch (error) {
        console.error('Error loading campaigns:', error);
    }
}

// admin.js - Fix scholarship form submission
document.getElementById('scholarship-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Show loading state
    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
    submitBtn.disabled = true;
    
    // Get all form data
    const scholarshipData = {
        name: document.getElementById('scholarship-name').value.trim(),
        provider: document.getElementById('scholarship-provider').value.trim(),
        amount: parseFloat(document.getElementById('scholarship-amount').value),
        deadline: document.getElementById('scholarship-deadline').value,
        link: document.getElementById('scholarship-link').value.trim(),
        description: document.getElementById('scholarship-description').value.trim(),
        min_academic_score: document.getElementById('min-academic-score').value ? parseFloat(document.getElementById('min-academic-score').value) : null,
        max_income: document.getElementById('max-income').value ? parseFloat(document.getElementById('max-income').value) : null,
        eligible_courses: document.getElementById('eligible-courses').value.split(',').map(s => s.trim()).filter(s => s),
        merit_based: document.getElementById('merit-based').checked,
        need_based: document.getElementById('need-based').checked,
        requires_extracurricular: document.getElementById('requires-extracurricular').checked,
        other_requirements: document.getElementById('other-requirements').value.trim()
    };
    
    // Validate required fields
    if (!scholarshipData.name || !scholarshipData.provider || !scholarshipData.amount || !scholarshipData.deadline || !scholarshipData.link) {
        showNotification('Please fill all required fields (Name, Provider, Amount, Deadline, Link)', 'error');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        return;
    }
    
    try {
        const token = localStorage.getItem('adminToken');
        if (!token) {
            showNotification('Please login again', 'error');
            showLoginModal();
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/admin/scholarships`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify(scholarshipData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Scholarship added successfully!', 'success');
            this.reset();
            
            // Reset checkboxes
            document.getElementById('merit-based').checked = false;
            document.getElementById('need-based').checked = false;
            document.getElementById('requires-extracurricular').checked = false;
            
            // Switch to scholarships tab to see the new one
            setTimeout(() => {
                document.querySelector('[data-tab="scholarships"]').click();
            }, 1000);
        } else {
            showNotification('Error: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error adding scholarship:', error);
        showNotification('Failed to add scholarship. Check console for details.', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
});
// Work-Study Form Submission
document.getElementById('work-study-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const workData = {
        title: document.getElementById('work-title').value,
        organization: document.getElementById('work-organization').value,
        stipend: document.getElementById('work-stipend').value,
        hours_per_week: document.getElementById('work-hours').value,
        duration_months: document.getElementById('work-duration').value,
        deadline: document.getElementById('work-deadline').value,
        location: document.getElementById('work-location').value,
        remote: document.getElementById('work-remote').checked,
        required_skills: document.getElementById('work-skills').value.split(',').map(s => s.trim()).filter(s => s),
        description: document.getElementById('work-description').value
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/work-study`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + localStorage.getItem('adminToken')
            },
            body: JSON.stringify(workData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Work-study opportunity added!', 'success');
            closeModal('work-study-modal');
            this.reset();
            loadWorkStudy();
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Failed to add work-study', 'error');
    }
});

// Notification function (matches index style)
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
        <span>${message}</span>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Search functions
function searchScholarships() {
    const query = document.getElementById('scholarship-search').value.toLowerCase();
    const cards = document.querySelectorAll('#scholarships-list .card');
    
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(query) ? 'block' : 'none';
    });
}

function searchStudents() {
    const query = document.getElementById('student-search').value.toLowerCase();
    const cards = document.querySelectorAll('#students-list .card');
    
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(query) ? 'block' : 'none';
    });
}

// Placeholder functions for actions
function viewApplication(id) { showNotification('Viewing application: ' + id, 'info'); }
function editScholarship(id) { showNotification('Edit scholarship: ' + id, 'info'); }
function viewScholarship(id) { showNotification('Viewing scholarship: ' + id, 'info'); }
function deleteScholarship(id) { 
    if (confirm('Are you sure you want to delete this scholarship?')) {
        showNotification('Scholarship deleted', 'success');
    }
}
function editWorkStudy(id) { showNotification('Edit work-study: ' + id, 'info'); }
function viewWorkStudy(id) { showNotification('Viewing work-study: ' + id, 'info'); }
function viewStudent(id) { showNotification('Viewing student profile: ' + id, 'info'); }
function viewCampaign(id) { showNotification('Viewing campaign: ' + id, 'info'); }
function findEligibleStudents() { showNotification('Finding eligible students...', 'info'); }

// admin.js - Fix loadScholarshipsForMatching function (REPLACE the existing function)
async function loadScholarshipsForMatching() {
    const select = document.getElementById('scholarship-select');
    if (!select) return;
    
    select.innerHTML = '<option value="">Loading scholarships...</option>';
    
    try {
        const token = localStorage.getItem('adminToken');
        if (!token) {
            showNotification('Please login again', 'error');
            select.innerHTML = '<option value="">Please login again</option>';
            return;
        }
        
        console.log('Fetching scholarships for matching...');
        const response = await fetch(`${API_BASE_URL}/admin/scholarships`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Scholarships data:', data);
        
        if (data.success && data.scholarships && data.scholarships.length > 0) {
            select.innerHTML = '<option value="">Select a scholarship...</option>';
            data.scholarships.forEach(s => {
                // Only show active scholarships
                if (s.status === 'active') {
                    select.innerHTML += `<option value="${s.id}">${escapeHtml(s.name)} (₹${Number(s.amount).toLocaleString()})</option>`;
                }
            });
            
            // If no active scholarships
            if (select.options.length === 1) {
                select.innerHTML = '<option value="">No active scholarships available</option>';
            }
        } else {
            select.innerHTML = '<option value="">No scholarships found</option>';
            console.log('No scholarships found or error:', data);
        }
    } catch (error) {
        console.error('Error loading scholarships for matching:', error);
        select.innerHTML = `<option value="">Error: ${error.message}</option>`;
    }
}

// Update findEligibleStudents function
async function findEligibleStudents() {
    const scholarshipId = document.getElementById('scholarship-select')?.value;
    
    if (!scholarshipId) {
        showNotification('Please select a scholarship first', 'error');
        return;
    }
    
    const container = document.getElementById('matching-results');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Finding eligible students...</p></div>';
    
    try {
        const token = localStorage.getItem('adminToken');
        if (!token) {
            showNotification('Please login again', 'error');
            return;
        }
        
        console.log(`Finding eligible students for scholarship: ${scholarshipId}`);
        const response = await fetch(`${API_BASE_URL}/admin/scholarships/${scholarshipId}/students`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Eligible students:', data);
        
        if (data.success && data.eligible_students && data.eligible_students.length > 0) {
            container.innerHTML = `
                <h3 style="margin-bottom: 20px;">
                    <i class="fas fa-users"></i> 
                    Found ${data.eligible_students.length} Eligible Students
                </h3>
                <div class="cards-grid">
                    ${data.eligible_students.map(student => `
                        <div class="card match-card">
                            <div class="card-header">
                                <i class="fas fa-user-graduate"></i>
                                <span class="status-badge" style="background: #4caf50; color: white;">
                                    Match: ${student.match_score}%
                                </span>
                            </div>
                            <h3>${escapeHtml(student.student.name || 'Unknown')}</h3>
                            <p><i class="fas fa-envelope"></i> ${escapeHtml(student.student.email || 'No email')}</p>
                            <p><i class="fas fa-star"></i> Score: ${student.student.academic_score || 'N/A'}%</p>
                            <p><i class="fas fa-rupee-sign"></i> Income: ₹${Number(student.student.family_income || 0).toLocaleString()}</p>
                            <p><i class="fas fa-graduation-cap"></i> ${escapeHtml(student.student.course || 'Not specified')}</p>
                            <div class="card-footer">
                                <button class="btn-small view" onclick="viewStudentProfile(${student.student.id})">
                                    <i class="fas fa-eye"></i> View Profile
                                </button>
                                <button class="btn-small edit" onclick="notifyStudent(${student.student.id})">
                                    <i class="fas fa-bell"></i> Notify
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-user-graduate"></i>
                    <p>No eligible students found for this scholarship</p>
                    <p style="font-size: 12px; margin-top: 10px;">Try selecting a different scholarship</p>
                    <button class="btn-primary" style="margin-top: 15px;" onclick="loadScholarshipsForMatching()">
                        <i class="fas fa-sync"></i> Refresh Scholarships
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error finding eligible students:', error);
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <p>Failed to find eligible students: ${error.message}</p>
                <button class="btn-primary" onclick="findEligibleStudents()">
                    <i class="fas fa-sync"></i> Retry
                </button>
            </div>
        `;
    }
}

function viewStudentProfile(studentId) {
    showNotification(`Viewing student profile: ${studentId}`, 'info');
    // You can implement a modal to show detailed profile
}

function notifyStudent(studentId) {
    showNotification(`Notification sent to student!`, 'success');
}