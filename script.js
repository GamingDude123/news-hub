document.addEventListener("DOMContentLoaded", () => {
    const newsContainer = document.getElementById('news-container');

    // Fetch and display news
    fetch('/news')
        .then(response => response.json())
        .then(articles => {
            articles.forEach(article => {
                const card = document.createElement('div');
                card.className = 'news-card';
                card.innerHTML = `
                    <h3>${article.title}</h3>
                    <p>Source: ${article.source} | Bias: ${article.bias}</p>
                    <a href="${article.url}" target="_blank">Read More</a>
                `;
                newsContainer.appendChild(card);
            });
        })
        .catch(err => console.error('Error fetching news:', err));
});