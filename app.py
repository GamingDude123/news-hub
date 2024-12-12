from flask import Flask, jsonify, request # type: ignore
import requests # type: ignore

app = Flask(__name__)

# Configurations
NEWS_API_KEY = 'b2471c0c90be4b09912318468832c73e'  # Replace with your NewsAPI key
BIAS_RATINGS = {
    'left': ['The Guardian', 'CNN'],
    'center': ['BBC News', 'Reuters'],
    'right': ['Fox News', 'The Daily Wire']
}

@app.route('/news', methods=['GET'])
def get_news():
    category = request.args.get('category', 'general')
    url = f'https://newsapi.org/v2/top-headlines?category={category}&apiKey={NEWS_API_KEY}'
    response = requests.get(url).json()

    # Process news data
    articles = []
    for article in response.get('articles', []):
        source = article['source']['name']
        bias = next((k for k, v in BIAS_RATINGS.items() if source in v), 'unknown')
        articles.append({
            'title': article['title'],
            'source': source,
            'bias': bias,
            'url': article['url']
        })
    return jsonify(articles)

@app.route('/preferences', methods=['POST'])
def save_preferences():
    data = request.json
    # Save user preferences logic here
    return jsonify({'status': 'Preferences saved successfully'})

if __name__ == '__main__':
    app.run(debug=True)
