document.addEventListener("DOMContentLoaded", function () {
	const countryField = document.getElementById("id_country");
	const provinceField = document.getElementById("id_province");
	const cityField = document.getElementById("id_city");
	const telIdField = document.getElementById("tel_id"); // hidden input
	const telId = telIdField ? telIdField.value : null;

	function updateSelectField(field, items) {
		if (!field) return;
		field.innerHTML = '<option value="">---------</option>';
		items.forEach(item => {
			const option = document.createElement("option");
			option.value = item.name;
			option.textContent = item.name;
			option.dataset.code = item.code;
			field.appendChild(option);
		});
	}

	function fetchProvinces(countryCode) {
		const data = {
			country: countryCode,
		};
		if (telId) {
			data.tel_id = telId;
		}

		fetch("/accounts/get_provinces/", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": getCSRFToken(),
			},
			body: JSON.stringify(data),
		})
			.then(response => response.json())
			.then(data => {
				if (data.error) {
					console.error(data.error);
					return;
				}
				updateSelectField(provinceField, data.provinces);
				updateSelectField(cityField, []);
			})
			.catch(error => console.error("Error fetching provinces:", error));
	}

	function fetchCities(countryCode, provinceCode) {
		const data = {
			country: countryCode,
			province: provinceCode,
		};
		if (telId) {
			data.tel_id = telId;
		}

		fetch("/accounts/get_cities/", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": getCSRFToken(),
			},
			body: JSON.stringify(data),
		})
			.then(response => response.json())
			.then(data => {
				if (data.error) {
					console.error(data.error);
					return;
				}
				updateSelectField(cityField, data.cities);
			})
			.catch(error => console.error("Error fetching cities:", error));
	}

	if (countryField) {
		countryField.addEventListener("change", function () {
			const selectedCountry = this.value;
			if (selectedCountry) {
				fetchProvinces(selectedCountry);
			} else {
				updateSelectField(provinceField, []);
				updateSelectField(cityField, []);
			}
		});
	}

	if (provinceField) {
		provinceField.addEventListener("change", function () {
			const selectedOption = this.options[this.selectedIndex];
			const provinceCode = selectedOption?.dataset.code;
			const selectedCountry = countryField.value;
			if (provinceCode && selectedCountry) {
				fetchCities(selectedCountry, provinceCode);
			} else {
				updateSelectField(cityField, []);
			}
		});
	}

	// Get CSRF token for POST requests
	function getCSRFToken() {
		const name = "csrftoken";
		const cookies = document.cookie.split(";");
		for (let i = 0; i < cookies.length; i++) {
			const cookie = cookies[i].trim();
			if (cookie.startsWith(name + "=")) {
				return decodeURIComponent(cookie.substring(name.length + 1));
			}
		}
		return "";
	}
});
