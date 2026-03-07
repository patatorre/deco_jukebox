
import requests
import os
import time



def search_discogs_artist(artist_name, token):
    url = "https://api.discogs.com/database/search"
    headers = {
        'User-Agent': 'YourApp/1.0',
        'Authorization': f'Discogs token={token}'
    }
    params = {
        'q': artist_name,
        'type': 'artist',
        'per_page': 1
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()


def get_release_genres_and_year(release_id, token):
    url = f"https://api.discogs.com/releases/{release_id}"
    headers = {
        'User-Agent': 'YourApp/1.0',
        'Authorization': f'Discogs token={token}'
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    genres = data.get('genres', [])
    #styles = data.get('styles', [])
    year = data.get('year')  # may be None if not present

    return genres, year


def get_artist_releases(artist_id, token, per_page=50):
    url = f"https://api.discogs.com/artists/{artist_id}/releases"
    headers = {
        'User-Agent': 'YourApp/1.0',
        'Authorization': f'Discogs token={token}'
    }
    params = {
        'per_page': per_page,
        'page': 1
    }
    all_releases = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        releases = data.get('releases', [])
        all_releases.extend(releases)

        # Pagination: check if there's a next page
        if not data.get('pagination', {}).get('urls', {}).get('next'):
            break
        params['page'] += 1
        time.sleep(0.2)  # be kind to the API

    return all_releases


def get_release_id_by_artist_and_album(artist_name, album_name, token):
    """
    Search Discogs for a release ID using artist name and album title.

    Args:
        artist_name (str): Name of the artist
        album_name (str): Name of the album/release
        token (str): Discogs user token

    Returns:
        int or None: The release ID if found, None otherwise
    """
    # Build search URL with filters
    url = "https://api.discogs.com/database/search"

    headers = {
        'User-Agent': 'YourGenreFetcher/1.0 +http://yourapp.example.com',  # Required!
        'Authorization': f'Discogs token={token}'
    }

    params = {
        'type': 'release',  # Only search releases
        'artist': artist_name,  # Filter by artist
        'release_title': album_name,  # Filter by album title
        'per_page': 5  # Get top 5 matches
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        results = data.get('results', [])

        if not results:
            print(f"No releases found for {artist_name} - {album_name}")
            return None

        # Display matches to help with selection
        print(f"Found {len(results)} potential matches:")
        for i, result in enumerate(results):  # Show first 3
            print(f"  {i + 1}. {result.get('title')} (Year: {result.get('year', 'N/A')})")

        # Select a release that has the earliest release date
        earliest_release_date = 6666
        best_idx = 0
        for idx, result in enumerate(results):
            year = int(result.get('year', '0'))
            if year > 0 :
                if year < earliest_release_date:
                    earliest_release_date = year
                    best_idx = idx
        best_match = results[best_idx]
        release_id = best_match.get('id')

        if release_id:
            print(f"Selected release ID: {release_id}")
            return release_id
        else:
            print("No ID found in result")
            return None

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


# Example usage with your existing genre-fetching function
def get_genres_for_album(artist_name, album_name, token):
    """Get genres for a specific album by artist and title."""
    release_id = get_release_id_by_artist_and_album(artist_name, album_name, token)

    if release_id:
        # Use your existing get_release_genres function
        genres, year = get_release_genres_and_year(release_id, token)
        return {
            'artist': artist_name,
            'album': album_name,
            'genre': genres[0],
            'year': year
        }
    return None


def get_album_genre_and_year(artist_name, album_name):
    discogs_token = os.getenv('DISCOGS_PERSONAL_TOKEN')
    result = get_genres_for_album(artist_name, album_name, discogs_token)
    if result:
        return result['genre'], result['year']
    else:
        return 'unknown', '1066'

# Test routine if run as main
if __name__ == "__main__":
    discogs_token = os.getenv('DISCOGS_PERSONAL_TOKEN')
    #print(discogs_token)
    artist_name = 'Daft Punk'
    album_name = 'Random Access Memories'

    result = get_genres_for_album('Daft Punk', 'Random Access Memories', discogs_token)
    if result:
        print(f"Genre: {result['genre']}")
        print(f"year: {result['year']}")

    # search_result = search_discogs_artist(artist_name, discogs_token)
    # artist_id = search_result['results'][0]['id']  # get the first match's ID
    # print(f"{artist_name} Artist ID: {artist_id}")
    # releases = get_artist_releases(artist_id, discogs_token)
    # for release in releases[:5]:   # look at first 5 releases
    #     genres, styles = get_release_genres(release['id'], discogs_token)
    #     print(f"Release: {release['title']} (ID: {release['id']}) genres = {genres}, styles = {styles}")

