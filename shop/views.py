from django.shortcuts import render, get_object_or_404,redirect
from .models import Product
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from .cart import Cart
from .models import ProductVariant
from .forms import OrderCreateForm
from .models import OrderItem, ProductVariant

def product_list(request):
    products = Product.objects.all()
    return render(request, 'shop/product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {'product': product})

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

            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            
            order.total_price = cart.get_total_price()
            order.save()

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product_variant=item['variant'],
                    quantity=item['quantity']
                )
            
            cart.clear()
            return render(request, 'shop/order_created.html', {'order': order})
    else:
        form = OrderCreateForm()
    
    return render(request, 'shop/order_checkout.html', {'cart': cart, 'form': form})