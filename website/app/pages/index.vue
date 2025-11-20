<template>
	<div class="container">

		<!-- SLIDER -->
		<BannerSlider :banners="bannerImages">
			<div class="max-w-xl text-white">
				<h1 class="text-4xl md:text-5xl font-bold mb-4 drop-shadow-lg">
					Premium Stainless Steel Cookware
				</h1>
				<p class="text-lg md:text-xl text-gray-100 mb-6 drop-shadow">
					Built for chefs. Crafted for homes. Designed to last a lifetime.
				</p>
				<button class="bg-brand-primary text-white px-6 py-3 rounded-lg hover:bg-brand-primaryLight">
					Shop Now
				</button>
			</div>
		</BannerSlider>

		<!-- Featured Catagories -->
		<section class="mt-10">
			<div class="container grid grid-cols-2 md:grid-cols-4 gap-6">
				<div class="bg-white shadow rounded-lg p-6 text-center hover:shadow-lg transition">
					<img src="/icons/pan.png" class="h-20 mx-auto mb-4" />
					<h3 class="font-semibold">Frying Pans</h3>
				</div>
				<div class="bg-white shadow rounded-lg p-6 text-center hover:shadow-lg transition">
					<img src="/icons/pot.png" class="h-20 mx-auto mb-4" />
					<h3 class="font-semibold">Cookware Sets</h3>
				</div>
				<div class="bg-white shadow rounded-lg p-6 text-center hover:shadow-lg transition">
					<img src="/icons/pan.png" class="h-20 mx-auto mb-4" />
					<h3 class="font-semibold">Kitchen Tools</h3>
				</div>
				<div class="bg-white shadow rounded-lg p-6 text-center hover:shadow-lg transition">
					<img src="/icons/pot.png" class="h-20 mx-auto mb-4" />
					<h3 class="font-semibold">Steel Bowls</h3>
				</div>
			</div>
		</section>

		<!-- Best Seller -->
		<section class="mt-16">
			<div class="container">

				<!-- Section Title -->
				<h2 class="text-2xl font-bold text-brand-primary mb-6">
					Best Sellers
				</h2>

				<!-- Products Grid -->
				<div class="grid grid-cols-2 md:grid-cols-4 gap-6">

					<!-- Product Card -->
					<div class="bg-white shadow rounded-lg overflow-hidden hover:shadow-xl transition">
						<img src="/products/pan.png" class="w-full h-40 object-cover" />
						<div class="p-4">
							<h3 class="font-semibold text-brand-text">Premium Steel Fry Pan</h3>
							<p class="text-brand-accent font-semibold mt-2">₹1,499</p>
						</div>
					</div>

					<div class="bg-white shadow rounded-lg overflow-hidden hover:shadow-xl transition">
						<img src="/products/pan.png" class="w-full h-40 object-cover" />
						<div class="p-4">
							<h3 class="font-semibold text-brand-text">Tri-Ply Steel Cook Pot</h3>
							<p class="text-brand-accent font-semibold mt-2">₹2,199</p>
						</div>
					</div>

					<div class="bg-white shadow rounded-lg overflow-hidden hover:shadow-xl transition">
						<img src="/products/pan.png" class="w-full h-40 object-cover" />
						<div class="p-4">
							<h3 class="font-semibold text-brand-text">Flat Steel Tawa</h3>
							<p class="text-brand-accent font-semibold mt-2">₹999</p>
						</div>
					</div>

					<div class="bg-white shadow rounded-lg overflow-hidden hover:shadow-xl transition">
						<img src="/products/pan.png" class="w-full h-40 object-cover" />
						<div class="p-4">
							<h3 class="font-semibold text-brand-text">Stainless Steel Kadai</h3>
							<p class="text-brand-accent font-semibold mt-2">₹1,799</p>
						</div>
					</div>

				</div>

				<!-- Why Choose Us -->
				<section class="mt-20 py-12 bg-brand-surface rounded-lg">
					<div class="container">

						<!-- Section Title -->
						<h2 class="text-3xl font-bold text-brand-primary text-center mb-10">
							Why Choose Us
						</h2>

						<!-- 3 Columns -->
						<div class="grid md:grid-cols-3 gap-10 text-center">

							<!-- Feature 1 -->
							<div class="flex flex-col items-center">
								<img src="/icons/premium.png" class="h-20 mb-4" />
								<h3 class="text-xl font-semibold text-brand-primary">Premium Steel</h3>
								<p class="text-brand-textSoft mt-2 max-w-xs">
									High-grade stainless steel engineered for durability, performance, and everyday cooking comfort.
								</p>
							</div>

							<!-- Feature 2 -->
							<div class="flex flex-col items-center">
								<img src="/icons/approved.png" class="h-20 mb-4" />
								<h3 class="text-xl font-semibold text-brand-primary">Chef Approved</h3>
								<p class="text-brand-textSoft mt-2 max-w-xs">
									Our cookware is trusted by culinary professionals across top kitchens worldwide.
								</p>
							</div>

							<!-- Feature 3 -->
							<div class="flex flex-col items-center">
								<img src="/icons/warranty.png" class="h-20 mb-4" />
								<h3 class="text-xl font-semibold text-brand-primary">Lifetime Warranty</h3>
								<p class="text-brand-textSoft mt-2 max-w-xs">
									Built to last. Every product comes with long-term reliability backed by our warranty promise.
								</p>
							</div>

						</div>

					</div>
				</section>

				<!-- About Us -->
				<section class="mt-20 py-16">
					<div class="container grid md:grid-cols-2 gap-12 items-center">

						<!-- About Image -->
						<div>
							<img src="/about/about.png" class="w-full h-[350px] object-cover rounded-lg shadow" />
						</div>

						<!-- About Content -->
						<div>
							<h2 class="text-3xl font-bold text-brand-primary mb-4">
								Craftsmanship Meets Modern Cooking
							</h2>

							<p class="text-brand-textSoft leading-relaxed mb-6">
								For years, we’ve specialized in creating high-quality stainless steel cookware
								that blends durability, beauty, and performance.
								Every product is crafted with precision using premium materials —
								built for chefs, perfect for home kitchens.
							</p>

							<p class="text-brand-textSoft leading-relaxed mb-6">
								Our mission is simple: to elevate your cooking experience with steel
								that lasts a lifetime. From tri-ply pans to professional-grade kitchen essentials,
								each piece reflects a promise of quality and trust.
							</p>

							<button class="bg-brand-primary text-white px-6 py-3 rounded-lg hover:bg-brand-primaryLight">
								Learn More
							</button>
						</div>

					</div>
				</section>


			</div>
		</section>

	</div>
</template>

<script setup>
const bannerImages = [
	"/banners/banner1.png",
	"/banners/banner2.png",
];
</script>
