document.addEventListener("DOMContentLoaded", function () {
	const countryField = document.getElementById("id_country");
	const provinceField = document.getElementById("id_province");
	const cityField = document.getElementById("id_city");

	function updateSelectField(field, items) {
		if (!field) return;

		field.innerHTML = '<option value="">---------</option>';

		items.forEach(item => {
			const option = document.createElement("option");
			option.value = item.code;        // ذخیره CODE
			option.textContent = item.name;  // نمایش NAME
			field.appendChild(option);
		});
	}

	function fetchProvinces(countryCode) {
		fetch("/accounts/get_provinces/", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": getCSRFToken(),
			},
			body: JSON.stringify({ country: countryCode }),
		})
			.then(res => res.json())
			.then(data => {
				if (data.error) return;
				updateSelectField(provinceField, data.provinces);
				updateSelectField(cityField, []);
			});
	}

	function fetchCities(countryCode, provinceCode) {
		fetch("/accounts/get_cities/", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": getCSRFToken(),
			},
			body: JSON.stringify({
				country: countryCode,
				province: provinceCode,
			}),
		})
			.then(res => res.json())
			.then(data => {
				if (data.error) return;
				updateSelectField(cityField, data.cities);
			});
	}

	if (countryField) {
		countryField.addEventListener("change", function () {
			if (this.value) {
				fetchProvinces(this.value);
			} else {
				updateSelectField(provinceField, []);
				updateSelectField(cityField, []);
			}
		});
	}

	if (provinceField) {
		provinceField.addEventListener("change", function () {
			if (this.value && countryField.value) {
				fetchCities(countryField.value, this.value);
			} else {
				updateSelectField(cityField, []);
			}
		});
	}

	function getCSRFToken() {
		const name = "csrftoken";
		return document.cookie
			.split(";")
			.map(c => c.trim())
			.find(c => c.startsWith(name + "="))
			?.split("=")[1] || "";
	}
});
