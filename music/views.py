from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
from bs4 import BeautifulSoup as bs
import re



# Create your views here.
def top_artists():
    
    
    url = "https://spotify-scraper.p.rapidapi.com/v1/chart/artists/top"
    
    querystring = {"type":"weekly"}
    
    headers = {
	"x-rapidapi-key": "420f087612msh2ab2f3663ca16f9p12fd4bjsn6e69cd71ebc7",
	"x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    
    response_data = response.json()

    artists_info = []

    if 'artists' in response_data:

        for artist in response_data['artists']:
            name = artist.get('name', 'No Name')
            avatar_url = artist.get('visuals', {}).get('avatar', [{}])[0].get('url', 'No URL')
            artist_id = artist.get('id', 'No ID')
            artists_info.append((name, avatar_url, artist_id))

    return artists_info

def top_tracks():
    url = "https://spotify-scraper.p.rapidapi.com/v1/chart/tracks/top"
    
    querystring = {"type":"weekly"}
    
    headers = {
	"x-rapidapi-key": "420f087612msh2ab2f3663ca16f9p12fd4bjsn6e69cd71ebc7",
	"x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    track_details = []

    if 'tracks' in data:
        shortened_data = data['tracks'][:18]

        # id, name, artist, cover url 
        for track in shortened_data:
            track_id = track['id']
            track_name = track['name']
            artist_name = track['artists'][0]['name'] if track['artists'] else None
            cover_url = track['album']['cover'][0]['url'] if track['album']['cover'] else None

            track_details.append({
                'id': track_id,
                'name': track_name,
                'artist': artist_name,
                'cover_url': cover_url
            })

    else:
        print("track not foun in response")

    return track_details



    
def get_audio_details(query):
    url = "https://spotify-scraper.p.rapidapi.com/v1/track/download"
    
    querystring = {"track":query}
    
    headers = {
	"x-rapidapi-key": "420f087612msh2ab2f3663ca16f9p12fd4bjsn6e69cd71ebc7",
	"x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    
    audio_details = []

    if response.status_code == 200:
        response_data = response.json()

        if 'youtubeVideo' in response_data and 'audio' in response_data['youtubeVideo']:
            audio_list = response_data['youtubeVideo']['audio']
            if audio_list:
                first_audio_url = audio_list[0]['url']
                duration_text = audio_list[0]['durationText']

                audio_details.append(first_audio_url)
                audio_details.append(duration_text)
            else:
                print("No audio data availble")
        else:
            print("No 'youtubeVideo' or 'audio' key found")
    else:
        print("Failed to fetch data")

    return audio_details
@login_required(login_url='login')
def index(request):
    artists_info = top_artists()
    top_track_list = top_tracks()

    # divide the list into three parts
    first_six_tracks = top_track_list[:6]
    second_six_tracks = top_track_list[6:12]
    third_six_tracks = top_track_list[12:18]

    print(top_track_list)
    context = {
        'artists_info' : artists_info,
        'first_six_tracks': first_six_tracks,
        'second_six_tracks': second_six_tracks,
        'third_six_tracks': third_six_tracks,
    }
    return render(request, 'index.html', context)

def get_track_image(track_id, track_name):
    url = 'https://open.spotify.com/track/'+track_id
    r = requests.get(url)
    soup = bs(r.content)
    image_links_html = soup.find('img', {'alt': track_name})
    if image_links_html:
        image_links = image_links_html['srcset']
    else:
        image_links = ''

    match = re.search(r'https:\/\/i\.scdn\.co\/image\/[a-zA-Z0-9]+ 640w', image_links)

    if match:
        url_640w = match.group().rstrip(' 640w')
    else:
        url_640w = ''

    return url_640w

def music(request, pk):
    track_id = pk
    url = "https://spotify-scraper.p.rapidapi.com/v1/track/metadata"
    
    querystring = {"trackId": track_id}

    headers = {
	"x-rapidapi-key": "420f087612msh2ab2f3663ca16f9p12fd4bjsn6e69cd71ebc7",
	"x-rapidapi-host": "spotify-scraper.p.rapidapi.com"}
    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        # extrack track_name, artist_name

        track_name = data.get("name")
        artists_list = data.get("artists", [])
        first_artist_name = artists_list[0].get("name") if artists_list else "No artist found"

        audio_details_query = track_name + first_artist_name
        audio_details = get_audio_details(audio_details_query)
        audio_url = audio_details[0]
        duration_text = audio_details[1]

        track_image = get_track_image(track_id, track_name)
        
        
        context = {
            'track_name': track_name,
            'artist_name': first_artist_name,
            'audio_url': audio_url,
            'duration_text': duration_text,
            'track_image': track_image,

        }
    
    return render(request, 'music.html', context)

def profile(request, pk):
    return render(request, 'profile.html')

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            # log user in 
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('login')
    return render(request, 'login.html')

def signup(request):
    if request.method == "POST":
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, "Email Has been Taken")
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, "Username Has been Taken")
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                # login user
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)
                return redirect("/")
        
        else:
            messages.info(request, 'Password Not Matching ....')
            return redirect('signup')
    
    else:
        return render(request, 'signup.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('login')
