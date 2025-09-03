import pandas as pd
import numpy as np
import ast
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

movies = pd.read_csv("C:/Users/shrey/Downloads/tmdb_5000_movies.csv")
credits = pd.read_csv("C:/Users/shrey/Downloads/tmdb_5000_credits.csv")
credits.rename(columns={'title': 'credit_title'}, inplace=True)

movies = movies.merge(credits, left_on='id', right_on='movie_id')

def extract_cast(text):
    try:
        data = ast.literal_eval(text)
        return " ".join([member['name'] for member in data[:3]])
    except:
        return ""

def extract_director(text):
    try:
        data = ast.literal_eval(text)
        for crew_member in data:
            if crew_member['job'] == 'Director':
                return crew_member['name']
        return ""
    except:
        return ""

def extract_genres(text):
    try:
        data = ast.literal_eval(text)
        return " ".join([genre['name'] for genre in data[:]])
    except:
        return ""

def extract_keywords(text):
    try:
        data = ast.literal_eval(text)
        # Take first 10 keyword names, lowercase, remove spaces inside names, then join with space
        return " ".join([kw['name'].lower().replace(" ", "") for kw in data[:10]])
    except:
        return ""

movies['cast'] = movies['cast'].apply(extract_cast)
movies['director'] = movies['crew'].apply(extract_director)
movies['keywords'] = movies['keywords'].apply(extract_keywords)
movies['genres'] = movies['genres'].apply(extract_genres)
movies['overview'] = movies['overview'].fillna("")

movies_df = movies[['title', 'overview', 'genres', 'cast', 'director', 'keywords', 'vote_average', 'release_date', 'popularity']].copy()
movies_df = movies_df.dropna()

features = ['genres', 'cast', 'director', 'keywords']
tfidf_features = {}
for feature in features:
    vec = TfidfVectorizer()
    tfidf_matrix = vec.fit_transform(movies_df[feature])
    tfidf_features[feature] = tfidf_matrix

sequel_map = {
    "Iron Man": "Iron Man 2",
    "Iron Man 2": "Iron Man 3",
    "Batman Begins": "The Dark Knight",
    "The Dark Knight": "The Dark Knight Rises",
    "The Internship": "The Internship Games",
    "Rise of the Planet of the Apes": "Dawn of the Planet of the Apes",
    "Harry Potter and the Philosopher's Stone": "Harry Potter and the Chamber of Secrets",
    "Harry Potter and the Chamber of Secrets": "Harry Potter and the Prisoner of Azkaban",
    "Harry Potter and the Prisoner of Azkaban": "Harry Potter and the Goblet of Fire",
    "Harry Potter and the Goblet of Fire": "Harry Potter and the Order of the Phoenix",
    "Harry Potter and the Order of the Phoenix": "Harry Potter and the Half-Blood Prince",
    "Mission: Impossible": "Mission: Impossible II",
    "Mission: Impossible II": "Mission: Impossible III",
    "Mission: Impossible III": "Mission: Impossible - Ghost Protocol",
    "Mission: Impossible - Ghost Protocol": "Mission: Impossible - Rogue Nation",
    "The Matrix": "The Matrix Reloaded",
    "The Matrix Reloaded": "The Matrix Revolutions",
}

def boost_keyword_weight(user_weights, boost_factor=1.5):
    boosted_weights = {}
    for k, v in user_weights.items():
        if k == 'keywords':
            boosted_weights[k] = v * boost_factor
        else:
            boosted_weights[k] = v
    total = sum(boosted_weights.values())
    return {k: v / total for k, v in boosted_weights.items()}

def recommend_with_dynamic_weights(title, user_weights, top_n=10):
    if title not in movies_df['title'].values:
        return f"'{title}' not found in the dataset."

    idx = movies_df[movies_df['title'] == title].index[0]

    sequel_title = sequel_map.get(title)
    sequel_row = None
    if sequel_title and sequel_title in movies_df['title'].values:
        sequel_row = movies_df[movies_df['title'] == sequel_title].iloc[0]

    normalized_weights = boost_keyword_weight(user_weights, boost_factor=1.8)

    genre_sim = cosine_similarity(tfidf_features['genres'][idx], tfidf_features['genres'])[0]
    cast_sim = cosine_similarity(tfidf_features['cast'][idx], tfidf_features['cast'])[0]
    director_sim = cosine_similarity(tfidf_features['director'][idx], tfidf_features['director'])[0]
    keyword_sim = cosine_similarity(tfidf_features['keywords'][idx], tfidf_features['keywords'])[0]
    popularity_values = movies_df['popularity'].values

    year_diff = movies_df['release_date'].apply(lambda x: abs(int(x[:4]) - int(movies_df['release_date'][idx][:4])))
    year_sim = np.exp(-(year_diff**2)/(2 * 5**2)).values

    similarity_score = (
        normalized_weights.get('genre', 0) * genre_sim +
        normalized_weights.get('cast', 0) * cast_sim +
        normalized_weights.get('director', 0) * director_sim +
        normalized_weights.get('keywords', 0) * keyword_sim +
        normalized_weights.get('year', 0) * year_sim
    )

    normalized_popularity = (popularity_values - popularity_values.min()) / (popularity_values.max() - popularity_values.min())
    normalized_rating = (movies_df['vote_average'] - movies_df['vote_average'].min()) / (movies_df['vote_average'].max() - movies_df['vote_average'].min())
    score = similarity_score * (1 + 0.8 * normalized_popularity + 0.2 * normalized_rating)

    movies_df['score'] = score
    filtered_df = movies_df[(movies_df.index != idx) & (movies_df['vote_average'] >= 6.5)]
    result = filtered_df.sort_values(by='score', ascending=False)

    if sequel_row is not None:
        result = pd.concat([pd.DataFrame([sequel_row]), result[result['title'] != sequel_title]])

    return result.head(top_n)[['title', 'genres', 'vote_average', 'release_date', 'score']]
