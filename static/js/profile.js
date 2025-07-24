$(document).ready(function() {
    const profileDiv = $('#profileData');
    const inviteForm = $('#inviteForm');
    const inviteMessage = $('#inviteMessage');
    
    if (profileDiv.length) {
        loadProfile();
    }
    
    if (inviteForm.length) {
        inviteForm.submit(function(e) {
            e.preventDefault();
            const inviteCode = $('#invite_code').val().trim();
            
            inviteMessage.empty();
            
            // Валидация
            if (!inviteCode) {
                showMessage(inviteMessage, 'warning', 'Пожалуйста, введите инвайт-код');
                return;
            }
            
            showMessage(inviteMessage, 'info', 'Активация инвайт-кода...');
            
            $.ajax({
                url: '/api/profile/activate-invite/',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                data: JSON.stringify({
                    invite_code: inviteCode
                }),
                success: function(response) {
                    showMessage(inviteMessage, 'success', 'Инвайт-код успешно активирован!');
                    $('#inviteForm')[0].reset();
                    loadProfile();
                },
                error: function(xhr) {
                    const errorMessage = extractInviteErrorMessage(xhr);
                    showMessage(inviteMessage, 'danger', errorMessage);
                }
            });
        });
    }
});

function loadProfile() {
    const profileDiv = $('#profileData');
    profileDiv.html(`
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
            <p class="mt-2">Загрузка профиля...</p>
        </div>
    `);
    
    $.ajax({
        url: '/api/profile/',
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(data) {
            renderProfile(data, profileDiv);
        },
        error: function(xhr) {
            if (xhr.status === 401) {
                window.location.href = '/';
            } else {
                profileDiv.html(`
                    <div class="alert alert-danger fade-in">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Ошибка загрузки профиля
                    </div>
                `);
            }
        }
    });
}

function renderProfile(data, container) {
    let profileHtml = `
        <div class="row">
            <div class="col-md-6">
                <p>
                    <strong><i class="fas fa-mobile-alt me-2"></i>Телефон:</strong> 
                    ${data.phone_number}
                </p>
                <p>
                    <strong><i class="fas fa-id-card me-2"></i>Ваш инвайт-код:</strong> 
                    <span class="badge bg-primary">${data.invite_code}</span>
                </p>
                <p>
                    <strong><i class="fas fa-link me-2"></i>Активированный инвайт-код:</strong> 
                    ${data.activated_invite_code ? 
                      '<span class="badge bg-success">' + data.activated_invite_code + '</span>' : 
                      '<span class="badge bg-secondary">Не активирован</span>'}
                </p>
            </div>
            <div class="col-md-6">
                <p>
                    <strong><i class="fas fa-calendar-alt me-2"></i>Дата регистрации:</strong> 
                    ${new Date(data.created_at).toLocaleDateString('ru-RU')}
                </p>
                <p>
                    <strong><i class="fas fa-users me-2"></i>Количество рефералов:</strong> 
                    ${data.referrals.length}
                </p>
            </div>
        </div>
        
        <hr class="my-4">
        
        <h5>
            <i class="fas fa-user-friends me-2"></i>Ваши рефералы (${data.referrals.length})
        </h5>
    `;
    
    if (data.referrals.length > 0) {
        profileHtml += '<ul class="list-group">';
        data.referrals.forEach(function(referral) {
            profileHtml += `
                <li class="list-group-item">
                    <i class="fas fa-user me-2"></i>${referral}
                </li>
            `;
        });
        profileHtml += '</ul>';
    } else {
        profileHtml += `
            <div class="alert alert-info fade-in">
                <i class="fas fa-info-circle me-2"></i>
                У вас пока нет рефералов. Поделитесь своим инвайт-кодом с друзьями!
            </div>
        `;
    }
    
    container.html(profileHtml);
}

function showMessage(container, type, message) {
    const icons = {
        'info': 'fas fa-spinner fa-spin',
        'success': 'fas fa-check-circle',
        'warning': 'fas fa-exclamation-triangle',
        'danger': 'fas fa-exclamation-circle'
    };
    
    const icon = icons[type] || 'fas fa-info-circle';
    container.html(`
        <div class="alert alert-${type} fade-in">
            <i class="${icon} me-2"></i>${message}
        </div>
    `);
}

function extractInviteErrorMessage(xhr) {
    if (xhr.responseJSON) {
        if (xhr.responseJSON.message) {
            return xhr.responseJSON.message;
        }
        if (xhr.responseJSON.error) {
            return xhr.responseJSON.error;
        }
        if (xhr.responseJSON.detail) {
            return xhr.responseJSON.detail;
        }
        for (const key in xhr.responseJSON) {
            if (Array.isArray(xhr.responseJSON[key]) && xhr.responseJSON[key].length > 0) {
                return xhr.responseJSON[key][0];
            }
            if (typeof xhr.responseJSON[key] === 'string') {
                return xhr.responseJSON[key];
            }
        }
    }
    return 'Ошибка активации инвайт-кода';
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}