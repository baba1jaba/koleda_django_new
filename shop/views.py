from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Comment, OrderItem, ProductVariant, Brand, ScentType
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from .cart import Cart
from .forms import OrderCreateForm, CommentForm  
from django.db.models import Avg, Q 
from django.db import transaction 
from django.contrib import messages

def product_list(request):
    products = Product.objects.annotate(average_rating=Avg('comments__rating'))

    selected_brands = request.GET.getlist('brand')
    selected_scents = request.GET.getlist('scent')
    selected_genders = request.GET.getlist('gender') 
    rating_min = request.GET.get('rating_min')
    rating_max = request.GET.get('rating_max')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')


    if selected_brands:
        products = products.filter(brand_id__in=selected_brands)

   
    if selected_scents:
        if hasattr(Product, 'scent_type'):
            products = products.filter(scent_type_id__in=selected_scents)
        elif hasattr(Product, 'scent'):
            products = products.filter(scent_id__in=selected_scents)

   
    if selected_genders:
                products = products.filter(gender__in=selected_genders)

    
    if rating_min:
        products = products.filter(average_rating__gte=float(rating_min))
    if rating_max:
        products = products.filter(average_rating__lte=float(rating_max))

    
    if price_min:
        products = products.filter(variants__price__gte=price_min)
    if price_max:
        products = products.filter(variants__price__lte=price_max)

   
    products = products.distinct()

   
    all_brands = Brand.objects.filter(id__in=Product.objects.values_list('brand_id', flat=True).distinct())
    
    if hasattr(Product, 'scent_type'):
        all_scents = ScentType.objects.filter(id__in=Product.objects.values_list('scent_type_id', flat=True).distinct())
    elif hasattr(Product, 'scent'):
        all_scents = ScentType.objects.filter(id__in=Product.objects.values_list('scent_id', flat=True).distinct())
    else:
        all_scents = ScentType.objects.all()

    context = {
        'products': products,
        'brands': all_brands,
        'scent_types': all_scents,
        'selected_brands': [int(b) for b in selected_brands if b.isdigit()],
        'selected_scents': [int(s) for s in selected_scents if s.isdigit()],
        'selected_genders': selected_genders, 
        'rating_min': rating_min,
        'rating_max': rating_max,
        'price_min': price_min,
        'price_max': price_max,
    }
    return render(request, 'shop/product_list.html', context)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    comments = product.comments.all()  
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')  
            
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.product = product 
            comment.user = request.user 
            comment.save()
            return redirect('product_detail', pk=product.pk) 
    else:
        form = CommentForm()
        
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'comments': comments,
        'form': form
    })

class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

def cart_add(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    cart.add(variant=variant)
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart_detail.html', {'cart': cart})

def cart_add_detail(request, product_id):
    cart = Cart(request)
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id)
            cart.add(variant=variant)
    return redirect('cart_detail')

def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            
            for item in cart:
                variant = item['variant']
                quantity = item['quantity']
                if variant.stock < quantity:
                    messages.error(
                        request, 
                        f"К сожалению, товара '{variant.product.brand.name} - {variant.product.name} ({variant.volume} мл)' "
                        f"недостаточно на складе. Осталось: {variant.stock} шт."
                    )
                    return render(request, 'shop/order_checkout.html', {'cart': cart, 'form': form})

   
            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    if request.user.is_authenticated:
                        order.user = request.user
                    
                    order.total_price = cart.get_total_price()
                    order.save()

                    for item in cart:
                        variant = item['variant']
                        quantity = item['quantity']
                        
                  
                        variant.stock -= quantity
                        variant.save()
                        
                    
                        OrderItem.objects.create(
                            order=order,
                            product_variant=variant,
                            quantity=quantity,
                            price=variant.price
                        )
                    
                 
                    cart.clear()
                    
            except Exception as e:
                messages.error(request, f"Произошла ошибка при сохранении заказа: {e}")
                return render(request, 'shop/order_checkout.html', {'cart': cart, 'form': form})
            
            return render(request, 'shop/order_created.html', {'order': order})
    else:
        form = OrderCreateForm()
    
    return render(request, 'shop/order_checkout.html', {'cart': cart, 'form': form})