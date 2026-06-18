from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Product

def api_get_products(request):
    category = request.GET.get('category')
    search = request.GET.get('search')
    
    products = Product.objects.all()
    
    if category:
        products = products.filter(category=category)
    if search:
        products = products.filter(name__icontains=search)
        
    data = []
    for p in products:
        data.append({
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "image": p.image,
            "category": p.category,
            "description": p.description,
        })
    return JsonResponse({"products": data})

def api_get_featured(request):
    products = Product.objects.all()[:4]
    data = [{"id": p.id, "name": p.name, "price": str(p.price), "image": p.image} for p in products]
    return JsonResponse({"featured": data})

@csrf_exempt
def api_save_order(request):
    if request.method == "POST":
        # Simplified order saving for demonstration without auth
        try:
            data = json.loads(request.body)
            # In a real API with auth, we would associate this with request.user
            return JsonResponse({"status": "success", "message": "Order placed via API!"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "method not allowed"}, status=405)
