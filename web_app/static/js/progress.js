class ProgressUI {
    constructor() {
        this.mainProgressFill = document.getElementById('mainProgressFill');
        this.mainProgressText = document.getElementById('mainProgressText');
        this.mainProgressPercent = document.getElementById('mainProgressPercent');
        this.etaText = document.getElementById('etaText');
        
        this.steps = {
            1: document.getElementById('step1'),
            2: document.getElementById('step2'),
            3: document.getElementById('step3'),
            4: document.getElementById('step4')
        };
        
        this.currentStep = 0;
        this.currentProgress = 0;
        this.animationFrame = null;
        
        this.reset();
    }
    
    updateProgress(data) {
        console.log('Updating progress UI:', data);
        
        // Handle different data formats
        const step = data.step || 0;
        const progress = data.progress || 0;
        const message = data.message || data.step_name || 'Processing...';
        const eta = data.eta;
        const type = data.type || 'progress';
        
        // Handle different message types
        switch (type) {
            case 'progress':
                this.updateProgressDisplay(step, progress, message, eta);
                break;
            case 'complete':
                this.handleCompletion(data);
                break;
            case 'error':
                this.handleError(data);
                break;
        }
    }
    
    updateProgressDisplay(step, progress, message, eta) {
        // Update step indicators
        this.updateStepIndicators(step);
        
        // Animate progress bar
        this.animateProgress(progress);
        
        // Update text
        this.updateProgressText(message, progress);
        
        // Update ETA
        this.updateETA(eta);
        
        // Store current values
        this.currentStep = step;
        this.currentProgress = progress;
    }
    
    updateStepIndicators(activeStep) {
        Object.keys(this.steps).forEach(stepNumber => {
            const stepElement = this.steps[stepNumber];
            const stepNum = parseInt(stepNumber);
            
            // Remove existing classes
            stepElement.classList.remove('active', 'completed');
            
            if (stepNum < activeStep) {
                // Completed step
                stepElement.classList.add('completed');
                this.animateStepCompletion(stepElement);
            } else if (stepNum === activeStep) {
                // Current active step
                stepElement.classList.add('active');
                this.animateStepActivation(stepElement);
            }
            // else: future step (no special class)
        });
    }
    
    animateStepCompletion(stepElement) {
        const stepNumber = stepElement.querySelector('.step-number');
        
        // Add checkmark animation
        if (!stepNumber.innerHTML.includes('✓')) {
            setTimeout(() => {
                stepNumber.innerHTML = '✓';
                stepElement.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    stepElement.style.transform = 'scale(1)';
                }, 200);
            }, 100);
        }
    }
    
    animateStepActivation(stepElement) {
        // Add pulsing animation for active step
        stepElement.style.transform = 'scale(1.02)';
        setTimeout(() => {
            stepElement.style.transform = 'scale(1)';
        }, 300);
    }
    
    animateProgress(targetProgress) {
        // Cancel any existing animation
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        
        const startProgress = this.currentProgress;
        const progressDiff = targetProgress - startProgress;
        const duration = 500; // 500ms animation
        let startTime = null;
        
        const animate = (currentTime) => {
            if (!startTime) startTime = currentTime;
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easeProgress = this.easeInOutCubic(progress);
            const currentValue = startProgress + (progressDiff * easeProgress);
            
            // Update progress bar
            this.mainProgressFill.style.width = `${currentValue}%`;
            this.mainProgressPercent.textContent = `${Math.round(currentValue)}%`;
            
            if (progress < 1) {
                this.animationFrame = requestAnimationFrame(animate);
            } else {
                this.animationFrame = null;
            }
        };
        
        this.animationFrame = requestAnimationFrame(animate);
    }
    
    easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
    }
    
    updateProgressText(message, progress) {
        this.mainProgressText.textContent = message;
        
        // Add some visual feedback based on progress
        if (progress >= 100) {
            this.mainProgressText.style.color = '#28a745';
            this.mainProgressText.style.fontWeight = 'bold';
        } else if (progress >= 75) {
            this.mainProgressText.style.color = '#667eea';
        } else {
            this.mainProgressText.style.color = '#333';
            this.mainProgressText.style.fontWeight = 'normal';
        }
    }
    
    updateETA(eta) {
        if (eta && eta > 0) {
            const minutes = Math.floor(eta / 60);
            const seconds = Math.floor(eta % 60);
            
            let etaText = 'ETA: ';
            if (minutes > 0) {
                etaText += `${minutes}m `;
            }
            etaText += `${seconds}s`;
            
            this.etaText.textContent = etaText;
            this.etaText.style.opacity = '1';
        } else {
            this.etaText.style.opacity = '0';
        }
    }
    
    handleCompletion(data) {
        // Animate to 100%
        this.animateProgress(100);
        
        // Mark all steps as completed
        this.updateStepIndicators(5); // Beyond last step to mark all complete
        
        // Update text
        this.updateProgressText('Processing completed successfully!', 100);
        
        // Hide ETA
        this.etaText.style.opacity = '0';
        
        // Add completion effects
        this.addCompletionEffects();
    }
    
    handleError(data) {
        // Show error state
        this.mainProgressText.textContent = data.message || 'An error occurred';
        this.mainProgressText.style.color = '#dc3545';
        this.mainProgressText.style.fontWeight = 'bold';
        
        // Add error styling to current step
        if (this.currentStep > 0 && this.steps[this.currentStep]) {
            const currentStepEl = this.steps[this.currentStep];
            currentStepEl.classList.remove('active');
            currentStepEl.classList.add('error');
            currentStepEl.style.borderColor = '#dc3545';
            currentStepEl.style.backgroundColor = 'rgba(220, 53, 69, 0.1)';
        }
        
        // Hide ETA
        this.etaText.style.opacity = '0';
    }
    
    addCompletionEffects() {
        // Add sparkle effect to progress bar
        this.mainProgressFill.style.background = 'linear-gradient(90deg, #28a745, #20c997)';
        
        // Pulse effect for completed steps
        Object.values(this.steps).forEach((step, index) => {
            setTimeout(() => {
                step.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    step.style.transform = 'scale(1)';
                }, 200);
            }, index * 100);
        });
    }
    
    reset() {
        // Reset progress bar
        this.mainProgressFill.style.width = '0%';
        this.mainProgressFill.style.background = 'linear-gradient(90deg, #667eea, #764ba2)';
        this.mainProgressPercent.textContent = '0%';
        
        // Reset text
        this.mainProgressText.textContent = 'Ready to start processing...';
        this.mainProgressText.style.color = '#333';
        this.mainProgressText.style.fontWeight = 'normal';
        
        // Hide ETA
        this.etaText.style.opacity = '0';
        
        // Reset all steps
        Object.values(this.steps).forEach(step => {
            step.classList.remove('active', 'completed', 'error');
            step.style.transform = 'scale(1)';
            step.style.borderColor = '';
            step.style.backgroundColor = '';
            
            const stepNumber = step.querySelector('.step-number');
            const originalNumber = step.id.replace('step', '');
            stepNumber.innerHTML = originalNumber;
        });
        
        // Reset state
        this.currentStep = 0;
        this.currentProgress = 0;
        
        // Cancel any ongoing animation
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    }
    
    showProcessingIndicators() {
        // Add visual indicators that processing is active
        const processingAnimation = document.querySelector('.processing-animation');
        if (processingAnimation) {
            processingAnimation.style.opacity = '1';
        }
    }
    
    hideProcessingIndicators() {
        // Hide processing indicators
        const processingAnimation = document.querySelector('.processing-animation');
        if (processingAnimation) {
            processingAnimation.style.opacity = '0.5';
        }
    }
}

// Initialize progress UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.progressUI = new ProgressUI();
    console.log('Progress UI initialized');
}); 