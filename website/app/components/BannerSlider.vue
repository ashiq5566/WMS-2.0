<template>
    <Swiper :modules="[Navigation, Pagination, Autoplay]" :loop="true" :pagination="{ clickable: true }"
        :autoplay="{ delay: 3000 }" class="w-full">
        <SwiperSlide v-for="(banner, i) in banners" :key="i">
            <!-- YOUR EXISTING BANNER STYLE -->
            <div class="w-full bg-cover bg-center min-h-[480px] rounded-lg flex flex-col justify-center px-6 py-12"
                :style="`background-image: url('${banner}');`">
                <!-- Banner Content Slot -->
                <slot />
            </div>
        </SwiperSlide>
    </Swiper>
</template>

<script setup>
import { Swiper, SwiperSlide } from "swiper/vue";
import { Navigation, Pagination, Autoplay } from "swiper/modules";
import "swiper/css";
import "swiper/css/pagination";

defineProps({
    banners: {
        type: Array,
        default: () => [],
    },
});
</script>
