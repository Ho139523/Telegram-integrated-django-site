$(document).ready(function() {
    $('#id_shipping_country').change(function() {
        var country_code = $(this).val();
        var provinceSelect = $('#id_shipping_province');



        // Clear current provinces
        provinceSelect.empty();

        if (country_code) {
            $.ajax({
                url: '/accounts/get-provinces/',  // Ensure this URL matches the one in urls.py
                data: {
                    'country_code': country_code
                },
                success: function(data) {
                    // Populate the province select box with the received provinces
                    $.each(data, function(key, value) {
                        provinceSelect.append(new Option(value[1], value[1]));
                    });
                },
                error: function(xhr, status, error) {
                    console.log("Error fetching provinces: " + error);
                }
            });
        }
    });
});
