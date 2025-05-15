document.addEventListener("DOMContentLoaded", function () {
	const countryField = document.getElementById("id_country");
	const provinceField = document.getElementById("id_province");
	const cityField = document.getElementById("id_city");

	function updateSelectField(field, items) {
		if (!field) return;
		field.innerHTML = '<option value="">---------</option>';
		items.forEach(item => {
			const option = document.createElement("option");
			option.value = item.name; // ✅ For form submission
			option.textContent = item.name;
			option.dataset.code = item.code; // ✅ For fetch use
			field.appendChild(option);
		});
	}

	function fetchProvinces(countryCode) {
		fetch(`/accounts/get_provinces/?country=${countryCode}`)
			.then(response => response.json())
			.then(data => {
				if (data.error) {
					console.error(data.error);
					return;
				}
				updateSelectField(provinceField, data.provinces);
				updateSelectField(cityField, []); // Clear cities
			})
			.catch(error => console.error("Error fetching provinces:", error));
	}

	function fetchCities(countryCode, provinceCode) {
		fetch(`/accounts/get_cities/?country=${countryCode}&province=${provinceCode}`)
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
});