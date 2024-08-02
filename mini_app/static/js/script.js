document.addEventListener('DOMContentLoaded', function() {
    const coinsElement = document.getElementById('coins');
    const coins = parseInt(coinsElement.textContent, 10);
    coinsElement.textContent = '0';

    let count = 0;
    const interval = setInterval(() => {
        count += Math.floor(coins / 100);
        coinsElement.textContent = count;

        if (count >= coins) {
            clearInterval(interval);
            coinsElement.textContent = coins;
        }
    }, 30);
});
