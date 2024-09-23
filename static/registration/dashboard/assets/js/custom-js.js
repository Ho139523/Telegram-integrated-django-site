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





// Submit the form when an image is selected
document.addEventListener('DOMContentLoaded', function() {
    let fileInput = document.getElementById('id_header_image');
    
    if (fileInput) {  // Ensure the file input is found
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                document.getElementById('headerForm').submit();
                console.log("form submitted.");
            } else {
                console.log("No file selected.");
            }
        });
    }
});


// Submit the form when an image is selected
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('id_avatar_image')) {  // Ensure the file input is found
        document.getElementById('id_avatar_image').addEventListener('change', function() {
            if (this.files.length > 0) {
                document.getElementById('avatarForm').submit();
            } else {
                console.log("No file selected.");
            }
        });
    }
});

