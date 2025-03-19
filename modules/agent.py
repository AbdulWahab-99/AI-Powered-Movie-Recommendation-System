# modules/agent.py

import os
import re
import difflib
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import StructuredTool, Tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from modules.recommender import hybrid_recommend, recommend_by_genre_mood, movies, hybrid_similarity_df

# Set your Gemini API key securely
os.environ["GOOGLE_API_KEY"] = "AIzaSyAjSx7bc2GbL_WOnCv-wysJNil0nLreFSg"

# ===== Tool: Hybrid Movie Recommender =====
def recommend_movies(movie_title: str, n: int = None):
    try:
        if n is None:
            n_search = re.search(r'\b(\d+)\b', movie_title)
            if n_search:
                n = int(n_search.group(1))
                movie_title = re.sub(r'\b\d+\b', '', movie_title).strip()
            else:
                n = 5

        all_titles = movies['title'].tolist()
        lower_titles = [t.lower() for t in all_titles]
        movie_title_lower = movie_title.lower()

        closest_matches = difflib.get_close_matches(movie_title_lower, lower_titles, n=1, cutoff=0.6)

        if not closest_matches:
            return f"Sorry, I couldn't find the movie '{movie_title}' in the database."

        matched_index = lower_titles.index(closest_matches[0])
        matched_title = all_titles[matched_index]

        movie_row = movies[movies['title'] == matched_title]
        movie_id = movie_row.iloc[0]['movie_id']

        recommended_ids = hybrid_recommend(movie_id, hybrid_similarity_df, n_recommendations=n)
        recommended_titles = movies[movies['movie_id'].isin(recommended_ids)]['title'].tolist()

        # Save context
        memory.save_context(
            {"input": movie_title},
            {
                "output": f"Recommended {n} movie(s) for {matched_title}",
                "last_movie": matched_title,
                "last_recommend_count": n,
                "last_genre": None
            }
        )

        return f"I recommend {n} movie(s) based on '{matched_title}': {', '.join(recommended_titles)}"
    except Exception as e:
        return f"Error: {str(e)}"

recommend_tool = StructuredTool.from_function(
    func=recommend_movies,
    name="recommend_movies",
    description="Recommend similar movies based on a movie title",
)

# ===== Tool: Genre & Mood Based =====
def recommend_by_genre_mood_tool(genre: str, mood: Optional[str] = None, n: int = 5):
    if not mood:
        mood = "any"
    
    recommendations = recommend_by_genre_mood(genre, mood, n)
    
    if recommendations:
        formatted = "\n".join([f"- {movie}" for movie in recommendations])
        response = f"Here are {n} {genre} movie(s) I recommend:\n{formatted}"
    else:
        response = f"Sorry, I couldn't find any {genre} movies for that mood."

    memory.save_context(
        {"input": f"{genre}" if mood == "any" else f"{genre} and {mood}"},
        {
            "output": f"Recommended {n} movies for genre {genre}" if mood == "any" else f"Recommended {n} movies for genre {genre} and mood {mood}",
            "last_genre": genre,
            "last_movie": None,
            "last_recommend_count": n
        }
    )
    return response



recommend_genre_tool = StructuredTool.from_function(
    func=recommend_by_genre_mood_tool,
    name="recommend_by_genre_mood",
    description="Recommend movies based on a genre and mood."
)

# ===== Gemini Chat Model =====
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.4
)

# ===== Memory =====
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    input_key="input",
    output_key="output",
    additional_memory_keys=["last_movie", "last_recommend_count", "last_genre"]
)

# ===== Prompt Template =====
prompt = ChatPromptTemplate.from_template("""
You are a friendly and helpful movie assistant.

First, acknowledge the user's request in a conversational tone (e.g., "Sure, let me find some great options for you!").

Then, decide which tool to use depending on whether the user is asking for:
- Movies similar to a specific movie (use 'recommend_movies')
- Movies based on genres and mood (use 'recommend_by_genre_mood')

Behavior guidelines:
- If the user asks for movies by genre only (e.g., "horror movies"), use the 'recommend_by_genre_mood' tool with just the genre (leave mood as None).
- If the user specifies both genre and mood (e.g., "thrilling horror movies" or "feel-good comedy"), use both genre and mood for recommendations.
- If the user says "Give me more like that", use memory values:
    - last_movie
    - last_genre
    - last_recommend_count
- If nothing matches, politely ask for clarification.

Formatting:
- Always respond with a simple and friendly list of movie titles (avoid asking unnecessary questions).
- Keep the response concise and easy to read.

You are designed to be conversational, helpful, and efficient!

Chat history:
{chat_history}

User input:
{input}

Memory:
- last_movie: {last_movie}
- last_genre: {last_genre}
- last_recommend_count: {last_recommend_count}

{agent_scratchpad}
""")

# ===== Create Agent =====
agent = create_openai_functions_agent(
    llm=llm,
    tools=[recommend_tool, recommend_genre_tool],
    prompt=prompt
)

# ===== Executor =====
agent_chain = AgentExecutor(
    agent=agent,
    tools=[recommend_tool, recommend_genre_tool],
    memory=memory,
    verbose=True
)
    