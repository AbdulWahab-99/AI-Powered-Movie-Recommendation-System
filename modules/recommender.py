import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

# Load data
ratings = pd.read_csv("Cleaned Datasets/movielens.csv")
avg_ratings = ratings.groupby('movie_id')['rating'].mean().reset_index()
avg_ratings.rename(columns={'rating': 'avg_rating'}, inplace=True)

movies = pd.read_csv("Cleaned Datasets/cleaned_movies.csv")
movies = movies.merge(avg_ratings, on='movie_id', how='left')

data = pd.read_csv("Cleaned Datasets/movielens.csv")

# --- Collaborative Filtering (CF) Similarity ---
user_item_matrix = data.pivot_table(index='user_id', columns='movie_id', values='rating')
user_item_matrix.fillna(0, inplace=True)
item_similarity = cosine_similarity(user_item_matrix.T)
item_similarity_df = pd.DataFrame(item_similarity, index=user_item_matrix.columns, columns=user_item_matrix.columns)

# --- Content-Based Filtering (CB) Similarity ---
genre_cols = [col for col in movies.columns if col.startswith('genre_')]
genre_similarity = cosine_similarity(movies[genre_cols])
genre_similarity_df = pd.DataFrame(genre_similarity, index=movies['movie_id'], columns=movies['movie_id'])

# --- Normalize both matrices ---
scaler = MinMaxScaler()
collab_norm = scaler.fit_transform(item_similarity_df)
genre_norm = scaler.fit_transform(genre_similarity_df)
collab_norm_df = pd.DataFrame(collab_norm, index=item_similarity_df.index, columns=item_similarity_df.columns)
genre_norm_df = pd.DataFrame(genre_norm, index=genre_similarity_df.index, columns=genre_similarity_df.columns)

# --- Hybrid Similarity ---
hybrid_similarity_df = (0.6 * collab_norm_df) + (0.4 * genre_norm_df)

# --- Hybrid Recommendation Function ---
def hybrid_recommend(movie_id, hybrid_df, n_recommendations=5):
    similar_scores = hybrid_df[movie_id].sort_values(ascending=False)
    similar_scores = similar_scores.drop(movie_id)
    top_movie_ids = similar_scores.head(n_recommendations).index.tolist()
    return top_movie_ids

# --- Genre + Mood Recommendation Function ---
def recommend_by_genre_mood(genre, mood=None, n=5):
    genre = genre.lower().strip()

    # Filter movies based on the provided genre
    genre_cols = [col for col in movies.columns if col.startswith('genre_')]
    genre_col = None
    for col in genre_cols:
        genre_name = GENRE_MAP.get(col.replace('genre_', ''), '').lower()
        if genre == genre_name:
            genre_col = col
            break

    if not genre_col:
        return f"⚠️ Genre '{genre}' not found. Please try another genre."

    filtered = movies[movies[genre_col] == 1]

    # Mood-based sorting logic
    if mood:
        mood = mood.lower()
        if mood in ["happy", "excited", "fun", "uplifting"]:
            filtered = filtered.sort_values(by="avg_rating", ascending=False)
        elif mood in ["dark", "sad", "serious", "emotional"]:
            filtered = filtered.sort_values(by="avg_rating", ascending=True)
        else:
            filtered = filtered.sort_values(by="avg_rating", ascending=False)
    else:
        filtered = filtered.sort_values(by="avg_rating", ascending=False)

    recommendations = filtered.head(n)

    # Format the output
    results = []
    for _, row in recommendations.iterrows():
        genres = get_movie_genres(row)
        formatted = f"🎬 **{row['title']}**\n   Genres: {genres}\n   Rating: ⭐ {row['avg_rating']:.1f}"
        results.append(formatted)

    return "\n\n".join(results)


# --- Genre Mapping ---
GENRE_MAP = {
    '0': 'unknown',
    '1': 'Action',
    '2': 'Adventure',
    '3': 'Animation',
    '4': "Children's",
    '5': 'Comedy',
    '6': 'Crime',
    '7': 'Documentary',
    '8': 'Drama',
    '9': 'Fantasy',
    '10': 'Film-Noir',
    '11': 'Horror',
    '12': 'Musical',
    '13': 'Mystery',
    '14': 'Romance',
    '15': 'Sci-Fi',
    '16': 'Thriller',
    '17': 'War',
    '18': 'Western'
}

def get_movie_genres(movie_row):
    genre_cols = [col for col in movie_row.index if col.startswith('genre_')]
    genre_ids = [col.replace('genre_', '') for col in genre_cols if movie_row[col] == 1]
    genres = [GENRE_MAP[gid] for gid in genre_ids if gid in GENRE_MAP]
    return ', '.join(genres)
