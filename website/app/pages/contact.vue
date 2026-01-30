<template>
	<div>

		<!-- 🔥 TOP BANNER -->
		<div class="w-full bg-cover bg-center min-h-[480px] relative flex items-center"
			style="background-image: url('/banners/banner2.png');">
			<!-- Overlay -->
			<div class="absolute inset-0 bg-black/40"></div>

			<!-- Text Content -->
			<div class="relative container text-white">
				<h1 class="text-4xl font-bold mb-3">Contact Us</h1>
				<p class="text-lg text-white/80 max-w-xl">
					We're here to help with orders, product questions, or anything you need.
				</p>
			</div>
		</div>

		<!-- 🔥 MAIN CONTACT SECTION -->
		<section class="mt-16 mb-20">
			<div class="container">

				<div class="grid md:grid-cols-2 gap-16">

					<!-- LEFT SIDE INFO -->
					<div class="space-y-6">

						<p class="text-brand-textSoft leading-relaxed max-w-md">
							Need support with your cookware, orders, or anything else?
							We’re always here to help. Reach out anytime!
						</p>

						<div class="">

							<!-- Address -->
							<div class="flex items-start gap-4 mb-4">
								<div
									class="w-12 h-12 flex items-center justify-center bg-brand-primary rounded-full text-white text-xl">
									📍
								</div>
								<p class="text-brand-text">
									<strong>KC Home Bazaar</strong> <br />
									Near Jayagopal pharmacy, police lane, Kottakkal
								</p>
							</div>

							<!-- Phone -->
							<div class="flex items-center gap-4 mb-4">
								<div
									class="w-12 h-12 flex items-center justify-center bg-brand-primary rounded-full text-white text-xl">
									📞
								</div>
								<a href="tel:+918075161117" class="text-brand-text hover:text-brand-primary transition">
									+91 8075161117
								</a>
							</div>

							<!-- Email -->
							<div class="flex items-center gap-4">
								<div
									class="w-12 h-12 flex items-center justify-center bg-brand-primary rounded-full text-white text-xl">
									✉️
								</div>
								<a href="mailto:support@kchomebazaar.com"
									class="text-brand-text hover:text-brand-primary transition">
									support@kchomebazaar.com
								</a>
							</div>

						</div>
					</div>

					<!-- RIGHT SIDE FORM -->
					<div class="bg-white shadow-lg rounded-xl p-10">
						<h2 class="text-2xl font-semibold text-brand-primary mb-6">Send us a message</h2>

						<form @submit.prevent="submitForm" class="space-y-6">

							<div>
								<label class="form-label">Name</label>
								<input v-model="form.name" type="text" class="form-input" placeholder="Your name"
									required />
							</div>

							<div>
								<label class="form-label">Email</label>
								<input v-model="form.email" type="email" class="form-input" placeholder="Your email"
									required />
							</div>

							<div>
								<label class="form-label">Message</label>
								<textarea v-model="form.message" rows="4" class="form-input"
									placeholder="Your message..." required></textarea>
							</div>

							<button
								class="w-full bg-brand-primary text-white py-3 rounded-lg hover:bg-brand-primaryLight transition font-semibold">
								Send Message
							</button>

						</form>
					</div>

				</div>

				<!-- MAP -->
				<div class="mt-20">
					<div
						class="w-full h-72 bg-gray-300 rounded-xl flex items-center justify-center text-brand-textSoft">
						Map Placeholder (Google Maps)
					</div>
				</div>

			</div>
		</section>

	</div>
</template>

<script setup>
import { ref } from "vue";

// Form state
const form = ref({
	name: "",
	email: "",
	message: "",
});

// Submit handler
const submitForm = async () => {
	// Basic validation (optional)
	if (!form.value.name || !form.value.email || !form.value.message) {
		alert("Please fill out all fields.");
		return;
	}

	// OPTIONAL: Structure for API call to your Django backend
	// Uncomment when backend is ready
	/*
	const { $axios } = useNuxtApp();
	try {
		const res = await $axios.post("/api/contact/", form.value);
		alert("Message sent successfully!");
	} catch (err) {
		console.error("Contact form error:", err);
		alert("Failed to send message.");
	}
	*/

	// For now show local success
	alert("Message submitted successfully!");

	// Reset form
	form.value = {
		name: "",
		email: "",
		message: "",
	};
};
</script>


<style scoped>
.form-label {
	@apply block text-brand-text font-medium mb-2;
}

.form-input {
	@apply w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:border-brand-primary;
}
</style>