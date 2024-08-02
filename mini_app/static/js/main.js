document.addEventListener('DOMContentLoaded', function () {
    const tg = window.Telegram.WebApp;
    const tg_id = tg.initDataUnsafe.user.id;

    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const targetPage = item.getAttribute('data-target');
            if (targetPage === '/main') {
                // Do nothing if the target page is '/main'
                return;
            }
            if (targetPage === '/leaderboard' || targetPage === '/friends' || targetPage === '/tasks') {
                window.location.href = `${targetPage}?tg_id=${tg_id}`;
            } else {
                window.location.href = `${targetPage}`;
            }
        });
    });

    fetch(`/user_data?tg_id=${tg_id}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                window.location.href = `/start`;
            } else {
                document.querySelector('.coin-amount').textContent = data.coins.toLocaleString();

                const walletContainer = document.getElementById('wallet-container');
                walletContainer.innerHTML = '';

                if (data.wallet) {
                    const walletDisplay = document.createElement('div');
                    walletDisplay.className = 'wallet-display';
                    walletDisplay.textContent = `${data.wallet.slice(0, 3)}...${data.wallet.slice(-3)}`;
                    walletContainer.appendChild(walletDisplay);
                } else {
                    const walletInput = document.createElement('input');
                    walletInput.type = 'text';
                    walletInput.className = 'wallet-input';
                    walletInput.placeholder = 'TON address';
                    walletInput.addEventListener('change', () => {
                        const walletAddress = walletInput.value.trim();
                        if (isValidTonAddress(walletAddress)) {
                            fetch('/wallet', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    tg_id: tg_id,
                                    account: { address: walletAddress }
                                }),
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.status === 'success') {
                                    walletInput.style.transition = 'all 0.5s ease';
                                    walletInput.style.width = '0';
                                    setTimeout(() => {
                                        walletInput.style.backgroundColor = '#ADD8E6';
                                        walletInput.style.width = '100%';
                                        setTimeout(() => {
                                            walletInput.value = 'Connected';
                                            setTimeout(() => {
                                                walletInput.value = `${walletAddress.slice(0, 3)}...${walletAddress.slice(-3)}`;
                                                walletInput.disabled = true;
                                                walletInput.classList.add('wallet-display');
                                                walletInput.classList.remove('wallet-input');
                                            }, 2000);
                                        }, 500);
                                    }, 500);
                                }
                            });
                        } else {
                            walletInput.classList.add('error');
                            setTimeout(() => {
                                walletInput.classList.remove('error');
                            }, 500);
                        }
                    });
                    walletContainer.appendChild(walletInput);
                }

                const languageDropdown = document.getElementById('language-dropdown');
                if (data.lang) {
                    languageDropdown.value = data.lang;
                }
                languageDropdown.addEventListener('change', () => {
                    const selectedLanguage = languageDropdown.value;
                    fetch('/update_language', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            tg_id: tg_id,
                            lang: selectedLanguage
                        }),
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            console.log('Language updated successfully');
                            window.location.reload(); // Перезагрузка страницы после успешного обновления языка
                        }
                    });
                });
            }
        });

    function isValidTonAddress(address) {
        return /^([a-zA-Z0-9_-]{48,64})$/.test(address);
    }

    fetch('/get_news')
        .then(response => response.json())
        .then(newsData => {
            const slidesContainer = document.querySelector('.news-slide');
            const dotsContainer = document.querySelector('.slider-dots');

            let currentIndex = 0;

            newsData.forEach((news, index) => {
                const slide = document.createElement('div');
                slide.className = 'news-item';
                slide.innerHTML = `<p>${news.text}</p>`;
                
                const buttonText = news.link && news.link !== 'No Link' ? 'Open' : ':)';
                const buttonClass = news.link && news.link !== 'No Link' ? 'news-button' : 'news-button disabled';

                slide.innerHTML += `<button class="${buttonClass}" ${news.link && news.link !== 'No Link' ? `onclick="window.open('${news.link}', '_blank')"` : ''}>${buttonText}</button>`;
                
                slidesContainer.appendChild(slide);

                const dot = document.createElement('span');
                dot.className = 'dot';
                dot.addEventListener('click', () => {
                    showSlide(index);
                });
                dotsContainer.appendChild(dot);
            });

            function showSlide(index) {
                const slides = document.querySelectorAll('.news-item');
                const dots = document.querySelectorAll('.dot');

                slides.forEach((slide, i) => {
                    slide.style.display = (i === index) ? 'block' : 'none';
                    dots[i].classList.toggle('active', i === index);
                });

                currentIndex = index;
            }

            function nextSlide() {
                currentIndex = (currentIndex + 1) % newsData.length;
                showSlide(currentIndex);
            }

            function prevSlide() {
                currentIndex = (currentIndex - 1 + newsData.length) % newsData.length;
                showSlide(currentIndex);
            }

            let startX = 0;

            document.querySelector('.news-slider').addEventListener('touchstart', (e) => {
                startX = e.touches[0].clientX;
            });

            document.querySelector('.news-slider').addEventListener('touchend', (e) => {
                const endX = e.changedTouches[0].clientX;
                if (startX > endX + 30) {
                    nextSlide();
                } else if (startX < endX - 30) {
                    prevSlide();
                }
            });

            showSlide(currentIndex);
        });
});
