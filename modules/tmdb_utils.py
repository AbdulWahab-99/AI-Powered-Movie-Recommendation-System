import requests

TMDB_API_KEY = "e8573ba8e0f5b955886ce85b955a56ec"  # Replace with your actual API key

def get_poster(movie_title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_title}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            poster_path = data['results'][0].get('poster_path')
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"  # notice the w500 size here!
    return None

def get_tmdb_id(movie_title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_title}"
    response = requests.get(url)
    if response.status_code == 200 and response.json()['results']:
        return response.json()['results'][0]['id']
    return None

def get_movie_cast(tmdb_id):
    if not tmdb_id:
        return "Cast not available"
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        cast_data = response.json().get('cast', [])
        cast_names = [member['name'] for member in cast_data[:10]]  # Top 10 cast members
        return ', '.join(cast_names) if cast_names else "Cast not available"
    return "Cast not available"


