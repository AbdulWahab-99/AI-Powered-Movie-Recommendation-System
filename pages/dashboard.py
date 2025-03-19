import streamlit as st
import pandas as pd
import re
from modules.recommender import hybrid_recommend, hybrid_similarity_df, movies, get_movie_genres
from modules.sentiment import predict_sentiment
from modules.tmdb_utils import get_poster, get_tmdb_id, get_movie_cast
from modules.agent import agent_chain, memory 

# ===== Streamlit Page Config =====
st.set_page_config(
    page_title="Movie Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hides the sidebar navigation completely
hide_menu = """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_menu, unsafe_allow_html=True)

# ===== AUTH PROTECTION =====
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    # st.stop()
    st.switch_page("app.py")
    st.rerun()

# ===== Main Dashboard =====
st.title("🎥 Movie Recommendation Dashboard")


# ======= Styling =======
st.markdown("""
    <style>
    .card {
        background-color: #141414;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        color: white;
        transition: transform 0.2s;
    }
    .card:hover {
        transform: scale(1.03);
        box-shadow: 0 6px 20px rgba(0,0,0,0.5);
    }
    .card img {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ===== Split Layout =====
main_col, chat_col = st.columns([4, 1])

with main_col:
    tabs = st.tabs(["🏠 Home", "🔍 Search Movie", "📝 Sentiment Analysis"])

    def clean_title(title):
        return re.sub(r'\s*\(\d{4}\)', '', title).strip()

    # ===== Home Tab =====
    with tabs[0]:
        st.subheader("Recommended for you")
        default_movie_ids = movies['movie_id'].sample(6).tolist()
        cols = st.columns(3)
        for idx, movie_id in enumerate(default_movie_ids):
            movie = movies[movies['movie_id'] == movie_id].iloc[0]
            clean_movie_title = clean_title(movie['title'])

            # Loading spinner while fetching API data
            with st.spinner(f"Loading poster and cast for {clean_movie_title}..."):
                poster_url = get_poster(clean_movie_title)
                tmdb_id = get_tmdb_id(clean_movie_title)
                movie_cast = get_movie_cast(tmdb_id)
            genres = get_movie_genres(movie)    
            with cols[idx % 3]:
                st.markdown(f"""
                    <div class="card">
                    <h4>{movie['title']}</h4>
                    <img src="{poster_url}" width="100%" height="400">
                    <p><strong>Genres:</strong> {genres if genres else 'N/A'}</p>
                    <p><strong>Rating:</strong> {'⭐ ' + str(movie['avg_rating']) if pd.notnull(movie['avg_rating']) else 'N/A'}</p>
                    <p><strong>Cast:</strong> {movie_cast}</p>
                    </div>
                """, unsafe_allow_html=True)

    # ===== Search Movie Tab =====
    with tabs[1]:
        st.subheader("Search or Browse for a Movie to get Recommendations")
        search_query = st.text_input("Search for a movie (or leave blank to browse all)")
        if search_query:
            filtered_movies = movies[movies['title'].str.contains(search_query, case=False, na=False)]
        else:
            filtered_movies = movies
        selected_movie = st.selectbox("Select a movie", filtered_movies['title'].values if not filtered_movies.empty else ["No movies found"])

        if selected_movie and selected_movie != "No movies found":
            st.success(f"You selected: {selected_movie}")
            if selected_movie:
                movie_id = filtered_movies[filtered_movies['title'] == selected_movie]['movie_id'].values[0]
                recommended_ids = hybrid_recommend(movie_id, hybrid_similarity_df, n_recommendations=6)
                st.markdown(f"### 🎯 Recommendations based on **{selected_movie}**")
                cols = st.columns(3)
                for idx, rec_id in enumerate(recommended_ids):
                    movie = movies[movies['movie_id'] == rec_id].iloc[0]
                    clean_movie_title = clean_title(movie['title'])
                    with st.spinner(f"Loading poster and cast for {clean_movie_title}..."):
                        poster_url = get_poster(clean_movie_title)
                        tmdb_id = get_tmdb_id(clean_movie_title)
                        movie_cast = get_movie_cast(tmdb_id)
                    genres = get_movie_genres(movie)
                    with cols[idx % 3]:
                        st.markdown(f"""
                            <div class="card">
                            <h4>{movie['title']}</h4>
                            <img src="{poster_url}" width="100%" height="400">
                            <p><strong>Genres:</strong> {genres if genres else 'N/A'}</p>
                            <p><strong>Rating:</strong> {'⭐ ' + str(movie['avg_rating']) if pd.notnull(movie['avg_rating']) else 'N/A'}</p>
                            <p><strong>Cast:</strong> {movie_cast}</p>
                            </div>
                        """, unsafe_allow_html=True)
        else:
            st.warning("No movies found! Try another title.")

    # ===== Sentiment Tab =====
    with tabs[2]:
        st.subheader("Sentiment Analysis for Reviews")
        review = st.text_area("Enter a movie review")
        if st.button("Analyze Sentiment"):
            if review:
                sentiment, confidence = predict_sentiment(review)
                st.info(f"Sentiment: **{sentiment}** (Confidence: {confidence:.2f})")
            else:
                st.warning("Please enter a review first.")

    # ===== Footer =====
    st.markdown("""---<center>Made with ❤️ | Movie Recommender</center>""", unsafe_allow_html=True)

# ===== Chatbot Sidebar =====
with chat_col:
    st.markdown("""
        <style>
            .chat-container {
                display: flex;
                flex-direction: column;
                gap: 12px;
                padding: 10px;
                background: #141414;
                border-radius: 15px;
                box-shadow: 0 0 10px rgba(0,0,0,0.4);
                max-height: 80vh;
                overflow-y: auto;
            }
            .user-bubble {
                background: #333333;
                padding: 12px 18px;
                border-radius: 20px 20px 5px 20px;
                align-self: flex-end;
                color: white;
                max-width: 85%;
                word-wrap: break-word;
                font-family: 'Helvetica Neue', sans-serif;
                font-size: 14px;
                line-height: 1.4;
            }
            .bot-bubble {
                background: #e50914;
                padding: 12px 18px;
                border-radius: 20px 20px 20px 5px;
                align-self: flex-start;
                color: white;
                max-width: 85%;
                word-wrap: break-word;
                font-family: 'Helvetica Neue', sans-serif;
                font-size: 14px;
                line-height: 1.4;
            }
            .chat-container::-webkit-scrollbar {
                width: 6px;
            }
            .chat-container::-webkit-scrollbar-thumb {
                background: #e50914;
                border-radius: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h3 style='color: #e50914; text-align: center; margin-bottom: 0;'>🎬 Movies Bot</h3>", unsafe_allow_html=True)
    st.caption("Your personal movie recommender 🎥")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # User input FIRST
    user_query = st.chat_input("Ask me about movies...")

    if user_query and user_query.strip():
        # Add user message immediately
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        with st.spinner("🎯 Chatbot is finding the best picks..."):
            # Get agent response on same cycle
            memory_variables = memory.load_memory_variables({})
            response = agent_chain.invoke({
                "input": user_query,
                "chat_history": memory.chat_memory.messages,
                "last_movie": memory_variables.get("last_movie", ""),
                "last_genre": memory_variables.get("last_genre", ""),
                "last_recommend_count": memory_variables.get("last_recommend_count", "")
            })
            bot_reply = response.get('output', "Hmm... I'm not sure how to respond to that.")
            st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})

    # Render chat history AFTER processing both user & bot
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        role_class = "user-bubble" if msg['role'] == "user" else "bot-bubble"
        st.markdown(f'<div class="{role_class}">{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
