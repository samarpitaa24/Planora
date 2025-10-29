// Password validation
document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const signupForm = document.querySelector('#signupForm form');
    
    // Add password validation elements
    if (passwordInput && document.getElementById('signupForm')) {
        // Create validation UI elements
        const validationHTML = `
            <div class="password-strength" id="passwordStrength">
                <div class="strength-bar"></div>
            </div>
            <div class="password-requirements" id="passwordRequirements">
                <p class="requirement" id="lengthReq">
                    <span class="req-icon">✗</span> At least 8 characters
                </p>
                <p class="requirement" id="uppercaseReq">
                    <span class="req-icon">✗</span> One uppercase letter
                </p>
                <p class="requirement" id="lowercaseReq">
                    <span class="req-icon">✗</span> One lowercase letter
                </p>
                <p class="requirement" id="numberReq">
                    <span class="req-icon">✗</span> One number
                </p>
                <p class="requirement" id="specialReq">
                    <span class="req-icon">✗</span> One special character (!@#$%^&*)
                </p>
            </div>
        `;
        
        passwordInput.insertAdjacentHTML('afterend', validationHTML);
        
        // Add password match indicator
        const matchHTML = '<span class="password-match-message" id="passwordMatch"></span>';
        confirmPasswordInput.insertAdjacentHTML('afterend', matchHTML);
        
        passwordInput.addEventListener('input', function() {
            validatePassword(this.value);
        });
        
        confirmPasswordInput.addEventListener('input', function() {
            checkPasswordMatch();
        });
        
        signupForm.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
            }
        });
    }
});

function validatePassword(password) {
    const lengthReq = document.getElementById('lengthReq');
    const uppercaseReq = document.getElementById('uppercaseReq');
    const lowercaseReq = document.getElementById('lowercaseReq');
    const numberReq = document.getElementById('numberReq');
    const specialReq = document.getElementById('specialReq');
    const strengthBar = document.querySelector('.strength-bar');
    
    let strength = 0;
    
    // Check length
    if (password.length >= 8) {
        lengthReq.classList.add('valid');
        strength++;
    } else {
        lengthReq.classList.remove('valid');
    }
    
    // Check uppercase
    if (/[A-Z]/.test(password)) {
        uppercaseReq.classList.add('valid');
        strength++;
    } else {
        uppercaseReq.classList.remove('valid');
    }
    
    // Check lowercase
    if (/[a-z]/.test(password)) {
        lowercaseReq.classList.add('valid');
        strength++;
    } else {
        lowercaseReq.classList.remove('valid');
    }
    
    // Check number
    if (/[0-9]/.test(password)) {
        numberReq.classList.add('valid');
        strength++;
    } else {
        numberReq.classList.remove('valid');
    }
    
    // Check special character
    if (/[!@#$%^&*]/.test(password)) {
        specialReq.classList.add('valid');
        strength++;
    } else {
        specialReq.classList.remove('valid');
    }
    
    // Update strength bar
    strengthBar.className = 'strength-bar';
    if (strength === 0) {
        strengthBar.style.width = '0%';
    } else if (strength <= 2) {
        strengthBar.style.width = '40%';
        strengthBar.style.background = '#ff4444';
    } else if (strength <= 4) {
        strengthBar.style.width = '70%';
        strengthBar.style.background = '#ffaa00';
    } else {
        strengthBar.style.width = '100%';
        strengthBar.style.background = '#00C851';
    }
    
    checkPasswordMatch();
}

function checkPasswordMatch() {
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    const matchMessage = document.getElementById('passwordMatch');
    
    if (!confirmPassword || !matchMessage) return;
    
    if (confirmPassword.value === '') {
        matchMessage.textContent = '';
        matchMessage.className = 'password-match-message';
        return;
    }
    
    if (password.value === confirmPassword.value) {
        matchMessage.textContent = '✓ Passwords match';
        matchMessage.className = 'password-match-message match';
    } else {
        matchMessage.textContent = '✗ Passwords do not match';
        matchMessage.className = 'password-match-message no-match';
    }
}

function validateForm() {
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    
    // Check all requirements
    const isValidLength = password.length >= 8;
    const hasUppercase = /[A-Z]/.test(password);
    const hasLowercase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecial = /[!@#$%^&*]/.test(password);
    
    if (!isValidLength || !hasUppercase || !hasLowercase || !hasNumber || !hasSpecial) {
        alert('Please meet all password requirements');
        return false;
    }
    
    if (password !== confirmPassword) {
        alert('Passwords do not match');
        return false;
    }
    
    return true;
}

function toggleForms(formType) {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');

    if (formType === 'signup') {
        loginForm.classList.remove('active');
        setTimeout(() => {
            signupForm.classList.add('active');
        }, 100);
    } else {
        signupForm.classList.remove('active');
        setTimeout(() => {
            loginForm.classList.add('active');
        }, 100);
    }
}

// Check URL hash to show appropriate form
window.addEventListener('DOMContentLoaded', () => {
    const hash = window.location.hash;
    if (hash === '#signup') {
        toggleForms('signup');
    }
});

// -------------------------------------------------------------------------------------------

function toggleForms(form) {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");

    if (form === "signup") {
        loginForm.classList.remove("active");
        signupForm.classList.add("active");
    } else {
        signupForm.classList.remove("active");
        loginForm.classList.add("active");
    }
}