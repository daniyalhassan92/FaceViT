from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .models import Video,VideoEmotions, VideoReport
from .models import Video
from django.conf import settings
from .inference import predict
from .reportgenerator import reportgeneratorGPT
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

def homePage(request):
    if request.user.is_authenticated:
        return render(request,"home.html")
    else:
        return redirect('signin')
def aboutUs(request):
    return HttpResponse("About Us")
def upload(request):
    return HttpResponse("upload")

def signin(request):
    context = {"message": ""}
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            context["message"] = "Username or Password is not correct!!!"

    return render(request, 'signin.html', context)


def signout(request):
    logout(request)
    return redirect('signin')


from django.shortcuts import render, redirect
from django.contrib.auth.models import User

def signup(request):
    context = {"message": ""}
    
    if request.method == 'POST':
        uname = request.POST.get('username')
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')
        
        if pass1 != pass2:
            context["message"] = "Passwords do not match!"
        else:
            if User.objects.filter(username=uname).exists() or User.objects.filter(email=email).exists():
                context["message"] = "Username or email already exists!"
            else:
                my_user = User.objects.create_user(uname, email, pass1)

                my_user.first_name = fname
                my_user.last_name = lname
                my_user.save()

                return redirect('signin')
    
    return render(request, 'signup.html', context)


from django.shortcuts import render, redirect, get_object_or_404
import os

def view_videos(request):
    if request.method == 'POST':
        video_id = request.POST.get('delete_video')
        if video_id:
            video = get_object_or_404(Video, id=video_id)
            
            try:
                file_path = video.video_file.path

                video.delete()

                os.remove(file_path)
                
                return redirect('view_videos')
            except Exception as e:
                print(f"Error: {e}")

    videos = Video.objects.all()
    return render(request, 'view_videos.html', {'videos': videos})



from django.shortcuts import render, redirect
def upload_video(request):
    if request.method == 'POST':
        video_title = request.POST.get('video_title')
        video_tags = request.POST.get('video_tags')
        video_description = request.POST.get('video_description')
        video_file = request.FILES.get('video_file')

        Video.objects.create(
            title=video_title,
            tags=video_tags,
            description=video_description,
            video_file=video_file
        )
        return redirect('view_videos')  

    return render(request, 'uploadVideos.html')




def generateReport(request):

    if request.user.is_authenticated and request.user.is_superuser:
    
        videos_reported = VideoReport.objects.all().values_list('video_id', flat=True)
        videos = Video.objects.filter(id__in=videos_reported)
        context = {
            'MEDIA_URL': settings.MEDIA_URL,
            'videos': videos
        }

        
        return render(request,'generateReport.html', context)

    
    elif not request.user.is_superuser:
        return redirect('access_denied')
    else:
        return redirect('adminsignin')




def generatereport(request):
    if request.method == 'POST':
        video_id = request.POST.get('video_id')

        # Check if report exists in the database
        report = VideoReport.objects.filter(video_id=video_id).first()

        if report and report.report:
            # If report exists in the database, return it
            return JsonResponse({'report': report.report})
        else:
            # If report doesn't exist, call GPT API to generate report
            video = Video.objects.get(id=video_id)
            emotions_and_timestamp = VideoEmotions.objects.filter(video=video).values_list('emotions_and_timestamp', flat=True)
            tags = video.tags
            # print(emotions_and_timestamp)
            # print(tags)
            # return JsonResponse({'emotions_and_timestamp': list(emotions_and_timestamp), 'tags': list(tags)})
            # return JsonResponse({'emotions_and_timestamp': list(emotions_and_timestamp)})
            generated_report = reportgeneratorGPT(tags, emotions_and_timestamp)
            
            if generated_report:
                
                video_report = VideoReport.objects.get(video_id=video_id)

                # Update the generated_report attribute
                video_report.report = generated_report

                # Save the changes to the database
                video_report.save()

                # print(generated_report)
                return JsonResponse({'report': generated_report})
            else:
                # If report generation fails, return an error response
                return JsonResponse({'error': 'Failed to generate report'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)





def emotionCapture(request):
    
    # if request.user.is_authenticated and request.user.is_superuser:
    
    videos = Video.objects.all()
    context = {
        'MEDIA_URL': settings.MEDIA_URL,
        'videos': videos
    }
    return render(request,'emotionCapture.html', context)

    # elif not request.user.is_superuser:
    #     return redirect('access_denied')
    # else:
    #     return redirect('adminsignin')


def prediction(request):
    if request.method == 'POST':
        video_chunks = [request.FILES[key] for key in request.FILES if key.startswith('video_chunk_')]
        
        uploaded_file = request.FILES.get('video')
        width = request.POST.get('width')
        videoduration = request.POST.get('videoduration')
        # print(videoduration)
        height = request.POST.get('height')
        video_id=request.POST.get('id')
        results = predict(video_chunks, width, height,videoduration)
        results = {"emotions_and_timestamp": results}
        # print(results)
        video_emotions, created = VideoEmotions.objects.get_or_create(video_id=video_id)
        video_report, created = VideoReport.objects.get_or_create(video_id=video_id)
        if(results):
            video_emotions.emotions_and_timestamp = results
            video_emotions.save()

        return JsonResponse(results)
    else:
        return render(request, 'upload.html')


def adminsignin(request):
    context={"message":""}
    if request.method=='POST':
        username=request.POST.get('username')
        pass1=request.POST.get('pass')
        user=authenticate(request,username=username,password=pass1)
        if user is not None and user.is_superuser:
            login(request,user)
            return redirect('emotion_capture')
        elif not user.is_superuser:
            context["message"]="You are not authorized to view the page!!!"
        else:
            context["message"]="Username or Password is not correct!!!"

    return render (request,'adminsignin.html',context)


def unauthorized_access_handler(request):
    return render(request, 'accessDenied.html', {'message': 'Access Denied'})
