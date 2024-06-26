from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests



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
            print("Track  not in data")

        return track_details    

    


# Create your views here.
@login_required(login_url='login')
def index(request):
    top_tracks_list = top_tracks()

    print(top_tracks_list)

    first_six = top_tracks_list[:6]
    second_six = top_tracks_list[6:12]
    third_six = top_tracks_list[12:18]

    artists_info = top_artists()
    print(artists_info)

    context = {
        'artists_info' : artists_info,
        'first_six': first_six,
        'second_six': second_six,
        'third_six' : third_six,
    }
    return render(request, 'index.html', context)

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
