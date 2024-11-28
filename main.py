import requests
from collections import Counter
from reactpy import component, html, hooks, run

cdn_1 = html.link(
    {
        "href": "https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css",
        "rel": "stylesheet",
    }
)

# Función de recomendación
def recomendar_animes(usuario):
    if not usuario.strip():  # Verificar que el usuario no esté vacío
        return {"animes": [{"title": "Por favor, ingresa un nombre de usuario válido.", "image_url": None}], "genres": []}

    try:
        # Obtener animes populares
        response_animes = requests.get("https://api.jikan.moe/v4/top/anime")
        if response_animes.status_code != 200:
            return {"animes": [{"title": "Error al obtener animes populares.", "image_url": None}], "genres": []}
        animes = response_animes.json()

        # Obtener datos del usuario desde la API
        response_user = requests.get(f"https://api.jikan.moe/v4/users/{usuario}/full")
        if response_user.status_code != 200:
            return {"animes": [{"title": f"Error al obtener datos del usuario '{usuario}'.", "image_url": None}], "genres": []}

        # Obtener favoritos del usuario
        favorites_url = f"https://api.jikan.moe/v4/users/{usuario}/favorites"
        response_favorites = requests.get(favorites_url)
        if response_favorites.status_code != 200:
            return {"animes": [{"title": f"Error al obtener los favoritos del usuario '{usuario}'.", "image_url": None}], "genres": []}
        favorites = response_favorites.json()
        favorite_ids = [fav['mal_id'] for fav in favorites['data']['anime']]

        # Buscar géneros de los favoritos del usuario
        user_genres = []
        for fav_id in favorite_ids:
            anime_url = f"https://api.jikan.moe/v4/anime/{fav_id}"
            response_anime = requests.get(anime_url)
            if response_anime.status_code == 200:
                anime_data = response_anime.json()
                genres = anime_data['data'].get('genres', [])
                user_genres.extend([genre['name'] for genre in genres])

        # Calcular géneros más comunes
        genre_counts = Counter(user_genres)
        max_frequency = max(genre_counts.values()) if genre_counts else 0
        relative_threshold = max(1, int(max_frequency * 0.6))
        filtered_genres = [genre for genre, count in genre_counts.items() if count >= relative_threshold]

        # Buscar animes populares con géneros comunes
        recommended_animes = []
        for popular_anime in animes['data']:
            anime_genres = [genre['name'] for genre in popular_anime.get('genres', [])]
            if any(genre in filtered_genres for genre in anime_genres):
                recommended_animes.append({
                    "title": popular_anime['title'],
                    "image_url": popular_anime['images']['jpg']['image_url'],
                    "genres": anime_genres,
                })

        # Obtener todos los géneros únicos recomendados
        all_genres = set(genre for anime in recommended_animes for genre in anime['genres'])

        return {
            "animes": recommended_animes if recommended_animes else [{"title": "No se encontraron recomendaciones.", "image_url": None}],
            "genres": list(all_genres)
        }
    except Exception as e:
        return {"animes": [{"title": f"Error inesperado: {str(e)}", "image_url": None}], "genres": []}

# Componente principal
@component
def App():
    usuario, set_usuario = hooks.use_state("")  # Estado para el nombre de usuario
    recomendaciones, set_recomendaciones = hooks.use_state({"animes": [], "genres": []})

    def obtener_recomendaciones(event=None):
        if usuario.strip():
            resultado = recomendar_animes(usuario)
            set_recomendaciones(resultado)
        else:
            set_recomendaciones({"animes": [{"title": "Please enter a valid username.", "image_url": None}], "genres": []})

    return html.div(
        {
            "className": "w-screen h-full",
            "style": {"backgroundColor": "rgb(255, 255, 255)"},  # Fondo blanco
        },
        cdn_1,
        # Encabezado
        html.div(
            {"className": "w-full bg-black flex items-center"},
            html.img(
                {
                    "src": "https://cdn.myanimelist.net/images/app_lp/applogo.png",
                    "alt": "MyAnimeList Logo",
                    "className": "w-48 h-16",
                }
            ),
            html.div(
                {"className": "w-full h-full flex items-center justify-center space-x-4"},
                html.h1({"className": "mr-64 text-3xl text-white font-bold"}, "Anime Recommender"),
            ),
        ),
        # Formulario
        html.div(
            {"className": "mt-12 p-4 w-full h-auto", "style": {"color": "black"}},
            html.div(
                {"className": "flex items-center justify-center space-x-4"},
                html.label({"className": "text-black font-bold text-xl"}, "Username: "),
                html.input(
                    {
                        "className": "text-black bg-white rounded-full border-2 border-gray-500 p-2 shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-red-500 transition-all duration-300",
                        "type": "text",
                        "value": usuario,
                        "on_change": lambda event: set_usuario(event["target"]["value"]),
                    }
                ),
                html.button(
                    {
                        "on_click": obtener_recomendaciones,
                        "className": "bg-black text-white rounded px-4 py-2 mx-5 hover:bg-gray-600",
                    },
                    "Get Recommendations",
                ),
            ),
            # Título de géneros
            html.h2({"className": "text-2xl text-black mt-5 font-bold"}, "Genres:"),
            html.div(
                {"className": "flex flex-wrap justify-start mt-4 space-x-2"},
                [
                    html.div(
                        {
                            "className": "bg-gray-200 text-black rounded px-3 py-1 m-1",
                        },
                        genre
                    )
                    for genre in recomendaciones["genres"]
                ],
            ),
            # Título de recomendaciones
            html.h2({"className": "text-3xl text-black mt-5 font-bold"}, "Recommendations:"),
            html.div(
                {"className": "flex flex-wrap justify-start mt-4"},
                [
                    html.div(
                        {
                            "className": " bg-gray-200 shadow-lg hover:shadow-xl w-44 h-auto p-3 rounded shadow-md m-2 flex flex-col items-center",
                        },
                        html.img({"src": anime["image_url"], "alt": anime["title"], "className": "w-32 h-48 rounded"}) if anime["image_url"] else None,
                        html.p({"className": "mt-2 text-center text-black"}, anime["title"]),
                    )
                    for anime in recomendaciones["animes"]
                ],
            ),
        ),
    )

# Ejecutar la aplicación
run(App)
