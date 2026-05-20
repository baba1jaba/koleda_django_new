from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Avg, Q 
from django.db import transaction 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash  

from .models import Product, Comment, OrderItem, ProductVariant, Brand, ScentType, Order, Profile  
from .cart import Cart
from .forms import OrderCreateForm, CommentForm, UserProfileForm

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
    if not request.user.is_authenticated:
        return redirect('login') 

    cart = Cart(request)
    user = request.user

    if not cart or len(cart) == 0:
        messages.error(request, "Ваша корзина пуста! Добавьте товары, прежде чем оформлять заказ.")
        return redirect('cart_detail')

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
                    order.user = user
                    order.total_price = cart.get_total_price()
                    order.save()

                    user.first_name = form.cleaned_data.get('first_name')
                    user.last_name = form.cleaned_data.get('last_name')
                    user.save()

                    profile, created = Profile.objects.get_or_create(user=user)
                    profile.phone = order.phone      
                    profile.address = order.address  
                    profile.save()

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
        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        
        if hasattr(user, 'profile'):
            if user.profile.phone:
                initial_data['phone'] = user.profile.phone
            if user.profile.address:
                initial_data['address'] = user.profile.address

        form = OrderCreateForm(initial=initial_data)
    
    return render(request, 'shop/order_checkout.html', {'cart': cart, 'form': form})

def cart_remove(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    cart.remove(variant) 
    return redirect('cart_detail')

def about_page(request):
    return render(request, 'shop/about.html')

@login_required
def profile_view(request):
    user = request.user
    
    
    profile, created = Profile.objects.get_or_create(user=user)
    
    
    if user.is_staff and request.method == 'POST' and 'update_status' in request.POST:
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()
        messages.success(request, f"Статус заказа #{order.id} успешно обновлен.")
        return redirect('profile')

    
    if request.method == 'POST' and 'update_profile' in request.POST:
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            
           
            profile.phone = form.cleaned_data.get('phone')
            profile.address = form.cleaned_data.get('address')
            profile.save()

            new_password = form.cleaned_data.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user) 
                messages.success(request, "Личные данные и пароль успешно изменены.")
            else:
                messages.success(request, "Личные данные успешно сохранены.")
                
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)
        form.fields['phone'].initial = profile.phone
        form.fields['address'].initial = profile.address

    if user.is_staff:
        orders = Order.objects.all().prefetch_related('items__product_variant__product__brand').order_by('-created_at')
    else:
        orders = Order.objects.filter(user=user).prefetch_related('items__product_variant__product__brand').order_by('-created_at')

    context = {
        'form': form,
        'orders': orders,
        'order_statuses': Order.STATUS_CHOICES if hasattr(Order, 'STATUS_CHOICES') else []
    }
    return render(request, 'registration/profile.html', context)

@login_required
def order_repeat(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart = Cart(request)
    added_any = False
    
    for item in order.items.all().select_related('product_variant__product__brand'):
        variant = item.product_variant
        
        if variant.stock > 0:
            quantity_to_add = min(item.quantity, variant.stock)
            cart.add(variant=variant, quantity=quantity_to_add, override_quantity=False)
            added_any = True
        else:
            messages.warning(
                request, 
                f"Товар '{variant.product.brand.name} - {variant.product.name}' сейчас отсутствует на складе и не был добавлен."
            )
            
    if added_any:
        messages.success(request, "Товары из заказа успешно перенесены в корзину!")
        return redirect('cart_detail')
    else:
        messages.error(request, "К сожалению, ни одного товара из этого заказа сейчас нет в наличии.")
        return redirect('profile')