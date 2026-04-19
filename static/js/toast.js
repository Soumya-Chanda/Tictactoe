/**
 * TicTacMaster — Toast Notification Utility
 * Usage: showToast('Message here', 'win' | 'loss' | 'draw' | 'info', durationMs)
 */

(function () {
    // Create toast element once
    const toast = document.createElement('div');
    toast.id = 'toast';
    document.body.appendChild(toast);

    let hideTimer = null;

    window.showToast = function (message, type = 'info', duration = 3000) {
        // Clear any pending hide
        if (hideTimer) clearTimeout(hideTimer);

        toast.textContent = message;
        toast.className = `show toast-${type}`;

        hideTimer = setTimeout(() => {
            toast.classList.remove('show');
        }, duration);
    };
})();
