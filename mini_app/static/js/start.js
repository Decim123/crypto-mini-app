document.addEventListener('DOMContentLoaded', function () {
    const tg = window.Telegram.WebApp;
    tg.expand(); // Расширить приложение на весь экран

    const tg_id = tg.initDataUnsafe.user.id;
    const username = tg.initDataUnsafe.user.username;
    const coins = Math.floor(Math.random() * (10000 - 2000 + 1)) + 2000;
    const isPremium = tg.initDataUnsafe.user.is_premium;

    logToServer(`User ID: ${tg_id}, Username: ${username}, Coins: ${coins}, Is Premium: ${isPremium}`);

    // Получаем параметр ref из URL
    const urlParams = new URLSearchParams(window.location.search);
    const referrerId = urlParams.get('ref');
    logToServer(`Referrer ID from URL: ${referrerId}`);

    document.getElementById('tg_id').value = tg_id;
    document.getElementById('username').value = username;
    document.getElementById('coins').value = coins;

    // Если пользователь новый, показываем анимацию начисления монет
    fetch(`/check_user?tg_id=${tg_id}`)
        .then(response => response.json())
        .then(data => {
            if (!data.exists) {
                // Пользователь новый, показываем анимацию начисления монет
                logToServer('New user detected. Showing coin animation.');
                showCoinAnimation(coins, referrerId);
            } else {
                // Пользователь уже существует, переходим на страницу main
                logToServer('Existing user detected. Redirecting to main.');
                window.location.href = `/main?tg_id=${tg_id}`;
            }
        });

    function showCoinAnimation(coins, referrerId) {
        const coinsStr = coins.toString();
        const digits = coinsStr.split('');
        const digitsContainer = document.getElementById('digits_container');

        digits.forEach((digit, index) => {
            const digitSpan = document.createElement('span');
            digitSpan.classList.add('digit');
            digitSpan.textContent = digit;
            digitSpan.style.animationDelay = `${index * 0.5}s`;
            digitsContainer.appendChild(digitSpan);
        });

        setTimeout(() => {
            document.getElementById('tgr_text').classList.add('zoom-in');
            document.getElementById('received_text').classList.add('zoom-in');
        }, digits.length * 500);

        setTimeout(() => {
            document.body.classList.add('fade-out');
        }, 3500);

        setTimeout(() => {
            logToServer('Registering user after animation.');
            registerUser(tg_id, username, coins, referrerId, isPremium);
        }, 4000);
    }

    function registerUser(tg_id, username, coins, referrerId, isPremium) {
        const requestBody = {
            tg_id: tg_id,
            username: username,
            coins: coins,
            is_premium: isPremium
        };

        if (referrerId) {
            requestBody.referrer_id = referrerId;
        }

        logToServer('Request body for registration: ' + JSON.stringify(requestBody));

        fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        }).then(response => response.json())
          .then(data => {
              logToServer('Response from /register: ' + JSON.stringify(data));
              if (data.status === 'success') {
                  window.location.href = `/main?tg_id=${tg_id}`;
              }
          });
    }

    function logToServer(message) {
        fetch('/log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
    }
});
