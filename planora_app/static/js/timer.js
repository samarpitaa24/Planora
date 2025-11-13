
// timer.js - Persistent Pomodoro Timer Implementation with Cross-Route Support

class PomodoroTimer {
  constructor() {
    // Timer state
    this.isRunning = false;
    this.isPaused = false;
    this.isBreak = false;
    this.currentCycle = 0;
    this.cyclesCompleted = 0;
    this.pauseCount = 0;
    this.totalStudyTime = 0; // in seconds
    this.sessionStartTime = null;
    this.currentPhaseStartTime = null;
    this.pauseStartTime = null;
    
    // Timer settings
    this.totalCycles = 4;
    this.focusTimeMinutes = 20;
    this.breakTimeMinutes = 5;
    this.selectedSubject = '';
    
    // Countdown
    this.timeRemaining = 0; // in seconds
    this.timerInterval = null;
    this.pauseCheckInterval = null;
    
    // Persistence
    this.storageKey = 'pomodoroTimerState';
    this.backgroundInterval = null;
    
    // Callbacks for tick events
    this.onTickCallbacks = [];
    
    // Initialize
    this.restoreState();
    this.initElements();
    this.attachEventListeners();
    this.updateSessionFormat();
    this.loadSubjects();
    this.startBackgroundTimer();
    
    // Sync UI if elements exist
    if (this.countdownEl) {
      this.syncUIWithState();
    }
  }

  // Register a callback for tick events
  onTick(callback) {
    if (typeof callback === 'function') {
      this.onTickCallbacks.push(callback);
    }
  }
  
  initElements() {
    // Timer Display
    this.countdownEl = document.getElementById('countdown');
    this.timerLabelEl = document.getElementById('timerLabel');
    this.cycleIndicatorEl = document.getElementById('cycleIndicator');
    
    // Controls
    this.startBtn = document.getElementById('startBtn');
    this.pauseBtn = document.getElementById('pauseBtn');
    this.resetBtn = document.getElementById('resetBtn');
    this.endBtn = document.getElementById('endBtn');
    
    // Settings
    this.subjectSelect = document.getElementById('subject');
    this.numCyclesSelect = document.getElementById('numCycles');
    this.focusTimeSelect = document.getElementById('focusTime');
    this.breakTimeSelect = document.getElementById('breakTime');
    this.sessionFormatText = document.getElementById('sessionFormatText');
    this.totalTimeText = document.getElementById('totalTimeText');
    
    // Stats
    this.cyclesCompletedEl = document.getElementById('cyclesCompleted');
    this.totalCyclesDisplayEl = document.getElementById('totalCyclesDisplay');
    this.pauseCountEl = document.getElementById('pauseCount');
    this.sessionStatusEl = document.getElementById('sessionStatus');
    this.studyTimeEl = document.getElementById('studyTime');
    
    // Modals
    this.cycleModal = document.getElementById('cycleModal');
    this.breakModal = document.getElementById('breakModal');
    this.completeModal = document.getElementById('completeModal');
    this.modalOkBtn = document.getElementById('modalOkBtn');
    this.modalSkipBtn = document.getElementById('modalSkipBtn');
    this.breakContinueBtn = document.getElementById('breakContinueBtn');
    this.completeOkBtn = document.getElementById('completeOkBtn');
    this.finalStudyTimeEl = document.getElementById('finalStudyTime');
    
    // Audio
    this.alarmSound = document.getElementById('alarmSound');
    
    // User ID
    const userIdEl = document.getElementById('userId');
    this.userId = userIdEl ? userIdEl.value : this.userId;
  }

  attachEventListeners() {
    if (!this.startBtn) return;
    
    // Control buttons
    this.startBtn.addEventListener('click', () => this.startTimer());
    this.pauseBtn.addEventListener('click', () => this.pauseTimer());
    this.resetBtn.addEventListener('click', () => this.resetTimer());
    this.endBtn.addEventListener('click', () => this.endSession());
    
    // Settings change listeners
    this.numCyclesSelect.addEventListener('change', () => this.updateSessionFormat());
    this.focusTimeSelect.addEventListener('change', () => this.updateSessionFormat());
    this.breakTimeSelect.addEventListener('change', () => this.updateSessionFormat());
    
    // Modal buttons
    this.modalOkBtn.addEventListener('click', () => this.startBreak());
    this.modalSkipBtn.addEventListener('click', () => this.skipBreak());
    this.breakContinueBtn.addEventListener('click', () => this.continueStudying());
    this.completeOkBtn.addEventListener('click', () => this.saveSessionAndReset());
  }

  // ==================== STATE PERSISTENCE ====================
  
  saveState() {
    const state = {
      isRunning: this.isRunning,
      isPaused: this.isPaused,
      isBreak: this.isBreak,
      currentCycle: this.currentCycle,
      cyclesCompleted: this.cyclesCompleted,
      pauseCount: this.pauseCount,
      totalStudyTime: this.totalStudyTime,
      sessionStartTime: this.sessionStartTime ? this.sessionStartTime.toISOString() : null,
      pauseStartTime: this.pauseStartTime ? this.pauseStartTime.toISOString() : null,
      totalCycles: this.totalCycles,
      focusTimeMinutes: this.focusTimeMinutes,
      breakTimeMinutes: this.breakTimeMinutes,
      selectedSubject: this.selectedSubject,
      timeRemaining: this.timeRemaining,
      lastUpdate: new Date().toISOString(),
      userId: this.userId
    };
    
    localStorage.setItem(this.storageKey, JSON.stringify(state));
  }

  restoreState() {
    const saved = localStorage.getItem(this.storageKey);
    if (!saved) return;
    
    try {
      const state = JSON.parse(saved);
      
      // Calculate time elapsed since last update
      const lastUpdate = new Date(state.lastUpdate);
      const now = new Date();
      const elapsedSeconds = Math.floor((now - lastUpdate) / 1000);
      
      // Restore state
      this.isRunning = state.isRunning;
      this.isPaused = state.isPaused;
      this.isBreak = state.isBreak;
      this.currentCycle = state.currentCycle;
      this.cyclesCompleted = state.cyclesCompleted;
      this.pauseCount = state.pauseCount;
      this.totalStudyTime = state.totalStudyTime;
      this.totalCycles = state.totalCycles;
      this.focusTimeMinutes = state.focusTimeMinutes;
      this.breakTimeMinutes = state.breakTimeMinutes;
      this.selectedSubject = state.selectedSubject;
      this.userId = state.userId;
      
      if (state.sessionStartTime) {
        this.sessionStartTime = new Date(state.sessionStartTime);
      }
      
      if (state.pauseStartTime) {
        this.pauseStartTime = new Date(state.pauseStartTime);
      }
      
      // Update time remaining based on elapsed time
      if (this.isRunning && !this.isPaused) {
        this.timeRemaining = Math.max(0, state.timeRemaining - elapsedSeconds);
        
        // Update study time if in focus mode
        if (!this.isBreak) {
          this.totalStudyTime += elapsedSeconds;
        }
      } else {
        this.timeRemaining = state.timeRemaining;
      }
      
      // Check if pause exceeded 10 minutes
      if (this.isPaused && this.pauseStartTime) {
        const pauseDuration = (now - this.pauseStartTime) / 1000;
        if (pauseDuration >= 600) {
          this.endSession(true);
          return;
        }
      }
      
    } catch (error) {
      console.error('Error restoring timer state:', error);
      localStorage.removeItem(this.storageKey);
    }
  }

  clearState() {
    localStorage.removeItem(this.storageKey);
  }

  // ==================== BACKGROUND TIMER ====================
  
  startBackgroundTimer() {
    // Clear any existing background timer
    if (this.backgroundInterval) {
      clearInterval(this.backgroundInterval);
    }
    
    // Run every second to keep timer accurate even when not on timer page
    this.backgroundInterval = setInterval(() => {
      if (this.isRunning && !this.isPaused) {
        this.backgroundTick();
      }
      
      // Check pause duration
      if (this.isPaused && this.pauseStartTime) {
        const now = new Date();
        const pauseDuration = (now - this.pauseStartTime) / 1000;
        if (pauseDuration >= 600) {
          clearInterval(this.backgroundInterval);
          this.endSession(true);
        }
      }
    }, 1000);
  }

  backgroundTick() {
    if (this.timeRemaining > 0) {
      this.timeRemaining--;
      
      // Update study time (only during focus, not break)
      if (!this.isBreak) {
        this.totalStudyTime++;
      }
      
      // Save state
      this.saveState();
      
      // Update UI if on timer page
      if (this.countdownEl) {
        this.updateDisplay();
        this.updateStudyTimeDisplay();
      }
      
      // Call tick callbacks (for floating indicator)
      this.onTickCallbacks.forEach(cb => {
        try {
          cb(this);
        } catch (error) {
          console.error('Error in tick callback:', error);
        }
      });
    } else {
      // Time's up!
      this.handlePhaseComplete();
    }
  }

  syncUIWithState() {
    if (!this.countdownEl) return;
    
    // Update all UI elements to reflect current state
    this.updateDisplay();
    
    if (this.timerLabelEl) {
      this.timerLabelEl.textContent = this.isBreak ? 'Break Time' : 'Focus Time';
    }
    
    if (this.cycleIndicatorEl) {
      if (this.isBreak) {
        this.cycleIndicatorEl.textContent = `Cycle ${this.cyclesCompleted} of ${this.totalCycles} - Break`;
      } else if (this.currentCycle > 0) {
        this.cycleIndicatorEl.textContent = `Cycle ${this.currentCycle} of ${this.totalCycles}`;
      } else {
        this.cycleIndicatorEl.textContent = `Cycle 0 of ${this.totalCycles}`;
      }
    }
    
    if (this.cyclesCompletedEl) {
      this.cyclesCompletedEl.textContent = this.cyclesCompleted;
    }
    
    if (this.totalCyclesDisplayEl) {
      this.totalCyclesDisplayEl.textContent = this.totalCycles;
    }
    
    if (this.pauseCountEl) {
      this.pauseCountEl.textContent = this.pauseCount;
    }
    
    if (this.sessionStatusEl) {
      if (!this.isRunning && this.currentCycle === 0) {
        this.sessionStatusEl.textContent = 'Not Started';
      } else if (this.isPaused) {
        this.sessionStatusEl.textContent = 'Paused';
      } else if (this.isBreak) {
        this.sessionStatusEl.textContent = 'On Break';
      } else if (this.isRunning) {
        this.sessionStatusEl.textContent = 'In Progress';
      }
    }
    
    this.updateStudyTimeDisplay();
    
    // Update buttons
    if (this.startBtn && this.pauseBtn) {
      this.startBtn.disabled = this.isRunning;
      this.pauseBtn.disabled = !this.isRunning;
    }
    
    // Update settings
    if (this.numCyclesSelect) {
      this.numCyclesSelect.value = this.totalCycles;
      this.focusTimeSelect.value = this.focusTimeMinutes;
      this.breakTimeSelect.value = this.breakTimeMinutes;
      
      if (this.isRunning || this.currentCycle > 0) {
        this.disableSettings();
      } else {
        this.enableSettings();
      }
    }
    
    if (this.subjectSelect && this.selectedSubject) {
      this.subjectSelect.value = this.selectedSubject;
    }
  }

  // ==================== MODAL MANAGEMENT (CROSS-ROUTE) ====================
  
  showModalCrossRoute(modalType) {
    // Store modal state in localStorage so it persists across routes
    localStorage.setItem('pomodoroModalPending', modalType);
    this.checkAndShowPendingModal();
  }

  checkAndShowPendingModal() {
    const pendingModal = localStorage.getItem('pomodoroModalPending');
    if (!pendingModal) return;
    
    // Check if modal elements exist (user is on timer page)
    if (pendingModal === 'cycle' && this.cycleModal) {
      this.cycleModal.style.display = 'flex';
      this.playAlarm();
    } else if (pendingModal === 'break' && this.breakModal) {
      this.breakModal.style.display = 'flex';
      this.playAlarm();
    } else if (pendingModal === 'complete' && this.completeModal) {
      this.showSessionCompleteModal();
      this.playAlarm();
    }
  }

  clearPendingModal() {
    localStorage.removeItem('pomodoroModalPending');
  }

  // ==================== TIMER CONTROL ====================

  async loadSubjects() {
    try {
      const response = await fetch('/timer/api/subjects');
      const data = await response.json();
      
      if (data.success && data.subjects && this.subjectSelect) {
        this.subjectSelect.innerHTML = '<option value="">--Select Subject--</option>';
        data.subjects.forEach(subject => {
          const option = document.createElement('option');
          option.value = subject;
          option.textContent = subject;
          this.subjectSelect.appendChild(option);
        });
        
        // Restore selected subject if any
        if (this.selectedSubject) {
          this.subjectSelect.value = this.selectedSubject;
        }
      }
    } catch (error) {
      console.error('Error loading subjects:', error);
    }
  }

  updateSessionFormat() {
    if (!this.numCyclesSelect) return;
    
    const cycles = parseInt(this.numCyclesSelect.value);
    const focusTime = parseInt(this.focusTimeSelect.value);
    const breakTime = parseInt(this.breakTimeSelect.value);
    
    const totalFocusTime = cycles * focusTime;
    const totalBreakTime = (cycles - 1) * breakTime;
    const totalTime = totalFocusTime + totalBreakTime;
    
    if (this.sessionFormatText) {
      this.sessionFormatText.textContent = `${cycles} cycle${cycles > 1 ? 's' : ''} × ${focusTime} mins with ${breakTime}-min breaks`;
    }
    
    if (this.totalTimeText) {
      this.totalTimeText.textContent = `~${totalTime} minutes (${totalFocusTime} min focus + ${totalBreakTime} min breaks)`;
    }
  }

  startTimer() {
    // Check if subject is selected
    this.selectedSubject = this.subjectSelect ? this.subjectSelect.value : this.selectedSubject;
    if (!this.selectedSubject) {
      alert('Please select a subject to start the timer!');
      return;
    }
    
    // If starting fresh session
    if (!this.isRunning && !this.isPaused) {
      // Get settings
      this.totalCycles = this.numCyclesSelect ? parseInt(this.numCyclesSelect.value) : this.totalCycles;
      this.focusTimeMinutes = this.focusTimeSelect ? parseInt(this.focusTimeSelect.value) : this.focusTimeMinutes;
      this.breakTimeMinutes = this.breakTimeSelect ? parseInt(this.breakTimeSelect.value) : this.breakTimeMinutes;
      
      // Initialize session
      this.currentCycle = 1;
      this.cyclesCompleted = 0;
      this.pauseCount = 0;
      this.totalStudyTime = 0;
      this.sessionStartTime = new Date();
      
      // Set time remaining
      this.timeRemaining = this.focusTimeMinutes * 60;
      
      // Disable settings during session
      this.disableSettings();
    }
    
    // Resume from pause
    if (this.isPaused) {
      this.isPaused = false;
      
      // Clear pause check
      if (this.pauseCheckInterval) {
        clearInterval(this.pauseCheckInterval);
        this.pauseCheckInterval = null;
      }
    }
    
    // Start countdown
    this.isRunning = true;
    
    // Save state
    this.saveState();
    
    // Sync UI
    this.syncUIWithState();
  }

  handlePhaseComplete() {
    this.isRunning = false;
    this.saveState();
    
    if (this.isBreak) {
      // Break completed
      this.showModalCrossRoute('break');
    } else {
      // Focus cycle completed
      this.cyclesCompleted++;
      
      // Check if all cycles are done
      if (this.cyclesCompleted >= this.totalCycles) {
        this.showModalCrossRoute('complete');
      } else {
        this.showModalCrossRoute('cycle');
      }
      
      this.saveState();
    }
    
    // Update UI if on timer page
    if (this.cyclesCompletedEl) {
      this.cyclesCompletedEl.textContent = this.cyclesCompleted;
    }
  }

  pauseTimer() {
    if (!this.isRunning) return;
    
    this.isPaused = true;
    this.isRunning = false;
    this.pauseCount++;
    this.pauseStartTime = new Date();
    
    // Save state
    this.saveState();
    
    // Update UI
    if (this.pauseCountEl) {
      this.pauseCountEl.textContent = this.pauseCount;
    }
    
    if (this.sessionStatusEl) {
      this.sessionStatusEl.textContent = 'Paused';
    }
    
    if (this.startBtn && this.pauseBtn) {
      this.startBtn.disabled = false;
      this.pauseBtn.disabled = true;
    }
  }

  resetTimer() {
    if (!confirm('Are you sure you want to reset the current cycle timer?')) {
      return;
    }
    
    // Reset time remaining to current phase duration
    if (this.isBreak) {
      this.timeRemaining = this.breakTimeMinutes * 60;
    } else {
      this.timeRemaining = this.focusTimeMinutes * 60;
    }
    
    // Reset running state
    this.isRunning = false;
    this.isPaused = false;
    
    // Save state
    this.saveState();
    
    // Update UI
    this.syncUIWithState();
  }

  endSession(autoEnd = false) {
    if (!autoEnd && !confirm('Are you sure you want to end this session?')) {
      return;
    }
    
    // Save session to database
    this.saveSession();
    
    // Reset everything
    this.resetToDefaults();
  }

  startBreak() {
    this.stopAlarm();
    this.clearPendingModal();
    this.closeCycleModal();
    
    // Set break mode
    this.isBreak = true;
    this.timeRemaining = this.breakTimeMinutes * 60;
    this.isRunning = true;
    
    // Save state
    this.saveState();
    
    // Update UI
    this.syncUIWithState();
  }

  skipBreak() {
    this.stopAlarm();
    this.clearPendingModal();
    this.closeCycleModal();
    
    // Move to next cycle
    this.currentCycle++;
    this.isBreak = false;
    this.timeRemaining = this.focusTimeMinutes * 60;
    this.isRunning = true;
    
    // Save state
    this.saveState();
    
    // Update UI
    this.syncUIWithState();
  }

  continueStudying() {
    this.stopAlarm();
    this.clearPendingModal();
    this.closeBreakModal();
    
    // Move to next cycle
    this.currentCycle++;
    this.isBreak = false;
    this.timeRemaining = this.focusTimeMinutes * 60;
    this.isRunning = true;
    
    // Save state
    this.saveState();
    
    // Update UI
    this.syncUIWithState();
  }

  async saveSessionAndReset() {
    this.stopAlarm();
    this.clearPendingModal();
    this.closeCompleteModal();
    
    // Save session
    await this.saveSession();
    
    // Reset to defaults
    this.resetToDefaults();
  }

  // formatDateForIST(date) {
  //   const year = date.getFullYear();
  //   const month = String(date.getMonth() + 1).padStart(2, '0');
  //   const day = String(date.getDate()).padStart(2, '0');
  //   const hours = String(date.getHours()).padStart(2, '0');
  //   const minutes = String(date.getMinutes()).padStart(2, '0');
  //   const seconds = String(date.getSeconds()).padStart(2, '0');
    
  //   return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
  // }

  // async saveSession() {
  //   try {
  //     let completionStatus;
  //     if (this.cyclesCompleted >= this.totalCycles) {
  //       completionStatus = 'Completed';
  //     } else if (this.cyclesCompleted === 0) {
  //       completionStatus = 'Not Completed';
  //     } else {
  //       completionStatus = 'Partially Completed';
  //     }
      
  //     const now = new Date();
  //     const startTimeStr = this.formatDateForIST(this.sessionStartTime);
  //     const endTimeStr = this.formatDateForIST(now);
  //     const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
      
  //     const sessionData = {
  //       user_id: this.userId,
  //       subject: this.selectedSubject,
  //       start_time: startTimeStr,
  //       end_time: endTimeStr,
  //       total_time: Math.floor(this.totalStudyTime / 60),
  //       no_of_cycles_decided: this.totalCycles,
  //       no_of_cycles_completed: this.cyclesCompleted,
  //       break_time: this.breakTimeMinutes,
  //       pause_count: this.pauseCount,
  //       timer_per_cycle: this.focusTimeMinutes,
  //       completion_status: completionStatus,
  //       date: dateStr
  //     };
      
  //     console.log('Saving session data:', sessionData);
      
  //     const response = await fetch('/timer/api/save-session', {
  //       method: 'POST',
  //       headers: { 'Content-Type': 'application/json' },
  //       body: JSON.stringify(sessionData)
  //     });
      
  //     const result = await response.json();
      
  //     if (result.success) {
  //       console.log('Session saved successfully:', result.session_id);
  //     } else {
  //       console.error('Error saving session:', result.error);
  //       // Don't show alert, just log error
  //     }
  //   } catch (error) {
  //     console.error('Error saving session:', error);
  //     // Don't show alert, just log error
  //   }
  // }

  formatDateForIST(date) {
    // Create IST timezone offset (+5:30)
    const istOffset = 5.5 * 60 * 60 * 1000; // 5.5 hours in milliseconds
    const istDate = new Date(date.getTime() + istOffset);
    
    const year = istDate.getUTCFullYear();
    const month = String(istDate.getUTCMonth() + 1).padStart(2, '0');
    const day = String(istDate.getUTCDate()).padStart(2, '0');
    const hours = String(istDate.getUTCHours()).padStart(2, '0');
    const minutes = String(istDate.getUTCMinutes()).padStart(2, '0');
    const seconds = String(istDate.getUTCSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
  }

  async saveSession() {
    try {
      let completionStatus;
      if (this.cyclesCompleted >= this.totalCycles) {
        completionStatus = 'Completed';
      } else if (this.cyclesCompleted === 0) {
        completionStatus = 'Not Completed';
      } else {
        completionStatus = 'Partially Completed';
      }
      
      const now = new Date();
      
      // Format times in IST
      const startTimeStr = this.formatDateForIST(this.sessionStartTime);
      const endTimeStr = this.formatDateForIST(now);
      
      // Format date for IST timezone
      const istOffset = 5.5 * 60 * 60 * 1000;
      const istNow = new Date(now.getTime() + istOffset);
      const dateStr = `${istNow.getUTCFullYear()}-${String(istNow.getUTCMonth() + 1).padStart(2, '0')}-${String(istNow.getUTCDate()).padStart(2, '0')}`;
      
      const sessionData = {
        user_id: this.userId,
        subject: this.selectedSubject,
        start_time: startTimeStr,
        end_time: endTimeStr,
        total_time: Math.floor(this.totalStudyTime / 60),
        no_of_cycles_decided: this.totalCycles,
        no_of_cycles_completed: this.cyclesCompleted,
        break_time: this.breakTimeMinutes,
        pause_count: this.pauseCount,
        timer_per_cycle: this.focusTimeMinutes,
        completion_status: completionStatus,
        date: dateStr
      };
      
      console.log('Saving session data:', sessionData);
      
      const response = await fetch('/timer/api/save-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessionData)
      });
      
      const result = await response.json();
      
      if (result.success) {
        console.log('Session saved successfully:', result.session_id);
      } else {
        console.error('Error saving session:', result.error);
        // Don't show alert, just log error
      }
    } catch (error) {
      console.error('Error saving session:', error);
      // Don't show alert, just log error
    }
  }







  resetToDefaults() {
    // Reset state
    this.isRunning = false;
    this.isPaused = false;
    this.isBreak = false;
    this.currentCycle = 0;
    this.cyclesCompleted = 0;
    this.pauseCount = 0;
    this.totalStudyTime = 0;
    this.sessionStartTime = null;
    this.pauseStartTime = null;
    
    // Reset settings
    this.totalCycles = 4;
    this.focusTimeMinutes = 20;
    this.breakTimeMinutes = 5;
    this.timeRemaining = 20 * 60;
    
    // Clear state
    this.clearState();
    
    // Update UI
    this.syncUIWithState();
    
    // Enable settings
    this.enableSettings();
  }

  updateDisplay() {
    if (!this.countdownEl) return;
    const minutes = Math.floor(this.timeRemaining / 60);
    const seconds = this.timeRemaining % 60;
    this.countdownEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  updateStudyTimeDisplay() {
    if (!this.studyTimeEl) return;
    const totalMinutes = Math.floor(this.totalStudyTime / 60);
    if (totalMinutes >= 60) {
      const hours = Math.floor(totalMinutes / 60);
      const mins = totalMinutes % 60;
      this.studyTimeEl.textContent = `${hours} hour${hours > 1 ? 's' : ''} ${mins} min${mins !== 1 ? 's' : ''}`;
    } else {
      this.studyTimeEl.textContent = `${totalMinutes} min${totalMinutes !== 1 ? 's' : ''}`;
    }
  }

  disableSettings() {
    if (!this.subjectSelect) return;
    this.subjectSelect.disabled = true;
    this.numCyclesSelect.disabled = true;
    this.focusTimeSelect.disabled = true;
    this.breakTimeSelect.disabled = true;
  }

  enableSettings() {
    if (!this.subjectSelect) return;
    this.subjectSelect.disabled = false;
    this.numCyclesSelect.disabled = false;
    this.focusTimeSelect.disabled = false;
    this.breakTimeSelect.disabled = false;
  }

  playAlarm() {
    if (this.alarmSound) {
      this.alarmSound.play().catch(err => console.error('Error playing alarm:', err));
    }
  }

  stopAlarm() {
    if (this.alarmSound) {
      this.alarmSound.pause();
      this.alarmSound.currentTime = 0;
    }
  }

  showCycleCompleteModal() {
    if (this.cycleModal) this.cycleModal.style.display = 'flex';
  }

  closeCycleModal() {
    if (this.cycleModal) this.cycleModal.style.display = 'none';
  }

  showBreakEndModal() {
    if (this.breakModal) this.breakModal.style.display = 'flex';
  }

  closeBreakModal() {
    if (this.breakModal) this.breakModal.style.display = 'none';
  }

  showSessionCompleteModal() {
    if (!this.completeModal) return;
    const totalMinutes = Math.floor(this.totalStudyTime / 60);
    if (this.finalStudyTimeEl) {
      if (totalMinutes >= 60) {
        const hours = Math.floor(totalMinutes / 60);
        const mins = totalMinutes % 60;
        this.finalStudyTimeEl.textContent = `${hours} hour${hours > 1 ? 's' : ''} ${mins} minute${mins !== 1 ? 's' : ''}`;
      } else {
        this.finalStudyTimeEl.textContent = `${totalMinutes} minute${totalMinutes !== 1 ? 's' : ''}`;
      }
    }
    this.completeModal.style.display = 'flex';
  }

  closeCompleteModal() {
    if (this.completeModal) this.completeModal.style.display = 'none';
  }
}

// Global timer instance
window.pomodoroTimer = window.pomodoroTimer || null;

// Initialize timer (can be called multiple times safely)
function initPomodoroTimer() {
  if (!window.pomodoroTimer) {
    window.pomodoroTimer = new PomodoroTimer();
  } else {
    // Reinitialize elements if navigating back to timer page
    window.pomodoroTimer.initElements();
    window.pomodoroTimer.attachEventListeners();
    window.pomodoroTimer.loadSubjects();
    window.pomodoroTimer.syncUIWithState();
    window.pomodoroTimer.checkAndShowPendingModal();
  }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPomodoroTimer);
} else {
  initPomodoroTimer();
}

// Export for manual initialization after AJAX content load
window.initPomodoroTimer = initPomodoroTimer;




// // timer.js - Persistent Pomodoro Timer Implementation with Cross-Route Support

// class PomodoroTimer {
//   constructor() {
//     // Timer state
//     this.isRunning = false;
//     this.isPaused = false;
//     this.isBreak = false;
//     this.currentCycle = 0;
//     this.cyclesCompleted = 0;
//     this.pauseCount = 0;
//     this.totalStudyTime = 0; // in seconds
//     this.sessionStartTime = null;
//     this.currentPhaseStartTime = null;
//     this.pauseStartTime = null;
    
//     // Timer settings
//     this.totalCycles = 4;
//     this.focusTimeMinutes = 20;
//     this.breakTimeMinutes = 5;
//     this.selectedSubject = '';
    
//     // Countdown
//     this.timeRemaining = 0; // in seconds
//     this.timerInterval = null;
//     this.pauseCheckInterval = null;
    
//     // Persistence
//     this.storageKey = 'pomodoroTimerState';
//     this.backgroundInterval = null;
    
//     // Initialize
//     this.restoreState();
//     this.initElements();
//     this.attachEventListeners();
//     this.updateSessionFormat();
//     this.loadSubjects();
//     this.startBackgroundTimer();
    
//     // Sync UI if elements exist
//     if (this.countdownEl) {
//       this.syncUIWithState();
//     }

//     this.onTickCallbacks = []; // NEW: callbacks for every tick
//     this.startBackgroundTimer();
//   }

//   // NEW: register a callback
//   onTick(callback) {
//     if (typeof callback === 'function') {
//       this.onTickCallbacks.push(callback);
//     }
//   }

//   backgroundTick() {
//     if (this.timeRemaining > 0) {
//       this.timeRemaining--;

//       // Update study time (only during focus, not break)
//       if (!this.isBreak) {
//         this.totalStudyTime++;
//       }

//       // Save state
//       this.saveState();

//       // Update UI if on timer page
//       if (this.countdownEl) {
//         this.updateDisplay();
//         this.updateStudyTimeDisplay();
//       }

//       // 🔹 Call tick callbacks
//       this.onTickCallbacks.forEach(cb => cb(this));
      
//     } else {
//       // Time's up!
//       this.handlePhaseComplete();

//       // 🔹 Call tick callbacks
//       this.onTickCallbacks.forEach(cb => cb(this));
//     }
//   }




  
//   initElements() {
//     // Timer Display
//     this.countdownEl = document.getElementById('countdown');
//     this.timerLabelEl = document.getElementById('timerLabel');
//     this.cycleIndicatorEl = document.getElementById('cycleIndicator');
    
//     // Controls
//     this.startBtn = document.getElementById('startBtn');
//     this.pauseBtn = document.getElementById('pauseBtn');
//     this.resetBtn = document.getElementById('resetBtn');
//     this.endBtn = document.getElementById('endBtn');
    
//     // Settings
//     this.subjectSelect = document.getElementById('subject');
//     this.numCyclesSelect = document.getElementById('numCycles');
//     this.focusTimeSelect = document.getElementById('focusTime');
//     this.breakTimeSelect = document.getElementById('breakTime');
//     this.sessionFormatText = document.getElementById('sessionFormatText');
//     this.totalTimeText = document.getElementById('totalTimeText');
    
//     // Stats
//     this.cyclesCompletedEl = document.getElementById('cyclesCompleted');
//     this.totalCyclesDisplayEl = document.getElementById('totalCyclesDisplay');
//     this.pauseCountEl = document.getElementById('pauseCount');
//     this.sessionStatusEl = document.getElementById('sessionStatus');
//     this.studyTimeEl = document.getElementById('studyTime');
    
//     // Modals
//     this.cycleModal = document.getElementById('cycleModal');
//     this.breakModal = document.getElementById('breakModal');
//     this.completeModal = document.getElementById('completeModal');
//     this.modalOkBtn = document.getElementById('modalOkBtn');
//     this.modalSkipBtn = document.getElementById('modalSkipBtn');
//     this.breakContinueBtn = document.getElementById('breakContinueBtn');
//     this.completeOkBtn = document.getElementById('completeOkBtn');
//     this.finalStudyTimeEl = document.getElementById('finalStudyTime');
    
//     // Audio
//     this.alarmSound = document.getElementById('alarmSound');
    
//     // User ID
//     const userIdEl = document.getElementById('userId');
//     this.userId = userIdEl ? userIdEl.value : this.userId;
//   }

//   attachEventListeners() {
//     if (!this.startBtn) return;
    
//     // Control buttons
//     this.startBtn.addEventListener('click', () => this.startTimer());
//     this.pauseBtn.addEventListener('click', () => this.pauseTimer());
//     this.resetBtn.addEventListener('click', () => this.resetTimer());
//     this.endBtn.addEventListener('click', () => this.endSession());
    
//     // Settings change listeners
//     this.numCyclesSelect.addEventListener('change', () => this.updateSessionFormat());
//     this.focusTimeSelect.addEventListener('change', () => this.updateSessionFormat());
//     this.breakTimeSelect.addEventListener('change', () => this.updateSessionFormat());
    
//     // Modal buttons
//     this.modalOkBtn.addEventListener('click', () => this.startBreak());
//     this.modalSkipBtn.addEventListener('click', () => this.skipBreak());
//     this.breakContinueBtn.addEventListener('click', () => this.continueStudying());
//     this.completeOkBtn.addEventListener('click', () => this.saveSessionAndReset());
//   }

//   // ==================== STATE PERSISTENCE ====================
  
//   saveState() {
//     const state = {
//       isRunning: this.isRunning,
//       isPaused: this.isPaused,
//       isBreak: this.isBreak,
//       currentCycle: this.currentCycle,
//       cyclesCompleted: this.cyclesCompleted,
//       pauseCount: this.pauseCount,
//       totalStudyTime: this.totalStudyTime,
//       sessionStartTime: this.sessionStartTime ? this.sessionStartTime.toISOString() : null,
//       pauseStartTime: this.pauseStartTime ? this.pauseStartTime.toISOString() : null,
//       totalCycles: this.totalCycles,
//       focusTimeMinutes: this.focusTimeMinutes,
//       breakTimeMinutes: this.breakTimeMinutes,
//       selectedSubject: this.selectedSubject,
//       timeRemaining: this.timeRemaining,
//       lastUpdate: new Date().toISOString(),
//       userId: this.userId
//     };
    
//     localStorage.setItem(this.storageKey, JSON.stringify(state));
//   }

//   restoreState() {
//     const saved = localStorage.getItem(this.storageKey);
//     if (!saved) return;
    
//     try {
//       const state = JSON.parse(saved);
      
//       // Calculate time elapsed since last update
//       const lastUpdate = new Date(state.lastUpdate);
//       const now = new Date();
//       const elapsedSeconds = Math.floor((now - lastUpdate) / 1000);
      
//       // Restore state
//       this.isRunning = state.isRunning;
//       this.isPaused = state.isPaused;
//       this.isBreak = state.isBreak;
//       this.currentCycle = state.currentCycle;
//       this.cyclesCompleted = state.cyclesCompleted;
//       this.pauseCount = state.pauseCount;
//       this.totalStudyTime = state.totalStudyTime;
//       this.totalCycles = state.totalCycles;
//       this.focusTimeMinutes = state.focusTimeMinutes;
//       this.breakTimeMinutes = state.breakTimeMinutes;
//       this.selectedSubject = state.selectedSubject;
//       this.userId = state.userId;
      
//       if (state.sessionStartTime) {
//         this.sessionStartTime = new Date(state.sessionStartTime);
//       }
      
//       if (state.pauseStartTime) {
//         this.pauseStartTime = new Date(state.pauseStartTime);
//       }
      
//       // Update time remaining based on elapsed time
//       if (this.isRunning && !this.isPaused) {
//         this.timeRemaining = Math.max(0, state.timeRemaining - elapsedSeconds);
        
//         // Update study time if in focus mode
//         if (!this.isBreak) {
//           this.totalStudyTime += elapsedSeconds;
//         }
//       } else {
//         this.timeRemaining = state.timeRemaining;
//       }
      
//       // Check if pause exceeded 10 minutes
//       if (this.isPaused && this.pauseStartTime) {
//         const pauseDuration = (now - this.pauseStartTime) / 1000;
//         if (pauseDuration >= 600) {
//           this.endSession(true);
//           return;
//         }
//       }
      
//     } catch (error) {
//       console.error('Error restoring timer state:', error);
//       localStorage.removeItem(this.storageKey);
//     }
//   }

//   clearState() {
//     localStorage.removeItem(this.storageKey);
//   }

//   // ==================== BACKGROUND TIMER ====================
  
//   startBackgroundTimer() {
//     // Clear any existing background timer
//     if (this.backgroundInterval) {
//       clearInterval(this.backgroundInterval);
//     }
    
//     // Run every second to keep timer accurate even when not on timer page
//     this.backgroundInterval = setInterval(() => {
//       if (this.isRunning && !this.isPaused) {
//         this.backgroundTick();
//       }
      
//       // Check pause duration
//       if (this.isPaused && this.pauseStartTime) {
//         const now = new Date();
//         const pauseDuration = (now - this.pauseStartTime) / 1000;
//         if (pauseDuration >= 600) {
//           clearInterval(this.backgroundInterval);
//           this.endSession(true);
//         }
//       }
//     }, 1000);
//   }

//   backgroundTick() {
//     if (this.timeRemaining > 0) {
//       this.timeRemaining--;
      
//       // Update study time (only during focus, not break)
//       if (!this.isBreak) {
//         this.totalStudyTime++;
//       }
      
//       // Save state
//       this.saveState();
      
//       // Update UI if on timer page
//       if (this.countdownEl) {
//         this.updateDisplay();
//         this.updateStudyTimeDisplay();
//       }
//     } else {
//       // Time's up!
//       this.handlePhaseComplete();
//     }
//   }

//   syncUIWithState() {
//     if (!this.countdownEl) return;
    
//     // Update all UI elements to reflect current state
//     this.updateDisplay();
    
//     if (this.timerLabelEl) {
//       this.timerLabelEl.textContent = this.isBreak ? 'Break Time' : 'Focus Time';
//     }
    
//     if (this.cycleIndicatorEl) {
//       if (this.isBreak) {
//         this.cycleIndicatorEl.textContent = `Cycle ${this.cyclesCompleted} of ${this.totalCycles} - Break`;
//       } else if (this.currentCycle > 0) {
//         this.cycleIndicatorEl.textContent = `Cycle ${this.currentCycle} of ${this.totalCycles}`;
//       } else {
//         this.cycleIndicatorEl.textContent = `Cycle 0 of ${this.totalCycles}`;
//       }
//     }
    
//     if (this.cyclesCompletedEl) {
//       this.cyclesCompletedEl.textContent = this.cyclesCompleted;
//     }
    
//     if (this.totalCyclesDisplayEl) {
//       this.totalCyclesDisplayEl.textContent = this.totalCycles;
//     }
    
//     if (this.pauseCountEl) {
//       this.pauseCountEl.textContent = this.pauseCount;
//     }
    
//     if (this.sessionStatusEl) {
//       if (!this.isRunning && this.currentCycle === 0) {
//         this.sessionStatusEl.textContent = 'Not Started';
//       } else if (this.isPaused) {
//         this.sessionStatusEl.textContent = 'Paused';
//       } else if (this.isBreak) {
//         this.sessionStatusEl.textContent = 'On Break';
//       } else if (this.isRunning) {
//         this.sessionStatusEl.textContent = 'In Progress';
//       }
//     }
    
//     this.updateStudyTimeDisplay();
    
//     // Update buttons
//     if (this.startBtn && this.pauseBtn) {
//       this.startBtn.disabled = this.isRunning;
//       this.pauseBtn.disabled = !this.isRunning;
//     }
    
//     // Update settings
//     if (this.numCyclesSelect) {
//       this.numCyclesSelect.value = this.totalCycles;
//       this.focusTimeSelect.value = this.focusTimeMinutes;
//       this.breakTimeSelect.value = this.breakTimeMinutes;
      
//       if (this.isRunning || this.currentCycle > 0) {
//         this.disableSettings();
//       } else {
//         this.enableSettings();
//       }
//     }
    
//     if (this.subjectSelect && this.selectedSubject) {
//       this.subjectSelect.value = this.selectedSubject;
//     }
//   }

//   // ==================== MODAL MANAGEMENT (CROSS-ROUTE) ====================
  
//   showModalCrossRoute(modalType) {
//     // Store modal state in localStorage so it persists across routes
//     localStorage.setItem('pomodoroModalPending', modalType);
//     this.checkAndShowPendingModal();
//   }

//   checkAndShowPendingModal() {
//     const pendingModal = localStorage.getItem('pomodoroModalPending');
//     if (!pendingModal) return;
    
//     // Check if modal elements exist (user is on timer page)
//     if (pendingModal === 'cycle' && this.cycleModal) {
//       this.cycleModal.style.display = 'flex';
//       this.playAlarm();
//     } else if (pendingModal === 'break' && this.breakModal) {
//       this.breakModal.style.display = 'flex';
//       this.playAlarm();
//     } else if (pendingModal === 'complete' && this.completeModal) {
//       this.showSessionCompleteModal();
//       this.playAlarm();
//     }
//   }

//   clearPendingModal() {
//     localStorage.removeItem('pomodoroModalPending');
//   }

//   // ==================== TIMER CONTROL ====================

//   async loadSubjects() {
//     try {
//       const response = await fetch('/timer/api/subjects');
//       const data = await response.json();
      
//       if (data.success && data.subjects && this.subjectSelect) {
//         this.subjectSelect.innerHTML = '<option value="">--Select Subject--</option>';
//         data.subjects.forEach(subject => {
//           const option = document.createElement('option');
//           option.value = subject;
//           option.textContent = subject;
//           this.subjectSelect.appendChild(option);
//         });
        
//         // Restore selected subject if any
//         if (this.selectedSubject) {
//           this.subjectSelect.value = this.selectedSubject;
//         }
//       }
//     } catch (error) {
//       console.error('Error loading subjects:', error);
//     }
//   }

//   updateSessionFormat() {
//     if (!this.numCyclesSelect) return;
    
//     const cycles = parseInt(this.numCyclesSelect.value);
//     const focusTime = parseInt(this.focusTimeSelect.value);
//     const breakTime = parseInt(this.breakTimeSelect.value);
    
//     const totalFocusTime = cycles * focusTime;
//     const totalBreakTime = (cycles - 1) * breakTime;
//     const totalTime = totalFocusTime + totalBreakTime;
    
//     if (this.sessionFormatText) {
//       this.sessionFormatText.textContent = `${cycles} cycle${cycles > 1 ? 's' : ''} × ${focusTime} mins with ${breakTime}-min breaks`;
//     }
    
//     if (this.totalTimeText) {
//       this.totalTimeText.textContent = `~${totalTime} minutes (${totalFocusTime} min focus + ${totalBreakTime} min breaks)`;
//     }
//   }

//   startTimer() {
//     // Check if subject is selected
//     this.selectedSubject = this.subjectSelect ? this.subjectSelect.value : this.selectedSubject;
//     if (!this.selectedSubject) {
//       alert('Please select a subject to start the timer!');
//       return;
//     }
    
//     // If starting fresh session
//     if (!this.isRunning && !this.isPaused) {
//       // Get settings
//       this.totalCycles = this.numCyclesSelect ? parseInt(this.numCyclesSelect.value) : this.totalCycles;
//       this.focusTimeMinutes = this.focusTimeSelect ? parseInt(this.focusTimeSelect.value) : this.focusTimeMinutes;
//       this.breakTimeMinutes = this.breakTimeSelect ? parseInt(this.breakTimeSelect.value) : this.breakTimeMinutes;
      
//       // Initialize session
//       this.currentCycle = 1;
//       this.cyclesCompleted = 0;
//       this.pauseCount = 0;
//       this.totalStudyTime = 0;
//       this.sessionStartTime = new Date();
      
//       // Set time remaining
//       this.timeRemaining = this.focusTimeMinutes * 60;
      
//       // Disable settings during session
//       this.disableSettings();
//     }
    
//     // Resume from pause
//     if (this.isPaused) {
//       this.isPaused = false;
      
//       // Clear pause check
//       if (this.pauseCheckInterval) {
//         clearInterval(this.pauseCheckInterval);
//         this.pauseCheckInterval = null;
//       }
//     }
    
//     // Start countdown
//     this.isRunning = true;
    
//     // Save state
//     this.saveState();
    
//     // Sync UI
//     this.syncUIWithState();
//   }

//   handlePhaseComplete() {
//     this.isRunning = false;
//     this.saveState();
    
//     if (this.isBreak) {
//       // Break completed
//       this.showModalCrossRoute('break');
//     } else {
//       // Focus cycle completed
//       this.cyclesCompleted++;
      
//       // Check if all cycles are done
//       if (this.cyclesCompleted >= this.totalCycles) {
//         this.showModalCrossRoute('complete');
//       } else {
//         this.showModalCrossRoute('cycle');
//       }
      
//       this.saveState();
//     }
    
//     // Update UI if on timer page
//     if (this.cyclesCompletedEl) {
//       this.cyclesCompletedEl.textContent = this.cyclesCompleted;
//     }
//   }

//   pauseTimer() {
//     if (!this.isRunning) return;
    
//     this.isPaused = true;
//     this.isRunning = false;
//     this.pauseCount++;
//     this.pauseStartTime = new Date();
    
//     // Save state
//     this.saveState();
    
//     // Update UI
//     if (this.pauseCountEl) {
//       this.pauseCountEl.textContent = this.pauseCount;
//     }
    
//     if (this.sessionStatusEl) {
//       this.sessionStatusEl.textContent = 'Paused';
//     }
    
//     if (this.startBtn && this.pauseBtn) {
//       this.startBtn.disabled = false;
//       this.pauseBtn.disabled = true;
//     }
//   }

//   resetTimer() {
//     if (!confirm('Are you sure you want to reset the current cycle timer?')) {
//       return;
//     }
    
//     // Reset time remaining to current phase duration
//     if (this.isBreak) {
//       this.timeRemaining = this.breakTimeMinutes * 60;
//     } else {
//       this.timeRemaining = this.focusTimeMinutes * 60;
//     }
    
//     // Reset running state
//     this.isRunning = false;
//     this.isPaused = false;
    
//     // Save state
//     this.saveState();
    
//     // Update UI
//     this.syncUIWithState();
//   }

//   endSession(autoEnd = false) {
//     if (!autoEnd && !confirm('Are you sure you want to end this session?')) {
//       return;
//     }
    
//     // Save session to database
//     this.saveSession();
    
//     // Reset everything
//     this.resetToDefaults();
//   }

//   startBreak() {
//     this.stopAlarm();
//     this.clearPendingModal();
//     this.closeCycleModal();
    
//     // Set break mode
//     this.isBreak = true;
//     this.timeRemaining = this.breakTimeMinutes * 60;
//     this.isRunning = true;
    
//     // Save state
//     this.saveState();
    
//     // Update UI
//     this.syncUIWithState();
//   }

//   skipBreak() {
//     this.stopAlarm();
//     this.clearPendingModal();
//     this.closeCycleModal();
    
//     // Move to next cycle
//     this.currentCycle++;
//     this.isBreak = false;
//     this.timeRemaining = this.focusTimeMinutes * 60;
//     this.isRunning = true;
    
//     // Save state
//     this.saveState();
    
//     // Update UI
//     this.syncUIWithState();
//   }

//   continueStudying() {
//     this.stopAlarm();
//     this.clearPendingModal();
//     this.closeBreakModal();
    
//     // Move to next cycle
//     this.currentCycle++;
//     this.isBreak = false;
//     this.timeRemaining = this.focusTimeMinutes * 60;
//     this.isRunning = true;
    
//     // Save state
//     this.saveState();
    
//     // Update UI
//     this.syncUIWithState();
//   }

//   async saveSessionAndReset() {
//     this.stopAlarm();
//     this.clearPendingModal();
//     this.closeCompleteModal();
    
//     // Save session
//     await this.saveSession();
    
//     // Reset to defaults
//     this.resetToDefaults();
//   }

//   formatDateForIST(date) {
//     const year = date.getFullYear();
//     const month = String(date.getMonth() + 1).padStart(2, '0');
//     const day = String(date.getDate()).padStart(2, '0');
//     const hours = String(date.getHours()).padStart(2, '0');
//     const minutes = String(date.getMinutes()).padStart(2, '0');
//     const seconds = String(date.getSeconds()).padStart(2, '0');
    
//     return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
//   }

//   async saveSession() {
//     try {
//       let completionStatus;
//       if (this.cyclesCompleted >= this.totalCycles) {
//         completionStatus = 'Completed';
//       } else if (this.cyclesCompleted === 0) {
//         completionStatus = 'Not Completed';
//       } else {
//         completionStatus = 'Partially Completed';
//       }
      
//       const now = new Date();
//       const startTimeStr = this.formatDateForIST(this.sessionStartTime);
//       const endTimeStr = this.formatDateForIST(now);
//       const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
      
//       const sessionData = {
//         user_id: this.userId,
//         subject: this.selectedSubject,
//         start_time: startTimeStr,
//         end_time: endTimeStr,
//         total_time: Math.floor(this.totalStudyTime / 60),
//         no_of_cycles_decided: this.totalCycles,
//         no_of_cycles_completed: this.cyclesCompleted,
//         break_time: this.breakTimeMinutes,
//         pause_count: this.pauseCount,
//         timer_per_cycle: this.focusTimeMinutes,
//         completion_status: completionStatus,
//         date: dateStr
//       };
      
//       const response = await fetch('/timer/api/save-session', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify(sessionData)
//       });
      
//       const result = await response.json();
      
//       if (result.success) {
//         console.log('Session saved successfully:', result.session_id);
//       } else {
//         console.error('Error saving session:', result.error);
//         alert('Failed to save session. Please try again.');
//       }
//     } catch (error) {
//       console.error('Error saving session:', error);
//       alert('Failed to save session. Please check your connection.');
//     }
//   }

//   resetToDefaults() {
//     // Reset state
//     this.isRunning = false;
//     this.isPaused = false;
//     this.isBreak = false;
//     this.currentCycle = 0;
//     this.cyclesCompleted = 0;
//     this.pauseCount = 0;
//     this.totalStudyTime = 0;
//     this.sessionStartTime = null;
//     this.pauseStartTime = null;
    
//     // Reset settings
//     this.totalCycles = 4;
//     this.focusTimeMinutes = 20;
//     this.breakTimeMinutes = 5;
//     this.timeRemaining = 20 * 60;
    
//     // Clear state
//     this.clearState();
    
//     // Update UI
//     this.syncUIWithState();
    
//     // Enable settings
//     this.enableSettings();
//   }

//   updateDisplay() {
//     if (!this.countdownEl) return;
//     const minutes = Math.floor(this.timeRemaining / 60);
//     const seconds = this.timeRemaining % 60;
//     this.countdownEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
//   }

//   updateStudyTimeDisplay() {
//     if (!this.studyTimeEl) return;
//     const totalMinutes = Math.floor(this.totalStudyTime / 60);
//     if (totalMinutes >= 60) {
//       const hours = Math.floor(totalMinutes / 60);
//       const mins = totalMinutes % 60;
//       this.studyTimeEl.textContent = `${hours} hour${hours > 1 ? 's' : ''} ${mins} min${mins !== 1 ? 's' : ''}`;
//     } else {
//       this.studyTimeEl.textContent = `${totalMinutes} min${totalMinutes !== 1 ? 's' : ''}`;
//     }
//   }

//   disableSettings() {
//     if (!this.subjectSelect) return;
//     this.subjectSelect.disabled = true;
//     this.numCyclesSelect.disabled = true;
//     this.focusTimeSelect.disabled = true;
//     this.breakTimeSelect.disabled = true;
//   }

//   enableSettings() {
//     if (!this.subjectSelect) return;
//     this.subjectSelect.disabled = false;
//     this.numCyclesSelect.disabled = false;
//     this.focusTimeSelect.disabled = false;
//     this.breakTimeSelect.disabled = false;
//   }

//   playAlarm() {
//     if (this.alarmSound) {
//       this.alarmSound.play().catch(err => console.error('Error playing alarm:', err));
//     }
//   }

//   stopAlarm() {
//     if (this.alarmSound) {
//       this.alarmSound.pause();
//       this.alarmSound.currentTime = 0;
//     }
//   }

//   showCycleCompleteModal() {
//     if (this.cycleModal) this.cycleModal.style.display = 'flex';
//   }

//   closeCycleModal() {
//     if (this.cycleModal) this.cycleModal.style.display = 'none';
//   }

//   showBreakEndModal() {
//     if (this.breakModal) this.breakModal.style.display = 'flex';
//   }

//   closeBreakModal() {
//     if (this.breakModal) this.breakModal.style.display = 'none';
//   }

//   showSessionCompleteModal() {
//     if (!this.completeModal) return;
//     const totalMinutes = Math.floor(this.totalStudyTime / 60);
//     if (this.finalStudyTimeEl) {
//       if (totalMinutes >= 60) {
//         const hours = Math.floor(totalMinutes / 60);
//         const mins = totalMinutes % 60;
//         this.finalStudyTimeEl.textContent = `${hours} hour${hours > 1 ? 's' : ''} ${mins} minute${mins !== 1 ? 's' : ''}`;
//       } else {
//         this.finalStudyTimeEl.textContent = `${totalMinutes} minute${totalMinutes !== 1 ? 's' : ''}`;
//       }
//     }
//     this.completeModal.style.display = 'flex';
//   }

//   closeCompleteModal() {
//     if (this.completeModal) this.completeModal.style.display = 'none';
//   }
// }

// // Global timer instance
// window.pomodoroTimer = window.pomodoroTimer || null;

// // Initialize timer (can be called multiple times safely)
// function initPomodoroTimer() {
//   if (!window.pomodoroTimer) {
//     window.pomodoroTimer = new PomodoroTimer();
//   } else {
//     // Reinitialize elements if navigating back to timer page
//     window.pomodoroTimer.initElements();
//     window.pomodoroTimer.attachEventListeners();
//     window.pomodoroTimer.loadSubjects();
//     window.pomodoroTimer.syncUIWithState();
//     window.pomodoroTimer.checkAndShowPendingModal();
//   }
// }

// // Initialize on DOM ready
// if (document.readyState === 'loading') {
//   document.addEventListener('DOMContentLoaded', initPomodoroTimer);
// } else {
//   initPomodoroTimer();
// }

// // Export for manual initialization after AJAX content load
// window.initPomodoroTimer = initPomodoroTimer;





