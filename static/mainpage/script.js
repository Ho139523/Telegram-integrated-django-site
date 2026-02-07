// Theme toggle
const root = document.body;
const themeBtn = document.getElementById("themeBtn");
const themeIcon = document.getElementById("themeIcon");

function applyTheme(theme){
  root.setAttribute("data-theme", theme);
  themeIcon.className = (theme === "dark") ? "bi bi-sun" : "bi bi-moon-stars";
}
applyTheme(localStorage.getItem("theme") || "light");
themeBtn.addEventListener("click", () => {
  const next = (root.getAttribute("data-theme") === "light") ? "dark" : "light";
  localStorage.setItem("theme", next);
  applyTheme(next);
});

// bottom nav active state
document.querySelectorAll(".desktop-bottom-nav .nav-item-btn").forEach(btn => {
  btn.addEventListener("click", () => {
	document.querySelectorAll(".desktop-bottom-nav .nav-item-btn").forEach(b => b.classList.remove("active"));
	btn.classList.add("active");
  });
});

// Data with discounts in paginated vitrines
const newestProducts = Array.from({length: 22}, (_, i) => {
  const hasDiscount = (i % 5 === 2); // some items discounted
  const base = 390000 + i*75000;
  const percent = [10,15,20,25,30][i % 5];
  const finalPrice = hasDiscount ? Math.round(base * (1 - percent/100)) : base;

  return {
	id: "n" + (i+1),
	title: `محصول جدید شماره ${i+1}`,
	desc: ["کیفیت عالی", "ارسال سریع", "پرفروش", "اقتصادی"][i % 4],
	seed: "new" + (i+10),
	badge: hasDiscount ? "تخفیف ویژه" : ["جدید","محبوب","منتخب","پیشنهادی"][i % 4],
	badgeIcon: hasDiscount ? "bi-lightning-charge" : ["bi-sparkles","bi-heart","bi-star","bi-award"][i % 4],
	discountPercent: hasDiscount ? percent : null,
	priceOriginal: base,
	priceFinal: finalPrice
  };
});

const homeProducts = Array.from({length: 18}, (_, i) => {
  const hasDiscount = (i % 4 === 1);
  const base = 280000 + i*63000;
  const percent = [10,12,18,22][i % 4];
  const finalPrice = hasDiscount ? Math.round(base * (1 - percent/100)) : base;

  return {
	id: "h" + (i+1),
	title: `کالای خانه ${i+1}`,
	desc: ["خانه و آشپزخانه", "کاربردی", "کیفیت بالا", "ارسال فوری"][i % 4],
	seed: "home" + (i+30),
	badge: hasDiscount ? "تخفیف ویژه" : ["منتخب","پیشنهادی","محبوب","جدید"][i % 4],
	badgeIcon: hasDiscount ? "bi-lightning-charge" : ["bi-award","bi-check2-circle","bi-heart","bi-sparkles"][i % 4],
	discountPercent: hasDiscount ? percent : null,
	priceOriginal: base,
	priceFinal: finalPrice
  };
});

function fmtToman(num){
  return num.toLocaleString("fa-IR") + " تومان";
}

function productCardHTML(p){
  const discountBadge = p.discountPercent
	? `<span class="discount-badge">٪${p.discountPercent}-</span>`
	: "";

  const priceBlock = p.discountPercent
	? `
	  <div class="d-flex align-items-center justify-content-between">
		<div class="d-flex flex-column">
		  <span class="old-price">${fmtToman(p.priceOriginal)}</span>
		  <span class="price">${fmtToman(p.priceFinal)}</span>
		</div>
		<div class="d-flex align-items-center gap-2">
		  <span class="discount-pill"><i class="bi bi-percent"></i> ${p.discountPercent}%</span>
		  <button class="btn btn-sm btn-grad"><i class="bi bi-cart-plus"></i></button>
		</div>
	  </div>
	`
	: `
	  <div class="d-flex align-items-center justify-content-between">
		<span class="price">${fmtToman(p.priceFinal)}</span>
		<button class="btn btn-sm btn-grad"><i class="bi bi-cart-plus"></i></button>
	  </div>
	`;

  return `
	<div class="col-12 col-sm-6 col-lg-3">
	  <div class="product-card">
		<div class="thumb" style="background-image:url('https://picsum.photos/seed/${p.seed}/1200/700'); background-size:cover; background-position:center;">
		  ${discountBadge}
		</div>
		<div class="p-3">
		  <div class="d-flex align-items-center justify-content-between mb-2">
			<span class="badge-soft"><i class="bi ${p.badgeIcon} me-1"></i> ${p.badge}</span>
			<button class="btn btn-sm btn-outline-secondary" title="ذخیره برای بعدا">
			  <i class="bi bi-bookmark"></i>
			</button>
		  </div>
		  <div class="fw-bold mb-1">${p.title}</div>
		  <div class="muted small mb-3">${p.desc}</div>
		  ${priceBlock}
		</div>
	  </div>
	</div>
  `;
}

/* FIX #3: Pagination format => قبلی 1 2 ... 9 10 بعدی */
function renderPaginationPretty(containerUl, currentPage, totalPages, onChange){
  const makeItem = (label, page, disabled=false, active=false, aria=null) => {
	const li = document.createElement("li");
	li.className = `page-item ${disabled ? "disabled" : ""} ${active ? "active" : ""}`;
	const a = document.createElement("a");
	a.className = "page-link";
	a.href = "#";
	a.textContent = label;
	if(aria) a.setAttribute("aria-label", aria);
	a.addEventListener("click", (e) => {
	  e.preventDefault();
	  if(disabled || page === currentPage) return;
	  onChange(page);
	});
	li.appendChild(a);
	return li;
  };

  const dots = () => {
	const li = document.createElement("li");
	li.className = "page-item disabled";
	li.innerHTML = `<span class="page-link">…</span>`;
	return li;
  };

  containerUl.innerHTML = "";

  // prev
  containerUl.appendChild(makeItem("قبلی", currentPage-1, currentPage === 1, false, "previous"));

  // pages
  if(totalPages <= 5){
	for(let p=1; p<=totalPages; p++){
	  containerUl.appendChild(makeItem(String(p), p, false, p === currentPage));
	}
  } else {
	// 1 2 ... (n-1) n
	containerUl.appendChild(makeItem("1", 1, false, currentPage === 1));
	containerUl.appendChild(makeItem("2", 2, false, currentPage === 2));

	containerUl.appendChild(dots());

	containerUl.appendChild(makeItem(String(totalPages-1), totalPages-1, false, currentPage === totalPages-1));
	containerUl.appendChild(makeItem(String(totalPages), totalPages, false, currentPage === totalPages));
  }

  // next
  containerUl.appendChild(makeItem("بعدی", currentPage+1, currentPage === totalPages, false, "next"));
}

function setupPaginatedShowcase({data, gridId, paginationId, perPage=8}){
  const grid = document.getElementById(gridId);
  const pagination = document.getElementById(paginationId);

  let currentPage = 1;
  const totalPages = Math.max(1, Math.ceil(data.length / perPage));

  const render = () => {
	const start = (currentPage - 1) * perPage;
	const pageItems = data.slice(start, start + perPage);
	grid.innerHTML = pageItems.map(productCardHTML).join("");

	renderPaginationPretty(pagination, currentPage, totalPages, (nextPage) => {
	  currentPage = nextPage;
	  render();
	  grid.scrollIntoView({behavior:"smooth", block:"start"});
	});
  };

  render();
}

setupPaginatedShowcase({ data: newestProducts, gridId: "newestGrid", paginationId: "newestPagination", perPage: 8 });
setupPaginatedShowcase({ data: homeProducts, gridId: "homeGrid", paginationId: "homePagination", perPage: 8 });