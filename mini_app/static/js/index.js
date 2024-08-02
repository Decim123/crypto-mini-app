document.addEventListener('DOMContentLoaded', function () {
    Telegram.WebApp.ready();
    Telegram.WebApp.expand(); // Расширить приложение на весь экран
    const user = Telegram.WebApp.initDataUnsafe.user;

    // Получаем параметр ref из URL
    const urlParams = new URLSearchParams(window.location.search);
    const referrerId = urlParams.get('ref');

    if (user) {
        fetch(`/check_user?tg_id=${user.id}`)
            .then(response => response.json())
            .then(data => {
                if (data.exists) {
                    window.location.href = `/main?tg_id=${user.id}`;
                } else {
                    if (referrerId) {
                        window.location.href = `/start?tg_id=${user.id}&username=${user.username || "No username"}&ref=${referrerId}`;
                    } else {
                        window.location.href = `/start?tg_id=${user.id}&username=${user.username || "No username"}`;
                    }
                }
            });
    }
});
