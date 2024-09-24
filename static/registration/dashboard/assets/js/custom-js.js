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



document.getElementById('editProfileBtn').addEventListener('click', function() {
  // Toggle visibility of profile info and form fields
  const aboutMeText = document.getElementById('aboutMeText');
  const fullNameText = document.getElementById('fullNameText');
  const phoneText = document.getElementById('phoneText');
  const addressText = document.getElementById('addressText');
  const birthdayText = document.getElementById('birthdayText');
  const socialText = document.getElementById('socialText');
  
  const aboutmeField = document.getElementById('aboutmeField');
  const fnameField = document.getElementById('fnameField');
  const lnameField = document.getElementById('lnameField');
  const phoneField = document.getElementById('phoneField');
  const addressField = document.getElementById('addressField');
  const birthdayField = document.getElementById('birthdayField');
  const tweeterField = document.getElementById('tweeterField');
  const instagramField = document.getElementById('instagramField');
  
  // Hide static text and show form fields
  aboutMeText.classList.toggle('d-none');
  fullNameText.classList.toggle('d-none');
  phoneText.classList.toggle('d-none');
  addressText.classList.toggle('d-none');
  birthdayText.classList.toggle('d-none');
  socialText.classList.toggle('d-none');
  
  aboutmeField.classList.remove('d-none');
  fnameField.classList.remove('d-none');
  lnameField.classList.remove('d-none');
  phoneField.classList.remove('d-none');
  addressField.classList.remove('d-none');
  birthdayField.classList.remove('d-none');
  tweeterField.classList.remove('d-none');
  instagramField.classList.remove('d-none');

  // Change the edit icon to a submit button
  const icon = this.querySelector('i');
  if (icon.classList.contains('fa-user-edit')) {
    icon.classList.remove('fa-user-edit');
    icon.classList.add('fa-check');
    icon.setAttribute('title', 'Submit Changes');
    
  } else {
    // Submit the form when the tick icon is clicked
    document.getElementById('profileForm').submit();
  }
});

