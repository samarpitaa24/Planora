/* planora_app/static/js/settings.js */

document.addEventListener("DOMContentLoaded", function () {
  console.log("Settings script initialized.");

  // Helper function to display alerts with smooth fade-in
  function showAlert(alertEl, message, isSuccess = true) {
    if (!alertEl) return;
    alertEl.textContent = message;
    alertEl.className = "settings-alert " + (isSuccess ? "settings-alert-success" : "settings-alert-error");
    alertEl.style.display = "block";
    alertEl.style.opacity = "0";
    
    // Quick fade-in animation
    setTimeout(() => {
      alertEl.style.transition = "opacity 0.2s ease";
      alertEl.style.opacity = "1";
    }, 10);

    // Auto-hide after 5 seconds
    if (alertEl.timeoutId) {
      clearTimeout(alertEl.timeoutId);
    }
    alertEl.timeoutId = setTimeout(() => {
      alertEl.style.opacity = "0";
      setTimeout(() => {
        alertEl.style.display = "none";
      }, 200);
    }, 5000);
  }

  // Helper to manage button loading states
  function setBtnLoading(button, isLoading = true, originalText = "Save") {
    if (!button) return;
    button.disabled = isLoading;
    if (isLoading) {
      button.innerHTML = '<span class="loading-spinner">Saving...</span>';
    } else {
      button.innerHTML = originalText;
    }
  }

  // ============================================
  // PROFILE DETAILS FORM SUBMIT (AJAX)
  // ============================================
  const profileForm = document.getElementById("profile-details-form");
  const profileAlert = document.getElementById("profile-alert");

  if (profileForm) {
    profileForm.addEventListener("submit", function (e) {
      e.preventDefault();
      
      const submitBtn = profileForm.querySelector('button[type="submit"]');
      setBtnLoading(submitBtn, true, "Save Profile Info");

      const formData = new FormData(profileForm);

      fetch("/settings/update-profile", {
        method: "POST",
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        setBtnLoading(submitBtn, false, "Save Profile Info");
        if (data.success) {
          showAlert(profileAlert, data.message, true);
          
          // Dynamically update default avatar initials if placeholder is present
          const fullNameVal = document.getElementById("full_name").value.trim();
          const usernameVal = document.getElementById("username").value.trim();
          const placeholder = document.getElementById("avatar-preview-placeholder");
          if (placeholder) {
            const letter = (fullNameVal || usernameVal || "U")[0].toUpperCase();
            placeholder.textContent = letter;
          }
        } else {
          showAlert(profileAlert, data.error || "Failed to update profile.", false);
        }
      })
      .catch(err => {
        console.error("Profile update error:", err);
        setBtnLoading(submitBtn, false, "Save Profile Info");
        showAlert(profileAlert, "An unexpected network error occurred.", false);
      });
    });
  }

  // ============================================
  // POMODORO SETTINGS FORM SUBMIT (AJAX)
  // ============================================
  const pomodoroForm = document.getElementById("pomodoro-settings-form");
  const pomodoroAlert = document.getElementById("pomodoro-alert");

  if (pomodoroForm) {
    pomodoroForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const submitBtn = pomodoroForm.querySelector('button[type="submit"]');
      setBtnLoading(submitBtn, true, "Save Timer Options");

      const formData = new FormData(pomodoroForm);

      fetch("/settings/update-pomodoro", {
        method: "POST",
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        setBtnLoading(submitBtn, false, "Save Timer Options");
        if (data.success) {
          showAlert(pomodoroAlert, data.message, true);
        } else {
          showAlert(pomodoroAlert, data.error || "Failed to update timer options.", false);
        }
      })
      .catch(err => {
        console.error("Timer update error:", err);
        setBtnLoading(submitBtn, false, "Save Timer Options");
        showAlert(pomodoroAlert, "An unexpected network error occurred.", false);
      });
    });
  }

  // ============================================
  // PASSWORD SECURITY FORM SUBMIT (AJAX)
  // ============================================
  const passwordForm = document.getElementById("change-password-form");
  const passwordAlert = document.getElementById("password-alert");

  if (passwordForm) {
    passwordForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const newPass = document.getElementById("new_password").value;
      const confirmPass = document.getElementById("confirm_password").value;

      if (newPass !== confirmPass) {
        showAlert(passwordAlert, "Passwords do not match.", false);
        return;
      }

      const submitBtn = passwordForm.querySelector('button[type="submit"]');
      setBtnLoading(submitBtn, true, "Update Password");

      const formData = new FormData(passwordForm);

      fetch("/settings/change-password", {
        method: "POST",
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        setBtnLoading(submitBtn, false, "Update Password");
        if (data.success) {
          showAlert(passwordAlert, data.message, true);
          passwordForm.reset();
        } else {
          showAlert(passwordAlert, data.error || "Failed to update password.", false);
        }
      })
      .catch(err => {
        console.error("Password update error:", err);
        setBtnLoading(submitBtn, false, "Update Password");
        showAlert(passwordAlert, "An unexpected network error occurred.", false);
      });
    });
  }

  // ============================================
  // PROFILE AVATAR ACTIONS (UPLOAD & REMOVE)
  // ============================================
  const avatarInput = document.getElementById("avatar-input");
  const removeAvatarBtn = document.getElementById("remove-avatar-btn");
  const wrapper = document.querySelector(".avatar-circle-wrapper");

  if (avatarInput) {
    avatarInput.addEventListener("change", function () {
      const file = avatarInput.files[0];
      if (!file) return;

      // Client-side file type check
      const validTypes = ["image/jpeg", "image/png", "image/jpg"];
      if (!validTypes.includes(file.type)) {
        showAlert(profileAlert, "Please select a valid image file (JPG or PNG).", false);
        avatarInput.value = ""; // Clear file
        return;
      }

      // Client-side size check (2 MB = 2 * 1024 * 1024 bytes)
      if (file.size > 2 * 1024 * 1024) {
        showAlert(profileAlert, "Image size exceeds 2 MB limit.", false);
        avatarInput.value = ""; // Clear file
        return;
      }

      const formData = new FormData();
      formData.append("avatar", file);

      // Show temporary uploading text or style
      const placeholder = document.getElementById("avatar-preview-placeholder");
      const img = document.getElementById("avatar-preview-img");
      
      fetch("/settings/update-avatar", {
        method: "POST",
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        avatarInput.value = ""; // Reset file input
        if (data.success) {
          showAlert(profileAlert, data.message, true);
          
          // Re-render image element and remove placeholder
          if (img) {
            img.src = data.avatar_url;
            img.style.display = "block";
          } else {
            // Create image element dynamically
            const newImg = document.createElement("img");
            newImg.id = "avatar-preview-img";
            newImg.src = data.avatar_url;
            newImg.alt = "Profile Picture";
            newImg.className = "avatar-image";
            
            if (placeholder) {
              placeholder.remove();
            }
            wrapper.appendChild(newImg);
          }
          
          // Show the remove button
          if (removeAvatarBtn) {
            removeAvatarBtn.style.display = "inline-block";
          }
        } else {
          showAlert(profileAlert, data.error || "Failed to upload photo.", false);
        }
      })
      .catch(err => {
        console.error("Avatar upload error:", err);
        avatarInput.value = "";
        showAlert(profileAlert, "An unexpected network error occurred during upload.", false);
      });
    });
  }

  if (removeAvatarBtn) {
    removeAvatarBtn.addEventListener("click", function () {
      if (!confirm("Are you sure you want to remove your profile picture?")) {
        return;
      }

      fetch("/settings/remove-avatar", {
        method: "POST"
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showAlert(profileAlert, data.message, true);
          
          // Remove preview image
          const img = document.getElementById("avatar-preview-img");
          if (img) {
            img.remove();
          }

          // Show initials placeholder
          const placeholder = document.getElementById("avatar-preview-placeholder");
          if (!placeholder) {
            const newPlaceholder = document.createElement("div");
            newPlaceholder.id = "avatar-preview-placeholder";
            newPlaceholder.className = "avatar-placeholder";
            
            const fullNameVal = document.getElementById("full_name").value.trim();
            const usernameVal = document.getElementById("username").value.trim();
            const letter = (fullNameVal || usernameVal || "U")[0].toUpperCase();
            newPlaceholder.textContent = letter;
            
            wrapper.appendChild(newPlaceholder);
          }
          
          // Hide remove button
          removeAvatarBtn.style.display = "none";
        } else {
          showAlert(profileAlert, data.error || "Failed to remove profile picture.", false);
        }
      })
      .catch(err => {
        console.error("Avatar remove error:", err);
        showAlert(profileAlert, "An unexpected network error occurred.", false);
      });
    });
  }
});
