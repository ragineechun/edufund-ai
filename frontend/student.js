const API_BASE_URL = window.location.origin.includes('localhost') 
    ? 'http://localhost:5000/api' 
    : '/api';

let currentUserId = null;
let allScholarships = [];
let allWorkStudy = [];
// Check authentication
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    if (!token) {
        window.location.href = '/';
        return;
    }
    
    currentUserId = user.id;
    document.getElementById('student-name').textContent = user.name || 'Student';
    loadDashboard();
});

// Load dashboard based on active tab
function loadDashboard() {
    const activeTab = document.querySelector('.nav-menu li.active')?.dataset.tab || 'assessment';
    
    if (activeTab === 'recommendations') {
        loadRecommendations();
    } else if (activeTab === 'applications') {
        loadApplications();
    } else if (activeTab === 'crowdfunding') {
        loadCampaigns();
    } else if (activeTab === 'profile') {
        loadProfile();
    }
}

// Tab switching
document.querySelectorAll('.nav-menu li').forEach(item => {
    item.addEventListener('click', function() {
        document.querySelectorAll('.nav-menu li').forEach(li => li.classList.remove('active'));
        this.classList.add('active');
        
        const tabId = this.dataset.tab;
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        
        // Load tab data
        if (tabId === 'recommendations') {
            loadRecommendations();
        } else if (tabId === 'applications') {
            loadApplications();
        } else if (tabId === 'crowdfunding') {
            loadCampaigns();
        } else if (tabId === 'profile') {
            loadProfile();
        }
    });
});

// Assessment Form
document.getElementById('student-assessment-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    document.getElementById('assessment-loading').style.display = 'block';
    document.getElementById('assessment-result').style.display = 'none';
    
    // Get form values
    const name = document.getElementById('studentName').value;
    const email = document.getElementById('email').value;
    
    // Profile data - only academic/financial fields (no name/email)
    const profileData = {
        academic_score: parseFloat(document.getElementById('academicScore').value),
        family_income: parseFloat(document.getElementById('familyIncome').value),
        extracurriculars: parseInt(document.getElementById('extracurriculars').value) || 0,
        siblings_education: parseInt(document.getElementById('siblingsEducation').value) || 0,
        course: document.getElementById('course').value,
        institution: document.getElementById('institution').value,
        course_duration: parseInt(document.getElementById('courseDuration').value) || 4,
        tuition_fee: parseFloat(document.getElementById('tuitionFee').value),
        preferred_location: document.getElementById('preferredLocation')?.value || null,
        preferred_hours: document.getElementById('preferredHours')?.value ? parseInt(document.getElementById('preferredHours').value) : null,
        expected_stipend: document.getElementById('expectedStipend')?.value ? parseFloat(document.getElementById('expectedStipend').value) : null,
        skills: document.getElementById('skills')?.value 
            ? document.getElementById('skills').value.split(',').map(s => s.trim()).filter(s => s)
            : []
    };
    
    console.log('Sending profile data:', profileData);
    
    try {
        const token = localStorage.getItem('token');
        console.log('Token:', token ? 'Present' : 'Missing');
        
        if (!token) {
            showNotification('Please login first', 'error');
            window.location.href = '/';
            return;
        }

        // Get current user from localStorage
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        console.log('Current user from localStorage:', user);
        
        // If user ID is missing, try to get it from /me endpoint
        if (!user.id) {
            try {
                const meResponse = await fetch(`${API_BASE_URL}/auth/me`, {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                const meData = await meResponse.json();
                if (meData.success && meData.user) {
                    user.id = meData.user.id;
                    user.name = meData.user.name;
                    user.email = meData.user.email;
                    localStorage.setItem('user', JSON.stringify(user));
                    console.log('Updated user from /me:', user);
                }
            } catch (error) {
                console.error('Error fetching user info:', error);
            }
        }
        
        if (!user.id) {
            showNotification('User ID not found. Please login again.', 'error');
            window.location.href = '/';
            return;
        }
        
        currentUserId = user.id;
        console.log('Using user ID:', currentUserId);
        
        // Save profile - send ONLY profile data, not name/email
        const profileResponse = await fetch(`${API_BASE_URL}/student/profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify(profileData)  // Send only profile data
        });
        
        console.log('Profile response status:', profileResponse.status);
        
        // Get response
        const profileData_response = await profileResponse.json();
        console.log('Profile response:', profileData_response);
        
        if (profileData_response.success) {
            showNotification('Profile saved successfully!', 'success');
            
            // Update user in localStorage with profile_completed flag
            user.profile_completed = true;
            localStorage.setItem('user', JSON.stringify(user));
            
            // Get AI assessment
            const assessResponse = await fetch(`${API_BASE_URL}/student/${currentUserId}/assess`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify(profileData)  // Send same data for assessment
            });
            
            const assessData = await assessResponse.json();
            console.log('Assessment response:', assessData);
            
            if (assessData.success) {
                // Display results
                document.getElementById('funding-gap').textContent = `₹${Number(assessData.assessment.funding_gap).toLocaleString()}`;
                document.getElementById('repayment-capacity').textContent = assessData.assessment.repayment_capacity;
                document.getElementById('eligibility-score').textContent = `${assessData.assessment.eligibility_score}%`;
                document.getElementById('risk-level').textContent = assessData.assessment.risk_level;
                document.getElementById('assessment-result').style.display = 'block';
                
                // Save recommendations
                if (assessData.recommendations) {
                    localStorage.setItem('recommendations', JSON.stringify(assessData.recommendations));
                }
                
                showNotification('Assessment completed!', 'success');
            } else {
                showNotification('Assessment failed: ' + (assessData.error || 'Unknown error'), 'error');
            }
        } else {
            showNotification('Profile save failed: ' + (profileData_response.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Failed to complete assessment. Check console.', 'error');
    } finally {
        document.getElementById('assessment-loading').style.display = 'none';
    }
});


// Load Recommendations 
async function loadRecommendations() {
    const container = document.getElementById('recommendations-container');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Finding best matches for you...</p></div>';
    
    try {
        // First check if we have a student profile
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        if (!user.profile_completed) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clipboard-list"></i>
                    <p>Please complete your assessment first to get personalized recommendations</p>
                    <button class="btn-primary" onclick="document.querySelector('[data-tab=\"assessment\"]').click()">
                        Go to Assessment
                    </button>
                </div>
            `;
            return;
        }
        
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/';
            return;
        }
        
        // Use the correct endpoint with user ID
        const response = await fetch(`${API_BASE_URL}/student/${currentUserId}/recommendations`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.recommendations && data.recommendations.length > 0) {
            displayRecommendations(data.recommendations);
        } else {
            // Fallback to rule-based recommendations
            const storedRecs = JSON.parse(localStorage.getItem('recommendations') || '[]');
            if (storedRecs.length > 0) {
                displayRuleBasedRecommendations(storedRecs);
            } else {
                container.innerHTML = '<p class="empty-state">No recommendations available. Complete your assessment first.</p>';
            }
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <p>Failed to load recommendations</p>
                <button class="btn-primary" onclick="loadRecommendations()">
                    <i class="fas fa-sync"></i> Try Again
                </button>
            </div>
        `;
    }
}

// Load Applications
async function loadApplications() {
    const container = document.getElementById('applications-list');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading applications...</p></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/student/${currentUserId}/applications`, {
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.applications && data.applications.length > 0) {
            container.innerHTML = data.applications.map(app => `
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-file-alt"></i>
                        <span class="status-badge ${app.status || 'pending'}">${app.status || 'pending'}</span>
                    </div>
                    <h3>Application for ${app.opportunity_type || 'opportunity'}</h3>
                    <p>Applied: ${app.applied_at ? new Date(app.applied_at).toLocaleDateString() : 'Unknown'}</p>
                    <p>Status: ${app.status || 'pending'}</p>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="empty-state">No applications yet</p>';
        }
    } catch (error) {
        console.error('Error loading applications:', error);
        container.innerHTML = '<p class="empty-state">Failed to load applications</p>';
    }
}






// Campaign Functions
function showCreateCampaign() {
    document.getElementById('campaign-modal').style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Campaign Form
document.getElementById('campaign-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Show loading state
    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
    submitBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('title', document.getElementById('campaign-title').value);
    formData.append('description', document.getElementById('campaign-description').value);
    formData.append('story', document.getElementById('campaign-story').value);
    formData.append('goal_amount', document.getElementById('campaign-goal').value);
    formData.append('category', document.getElementById('campaign-category').value);
    
    const imageFile = document.getElementById('campaign-image').files[0];
    if (imageFile) {
        formData.append('image', imageFile);
    }
    
    // Log form data for debugging
    console.log('Submitting campaign with data:');
    for (let pair of formData.entries()) {
        console.log(pair[0] + ': ' + pair[1]);
    }
    
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            showNotification('Please login first', 'error');
            window.location.href = '/';
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/crowdfunding/campaigns`, {
            method: 'POST',
            headers: { 
                'Authorization': 'Bearer ' + token
                // Don't set Content-Type header when using FormData
            },
            body: formData
        });
        
        const data = await response.json();
        console.log('Response:', data);
        
        if (data.success) {
            showNotification('Campaign created successfully!', 'success');
            closeModal('campaign-modal');
            this.reset();
            loadCampaigns();
        } else {
            showNotification('Failed to create campaign: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error creating campaign:', error);
        showNotification('Error creating campaign: ' + error.message, 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
});
// Apply for Opportunity
function applyForOpportunity(type) {
    showNotification(`Applied for ${type} successfully! (Demo)`, 'success');
}

// student.js - Fix donate function
async function donateToCampaign(campaignId) {
    const amount = prompt('Enter donation amount (₹):', '1000');
    
    if (!amount) return;
    
    const donationAmount = parseFloat(amount);
    if (isNaN(donationAmount) || donationAmount <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
    }
    
    const donorName = prompt('Your name (optional):', 'Anonymous');
    const donorMessage = prompt('Message (optional):', '');
    
    const donateBtn = event.target;
    const originalText = donateBtn.innerHTML;
    donateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    donateBtn.disabled = true;
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/crowdfunding/campaigns/${campaignId}/donate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                amount: donationAmount,
                name: donorName || 'Anonymous',
                message: donorMessage || '',
                anonymous: !donorName || donorName === 'Anonymous'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`Thank you for donating ₹${donationAmount.toLocaleString()}!`, 'success');
            
            // Reload campaigns to update progress
            setTimeout(() => {
                loadCampaigns();
            }, 1000);
        } else {
            showNotification('Donation failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error donating:', error);
        showNotification('Error processing donation', 'error');
    } finally {
        donateBtn.innerHTML = originalText;
        donateBtn.disabled = false;
    }
}

// student.js - Fix loadCampaigns with proper image display
async function loadCampaigns() {
    const container = document.getElementById('campaigns-list');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading campaigns...</p></div>';
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/crowdfunding/campaigns`, {
            headers: token ? { 'Authorization': 'Bearer ' + token } : {}
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Campaigns data:', data);
        
        if (data.success && data.campaigns && data.campaigns.length > 0) {
            container.innerHTML = data.campaigns.map(campaign => {
                const raised = campaign.raised_amount || 0;
                const goal = campaign.goal_amount || 1;
                const progress = (raised / goal) * 100;
                const progressPercent = Math.min(progress, 100);
                
                // Format deadline properly
                let deadlineText = 'No deadline';
                let deadlineClass = '';
                if (campaign.deadline) {
                    const deadlineDate = new Date(campaign.deadline);
                    deadlineText = deadlineDate.toLocaleDateString('en-IN', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    });
                    
                    const today = new Date();
                    if (deadlineDate < today) {
                        deadlineClass = 'deadline-passed';
                        deadlineText = `Expired on ${deadlineText}`;
                    } else if (campaign.days_left && campaign.days_left <= 7) {
                        deadlineClass = 'deadline-urgent';
                        deadlineText = `${deadlineText} (${campaign.days_left} days left!)`;
                    } else if (campaign.days_left) {
                        deadlineText = `${deadlineText} (${campaign.days_left} days left)`;
                    }
                }
                
                // Get image URL - handle both image_path and image_url
                let imageUrl = null;
                if (campaign.image_url) {
                    imageUrl = campaign.image_url;
                } else if (campaign.image_path) {
                    imageUrl = `/${campaign.image_path}`;
                }
                
                // Ensure image URL is absolute if needed
                if (imageUrl && !imageUrl.startsWith('http') && !imageUrl.startsWith('/')) {
                    imageUrl = '/' + imageUrl;
                }
                
                console.log(`Campaign ${campaign.id} image URL:`, imageUrl);
                
                return `
                    <div class="card campaign-card" data-campaign-id="${campaign.id}">
                        <div class="card-header">
                            <i class="fas fa-hand-holding-heart"></i>
                            <span class="status-badge ${campaign.status || 'active'}">${escapeHtml(campaign.status || 'active')}</span>
                        </div>
                        <h3>${escapeHtml(campaign.title || 'Untitled')}</h3>
                        <p class="provider">By: ${escapeHtml(campaign.student_name || 'Unknown')}</p>
                        
                        ${imageUrl ? `
                            <div style="margin: 10px 0; border-radius: 10px; overflow: hidden; background: #f5f5f5; min-height: 150px;">
                                <img src="${imageUrl}" 
                                     style="width: 100%; height: 150px; object-fit: cover; display: block;" 
                                     onerror="this.onerror=null; this.parentElement.innerHTML='<div style=\'height:150px; display:flex; align-items:center; justify-content:center; color:#999;\'><i class=\'fas fa-image\' style=\'font-size:40px;\'></i><br>No image</div>';">
                            </div>
                        ` : `
                            <div style="margin: 10px 0; background: #f5f5f5; border-radius: 10px; height: 150px; display: flex; align-items: center; justify-content: center; color: #999;">
                                <div style="text-align: center;">
                                    <i class="fas fa-image" style="font-size: 40px;"></i>
                                    <br>No image
                                </div>
                            </div>
                        `}
                        
                        <!-- Progress Bar -->
                        <div style="margin: 15px 0;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <span style="font-size: 14px; color: #666;">Raised</span>
                                <span style="font-size: 14px; font-weight: 600; color: #667eea;">${progressPercent.toFixed(1)}%</span>
                            </div>
                            <div style="background: #e0e0e0; height: 10px; border-radius: 5px; overflow: hidden;">
                                <div style="width: ${progressPercent}%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; transition: width 0.3s ease;"></div>
                            </div>
                        </div>
                        
                        <!-- Amount Raised -->
                        <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                            <div>
                                <div style="font-size: 20px; font-weight: 700; color: #333;">₹${raised.toLocaleString()}</div>
                                <div style="font-size: 12px; color: #666;">Raised</div>
                            </div>
                            <div>
                                <div style="font-size: 20px; font-weight: 700; color: #666;">₹${goal.toLocaleString()}</div>
                                <div style="font-size: 12px; color: #666;">Goal</div>
                            </div>
                        </div>
                        
                        <p><i class="fas fa-users"></i> ${campaign.donors?.length || 0} supporters</p>
                        <p><i class="fas fa-calendar ${deadlineClass}"></i> ${deadlineText}</p>
                        
                        ${campaign.description ? `<p style="color: #666; font-size: 14px; margin: 10px 0;">${escapeHtml(campaign.description.substring(0, 100))}${campaign.description.length > 100 ? '...' : ''}</p>` : ''}
                        
                        <button class="btn-primary" style="width: 100%; margin-top: 15px;" onclick="donateToCampaign(${campaign.id})" ${campaign.status !== 'active' ? 'disabled' : ''}>
                            <i class="fas fa-hand-holding-heart"></i> ${campaign.status === 'active' ? 'Donate Now' : 'Campaign Closed'}
                        </button>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-hand-holding-heart"></i>
                    <p>No active campaigns found</p>
                    <button class="btn-primary" onclick="showCreateCampaign()">
                        <i class="fas fa-plus"></i> Start a Campaign
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading campaigns:', error);
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <p>Failed to load campaigns: ${error.message}</p>
                <button class="btn-primary" onclick="loadCampaigns()">
                    <i class="fas fa-sync"></i> Retry
                </button>
            </div>
        `;
    }
}

// Add this to your student.js file - Image preview for campaign modal
document.addEventListener('DOMContentLoaded', function() {
    // Image upload preview for campaign modal
    const imageUploadArea = document.getElementById('image-upload-area');
    const imageInput = document.getElementById('campaign-image');
    const imagePreview = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');
    const removeImageBtn = document.getElementById('remove-image');
    
    if (imageUploadArea) {
        imageUploadArea.addEventListener('click', function() {
            imageInput.click();
        });
        
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(evt) {
                    previewImg.src = evt.target.result;
                    imagePreview.style.display = 'block';
                    imageUploadArea.style.display = 'none';
                };
                reader.readAsDataURL(file);
            }
        });
        
        if (removeImageBtn) {
            removeImageBtn.addEventListener('click', function() {
                imageInput.value = '';
                imagePreview.style.display = 'none';
                imageUploadArea.style.display = 'block';
                previewImg.src = '';
            });
        }
    }
});
// Helper function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
// Logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('recommendations');
    window.location.href = '/';
}

// Notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i> ${message}`;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animation styles if not present
if (!document.querySelector('#notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}


// Load profile with edit button
async function loadProfile() {
    const container = document.getElementById('profile-content');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading profile...</p></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const user = data.user;
            const profile = user.profile || {};
            
            container.innerHTML = `
                <div style="display: flex; justify-content: flex-end; margin-bottom: 20px;">
                    <button class="btn-primary" onclick="openEditProfileModal()">
                        <i class="fas fa-edit"></i> Edit Profile
                    </button>
                </div>
                <div class="card">
                    <h3><i class="fas fa-id-card"></i> Personal Information</h3>
                    <div class="profile-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 20px;">
                        <div>
                            <p><strong>Name:</strong> ${user.name || 'N/A'}</p>
                            <p><strong>Email:</strong> ${user.email || 'N/A'}</p>
                            <p><strong>Role:</strong> ${user.role || 'student'}</p>
                            <p><strong>Member since:</strong> ${user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</p>
                        </div>
                        <div>
                            <p><strong>Course:</strong> ${profile.course || 'Not set'}</p>
                            <p><strong>Institution:</strong> ${profile.institution || 'Not set'}</p>
                            <p><strong>Academic Score:</strong> ${profile.academic_score || 'N/A'}%</p>
                            <p><strong>Family Income:</strong> ₹${(profile.family_income || 0).toLocaleString()}</p>
                        </div>
                    </div>
                </div>
                
                <div class="card" style="margin-top: 20px;">
                    <h3><i class="fas fa-chart-line"></i> Academic Details</h3>
                    <div class="profile-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 20px;">
                        <div>
                            <p><strong>Extracurriculars:</strong> ${profile.extracurriculars || 0}</p>
                            <p><strong>Siblings in Education:</strong> ${profile.siblings_education || 0}</p>
                            <p><strong>Course Duration:</strong> ${profile.course_duration || 4} years</p>
                        </div>
                        <div>
                            <p><strong>Tuition Fee:</strong> ₹${(profile.tuition_fee || 0).toLocaleString()}</p>
                            <p><strong>Preferred Location:</strong> ${profile.preferred_location || 'Not specified'}</p>
                            <p><strong>Expected Stipend:</strong> ₹${(profile.expected_stipend || 0).toLocaleString()}</p>
                        </div>
                    </div>
                    <div style="margin-top: 20px;">
                        <p><strong>Skills:</strong> ${profile.skills && profile.skills.length ? profile.skills.join(', ') : 'None specified'}</p>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = '<p class="empty-state">Failed to load profile</p>';
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        container.innerHTML = '<p class="empty-state">Failed to load profile</p>';
    }
}

// Open edit profile modal with current data
async function openEditProfileModal() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const user = data.user;
            const profile = user.profile || {};
            
            // Fill the form with current data
            document.getElementById('edit-name').value = user.name || '';
            document.getElementById('edit-email').value = user.email || '';
            document.getElementById('edit-familyIncome').value = profile.family_income || '';
            document.getElementById('edit-academicScore').value = profile.academic_score || '';
            document.getElementById('edit-extracurriculars').value = profile.extracurriculars || 0;
            document.getElementById('edit-siblingsEducation').value = profile.siblings_education || 0;
            document.getElementById('edit-course').value = profile.course || '';
            document.getElementById('edit-institution').value = profile.institution || '';
            document.getElementById('edit-courseDuration').value = profile.course_duration || 4;
            document.getElementById('edit-tuitionFee').value = profile.tuition_fee || '';
            document.getElementById('edit-preferredLocation').value = profile.preferred_location || '';
            document.getElementById('edit-preferredHours').value = profile.preferred_hours || '';
            document.getElementById('edit-expectedStipend').value = profile.expected_stipend || '';
            document.getElementById('edit-skills').value = profile.skills ? profile.skills.join(', ') : '';
            
            // Show modal
            document.getElementById('edit-profile-modal').style.display = 'flex';
        }
    } catch (error) {
        console.error('Error loading profile for edit:', error);
        showNotification('Failed to load profile data', 'error');
    }
}

// Handle edit profile form submission
document.getElementById('edit-profile-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const profileData = {
        academic_score: parseFloat(document.getElementById('edit-academicScore').value),
        family_income: parseFloat(document.getElementById('edit-familyIncome').value),
        extracurriculars: parseInt(document.getElementById('edit-extracurriculars').value) || 0,
        siblings_education: parseInt(document.getElementById('edit-siblingsEducation').value) || 0,
        course: document.getElementById('edit-course').value,
        institution: document.getElementById('edit-institution').value,
        course_duration: parseInt(document.getElementById('edit-courseDuration').value) || 4,
        tuition_fee: parseFloat(document.getElementById('edit-tuitionFee').value),
        preferred_location: document.getElementById('edit-preferredLocation')?.value || null,
        preferred_hours: document.getElementById('edit-preferredHours')?.value ? parseInt(document.getElementById('edit-preferredHours').value) : null,
        expected_stipend: document.getElementById('edit-expectedStipend')?.value ? parseFloat(document.getElementById('edit-expectedStipend').value) : null,
        skills: document.getElementById('edit-skills')?.value 
            ? document.getElementById('edit-skills').value.split(',').map(s => s.trim()).filter(s => s)
            : []
    };
    
    try {
        const token = localStorage.getItem('token');
        
        const response = await fetch(`${API_BASE_URL}/student/profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify(profileData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Profile updated successfully!', 'success');
            closeModal('edit-profile-modal');
            loadProfile(); // Reload profile
        } else {
            showNotification('Failed to update profile: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        showNotification('Error updating profile', 'error');
    }
});

// ============================================
// ALL SCHOLARSHIPS VIEW
// ============================================

// Load all scholarships
async function loadAllScholarships() {
    const container = document.getElementById('all-scholarships-list');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading scholarships...</p></div>';
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/student/scholarships/all`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        const data = await response.json();
        
        if (data.success) {
            allScholarships = data.scholarships || [];
            displayAllScholarships(allScholarships);
        } else {
            container.innerHTML = '<p class="empty-state">Failed to load scholarships</p>';
        }
    } catch (error) {
        console.error('Error loading scholarships:', error);
        container.innerHTML = '<p class="empty-state">Error loading scholarships</p>';
    }
}


// Display all scholarships with Apply Now button containing the link
function displayAllScholarships(scholarships) {
    const container = document.getElementById('all-scholarships-list');
    
    if (scholarships.length === 0) {
        container.innerHTML = '<p class="empty-state">No scholarships available</p>';
        return;
    }
    
    container.innerHTML = scholarships.map(s => `
        <div class="card scholarship-card">
            <div class="card-header">
                <i class="fas fa-award" style="font-size: 24px; color: #667eea;"></i>
                <span class="status-badge ${s.status || 'active'}">${s.status || 'active'}</span>
            </div>
            <h3>${s.name}</h3>
            <p class="provider"><i class="fas fa-building"></i> ${s.provider}</p>
            <p class="amount" style="font-size: 24px; font-weight: 700; color: #667eea; margin: 10px 0;">
                ₹${Number(s.amount).toLocaleString()}
            </p>
            <div style="background: #f8f9ff; padding: 15px; border-radius: 10px; margin: 15px 0;">
                <p style="margin: 5px 0;">
                    <i class="fas fa-calendar" style="color: #667eea; width: 20px;"></i>
                    <strong>Deadline:</strong> ${s.deadline ? new Date(s.deadline).toLocaleDateString() : 'Not specified'}
                </p>
                <p style="margin: 5px 0;">
                    <i class="fas fa-star" style="color: #667eea; width: 20px;"></i>
                    <strong>Min Score:</strong> ${s.min_academic_score || 'Not specified'}%
                </p>
                <p style="margin: 5px 0;">
                    <i class="fas fa-rupee-sign" style="color: #667eea; width: 20px;"></i>
                    <strong>Max Income:</strong> ${s.max_income ? '₹' + Number(s.max_income).toLocaleString() : 'Not specified'}
                </p>
            </div>
            
            ${s.description ? `<p style="color: #666; font-size: 14px; margin: 10px 0;">${s.description}</p>` : ''}
            
            <div style="margin-top: 20px; display: flex; gap: 10px;">
                <!-- Apply Now button with link - opens in new tab -->
                <a href="${s.link || '#'}" target="_blank" rel="noopener noreferrer" 
                   class="btn-primary" style="flex: 2; text-align: center; text-decoration: none; display: inline-block;">
                    <i class="fas fa-external-link-alt"></i> Apply Now
                </a>
                <button class="btn-secondary" style="flex: 1;" onclick="saveScholarship('${s.id}')">
                    <i class="fas fa-bookmark"></i> Save
                </button>
            </div>
            
            <!-- Show link preview (optional) -->
            ${s.link && s.link !== '#' ? `
                <p style="font-size: 11px; color: #999; margin-top: 8px; text-align: right;">
                    <i class="fas fa-link"></i> ${s.link.substring(0, 40)}${s.link.length > 40 ? '...' : ''}
                </p>
            ` : ''}
        </div>
    `).join('');
}
// Search scholarships
function searchAllScholarships() {
    const searchTerm = document.getElementById('scholarship-search').value.toLowerCase();
    const filter = document.getElementById('scholarship-filter').value;
    
    let filtered = allScholarships;
    
    // Apply search
    if (searchTerm) {
        filtered = filtered.filter(s => 
            s.name.toLowerCase().includes(searchTerm) ||
            s.provider.toLowerCase().includes(searchTerm) ||
            (s.description && s.description.toLowerCase().includes(searchTerm))
        );
    }
    
    // Apply filters
    if (filter === 'merit') {
        filtered = filtered.filter(s => s.merit_based);
    } else if (filter === 'need') {
        filtered = filtered.filter(s => s.need_based);
    } else if (filter === 'active') {
        filtered = filtered.filter(s => s.status === 'active');
    }
    
    displayAllScholarships(filtered);
}

// ============================================
// ALL WORK-STUDY VIEW
// ============================================

// Load all work-study programs
async function loadAllWorkStudy() {
    const container = document.getElementById('all-workstudy-list');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading work-study programs...</p></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/work-study/opportunities`, {
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        });
        
        const data = await response.json();
        
        if (data.success) {
            allWorkStudy = data.opportunities || [];
            displayAllWorkStudy(allWorkStudy);
        } else {
            container.innerHTML = '<p class="empty-state">Failed to load work-study programs</p>';
        }
    } catch (error) {
        console.error('Error loading work-study:', error);
        container.innerHTML = '<p class="empty-state">Error loading work-study programs</p>';
    }
}

// Display all work-study programs
function displayAllWorkStudy(programs) {
    const container = document.getElementById('all-workstudy-list');
    
    if (programs.length === 0) {
        container.innerHTML = '<p class="empty-state">No work-study programs available</p>';
        return;
    }
    
    container.innerHTML = programs.map(p => `
        <div class="card workstudy-card">
            <div class="card-header">
                <i class="fas fa-briefcase" style="font-size: 24px; color: #667eea;"></i>
                <span class="status-badge ${p.status || 'open'}">${p.status || 'open'}</span>
            </div>
            <h3>${p.title}</h3>
            <p class="provider"><i class="fas fa-building"></i> ${p.organization}</p>
            <p class="amount" style="font-size: 24px; font-weight: 700; color: #667eea; margin: 10px 0;">
                ₹${Number(p.stipend).toLocaleString()}/month
            </p>
            <p><i class="fas fa-clock"></i> ${p.hours_per_week} hours/week • ${p.duration_months || 6} months</p>
            <p><i class="fas fa-map-marker-alt"></i> ${p.remote ? 'Remote' : p.location || 'On-site'}</p>
            ${p.required_skills && p.required_skills.length ? 
                `<p><i class="fas fa-code"></i> Skills: ${p.required_skills.join(', ')}</p>` : ''}
            <p><i class="fas fa-calendar"></i> Deadline: ${p.deadline ? new Date(p.deadline).toLocaleDateString() : 'Rolling'}</p>
            <div style="margin-top: 15px;">
                <button class="btn-primary" style="width: 100%;" onclick="applyForWorkStudy('${p.id}')">
                    <i class="fas fa-paper-plane"></i> Apply Now
                </button>
            </div>
        </div>
    `).join('');
}

// Search work-study programs
function searchAllWorkStudy() {
    const searchTerm = document.getElementById('workstudy-search').value.toLowerCase();
    const filter = document.getElementById('workstudy-filter').value;
    
    let filtered = allWorkStudy;
    
    // Apply search
    if (searchTerm) {
        filtered = filtered.filter(p => 
            p.title.toLowerCase().includes(searchTerm) ||
            p.organization.toLowerCase().includes(searchTerm) ||
            (p.required_skills && p.required_skills.some(s => s.toLowerCase().includes(searchTerm)))
        );
    }
    
    // Apply filters
    if (filter === 'remote') {
        filtered = filtered.filter(p => p.remote);
    } else if (filter === 'onsite') {
        filtered = filtered.filter(p => !p.remote);
    } else if (filter === 'high-stipend') {
        filtered = filtered.filter(p => p.stipend >= 20000);
    }
    
    displayAllWorkStudy(filtered);
}

// ============================================
// ENHANCED RECOMMENDATIONS
// ============================================

// Load recommendations (updated to show database matches)


// Display database-matched recommendations
function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendations-container');
    
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p class="empty-state">No matching opportunities found</p>';
        return;
    }
    
    // Separate by type
    const scholarships = recommendations.filter(r => r.type === 'scholarship');
    const workStudy = recommendations.filter(r => r.type === 'work_study');
    
    let html = '';
    
    if (scholarships.length > 0) {
        html += '<h3 style="margin: 20px 0 10px;"><i class="fas fa-award"></i> Matched Scholarships</h3>';
        html += '<div class="recommendations-grid">';
        scholarships.forEach(rec => {
            // Log the link for debugging
            console.log('Scholarship link:', rec.link);
            
            html += `
                <div class="recommendation-card">
                    <div class="recommendation-icon">
                        <i class="fas fa-award"></i>
                    </div>
                    <h3>${rec.name || rec.title}</h3>
                    <p class="provider">${rec.provider || rec.organization}</p>
                    <div class="recommendation-amount">₹${Number(rec.amount || 0).toLocaleString()}</div>
                    <div class="match-score" style="background: #4caf50; color: white; padding: 5px 10px; border-radius: 20px; display: inline-block; margin: 10px 0;">
                        Match: ${rec.match_score}%
                    </div>
                    ${rec.reasons && rec.reasons.length ? `
                        <div style="text-align: left; margin: 10px 0;">
                            ${rec.reasons.slice(0, 2).map(r => `<p style="font-size: 12px; color: #666;">✓ ${r}</p>`).join('')}
                        </div>
                    ` : ''}
                    <!-- Apply Now button with link - opens in new tab -->
                    <a href="${rec.link || '#'}" target="_blank" rel="noopener noreferrer" 
                       class="btn-primary" style="width: 100%; text-align: center; text-decoration: none; display: inline-block; box-sizing: border-box;">
                        <i class="fas fa-external-link-alt"></i> Apply Now
                    </a>
                </div>
            `;
        });
        html += '</div>';
    }
    
    if (workStudy.length > 0) {
        html += '<h3 style="margin: 30px 0 10px;"><i class="fas fa-briefcase"></i> Matched Work-Study Programs</h3>';
        html += '<div class="recommendations-grid">';
        workStudy.forEach(rec => {
            html += `
                <div class="recommendation-card">
                    <div class="recommendation-icon">
                        <i class="fas fa-briefcase"></i>
                    </div>
                    <h3>${rec.title}</h3>
                    <p class="provider">${rec.organization}</p>
                    <div class="recommendation-amount">₹${Number(rec.stipend).toLocaleString()}/month</div>
                    <p>${rec.hours_per_week} hours/week</p>
                    <div class="match-score" style="background: #4caf50; color: white; padding: 5px 10px; border-radius: 20px; display: inline-block; margin: 10px 0;">
                        Match: ${rec.match_score}%
                    </div>
                    <button class="btn-primary" style="width: 100%;" onclick="applyForWorkStudy('${rec.id}')">
                        <i class="fas fa-paper-plane"></i> Apply Now
                    </button>
                </div>
            `;
        });
        html += '</div>';
    }
    
    container.innerHTML = html;
}

// Rule-based recommendations fallback
function displayRuleBasedRecommendations(recommendations) {
    const container = document.getElementById('recommendations-container');
    
    container.innerHTML = `
        <div style="background: #fff3e0; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <i class="fas fa-info-circle"></i> Showing rule-based recommendations. Complete profile for AI-matched results.
        </div>
        <div class="recommendations-grid">
            ${recommendations.map(rec => `
                <div class="recommendation-card">
                    <div class="recommendation-icon">
                        <i class="fas ${rec.icon || 'fa-gift'}"></i>
                    </div>
                    <h3>${rec.type}</h3>
                    <div class="recommendation-amount">₹${(rec.amount || 0).toLocaleString()}</div>
                    <p class="recommendation-desc">${rec.description || ''}</p>
                    <button class="btn-primary" style="width: 100%;" onclick="applyForOpportunity('${rec.type}')">
                        Apply Now
                    </button>
                </div>
            `).join('')}
        </div>
    `;
}

// ============================================
// APPLICATION FUNCTIONS
// ============================================

// Apply for scholarship
async function applyForScholarship(scholarshipId) {
    try {
        const token = localStorage.getItem('token');
        
        const response = await fetch(`${API_BASE_URL}/student/${currentUserId}/apply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                opportunity_id: scholarshipId,
                type: 'scholarship',
                message: 'Applying for this scholarship opportunity'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Application submitted successfully!', 'success');
        } else {
            showNotification('Failed to submit application', 'error');
        }
    } catch (error) {
        console.error('Error applying:', error);
        showNotification('Error submitting application', 'error');
    }
}

// Apply for work-study
async function applyForWorkStudy(workStudyId) {
    try {
        const token = localStorage.getItem('token');
        
        const response = await fetch(`${API_BASE_URL}/work-study/opportunities/${workStudyId}/apply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                message: 'Interested in this work-study position'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Application submitted successfully!', 'success');
        } else {
            showNotification('Failed to submit application', 'error');
        }
    } catch (error) {
        console.error('Error applying:', error);
        showNotification('Error submitting application', 'error');
    }
}

// Check eligibility
async function checkEligibility(scholarshipId) {
    showNotification('Checking eligibility...', 'info');
    // This would call an API endpoint to check eligibility
    setTimeout(() => {
        showNotification('You are eligible for this scholarship!', 'success');
    }, 1000);
}

// Save scholarship for later
function saveScholarship(scholarshipId) {
    let saved = JSON.parse(localStorage.getItem('savedScholarships') || '[]');
    if (!saved.includes(scholarshipId)) {
        saved.push(scholarshipId);
        localStorage.setItem('savedScholarships', JSON.stringify(saved));
        showNotification('Scholarship saved!', 'success');
    } else {
        showNotification('Already saved', 'info');
    }
}

// ============================================
// UPDATE TAB SWITCHING
// ============================================

// Update the tab switching to include new tabs
document.querySelectorAll('.nav-menu li').forEach(item => {
    item.addEventListener('click', function() {
        document.querySelectorAll('.nav-menu li').forEach(li => li.classList.remove('active'));
        this.classList.add('active');
        
        const tabId = this.dataset.tab;
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        
        // Load tab data
        if (tabId === 'recommendations') {
            loadRecommendations();
        } else if (tabId === 'applications') {
            loadApplications();
        } else if (tabId === 'crowdfunding') {
            loadCampaigns();
        } else if (tabId === 'profile') {
            loadProfile();
        } else if (tabId === 'all-scholarships') {
            loadAllScholarships();
        } else if (tabId === 'all-workstudy') {
            loadAllWorkStudy();
        }
    });
});