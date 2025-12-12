"use strict";

// хедер
window.addEventListener('scroll', function() {
    // УБИРАЕМ эту проверку:
    // if (window.innerWidth <= 768) return;
    
    const header = document.getElementById('header');
    const body = document.body;
    
    console.log('Scroll position:', window.scrollY);
    
    if (window.scrollY > 50) {
        header.classList.add('small');
        body.classList.add('small-header');
        console.log('Header minimized');
    } else {
        header.classList.remove('small');
        body.classList.remove('small-header');
        console.log('Header normal');
    }
});

// Проверяем при загрузке если уже прокручено
window.addEventListener('load', function() {
    // УБИРАЕМ эту проверку:
    // if (window.innerWidth <= 768) return;
    
    const header = document.getElementById('header');
    const body = document.body;
    
    if (window.scrollY > 50) {
        header.classList.add('small');
        body.classList.add('small-header');
    }
});



// счетчик подписчиков
(function() {
    'use strict';
    
    const CONFIG = {
        channel: 'NEFTGG',
        updateInterval: 300000, // 5 минут
        fallbackCount: 2089,
        animationDuration: 2000, // Длительность анимации в мс
        easing: 'easeOutQuad' // Функция плавности
    };
    
    // Функция для плавного перехода
    function easeOutQuad(t) {
        return t * (2 - t);
    }
    
    // Функция анимации счетчика
    function animateCounter(element, start, end, duration) {
        const startTime = performance.now();
        const diff = end - start;
        
        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Применяем функцию плавности
            const easedProgress = easeOutQuad(progress);
            const currentValue = Math.floor(start + diff * easedProgress);
            
            element.textContent = currentValue.toLocaleString('ru-RU');
            
            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.textContent = end.toLocaleString('ru-RU');
            }
        }
        
        requestAnimationFrame(update);
    }
    
    async function getSubscribers() {
        // Метод 1: tg.i-c-a.su
        try {
            const response = await fetch(`https://tg.i-c-a.su/json/${CONFIG.channel}`);
            const data = await response.json();
            if (data.members_count > 0) return data.members_count;
        } catch (error) {
            console.log('Метод 1 не сработал');
        }
        
        // Метод 2: telegram-widget
        try {
            const response = await fetch(`https://telegram-widget.vercel.app/api/channel?username=${CONFIG.channel}`);
            const data = await response.json();
            if (data.members > 0) return data.members;
        } catch (error) {
            console.log('Метод 2 не сработал');
        }
        
        return CONFIG.fallbackCount;
    }
    
    async function updateCounter() {
        const element = document.getElementById('subscribersCount');
        if (element) {
            const currentCount = parseInt(element.textContent.replace(/\s/g, '')) || 0;
            const newCount = await getSubscribers();
            
            if (currentCount !== newCount) {
                animateCounter(element, currentCount, newCount, CONFIG.animationDuration);
                console.log('✅ Подписчиков:', newCount);
            }
        }
    }
    
    // Инициализация с анимацией от 0
    document.addEventListener('DOMContentLoaded', async function() {
        const element = document.getElementById('subscribersCount');
        if (element) {
            // Сначала установим 0
            element.textContent = '0';
            
            // Дадим странице немного загрузиться
            setTimeout(async () => {
                const count = await getSubscribers();
                animateCounter(element, 0, count, CONFIG.animationDuration);
                
                // Запускаем периодическое обновление
                setInterval(updateCounter, CONFIG.updateInterval);
            }, 500);
        }
    });
})();




// счетчик подписчиков
(function() {
    'use strict';
    
    const CONFIG = {
        channel: 'NEFTGG',
        updateInterval: 300000, // 5 минут
        fallbackCount: 2089,
        animationDuration: 2000, // Длительность анимации в мс
        easing: 'easeOutQuad' // Функция плавности
    };
    
    // Функция для плавного перехода
    function easeOutQuad(t) {
        return t * (2 - t);
    }
    
    // Функция анимации счетчика
    function animateCounter(element, start, end, duration) {
        const startTime = performance.now();
        const diff = end - start;
        
        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Применяем функцию плавности
            const easedProgress = easeOutQuad(progress);
            const currentValue = Math.floor(start + diff * easedProgress);
            
            // Убрано .toLocaleString('ru-RU') - теперь без разделителей тысяч
            element.textContent = currentValue;
            
            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                // Также убрано здесь
                element.textContent = end;
            }
        }
        
        requestAnimationFrame(update);
    }
    
    async function getSubscribers() {
        // Метод 1: tg.i-c-a.su
        try {
            const response = await fetch(`https://tg.i-c-a.su/json/${CONFIG.channel}`);
            const data = await response.json();
            if (data.members_count > 0) return data.members_count;
        } catch (error) {
            console.log('Метод 1 не сработал');
        }
        
        // Метод 2: telegram-widget
        try {
            const response = await fetch(`https://telegram-widget.vercel.app/api/channel?username=${CONFIG.channel}`);
            const data = await response.json();
            if (data.members > 0) return data.members;
        } catch (error) {
            console.log('Метод 2 не сработал');
        }
        
        return CONFIG.fallbackCount;
    }
    
    async function updateCounter() {
        const element = document.getElementById('subscribersCount');
        if (element) {
            // Убираем все нецифровые символы при получении текущего значения
            const currentCount = parseInt(element.textContent.replace(/\D/g, '')) || 0;
            const newCount = await getSubscribers();
            
            if (currentCount !== newCount) {
                animateCounter(element, currentCount, newCount, CONFIG.animationDuration);
                console.log('✅ Подписчиков:', newCount);
            }
        }
    }
    
    // Инициализация с анимацией от 0
    document.addEventListener('DOMContentLoaded', async function() {
        const element = document.getElementById('subscribersCount');
        if (element) {
            // Сначала установим 0
            element.textContent = '0';
            
            // Дадим странице немного загрузиться
            setTimeout(async () => {
                const count = await getSubscribers();
                animateCounter(element, 0, count, CONFIG.animationDuration);
                
                // Запускаем периодическое обновление
                setInterval(updateCounter, CONFIG.updateInterval);
            }, 500);
        }
    });
})();
