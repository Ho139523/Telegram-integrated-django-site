document.addEventListener('DOMContentLoaded', function() {
    const closeButtons = document.querySelectorAll('.btn-close');

    closeButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const alertWrapper = btn.closest('.alert-wrapper');
            const alert = btn.closest('.alert');

            alert.classList.add('fade-out');

            setTimeout(function() {
                alert.remove();

                // Check if there are no more alerts in the wrapper
                if (alertWrapper && alertWrapper.querySelectorAll('.alert').length === 0) {
                    alertWrapper.classList.add('fade-out');
                    setTimeout(function() {
                        alertWrapper.remove();
                    }, 1000); // Remove the wrapper after 1 second (1000ms) for fade-out transition
                }
            }, 1000); // Keep alert visible for 1 second before applying fade-out
        });
    });
});
