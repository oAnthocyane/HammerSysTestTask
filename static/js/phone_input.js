$(document).ready(function() {
    const phoneForm = $('#phoneForm');
    const messageDiv = $('#message');
    
    if (phoneForm.length) {
        phoneForm.submit(function(e) {
            e.preventDefault();
            const phoneNumber = $('#phone_number').val().trim();
            
            messageDiv.empty();
            
            if (!phoneNumber.startsWith('+')) {
                showMessage(messageDiv, 'warning', 'Номер телефона должен начинаться с \'+\'');
                return;
            }
            
            if (phoneNumber.length < 10) {
                showMessage(messageDiv, 'warning', 'Номер телефона слишком короткий');
                return;
            }
            
            showMessage(messageDiv, 'info', 'Отправка кода...');
            
            $.ajax({
                url: '/api/auth/send-code/',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                data: JSON.stringify({
                    phone_number: phoneNumber
                }),
                success: function(response) {
                let successMessage = response.message;
                if (response.code) {
                    successMessage += `<br><strong>Тестовый код:</strong> <span class="badge bg-success">${response.code}</span>`;
                    successMessage += '<br><small class="text-muted">В реальной системе код был бы отправлен по SMS</small>';
                }
                showMessage(messageDiv, 'success', successMessage);
                setTimeout(function() {
                    window.location.href = '/code-input/?phone=' + encodeURIComponent(phoneNumber);
                }, 3000);
            },
                            error: function(xhr) {
                    const errorMessage = extractErrorMessage(xhr);
                    showMessage(messageDiv, 'danger', errorMessage);
                }
            });
        });
    }
});

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

function extractErrorMessage(xhr) {
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
    return 'Ошибка при отправке кода';
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