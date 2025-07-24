$(document).ready(function() {
    const urlParams = new URLSearchParams(window.location.search);
    const phoneNumber = urlParams.get('phone');
    const phoneNumberDisplay = $('#phoneNumberDisplay');
    const codeForm = $('#codeForm');
    const messageDiv = $('#message');
    
    if (phoneNumberDisplay.length) {
        if (phoneNumber) {
            phoneNumberDisplay.html(`
                <div class="alert alert-info fade-in">
                    <i class="fas fa-mobile-alt me-2"></i>
                    Код отправлен на номер: <strong>${phoneNumber}</strong>
                </div>
            `);
            $('#codeForm').prepend(`<input type="hidden" id="phone_number" value="${phoneNumber}">`);
        } else {
            phoneNumberDisplay.html(`
                <div class="alert alert-warning fade-in">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Номер телефона не найден. Пожалуйста, <a href="/">начните сначала</a>.
                </div>
            `);
            if ($('button[type="submit"]').length) {
                $('button[type="submit"]').prop('disabled', true);
            }
        }
    }
    
    if (codeForm.length) {
        codeForm.submit(function(e) {
            e.preventDefault();
            const phoneNumber = $('#phone_number').val();
            const code = $('#code').val().trim();
            
            messageDiv.empty();
            
            if (!code || code.length !== 4) {
                showMessage(messageDiv, 'warning', 'Код должен состоять из 4 символов');
                return;
            }
            
            showMessage(messageDiv, 'info', 'Проверка кода...');
            
            $.ajax({
                url: '/api/auth/verify-code/',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                data: JSON.stringify({
                    phone_number: phoneNumber,
                    code: code
                }),
                success: function(response) {
                    const userType = response.is_new_user ? 'нового' : 'существующего';
                    showMessage(messageDiv, 'success', `Аутентификация успешна! Добро пожаловать, ${userType} пользователь.`);
                    setTimeout(function() {
                        window.location.href = '/profile/';
                    }, 2000);
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
    return 'Ошибка при проверке кода';
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