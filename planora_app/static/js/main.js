
// main.js - Main JavaScript file for your Flask app
// Location: static/js/main.js

// ============================================
// INITIALIZE ON PAGE LOAD
// ============================================

document.addEventListener('DOMContentLoaded', function() {
  console.log('App initialized');
  
  // Initialize Pomodoro Timer
  if (typeof window.initPomodoroTimer === 'function') {
    window.initPomodoroTimer();
  }
  
  // Setup floating indicator for all pages
  setupFloatingIndicator();
  
  // Initialize AJAX navigation if you use it
  initAjaxNavigation();
});

// ============================================
// FLOATING INDICATOR UPDATES
// ============================================

function setupFloatingIndicator() {
  // Ensure timer is initialized first
  if (!window.pomodoroTimer) {
    // If timer doesn't exist yet, try to initialize it
    if (typeof window.initPomodoroTimer === 'function') {
      window.initPomodoroTimer();
    }
    
    // If still no timer, wait and try again
    if (!window.pomodoroTimer) {
      setTimeout(setupFloatingIndicator, 100);
      return;
    }
  }

  // Register callback once
  if (!window._floatingIndicatorRegistered) {
    window.pomodoroTimer.onTick(updateFloatingIndicator);
    window._floatingIndicatorRegistered = true;
  }

  // Initial update immediately
  updateFloatingIndicator();
  
  // Also update every second to ensure it stays synced
  if (!window._floatingIndicatorInterval) {
    window._floatingIndicatorInterval = setInterval(updateFloatingIndicator, 1000);
  }
}

function updateFloatingIndicator() {
  const indicator = document.getElementById('floatingTimerIndicator');
  const timeEl = document.getElementById('floatingTimerTime');
  const statusEl = document.getElementById('floatingTimerStatus');

  if (!indicator || !window.pomodoroTimer) return;

  const timer = window.pomodoroTimer;

  // Show indicator only if timer is running or paused
  if (timer.isRunning || timer.isPaused) {
    indicator.classList.add('active');

    // Update time
    const minutes = Math.floor(timer.timeRemaining / 60);
    const seconds = timer.timeRemaining % 60;
    timeEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

    // Update status and style
    if (timer.isPaused) {
      statusEl.textContent = 'Paused';
      indicator.className = 'floating-timer-indicator active paused-mode';
    } else if (timer.isBreak) {
      statusEl.textContent = 'Break Time';
      indicator.className = 'floating-timer-indicator active break-mode';
    } else {
      statusEl.textContent = `Focus - Cycle ${timer.currentCycle}/${timer.totalCycles}`;
      indicator.className = 'floating-timer-indicator active';
    }
  } else {
    indicator.classList.remove('active');
  }
}

function navigateToTimer() {
  window.location.href = '/timer';
}

// Make navigateToTimer available globally
window.navigateToTimer = navigateToTimer;

// ============================================
// AJAX NAVIGATION (Optional - only if you use AJAX)
// ============================================

function initAjaxNavigation() {
  // Intercept links with data-ajax attribute
  document.addEventListener('click', function(e) {
    const link = e.target.closest('a[data-ajax]');
    if (link && link.href) {
      e.preventDefault();
      loadPageViaAjax(link.href);
    }
  });
}

function loadPageViaAjax(url) {
  fetch(url)
    .then(response => response.text())
    .then(html => {
      const mainContent = document.getElementById('main-content');
      if (mainContent) {
        mainContent.innerHTML = html;
        
        // Reinitialize timer and floating indicator after AJAX page load
        if (typeof window.initPomodoroTimer === 'function') {
          window.initPomodoroTimer();
        }
        setupFloatingIndicator();
        
        // Update browser history
        history.pushState({}, '', url);
      }
    })
    .catch(error => {
      console.error('Page load error:', error);
    });
}

// ============================================
// DEBUG HELPERS
// ============================================

// Check timer status from console
window.checkTimerStatus = function() {
  if (window.pomodoroTimer) {
    console.log('Timer Status:', {
      isRunning: window.pomodoroTimer.isRunning,
      isPaused: window.pomodoroTimer.isPaused,
      timeRemaining: window.pomodoroTimer.timeRemaining,
      currentCycle: window.pomodoroTimer.currentCycle,
      cyclesCompleted: window.pomodoroTimer.cyclesCompleted,
      totalStudyTime: Math.floor(window.pomodoroTimer.totalStudyTime / 60) + ' minutes'
    });
  } else {
    console.log('Timer not initialized');
  }
};

// Reset timer state from console
window.resetTimerState = function() {
  if (confirm('This will clear all timer data and reload the page. Continue?')) {
    localStorage.removeItem('pomodoroTimerState');
    localStorage.removeItem('pomodoroModalPending');
    console.log('Timer state cleared');
    location.reload();
  }
};

console.log('Main.js loaded. Debug commands available:');
console.log('  - window.checkTimerStatus() : Check timer status');
console.log('  - window.resetTimerState()   : Reset timer completely');






// // main.js - Main JavaScript file for your Flask app
// // Location: static/js/main.js

// // ============================================
// // INITIALIZE ON PAGE LOAD
// // ============================================

// document.addEventListener('DOMContentLoaded', function() {
//   console.log('App initialized');
  
//   // Initialize Pomodoro Timer
//   if (typeof window.initPomodoroTimer === 'function') {
//     window.initPomodoroTimer();
//   }
  
//   // Setup floating indicator for all pages
//   setupFloatingIndicator();
  
//   // Initialize AJAX navigation if you use it
//   initAjaxNavigation();
// });

// // ============================================
// // FLOATING INDICATOR UPDATES
// // ============================================

// function setupFloatingIndicator() {
//   if (!window.pomodoroTimer) return;

//   // Register callback once
//   if (!window._floatingIndicatorRegistered) {
//     window.pomodoroTimer.onTick(updateFloatingIndicator);
//     window._floatingIndicatorRegistered = true;
//   }

//   // Initial update immediately
//   updateFloatingIndicator();
// }

// function updateFloatingIndicator() {
//   const indicator = document.getElementById('floatingTimerIndicator');
//   const timeEl = document.getElementById('floatingTimerTime');
//   const statusEl = document.getElementById('floatingTimerStatus');

//   if (!indicator || !window.pomodoroTimer) return;

//   const timer = window.pomodoroTimer;

//   // Show indicator only if timer is running or paused
//   if (timer.isRunning || timer.isPaused) {
//     indicator.classList.add('active');

//     // Update time
//     const minutes = Math.floor(timer.timeRemaining / 60);
//     const seconds = timer.timeRemaining % 60;
//     timeEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

//     // Update status and style
//     if (timer.isPaused) {
//       statusEl.textContent = 'Paused';
//       indicator.className = 'floating-timer-indicator active paused-mode';
//     } else if (timer.isBreak) {
//       statusEl.textContent = 'Break Time';
//       indicator.className = 'floating-timer-indicator active break-mode';
//     } else {
//       statusEl.textContent = `Focus - Cycle ${timer.currentCycle}/${timer.totalCycles}`;
//       indicator.className = 'floating-timer-indicator active';
//     }
//   } else {
//     indicator.classList.remove('active');
//   }
// }

// function navigateToTimer() {
//   window.location.href = '/timer';
// }

// // Make navigateToTimer available globally
// window.navigateToTimer = navigateToTimer;

// // ============================================
// // AJAX NAVIGATION (Optional - only if you use AJAX)
// // ============================================

// function initAjaxNavigation() {
//   // Intercept links with data-ajax attribute
//   document.addEventListener('click', function(e) {
//     const link = e.target.closest('a[data-ajax]');
//     if (link && link.href) {
//       e.preventDefault();
//       loadPageViaAjax(link.href);
//     }
//   });
// }

// function loadPageViaAjax(url) {
//   fetch(url)
//     .then(response => response.text())
//     .then(html => {
//       const mainContent = document.getElementById('main-content');
//       if (mainContent) {
//         mainContent.innerHTML = html;
        
//         // Reinitialize timer and floating indicator after AJAX page load
//         if (typeof window.initPomodoroTimer === 'function') {
//           window.initPomodoroTimer();
//         }
//         setupFloatingIndicator();
        
//         // Update browser history
//         history.pushState({}, '', url);
//       }
//     })
//     .catch(error => {
//       console.error('Page load error:', error);
//     });
// }

// // ============================================
// // DEBUG HELPERS
// // ============================================

// // Check timer status from console
// window.checkTimerStatus = function() {
//   if (window.pomodoroTimer) {
//     console.log('Timer Status:', {
//       isRunning: window.pomodoroTimer.isRunning,
//       isPaused: window.pomodoroTimer.isPaused,
//       timeRemaining: window.pomodoroTimer.timeRemaining,
//       currentCycle: window.pomodoroTimer.currentCycle,
//       cyclesCompleted: window.pomodoroTimer.cyclesCompleted,
//       totalStudyTime: Math.floor(window.pomodoroTimer.totalStudyTime / 60) + ' minutes'
//     });
//   } else {
//     console.log('Timer not initialized');
//   }
// };

// // Reset timer state from console
// window.resetTimerState = function() {
//   if (confirm('This will clear all timer data and reload the page. Continue?')) {
//     localStorage.removeItem('pomodoroTimerState');
//     localStorage.removeItem('pomodoroModalPending');
//     console.log('Timer state cleared');
//     location.reload();
//   }
// };

// console.log('Main.js loaded. Debug commands available:');
// console.log('  - window.checkTimerStatus() : Check timer status');
// console.log('  - window.resetTimerState()   : Reset timer completely');
