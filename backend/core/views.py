from django.http import HttpResponse, JsonResponse

def home(request):
    return HttpResponse("AirGo backend operativo")

def health(request):
    return JsonResponse({"status": "ok"})
